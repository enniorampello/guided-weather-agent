"""
Weather Agent CLI

A beautiful command-line interface for getting weather information using AI.
"""

import os
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from calendar_client import create_calendar_client
from utils import setup_llm
from weather_agent import WeatherAgent


class CustomState(MessagesState):
    gathering_mode: bool


if __name__ == "__main__":
    agent = WeatherAgent(
        email=os.environ["WEATHER_AGENT_EMAIL"],
        password=os.environ["WEATHER_AGENT_PASSWORD"],
        headless=True,
    )

    client = create_calendar_client()
    primary_calendar_id = client.get_primary_calendar_id()

    agent.login()

    llm = setup_llm()
    tools = [
        agent.extract_city_weather,
        agent.add_city_to_favorites,
        agent.remove_city_from_favorites,
        client.create_event,
        client.get_events_for_date,
    ]
    llm_with_tools = llm.bind_tools(tools)

    # System message
    def get_sys_msg(gathering_mode: bool):
        base_msg = f"You are a helpful assistant tasked with getting weather information for a given city. Today is {datetime.now().strftime('%A, %Y-%m-%d')}"
        if gathering_mode:
            return SystemMessage(
                content=base_msg
                + "\n\nYou are in information gathering mode. Make multiple tool calls as needed to collect all necessary information before providing a final response. Do not respond to the user until you have gathered all required data."
            )
        else:
            return SystemMessage(
                content=base_msg
                + "\n\nYou have gathered all necessary information. Provide a comprehensive response to the user."
            )

    # Node
    def assistant(state: CustomState):
        sys_msg = get_sys_msg(state.get("gathering_mode", True))
        response = llm_with_tools.invoke([sys_msg] + state["messages"])

        # Ensure sequential tool calls by limiting to one tool call at a time
        tool_calls = getattr(response, "tool_calls", [])
        if len(tool_calls) > 1:
            # Create a new AIMessage with only the first tool call for sequential execution
            response = AIMessage(
                content=response.content,
                tool_calls=tool_calls[:1],
                additional_kwargs=response.additional_kwargs,
                response_metadata=response.response_metadata,
                id=response.id,
            )

        # Switch to response mode if no tool calls were made
        new_gathering_mode = bool(getattr(response, "tool_calls", []))

        return {"messages": [response], "gathering_mode": new_gathering_mode}

    builder = StateGraph(CustomState)

    # Add nodes
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Add edges: these determine the control flow
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    # builder.add_edge("tools", "tools")
    builder.add_edge("tools", "assistant")
    graph = builder.compile()

    messages = []

    console = Console()
    console.print(
        Panel("Welcome to Weather Agent Chat! Type 'exit' to quit.", style="bold cyan")
    )
    while True:
        user_input = Prompt.ask("[bold green]You[/bold green]")
        if user_input.strip().lower() in {"exit", "quit"}:
            console.print("[bold red]Goodbye![/bold red]")
            break
        with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
            messages.append(HumanMessage(content=user_input))
            response = graph.invoke({"messages": messages, "gathering_mode": True})
            messages.append(AIMessage(content=response["messages"][-1].content))
        if response["messages"][-1].content:
            console.print(
                Panel(
                    Markdown(response["messages"][-1].content),
                    title="[bold yellow]Weather Agent[/bold yellow]",
                    style="bold magenta",
                )
            )
        else:
            console.print("[bold red]No response from agent.[/bold red]")


# Example question is: Create a new meeting for today and add the weather in london to the description. The event should be called "coffee with Guided team"
# create an event either in london or paris depending on which city is warmer
