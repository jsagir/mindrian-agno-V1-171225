#!/usr/bin/env python3
"""
Mindrian Demo - Interactive conversation with Larry

This demo shows how to:
1. Initialize the Mindrian orchestrator
2. Have a conversation with Larry to clarify a problem
3. Route to appropriate frameworks
4. Generate analysis output

Usage:
    python demo.py
"""

import asyncio
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from mindrian import MindrianOrchestrator, LarryMode


console = Console()


async def interactive_demo():
    """Run interactive conversation demo"""
    console.print(Panel.fit(
        "[bold blue]Mindrian[/bold blue] - AI Innovation Platform\n"
        "[dim]Built on Agno with Multi-MCP Orchestration[/dim]",
        border_style="blue"
    ))

    # Initialize orchestrator
    console.print("\n[yellow]Initializing Mindrian...[/yellow]")

    orchestrator = MindrianOrchestrator()
    await orchestrator.initialize()

    # Show available frameworks
    frameworks = orchestrator.get_available_frameworks()
    if frameworks:
        console.print(f"\n[green]Loaded {len(frameworks)} frameworks:[/green] {', '.join(frameworks[:5])}...")

    # Show registered agents
    agents = orchestrator.get_registered_agents()
    if agents:
        console.print(f"[green]Registered {len(agents)} agents:[/green] {', '.join(agents[:5])}...")

    console.print("\n[bold]Starting conversation with Larry...[/bold]")
    console.print("[dim]Larry will ask questions to understand your problem.[/dim]")
    console.print("[dim]Type 'quit' to exit, 'mode <mode>' to change Larry's mode[/dim]")
    console.print("[dim]Available modes: clarify, explore, coach, challenge, output[/dim]\n")

    # Create session
    session = orchestrator.create_session()

    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "quit":
                break

            if user_input.lower().startswith("mode "):
                mode_name = user_input.split(" ", 1)[1].strip().upper()
                try:
                    mode = LarryMode[mode_name]
                    orchestrator.set_larry_mode(mode)
                    console.print(f"[yellow]Switched to {mode.value} mode[/yellow]")
                    continue
                except KeyError:
                    console.print(f"[red]Unknown mode: {mode_name}[/red]")
                    continue

            if user_input.lower() == "summary":
                summary = orchestrator.get_session_summary()
                console.print(Panel(
                    f"Session: {summary.get('session_id', 'N/A')[:8]}...\n"
                    f"State: {summary.get('state', 'N/A')}\n"
                    f"Problem Type: {summary.get('problem_type', 'Not classified')}\n"
                    f"Messages: {summary.get('message_count', 0)}\n"
                    f"Frameworks Used: {', '.join(summary.get('frameworks_used', [])) or 'None'}",
                    title="Session Summary"
                ))
                continue

            # Process with orchestrator
            response = await orchestrator.process(user_input, session.session_id)

            # Display response
            console.print("\n[bold blue]Larry[/bold blue]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    # Show final summary
    console.print("\n[bold]Session Complete![/bold]")
    summary = orchestrator.get_session_summary()

    if summary.get("larry_summary"):
        larry_summary = summary["larry_summary"]
        console.print(Panel(
            f"Problem Clarity: {larry_summary.get('problem_clarity', 0):.0%}\n"
            f"What: {larry_summary.get('problem', {}).get('what', 'Not defined')}\n"
            f"Who: {larry_summary.get('problem', {}).get('who', 'Not defined')}\n"
            f"Success: {larry_summary.get('problem', {}).get('success', 'Not defined')}\n"
            f"Questions Asked: {larry_summary.get('questions_asked', 0)}\n"
            f"Recommended Frameworks: {', '.join(larry_summary.get('recommended_frameworks', [])) or 'None'}",
            title="Problem Clarity Summary"
        ))


async def quick_demo():
    """Run a quick non-interactive demo"""
    console.print("[bold]Quick Demo - Automated Conversation[/bold]\n")

    orchestrator = MindrianOrchestrator()
    await orchestrator.initialize()

    # Simulate a conversation
    messages = [
        "I want to build an AI chatbot for my company",
        "Customer support - they spend too much time answering repetitive questions",
        "IT support team, handling about 500 tickets per day",
        "Cut resolution time from 15 minutes to 5 minutes on average",
    ]

    for msg in messages:
        console.print(f"\n[green]User:[/green] {msg}")
        response = await orchestrator.process(msg)
        console.print(f"[blue]Larry:[/blue] {response[:500]}...")

    # Get summary
    summary = orchestrator.get_session_summary()
    console.print(f"\n[bold]Final State:[/bold] {summary.get('state', 'N/A')}")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_demo())
    else:
        asyncio.run(interactive_demo())


if __name__ == "__main__":
    main()
