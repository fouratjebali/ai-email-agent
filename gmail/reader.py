import base64
from dataclasses import dataclass
from typing import Optional
from auth.gmail_auth import get_gmail_service


@dataclass
class Email:
    """Représente un email récupéré depuis Gmail."""
    id: str
    subject: str
    sender: str
    body: str
    date: str
    is_read: bool

    def short_body(self, max_chars: int = 300) -> str:
        """Retourne les premiers caractères du corps."""
        return self.body[:max_chars] + "..." if len(self.body) > max_chars else self.body


def _get_header(headers: list, name: str) -> str:
    """Extrait la valeur d'un header par son nom."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(payload: dict) -> str:
    """Décode le corps base64 d'un email en texte lisible."""
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
    elif "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    return body.strip()


def fetch_emails(max_results: int = 10, query: str = "is:unread") -> list[Email]:
    """
    Récupère des emails depuis Gmail.

    Args:
        max_results : nombre max d'emails à récupérer
        query       : filtre Gmail (ex: 'is:unread', 'from:boss@gmail.com')

    Returns:
        Liste d'objets Email
    """
    service = get_gmail_service()
    emails = []

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        q=query
    ).execute()

    messages = results.get("messages", [])

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = msg_data["payload"]["headers"]
        labels  = msg_data.get("labelIds", [])

        email = Email(
            id=msg["id"],
            subject=_get_header(headers, "Subject") or "(Sans objet)",
            sender=_get_header(headers, "From"),
            body=_decode_body(msg_data["payload"]),
            date=_get_header(headers, "Date"),
            is_read="UNREAD" not in labels,
        )
        emails.append(email)

    return emails


def fetch_single_email(email_id: str) -> Optional[Email]:
    """Récupère un seul email par son ID Gmail."""
    service = get_gmail_service()

    msg_data = service.users().messages().get(
        userId="me",
        id=email_id,
        format="full"
    ).execute()

    headers = msg_data["payload"]["headers"]
    labels  = msg_data.get("labelIds", [])

    return Email(
        id=email_id,
        subject=_get_header(headers, "Subject") or "(Sans objet)",
        sender=_get_header(headers, "From"),
        body=_decode_body(msg_data["payload"]),
        date=_get_header(headers, "Date"),
        is_read="UNREAD" not in labels,
    )