"""One-time local OAuth consent, so the deployed service can send as the user.

    1. Cloud Console -> APIs & Services -> Credentials -> Create OAuth client ID
       -> application type "Desktop app". Download the JSON.
    2. Save it as credentials/oauth_client.json
    3. uv run python scripts/gmail_auth.py

Writes credentials/gmail_token.json, which carries the refresh token. Upload that
to Secret Manager for Cloud Run (the command is printed at the end).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow

from berkas.submitter import CLIENT_PATH, SCOPES, TOKEN_PATH


def main() -> None:
    if not CLIENT_PATH.exists():
        sys.exit(
            f"Missing {CLIENT_PATH}.\n"
            "Create an OAuth client ID of type 'Desktop app' in the Cloud Console, "
            "download the JSON, and save it there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_PATH), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"\nWrote {TOKEN_PATH}")

    if not creds.refresh_token:
        print(
            "\nWARNING: no refresh token in the response. The deployed service will stop "
            "sending when the access token expires in an hour. Revoke the grant at "
            "https://myaccount.google.com/permissions and run this again."
        )
        return

    print(
        "\nNext, make it available to Cloud Run:\n\n"
        "  gcloud secrets create berkas-gmail-token \\\n"
        f"      --data-file={TOKEN_PATH} \\\n"
        "      --project=project-336ac302-a8b2-4026-98e\n"
    )


if __name__ == "__main__":
    main()
