"""The two invariants, tested against the HTTP surface.

Berkas claims that the gates are real -- that they live in the API rather than in
a disabled button. That claim is only worth what it is tested at, so these drive
the endpoints the way a sceptical judge with curl would.

Firestore is swapped for a dict. The gates are pure control flow; they should not
need a database to be true.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from berkas import store
from berkas.models import Draft, StoredSpec


@pytest.fixture
def client(monkeypatch):
    specs: dict[str, StoredSpec] = {}
    drafts: dict[str, Draft] = {}
    receipts: list = []
    sent: list = []

    monkeypatch.setattr(store, "save_spec", lambda s: specs.__setitem__(s.spec_id, s) or s)
    monkeypatch.setattr(store, "get_spec", lambda i: specs.get(i))
    monkeypatch.setattr(store, "save_draft", lambda d: drafts.__setitem__(d.draft_id, d) or d)
    monkeypatch.setattr(store, "get_draft", lambda i: drafts.get(i))
    monkeypatch.setattr(store, "save_receipt", lambda r: receipts.append(r) or r)
    monkeypatch.setattr(store, "get_answers", lambda i: {})
    monkeypatch.setattr(store, "save_answers", lambda i, a: None)

    class FakeSend:
        message_id, thread_id = "msg-1", "thr-1"

        def __init__(self, to, subject):
            self.to, self.subject = to, subject

    def fake_send(to, subject, body, attachments=None):
        sent.append({"to": to, "subject": subject, "body": body})
        return FakeSend(to, subject)

    from berkas import submitter

    monkeypatch.setattr(submitter, "send", fake_send)

    import main

    c = TestClient(main.app)
    c.specs, c.drafts, c.receipts, c.sent = specs, drafts, receipts, sent
    return c


def _spec(client, *, corrected: bool, cap: int = 500) -> StoredSpec:
    spec = StoredSpec(
        programme="IISMA 2026",
        sections=[{"name": "motivation", "word_cap": cap, "required": True}],
        human_corrected=corrected,
    )
    client.specs[spec.spec_id] = spec
    return spec


def _draft(client, spec: StoredSpec, words: int) -> Draft:
    draft = Draft(spec_id=spec.spec_id, sections={"motivation": " ".join(["x"] * words)})
    client.drafts[draft.draft_id] = draft
    return draft


# --- Gate 1 --------------------------------------------------------------------

def test_drafting_refuses_a_spec_no_human_has_confirmed(client):
    spec = _spec(client, corrected=False)
    r = client.post(f"/api/draft/{spec.spec_id}")
    assert r.status_code == 409
    assert "confirmed by a human" in r.json()["detail"]


def test_correcting_a_spec_records_exactly_which_fields_changed(client):
    spec = _spec(client, corrected=False, cap=300)
    body = spec.model_dump()
    body["sections"][0]["word_cap"] = 500          # he fixes a cap the model misread
    body["programme"] = "IISMA 2026 — Undergraduate"

    r = client.put(f"/api/spec/{spec.spec_id}", json=body)
    assert r.status_code == 200
    out = r.json()
    assert out["human_corrected"] is True
    assert sorted(out["corrected_fields"]) == ["programme", "sections[0].word_cap"]
    assert out["corrected_at"]
    # the original reading survives, so the correction stays auditable
    assert out["extracted"]["sections"][0]["word_cap"] == 300


def test_an_untouched_spec_still_records_that_a_human_passed_it(client):
    """Confirming without editing is a decision too, and must be recorded as one."""
    spec = _spec(client, corrected=False)
    r = client.put(f"/api/spec/{spec.spec_id}", json=spec.model_dump())
    assert r.json()["human_corrected"] is True
    assert r.json()["corrected_fields"] == []


# --- Gate 2 --------------------------------------------------------------------

def test_send_refuses_without_explicit_confirmation(client):
    spec = _spec(client, corrected=True)
    draft = _draft(client, spec, words=10)
    r = client.post(f"/api/send/{draft.draft_id}", json={"confirm": False, "to": "a@b.com"})
    assert r.status_code == 400
    assert client.sent == []


def test_send_refuses_a_violating_draft_even_when_confirmed(client):
    """The disabled button is UI. This is the gate."""
    spec = _spec(client, corrected=True, cap=500)
    draft = _draft(client, spec, words=611)
    r = client.post(f"/api/send/{draft.draft_id}", json={"confirm": True, "to": "a@b.com"})
    assert r.status_code == 409
    assert r.json()["detail"]["violations"][0]["rule"] == "word_cap"
    assert client.sent == [], "a non-compliant packet reached the transport"
    assert client.receipts == [], "a receipt was written for a packet that never sent"


def test_send_refuses_an_ungrounded_packet(client):
    """The product's promise, enforced at the last possible moment."""
    spec = _spec(client, corrected=True)
    draft = Draft(spec_id=spec.spec_id, sections={"motivation": "I led [NEEDS: team size]."})
    client.drafts[draft.draft_id] = draft
    r = client.post(f"/api/send/{draft.draft_id}", json={"confirm": True, "to": "a@b.com"})
    assert r.status_code == 409
    assert r.json()["detail"]["violations"][0]["rule"] == "ungrounded_claim"
    assert client.sent == []


def test_a_compliant_confirmed_packet_sends_and_returns_a_receipt(client):
    spec = _spec(client, corrected=True, cap=500)
    draft = _draft(client, spec, words=480)
    r = client.post(f"/api/send/{draft.draft_id}", json={"confirm": True, "to": "a@b.com"})
    assert r.status_code == 200

    receipt = r.json()
    assert receipt["gmail_message_id"] == "msg-1"
    assert receipt["compliance_passed"] is True
    assert receipt["confirmed_by_human_at"]
    assert len(client.sent) == 1
    assert client.sent[0]["to"] == "a@b.com"
