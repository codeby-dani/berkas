"""Firestore: specs, drafts, receipts.

The receipt collection is the point. A packet that left the building has a
timestamped row here carrying the Gmail message id and the moment a human
confirmed it -- which is what makes the outbound action checkable after the fact
rather than merely claimed.
"""

from __future__ import annotations

import os
from functools import lru_cache

from google.cloud import firestore

from berkas.models import Draft, Receipt, StoredSpec

SESSIONS = "sessions"
SPECS = "specs"
DRAFTS = "drafts"
RECEIPTS = "receipts"


@lru_cache(maxsize=1)
def db() -> firestore.Client:
    return firestore.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT"))


def save_spec(spec: StoredSpec) -> StoredSpec:
    db().collection(SPECS).document(spec.spec_id).set(spec.model_dump())
    return spec


def get_spec(spec_id: str) -> StoredSpec | None:
    snap = db().collection(SPECS).document(spec_id).get()
    return StoredSpec.model_validate(snap.to_dict()) if snap.exists else None


def save_draft(draft: Draft) -> Draft:
    db().collection(DRAFTS).document(draft.draft_id).set(draft.model_dump())
    return draft


def get_draft(draft_id: str) -> Draft | None:
    snap = db().collection(DRAFTS).document(draft_id).get()
    return Draft.model_validate(snap.to_dict()) if snap.exists else None


def save_receipt(receipt: Receipt) -> Receipt:
    db().collection(RECEIPTS).document(receipt.receipt_id).set(receipt.model_dump())
    return receipt


def save_answers(spec_id: str, answers: dict[str, str]) -> None:
    db().collection(SPECS).document(spec_id).set({"answers": answers}, merge=True)


def get_answers(spec_id: str) -> dict[str, str]:
    snap = db().collection(SPECS).document(spec_id).get()
    return (snap.to_dict() or {}).get("answers", {}) if snap.exists else {}


def save_session_files(session_id: str, kind: str, files: list[dict]) -> int:
    """Store what a visitor uploaded. `kind` is "background" or "voice".

    Firestore caps a document at 1 MB, which is ample for the handful of documents
    this asks for and is the reason the API caps the upload rather than streaming
    it somewhere larger.
    """
    doc = db().collection(SESSIONS).document(session_id)
    existing = (doc.get().to_dict() or {}).get(kind, [])
    doc.set({kind: existing + files}, merge=True)
    return len(existing) + len(files)


def get_session_files(session_id: str, kind: str) -> list[dict]:
    snap = db().collection(SESSIONS).document(session_id).get()
    return (snap.to_dict() or {}).get(kind, []) if snap.exists else []


def save_speaking(session_id: str, profile: dict) -> None:
    db().collection(SESSIONS).document(session_id).set({"speaking": profile}, merge=True)


def get_speaking(session_id: str) -> dict | None:
    snap = db().collection(SESSIONS).document(session_id).get()
    # A deleted recording is stored as an explicit null, not removed, so this
    # must read "or None" rather than trusting the key to be absent.
    return ((snap.to_dict() or {}).get("speaking") or None) if snap.exists else None


def delete_speaking(session_id: str) -> None:
    """Drop a recording and its profile. Redoing an answer must not leave the old
    level behind: a profile the applicant thought they had replaced would go on
    shaping every draft."""
    db().collection(SESSIONS).document(session_id).set({"speaking": None}, merge=True)
