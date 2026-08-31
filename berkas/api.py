"""HTTP surface. Both gates live here, and nowhere else.

Gate 1 is PUT /spec/{id}. Perception's reading is not a rulebook until a human has
been through it, and what they changed is recorded rather than merely allowed.
POST /draft refuses to run on a spec that has not been through it.

Gate 2 is POST /send/{id}. It refuses without an explicit confirmation, and it
refuses a draft that does not pass compliance. Both refusals are enforced here and
not in the browser, so a judge who curls the endpoint gets the same answer as a
judge who clicks the button. The disabled button is a courtesy; this is the gate.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from berkas import drafting, evidence, interview, perception, store, submitter
from berkas.compliance import check
from berkas.models import ExtractedSpec, Receipt, StoredSpec

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "service": "berkas",
        "ok": True,
        "model": os.environ.get("MODEL_ID", "gemini-3.7-flash"),
        "evidence_files": len(evidence.inventory()),
        "default_recipient": os.environ.get("BERKAS_DEMO_RECIPIENT", ""),
    }


# --- Screen 1: read the call ---------------------------------------------------

@router.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    """Read a call document. Reports requirements; scores nothing."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty upload")

    reading = await perception.extract(data, file.content_type or "application/pdf")
    spec = StoredSpec(**reading.model_dump(), extracted=reading)
    store.save_spec(spec)
    return {"spec_id": spec.spec_id, "spec": spec.model_dump()}


@router.get("/spec/{spec_id}")
def read_spec(spec_id: str) -> dict:
    spec = store.get_spec(spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")
    return spec.model_dump()


# --- Gate 1: correct it before it binds ----------------------------------------

def _corrections(before: ExtractedSpec, after: ExtractedSpec) -> list[str]:
    """Dotted paths the human changed. This is the audit trail, so it is explicit."""
    changed: list[str] = []
    for field in ("programme", "deadline", "voice_register", "extra_requirements"):
        if getattr(before, field) != getattr(after, field):
            changed.append(field)

    for i, new in enumerate(after.sections):
        old = before.sections[i] if i < len(before.sections) else None
        if old is None:
            changed.append(f"sections[{i}] (added)")
            continue
        for field in ("name", "word_cap", "required"):
            if getattr(old, field) != getattr(new, field):
                changed.append(f"sections[{i}].{field}")
    for i in range(len(after.sections), len(before.sections)):
        changed.append(f"sections[{i}] (removed)")

    return changed


@router.put("/spec/{spec_id}")
def correct_spec(spec_id: str, corrected: ExtractedSpec) -> dict:
    """GATE 1. Nothing is written until this has been through a human."""
    spec = store.get_spec(spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")

    baseline = spec.extracted or ExtractedSpec(**spec.model_dump())
    updated = StoredSpec(
        **corrected.model_dump(),
        spec_id=spec.spec_id,
        created_at=spec.created_at,
        extracted=baseline,
        human_corrected=True,
        corrected_fields=_corrections(baseline, corrected),
        corrected_at=datetime.now(timezone.utc).isoformat(),
    )
    store.save_spec(updated)
    return updated.model_dump()


# --- Interview -----------------------------------------------------------------

@router.post("/interview/{spec_id}")
async def run_interview(spec_id: str) -> dict:
    spec = _confirmed_spec(spec_id)
    questions = await interview.ask(spec)
    return {"questions": [q.model_dump() for q in questions]}


class Answers(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


@router.post("/answers/{spec_id}")
def put_answers(spec_id: str, body: Answers) -> dict:
    _confirmed_spec(spec_id)
    store.save_answers(spec_id, body.answers)
    return {"saved": len(body.answers)}


# --- Draft and check -----------------------------------------------------------

def _confirmed_spec(spec_id: str) -> StoredSpec:
    spec = store.get_spec(spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")
    if not spec.human_corrected:
        # Gate 1, enforced rather than assumed.
        raise HTTPException(
            409, "this spec has not been confirmed by a human; nothing is written until it is"
        )
    return spec


@router.post("/draft/{spec_id}")
async def make_draft(spec_id: str) -> dict:
    spec = _confirmed_spec(spec_id)
    draft = await drafting.write(spec, store.get_answers(spec_id))
    store.save_draft(draft)
    return {"draft_id": draft.draft_id, "draft": draft.model_dump(),
            "compliance": check(spec.model_dump(), draft.model_dump())}


class DraftEdit(BaseModel):
    sections: dict[str, str]


@router.put("/draft/{draft_id}")
def edit_draft(draft_id: str, body: DraftEdit) -> dict:
    """He fixes what the checker blocked. Re-checked on the way out."""
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    draft.sections = body.sections
    store.save_draft(draft)
    spec = store.get_spec(draft.spec_id)
    return {"draft": draft.model_dump(),
            "compliance": check(spec.model_dump(), draft.model_dump())}


@router.post("/check/{draft_id}")
def run_check(draft_id: str) -> dict:
    """Plain Python. No model runs in this path."""
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    spec = store.get_spec(draft.spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")
    return check(spec.model_dump(), draft.model_dump())


# --- Gate 2: send it -----------------------------------------------------------

class SendRequest(BaseModel):
    confirm: bool = False
    to: str | None = None
    subject: str | None = None


@router.post("/send/{draft_id}")
def send_packet(draft_id: str, body: SendRequest) -> dict:
    """GATE 2. Nothing auto-sends, and nothing non-compliant sends at all."""
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    spec = store.get_spec(draft.spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")

    if not body.confirm:
        raise HTTPException(400, "nothing sends without explicit confirmation")

    verdict = check(spec.model_dump(), draft.model_dump())
    if not verdict["passed"]:
        raise HTTPException(
            409,
            {
                "error": "this packet has unresolved violations and cannot be submitted",
                "violations": verdict["violations"],
            },
        )

    to = body.to or os.environ.get("BERKAS_DEMO_RECIPIENT", "")
    if not to:
        raise HTTPException(400, "no recipient")

    confirmed_at = datetime.now(timezone.utc).isoformat()
    subject = body.subject or f"Application — {spec.programme}"
    packet = "\n\n".join(
        f"{name}\n{'-' * len(name)}\n{text}" for name, text in draft.sections.items()
    )

    sent = submitter.send(to=to, subject=subject, body=packet)

    receipt = store.save_receipt(
        Receipt(
            gmail_message_id=sent.message_id,
            gmail_thread_id=sent.thread_id,
            to=sent.to,
            subject=sent.subject,
            spec_id=spec.spec_id,
            draft_id=draft.draft_id,
            compliance_passed=True,
            confirmed_by_human_at=confirmed_at,
        )
    )
    return receipt.model_dump()
