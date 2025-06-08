#!/usr/bin/env python3
"""
Weather.com Agent

A streamlined agent that logs into weather.com, searches for a city,
and extracts current weather information using AI-powered location selection.
It can also add and remove cities from the favorites list.
"""

import time

# import os
import markdownify as md
from typing import Dict, List, Optional, Literal
from textwrap import dedent

from selenium import webdriver
from selenium.webdriver.common.by import By

# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import RemoteConnection

# from browserbase import Browserbase
from utils import setup_llm


class CustomRemoteConnection(RemoteConnection):
    _signing_key = None

    def __init__(self, remote_server_addr: str, signing_key: str):
        super().__init__(remote_server_addr)
        self._signing_key = signing_key

    def get_remote_connection_headers(self, parsed_url, keep_alive=False):
        headers = super().get_remote_connection_headers(parsed_url, keep_alive)
        headers.update({"x-bb-signing-key": self._signing_key})
        return headers


class WeatherAgent:
    """Automated weather agent for weather.com with AI-powered city selection."""

    def __init__(
        self, email: str, password: str, headless: bool = True, timeout: int = 10
    ):
        self.login_url = "https://weather.com/en-GB/login"
        self.headless = headless
        self.timeout = timeout
        self.email = email
        self.password = password
        self.bb = None
        self.session = None
        self.driver = self.setup_driver()

    def setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options."""
        options = webdriver.ChromeOptions()

        options.add_experimental_option(
            "prefs",
            {
                "profile.default_content_setting_values.geolocation": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.media_stream": 2,
            },
        )

        # Use Browserbase for remote WebDriver
        # self.bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

        # self.session = self.bb.sessions.create(
        #     project_id=os.environ["BROWSERBASE_PROJECT_ID"],
        #     region="eu-central-1",
        # )
        # custom_conn = CustomRemoteConnection(
        #     self.session.selenium_remote_url, self.session.signing_key
        # )
        # driver = webdriver.Remote(custom_conn, options=options)

        return webdriver.Chrome(options=options)

    def accept_cookies(self) -> None:
        """Accept cookies and consent management."""
        print("🔍 Accepting cookies...")

        try:
            # Handle privacy-mgmt.com iframe
            WebDriverWait(self.driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe[src*='privacy-mgmt.com']")
                )
            )

            # Look for accept/consent button within the iframe
            accept_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button[title*='Accept'], button[title*='accept'], button[aria-label*='Accept'], button[aria-label*='accept'], .sp_choice_type_11",
                    )
                )
            )
            accept_button.click()
            print("✅ Cookies accepted")

            # Switch back to main frame
            self.driver.switch_to.default_content()
        except Exception:
            # Switch back to main frame in case we're stuck in iframe
            self.driver.switch_to.default_content()
            print("ℹ️  Cookies iframe not found or handled")

    def login(self) -> None:
        """Login to weather.com."""
        print("🔐 Logging into weather.com...")

        try:
            # Navigate to login page
            self.driver.get(self.login_url)

            # Accept cookies/consent before interacting with page
            self.accept_cookies()

            time.sleep(2)

            # Find and fill email field
            email_field = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "loginEmail"))
            )
            email_field.clear()
            email_field.send_keys(self.email)

            # Find and fill password field
            password_field = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "loginPassword"))
            )
            password_field.clear()
            password_field.send_keys(self.password)

            # Find and click login button
            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            ).click()

            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.current_url != self.login_url
            )

            self.driver.get("https://weather.com/en-GB/")

            print("✅ Login successful!")
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            raise e

    def search_for_city(self, city_name: str) -> Optional[Dict]:
        # TODO: this function could be more efficient if we check that we are already on the correct page

        print(f"🔍 Searching for: {city_name}")

        try:
            print("Waiting for search bar to be available...")
            # Find search input
            search_input = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "headerSearch_LocationSearch_input"))
            )

            print("✅ Search bar found")

            # Click on the search input to focus it
            search_input.click()
            time.sleep(0.5)

            # Enter city name
            search_input.clear()
            search_input.send_keys(
                city_name
            )  # TODO: this could be improved by caching the ids of the cities that have been searched for

            print("🔍 Inserted city name")
            time.sleep(1)
            # Wait for the search results listbox to appear and contain at least one option
            WebDriverWait(self.driver, self.timeout, 1).until(
                lambda d: (
                    d.find_element(By.ID, "headerSearch_LocationSearch_listbox")
                    and len(
                        d.find_element(
                            By.ID, "headerSearch_LocationSearch_listbox"
                        ).find_elements(By.CSS_SELECTOR, "button[role='option']")
                    )
                    > 0
                )
            )

            print("🔍 Waiting for search results...")
            options = self.driver.find_element(
                By.ID, "headerSearch_LocationSearch_listbox"
            ).find_elements(By.CSS_SELECTOR, "button[role='option']")

            if not options:
                print("❌ No search results found")
                return None

            print("✅ Search results found")
            # Extract location texts
            location_options = []
            for i, option in enumerate(options):
                location_text = option.text.replace("Save Location", "").strip()
                if location_text:
                    location_options.append(
                        {"index": i, "text": location_text, "element": option}
                    )

            print(f"📍 Found {len(location_options)} options:")
            for opt in location_options:
                print(f"  {opt['index'] + 1}. {opt['text']}")

            # Use AI to select best option
            selected_option = self.llm_select_best_location(city_name, location_options)

            if not selected_option:
                print("❌ Could not select location")
                return None

            print(f"🤖 LLM selected: {selected_option['text']}")

            return selected_option

        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return None

    def extract_city_weather(
        self, city_name: str, page: Literal["hourbyhour", "tenday"] = "hourbyhour"
    ) -> str:
        """
        Extract weather data for a given city. Only use this tool if the user asks for weather information for a specific city.

        Args:
            city_name (str): The name of the city to search for. Only one city is supported at a time.
            page (Literal["hourbyhour", "tenday"], optional): The weather page type to retrieve.
                Values can be 'hourbyhour' for hourly weather data for the next three days
                (Temperature, Weather, Precipitation Chance, Feels Like, Wind, Humidity, UV Index, Cloud Cover, Rain Amount),
                or 'tenday' for daily weather for each of the next 10 days with day and night data
                (Max/Min temperature, Precipitation Chance, Humidity, UV Index, Sunrise/Sunset times, Wind).
                Defaults to 'hourbyhour'.

        Returns:
            str: The extracted weather data in markdown format, or "" if extraction fails.
        """
        try:
            selected_option = self.search_for_city(city_name)

            if not selected_option:
                print("❌ Could not select location")
                return ""

            selected_option["element"].click()

            # Extract city ID from URL
            city_id = self.driver.current_url.split("/")[-1]
            self.driver.get(f"https://weather.com/weather/{page}/l/{city_id}")

            print("🔍 Waiting for main content...")
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "MainContent"))
            )
            print("✅ Main content found")

            print("🔍 Converting page to markdown...")
            markdown_page = md.markdownify(self.driver.page_source)
            print("✅ Page converted to markdown")

            return markdown_page  # TODO: this could be improved by cleaning the page before returning it (using something like readability)

        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return ""

    def add_city_to_favorites(self, city_name: str):
        """Add a city to the favorites list. Only use this tool if the user asks to add a city to the favorites list.

        Args:
            city_name (str): The name of the city to add to the favorites list.
        """
        print(f"🔍 Adding {city_name} to favorites...")

        try:
            selected_option = self.search_for_city(city_name)

            if not selected_option:
                print("❌ Could not select location")
                return

            favourite_button = self.driver.find_element(
                By.XPATH,
                f"//button[normalize-space(text())='{selected_option['text']}']",
            ).find_element(By.CLASS_NAME, "FavoriteStar--saveLocationCaption--aZzc8")

            if favourite_button.get_attribute("innerHTML") == "Save Location":
                selected_option["element"].find_element(
                    By.CSS_SELECTOR, "button[aria-label='favorite']"
                ).click()
            else:
                print(f"❌ {city_name} is already in favorites")
                return

            print(f"✅ {city_name} added to favorites")

        except Exception as e:
            print(f"❌ Add to favorites error: {str(e)}")

    def remove_city_from_favorites(self, city_name: str):
        """Remove a city from the favorites list. Only use this tool if the user asks to remove a city from the favorites list.

        Args:
            city_name (str): The name of the city to remove from the favorites list.
        """
        print(f"🔍 Removing {city_name} from favorites...")

        try:
            selected_option = self.search_for_city(city_name)

            if not selected_option:
                print("❌ Could not select location")
                return

            favourite_button = self.driver.find_element(
                By.XPATH,
                f"//button[normalize-space(text())='{selected_option['text']}']",
            ).find_element(By.CLASS_NAME, "FavoriteStar--saveLocationCaption--aZzc8")

            if favourite_button.get_attribute("innerHTML") == "Remove Location":
                selected_option["element"].find_element(
                    By.CSS_SELECTOR, "button[aria-label='favorite']"
                ).click()
            else:
                print(f"❌ {city_name} is not in favorites")
                return

            print(f"✅ {city_name} removed from favorites")

        except Exception as e:
            print(f"❌ Remove from favorites error: {str(e)}")

    def llm_select_best_location(
        self, search_query: str, location_options: List[Dict]
    ) -> Optional[Dict]:
        """Use AI to select the best location match."""
        try:
            llm = setup_llm()

            options_text = "\n".join(
                [f"{i + 1}. {opt['text']}" for i, opt in enumerate(location_options)]
            )

            prompt = dedent(
                f"""
                Select the most appropriate location from these search results.

                Search Query: "{search_query}"

                Options:
                {options_text}

                Respond with ONLY the number (1, 2, 3, etc.) of your selection. Start with 1."""
            )

            response = llm.invoke(prompt)

            try:
                selection_number = int(response.content.strip())  # type: ignore
                if 1 <= selection_number <= len(location_options):
                    return location_options[selection_number - 1]
            except ValueError:
                pass

        except Exception as e:
            print(f"⚠️  AI selection failed: {str(e)}")

        # Fallback to first option
        print("💡 Using first option as fallback")
        return location_options[0] if location_options else None
