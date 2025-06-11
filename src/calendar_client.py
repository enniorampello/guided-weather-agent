import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarClient:
    """Google Calendar API client with common operations."""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        """
        Initialize the Google Calendar client.

        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load the access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Handle Google Calendar API authentication."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars accessible to the authenticated user.

        Returns:
            List of calendar dictionaries with id, summary, and other properties
        """
        try:
            result = self.service.calendarList().list().execute()
            return result.get("items", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_primary_calendar_id(self) -> str:
        """Get the primary calendar ID."""
        return "primary"

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: List[str] = None,
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new calendar event.

        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
            calendar_id: Calendar ID to add event to

        Returns:
            Created event dictionary or None if failed
        """
        print(f"Creating event: {summary} from {start_time} to {end_time}")
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            result = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def list_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        List events from a calendar.

        Args:
            calendar_id: Calendar ID to list events from
            max_results: Maximum number of events to return
            time_min: Lower bound for event start time
            time_max: Upper bound for event start time

        Returns:
            List of event dictionaries
        """
        try:
            # Default to events from now
            if time_min is None:
                time_min = datetime.utcnow()

            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min.isoformat() + "Z",
                    timeMax=time_max.isoformat() + "Z" if time_max else None,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return events_result.get("items", [])

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific event by ID.

        Args:
            event_id: Event ID
            calendar_id: Calendar ID containing the event

        Returns:
            Event dictionary or None if not found
        """
        try:
            event = (
                self.service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )
            return event
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing event.

        Args:
            event_id: Event ID to update
            summary: New event title
            start_time: New event start datetime
            end_time: New event end datetime
            description: New event description
            location: New event location
            calendar_id: Calendar ID containing the event

        Returns:
            Updated event dictionary or None if failed
        """
        try:
            # Get existing event
            event = self.get_event(event_id, calendar_id)
            if not event:
                return None

            # Update fields if provided
            if summary is not None:
                event["summary"] = summary
            if description is not None:
                event["description"] = description
            if location is not None:
                event["location"] = location
            if start_time is not None:
                event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                }
            if end_time is not None:
                event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                }

            updated_event = (
                self.service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event)
                .execute()
            )
            return updated_event

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """
        Delete an event.

        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID containing the event

        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

    def search_events(
        self, query: str, calendar_id: str = "primary", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for events by text query.

        Args:
            query: Search query
            calendar_id: Calendar ID to search in
            max_results: Maximum number of events to return

        Returns:
            List of matching event dictionaries
        """
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    q=query,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return events_result.get("items", [])

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_events_for_date(
        self, date: datetime, calendar_id: str = "primary"
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific date.

        Args:
            date: Date to get events for
            calendar_id: Calendar ID to search in

        Returns:
            List of event dictionaries for the specified date
        """
        print(f"Getting events for date: {date}")
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self.list_events(
            calendar_id=calendar_id,
            time_min=start_of_day,
            time_max=end_of_day,
            max_results=100,
        )

    def create_recurring_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        recurrence_rule: str,
        description: str = "",
        location: str = "",
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """
        Create a recurring event.

        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            recurrence_rule: RRULE string (e.g., 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR')
            description: Event description
            location: Event location
            calendar_id: Calendar ID to add event to

        Returns:
            Created event dictionary or None if failed
        """
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
            "recurrence": [recurrence_rule],
        }

        try:
            result = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None


# Convenience functions for common operations
def create_calendar_client(
    credentials_file: str = "credentials.json", token_file: str = "token.json"
) -> GoogleCalendarClient:
    """Create and return a GoogleCalendarClient instance."""
    return GoogleCalendarClient(credentials_file, token_file)


def format_event_datetime(event: Dict[str, Any], field: str = "start") -> str:
    """
    Format event datetime for display.

    Args:
        event: Event dictionary
        field: Field to format ('start' or 'end')

    Returns:
        Formatted datetime string
    """
    dt_info = event.get(field, {})

    if "dateTime" in dt_info:
        dt = datetime.fromisoformat(dt_info["dateTime"].replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif "date" in dt_info:
        return dt_info["date"]
    else:
        return "Unknown"


def print_event_summary(event: Dict[str, Any]) -> None:
    """Print a summary of an event."""
    summary = event.get("summary", "No Title")
    start = format_event_datetime(event, "start")
    end = format_event_datetime(event, "end")
    location = event.get("location", "")

    print(f"Event: {summary}")
    print(f"Start: {start}")
    print(f"End: {end}")
    if location:
        print(f"Location: {location}")
    print("-" * 40)


if __name__ == "__main__":
    client = create_calendar_client()
    print(client.get_events_for_date(datetime.today()))
