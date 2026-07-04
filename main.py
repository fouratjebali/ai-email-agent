from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box
from agent.agent import EmailAgent

console = Console()

# Exemples d'instructions pour guider l'utilisateur
EXAMPLE_INSTRUCTIONS = [
    "1. Read my unread emails and show me a summary of each one",
    "2. Find all urgent emails and tell me what actions I need to take",
    "3. Read my emails, classify them and show the results",
    "4. Read email [paste an email ID] and suggest a professional reply",
    "5. Send an email to test@example.com with subject 'Test' and body 'Hello'",
    "6. Read my unread emails and automatically reply to any RECLAMATION",
]


def print_agent_step(node_name: str, message) -> None:
    """Affiche une étape du raisonnement de l'agent."""
    msg_type = type(message).__name__

    if node_name == "agent":
        # Message du LLM (raisonnement ou réponse finale)
        content = getattr(message, "content", "")
        tool_calls = getattr(message, "tool_calls", [])

        if tool_calls:
            # L'agent veut appeler un outil
            for tc in tool_calls:
                tool_name = tc.get("name", "unknown")
                tool_args = tc.get("args", {})
                console.print(
                    f"  [bold yellow]→ Calling tool:[/bold yellow] "
                    f"[cyan]{tool_name}[/cyan]"
                )
                if tool_args:
                    for k, v in tool_args.items():
                        v_str = str(v)[:80]
                        console.print(f"    [dim]{k}:[/dim] {v_str}")
        elif content:
            # Réponse textuelle de l'agent
            console.print(f"  [bold green]Agent:[/bold green] {content[:200]}")

    elif node_name == "tools":
        # Résultat d'un outil
        content = getattr(message, "content", "")
        console.print(
            f"  [bold blue]← Tool result:[/bold blue] "
            f"[dim]{content[:150]}...[/dim]"
        )


def run_agent_interactive():
    console.print(Panel(
        "[bold blue]AI Email Agent — Day 3[/bold blue]\n"
        "[dim]ReAct Agent with LangGraph — Type your instruction in natural language[/dim]",
        box=box.ROUNDED,
    ))

    # Afficher les exemples
    console.print("\n[bold]Example instructions:[/bold]")
    for ex in EXAMPLE_INSTRUCTIONS:
        console.print(f"  [dim]{ex}[/dim]")

    console.print("\n[dim]Type 'quit' to exit | Type 'demo' to run a demo[/dim]\n")

    # Initialiser l'agent (charge le LLM une seule fois)
    console.print("[yellow]Loading agent...[/yellow]")
    try:
        agent = EmailAgent()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return
    console.print("[green]Agent ready.[/green]\n")

    while True:
        console.print(Rule(style="dim"))

        # Lire l'instruction de l'utilisateur
        try:
            instruction = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Bye![/yellow]")
            break

        if not instruction:
            continue

        if instruction.lower() == "quit":
            console.print("[yellow]Bye![/yellow]")
            break

        if instruction.lower() == "demo":
            instruction = "Read my 5 most recent emails and classify each one. Show me a summary table."

        # Lancer l'agent en streaming
        console.print(f"\n[bold]Running agent...[/bold]\n")

        final_response = ""
        step_count = 0

        try:
            for node_name, message in agent.stream(instruction):
                step_count += 1
                print_agent_step(node_name, message)

                # Capturer la dernière réponse textuelle
                content = getattr(message, "content", "")
                tool_calls = getattr(message, "tool_calls", [])
                if content and not tool_calls and node_name == "agent":
                    final_response = content

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue

        # Afficher la réponse finale
        if final_response:
            console.print("\n")
            console.print(Panel(
                Markdown(final_response),
                title="[bold green]Final Answer[/bold green]",
                border_style="green",
                box=box.ROUNDED,
            ))

        console.print(f"\n[dim]Steps taken: {step_count}[/dim]")


def run_demo_scenarios():
    """Lance 3 scénarios de démo automatiquement."""
    try:
        agent = EmailAgent()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    scenarios = [
        {
            "name": "Scenario 1 — Read and Classify",
            "instruction": "Read my 3 most recent emails and classify each one. Give me a brief summary.",
        },
        {
            "name": "Scenario 2 — Find Urgent",
            "instruction": "Check my unread emails and identify any urgent ones that need immediate attention.",
        },
    ]

    for scenario in scenarios:
        console.print(Rule(f"[bold]{scenario['name']}[/bold]"))
        console.print(f"[cyan]Instruction:[/cyan] {scenario['instruction']}\n")

        try:
            response = agent.run(scenario["instruction"])
            console.print(Panel(
                response,
                title="[green]Agent Response[/green]",
                border_style="green",
            ))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo_scenarios()
    else:
        run_agent_interactive()