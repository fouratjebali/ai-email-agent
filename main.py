from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from gmail.reader import fetch_emails
from config.settings import settings

console = Console()


def test_gmail_connection():
    """Test 1 : vérifier que la connexion Gmail fonctionne."""
    console.print(Panel("[bold blue]Test 1 : Connexion Gmail[/bold blue]"))

    emails = fetch_emails(max_results=5, query="is:unread")

    if not emails:
        console.print("[yellow]Aucun email non-lu. Essai sans filtre...[/yellow]")
        emails = fetch_emails(max_results=5, query="")

    table = Table(title=f"{len(emails)} email(s) récupéré(s)")
    table.add_column("De",      style="cyan",  max_width=30)
    table.add_column("Sujet",   style="white", max_width=40)
    table.add_column("Date",    style="dim",   max_width=25)
    table.add_column("Lu",      style="green")

    for e in emails:
        table.add_row(
            e.sender[:30],
            e.subject[:40],
            e.date[:25],
            "✓" if e.is_read else "✗"
        )

    console.print(table)
    return emails


def test_llm_connection():
    """Test 2 : vérifier qu'Ollama répond."""
    console.print(Panel("[bold blue]Test 2 : Connexion Ollama LLM[/bold blue]"))

    llm = OllamaLLM(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.1,
    )

    response = llm.invoke("Reply with exactly: 'LLM OK'")
    console.print(f"[green]Réponse LLM : {response.strip()}[/green]")
    return llm


def test_email_analysis(emails, llm):
    """Test 3 : analyser un email avec le LLM."""
    console.print(Panel("[bold blue]Test 3 : Analyse d'un email par le LLM[/bold blue]"))

    if not emails:
        console.print("[red]Pas d'emails à analyser.[/red]")
        return

    email = emails[0]
    console.print(f"Email analysé → Sujet : [cyan]{email.subject}[/cyan]")

    prompt = PromptTemplate.from_template("""
You are a professional email assistant. Analyze this email carefully.

Email:
Subject: {subject}
From: {sender}
Body: {body}

Respond ONLY with this exact JSON format (no other text):
{{
  "category": "RECLAMATION or INFORMATION or SUPPORT or COMMERCIAL",
  "priority": "URGENT or NORMAL or LOW",
  "summary": "one sentence max",
  "suggested_reply": "a short professional reply in the same language as the email"
}}
""")

    chain = prompt | llm

    console.print("[yellow]Appel au LLM...[/yellow]")
    result = chain.invoke({
        "subject": email.subject,
        "sender":  email.sender,
        "body":    email.body[:800],
    })

    console.print(Panel(result, title="[green]Résultat LLM[/green]"))


if __name__ == "__main__":
    console.print(Panel(
        "[bold]AI Email Agent — Day 1 Setup Test[/bold]",
        style="bold blue"
    ))

    # Test 1 : Gmail
    emails = test_gmail_connection()

    # Test 2 : LLM
    llm = test_llm_connection()

    # Test 3 : Analyse
    test_email_analysis(emails, llm)

    console.print("\n[bold green]✓ Day 1 complet ! Tout fonctionne.[/bold green]\n")