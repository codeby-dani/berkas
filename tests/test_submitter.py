"""How the Gmail token is fetched.

The Secret Manager branch only runs on Cloud Run, so a mistake in it cannot fail
locally -- it deploys clean and then 500s on the one request that matters. That is
exactly what happened: access_secret_version(name={"name": ...}) passes a dict
where a string belongs and raises a protobuf TypeError. These tests pin the call
shape so the same mistake cannot come back silently.
"""

import json

import pytest

from berkas import submitter


@pytest.fixture
def token_file(tmp_path, monkeypatch):
    path = tmp_path / "gmail_token.json"
    path.write_text(json.dumps({"refresh_token": "local"}))
    monkeypatch.setattr(submitter, "TOKEN_PATH", path)
    monkeypatch.delenv("BERKAS_GMAIL_TOKEN_SECRET", raising=False)
    return path


def test_reads_the_local_token_when_no_secret_is_configured(token_file):
    assert json.loads(submitter._token_json())["refresh_token"] == "local"


def test_secret_manager_is_called_with_request_not_name(monkeypatch, tmp_path):
    """The regression. `name=` takes a string; the dict belongs in `request=`."""
    seen = {}

    class FakeClient:
        def access_secret_version(self, request=None, name=None, **kw):
            seen["request"], seen["name"] = request, name
            if not isinstance(request, dict):
                raise TypeError("bad argument type for built-in operation")
            return type("R", (), {"payload": type("P", (), {"data": b'{"refresh_token":"remote"}'})})

    monkeypatch.setitem(
        __import__("sys").modules, "google.cloud.secretmanager",
        type("M", (), {"SecretManagerServiceClient": FakeClient}),
    )
    monkeypatch.setenv("BERKAS_GMAIL_TOKEN_SECRET", "berkas-gmail-token")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proj")

    assert json.loads(submitter._token_json())["refresh_token"] == "remote"
    assert seen["name"] is None, "the dict must go to request=, never to name="
    assert seen["request"]["name"] == "projects/proj/secrets/berkas-gmail-token/versions/latest"


def test_missing_credentials_say_what_to_run(monkeypatch, tmp_path):
    monkeypatch.delenv("BERKAS_GMAIL_TOKEN_SECRET", raising=False)
    monkeypatch.setattr(submitter, "TOKEN_PATH", tmp_path / "absent.json")
    with pytest.raises(RuntimeError, match="scripts/gmail_auth.py"):
        submitter._token_json()
