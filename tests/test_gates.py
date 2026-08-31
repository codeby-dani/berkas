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


# --- Gate 3 --------------------------------------------------------------------
#
# The checker compares strings, so it cannot see through translation: a section in
# Indonesian saying "Sistem Informasi" is flagged against a corpus that attests the
# same credential in English. When the machine is wrong about him he overrules it,
# and the override is recorded rather than silently permitted.

def test_attesting_a_claim_clears_it_and_is_recorded(client, monkeypatch):
    from berkas import evidence

    # The corpus names it in English; the Indonesian section reverses the word order,
    # so string containment cannot match them. The claim is true, the checker is wrong.
    monkeypatch.setattr(evidence, "attested_text", lambda session_id=None: "Telkom University, Bandung")
    spec = _spec(client, corrected=True, cap=None)
    draft = Draft(spec_id=spec.spec_id,
                  sections={"motivation": "Saya menyelesaikan diploma di Universitas Telkom."})
    client.drafts[draft.draft_id] = draft

    blocked = client.post(f"/api/check/{draft.draft_id}").json()
    assert [v["rule"] for v in blocked["violations"]] == ["unverified_claim"]

    r = client.post(f"/api/attest/{draft.draft_id}",
                    json={"claims": ["Universitas", "Telkom"]})
    assert r.status_code == 200
    assert r.json()["compliance"]["passed"], "his attestation should clear the flag"
    assert r.json()["draft"]["attested_claims"] == ["Telkom", "Universitas"]
    assert r.json()["draft"]["attested_at"], "the override must be timestamped"


def test_an_attestation_reaches_the_receipt(client, monkeypatch):
    """The record of what was sent says who stood behind which claim."""
    from berkas import evidence

    monkeypatch.setattr(evidence, "attested_text", lambda session_id=None: "nothing relevant")
    spec = _spec(client, corrected=True, cap=None)
    draft = Draft(spec_id=spec.spec_id, sections={"motivation": "I worked at Acme Corporation Limited."})
    client.drafts[draft.draft_id] = draft

    client.post(f"/api/attest/{draft.draft_id}", json={"claims": ["Acme", "Corporation", "Limited"]})
    r = client.post(f"/api/send/{draft.draft_id}", json={"confirm": True, "to": "a@b.com"})
    assert r.status_code == 200
    assert r.json()["human_attested"] == ["Acme", "Corporation", "Limited"]


def test_editing_the_text_drops_earlier_attestations(client, monkeypatch):
    """Edited text is new text. Vouching for one sentence must not vouch for its
    replacement, or the override becomes a permanent bypass."""
    from berkas import evidence

    monkeypatch.setattr(evidence, "attested_text", lambda session_id=None: "nothing relevant")
    spec = _spec(client, corrected=True, cap=None)
    draft = Draft(spec_id=spec.spec_id, sections={"motivation": "I worked at Acme Corporation Limited."})
    client.drafts[draft.draft_id] = draft
    client.post(f"/api/attest/{draft.draft_id}", json={"claims": ["Acme", "Corporation", "Limited"]})

    r = client.put(f"/api/draft/{draft.draft_id}",
                   json={"sections": {"motivation": "I studied at Hogwarts School of Witchcraft."}})
    assert r.json()["draft"]["attested_claims"] == []
    assert not r.json()["compliance"]["passed"], "the new claim is not covered by the old attestation"


def test_attesting_nothing_is_refused(client):
    spec = _spec(client, corrected=True)
    draft = _draft(client, spec, words=10)
    assert client.post(f"/api/attest/{draft.draft_id}", json={"claims": []}).status_code == 400


def test_attesting_some_claims_does_not_clear_the_rest(client, monkeypatch):
    """Gate 3 must be per-claim.

    The first version offered one button that attested everything flagged at once.
    On a real run that list held "Sistem" and "Informasi" -- true, translated --
    alongside "Massachusetts", "Boston" and "Cambridge", which the model invented.
    One click would have put his name behind all of them. A gate that is easier to
    pass wholesale than to read is not a gate.
    """
    from berkas import evidence

    monkeypatch.setattr(evidence, "attested_text", lambda session_id=None: "Telkom University, Bandung")
    spec = _spec(client, corrected=True, cap=None)
    draft = Draft(
        spec_id=spec.spec_id,
        sections={"motivation": "Saya belajar di Universitas Telkom. I will study at Massachusetts Institute."},
    )
    client.drafts[draft.draft_id] = draft

    r = client.post(f"/api/attest/{draft.draft_id}", json={"claims": ["Universitas", "Telkom"]})
    assert r.status_code == 200
    assert r.json()["draft"]["attested_claims"] == ["Telkom", "Universitas"]

    still = r.json()["compliance"]
    assert not still["passed"], "the invented destination must survive a partial attestation"
    flagged = {c for v in still["violations"] if v["rule"] == "unverified_claim" for c in v["actual"]}
    assert "Massachusetts" in flagged
    assert "Universitas" not in flagged

    assert client.post(f"/api/send/{draft.draft_id}",
                       json={"confirm": True, "to": "a@b.com"}).status_code == 409
    assert client.sent == []


def test_a_single_digit_day_is_repaired_at_the_gate(client):
    """People type 2026-09-7. Repair the unambiguous case rather than refuse it."""
    spec = _spec(client, corrected=False)
    body = spec.model_dump()
    body["deadline"] = "2026-09-7"
    out = client.put(f"/api/spec/{spec.spec_id}", json=body).json()
    assert out["deadline"] == "2026-09-07"


def test_a_deadline_that_is_not_a_date_is_kept_verbatim(client):
    """Not repaired, not rejected: kept so compliance can show it back to them."""
    spec = _spec(client, corrected=False)
    body = spec.model_dump()
    body["deadline"] = "sometime in September"
    out = client.put(f"/api/spec/{spec.spec_id}", json=body).json()
    assert out["deadline"] == "sometime in September"
    assert "deadline" in out["corrected_fields"]
