import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """
    Retourne un service Gmail authentifié via OAuth 2.0.
    Lance le navigateur pour la première authentification,
    puis réutilise le token.json pour les fois suivantes.
    """
    creds = None

    # Si un token existe déjà, le charger
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Si pas de token valide, en créer un
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expiré mais rafraîchissable
            creds.refresh(Request())
        else:
            # Première fois : ouvrir le navigateur
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Sauvegarder pour les prochains appels
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)