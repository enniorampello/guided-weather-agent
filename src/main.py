#!/usr/bin/env python3
"""
Weather Agent CLI

A beautiful command-line interface for getting weather information using AI.
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState, StateGraph, START
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from utils import setup_llm
from weather_agent import WeatherAgent

if __name__ == "__main__":
    agent = WeatherAgent(
        email="weather.headcount131@passinbox.com",
        password="Guided.123",
        headless=False,
    )

    agent.login()

    llm = setup_llm()
    tools = [
        agent.extract_city_weather,
        agent.add_city_to_favorites,
        agent.remove_city_from_favorites,
    ]
    llm_with_tools = llm.bind_tools(tools)

    # System message
    sys_msg = SystemMessage(
        content=f"You are a helpful assistant tasked with getting weather information for a given city. Today is {datetime.now().strftime('%A, %Y-%m-%d')}"
    )

    # Node
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

    builder = StateGraph(MessagesState)

    # Add nodes
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Add edges: these determine the control flow
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
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
            response = graph.invoke({"messages": messages})
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
