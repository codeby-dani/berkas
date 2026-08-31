"""Gmail transport. Sends a real message and returns the ids Gmail assigns it.

This module is deliberately dumb: it sends what it is given. It holds no opinion
about whether the packet *should* go out. The compliance gate and the human
confirmation both live in the API route that calls this (see berkas/api.py), so
that there is exactly one code path to an inbox and it runs through both.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# The narrowest scope that can send. Not gmail.modify, not mail.google.com:
# Berkas is never able to read or delete the user's mail.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

TOKEN_PATH = Path(__file__).resolve().parent.parent / "credentials" / "gmail_token.json"
CLIENT_PATH = Path(__file__).resolve().parent.parent / "credentials" / "oauth_client.json"


@dataclass(frozen=True)
class SendResult:
    message_id: str
    thread_id: str
    to: str
    subject: str


def _token_json() -> str:
    """Read the OAuth token, from Secret Manager on Cloud Run or from disk locally."""
    secret = os.environ.get("BERKAS_GMAIL_TOKEN_SECRET")
    if secret:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        name = f"projects/{project}/secrets/{secret}/versions/latest"
        return client.access_secret_version(name={"name": name}).payload.data.decode()

    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text()

    raise RuntimeError(
        "No Gmail credentials. Run `uv run python scripts/gmail_auth.py` once locally, "
        "or set BERKAS_GMAIL_TOKEN_SECRET to a Secret Manager secret name."
    )


def _credentials() -> Credentials:
    creds = Credentials.from_authorized_user_info(json.loads(_token_json()), SCOPES)
    if not creds.valid:
        # The stored token is a refresh token; access tokens are minted per cold start.
        creds.refresh(Request())
    return creds


def send(
    to: str,
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
) -> SendResult:
    """Send a real email. Returns the ids Gmail assigns, which become the receipt."""
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attachments or []:
        data = Path(path).read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf" if str(path).lower().endswith(".pdf") else "octet-stream",
            filename=Path(path).name,
        )

    service = build("gmail", "v1", credentials=_credentials(), cache_discovery=False)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    return SendResult(
        message_id=sent["id"],
        thread_id=sent.get("threadId", ""),
        to=to,
        subject=subject,
    )
