from langchain.tools import Tool
from gmail.reader import fetch_emails
from gmail.sender import send_email
from .chains import analysis_chain, reply_chain, summary_chain
analyze_email_tool = Tool(
    name="Analyze Email",
    func=analysis_chain.invoke,
    description="Analyse un email et retourne sujet, priorité, résumé et réponse"
)
reply_email_tool = Tool(
    name="Reply Email",
    func=reply_chain.invoke,
    description="Génère une réponse professionnelle pour un email"
)
summary_email_tool = Tool(
    name="Summary Email",
    func=summary_chain.invoke,
    description="Résume un email en une seule phrase"
)
read_emails_tool = Tool(
    name="Read Emails",
    func=fetch_emails,
    description="Lire les emails depuis Gmail"
)
send_email_tool = Tool(
    name="Send Email",
    func=send_email,
    description="Envoyer un email via Gmail"
)
tools = [
    analyze_email_tool,
    reply_email_tool,
    summary_email_tool,
    read_emails_tool,
    send_email_tool
]
