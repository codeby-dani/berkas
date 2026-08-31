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
