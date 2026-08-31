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

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from berkas import (
    authenticity, drafting, evidence, interview, perception, speaking, store, submitter,
)
from berkas.compliance import check as _check
from berkas.models import ExtractedSpec, Receipt, StoredSpec

router = APIRouter()


MAX_UPLOAD = 700_000  # Firestore caps a document at 1 MB; leave room for the rest.


def _read_upload(file: UploadFile, data: bytes) -> str:
    """Text out of whatever they dropped. PDFs are extracted, not sent to a model."""
    name = (file.filename or "").lower()
    if name.endswith(".pdf") or (file.content_type or "").endswith("pdf"):
        import io

        from pypdf import PdfReader

        pages = PdfReader(io.BytesIO(data)).pages
        return "\n\n".join(p.extract_text() or "" for p in pages)
    return data.decode("utf-8", errors="replace")


@router.post("/corpus")
async def upload_corpus(
    session_id: str = Form(...),
    kind: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    """Their own writing. `kind` is "background" (facts) or "voice" (style).

    Kept apart on purpose. Background files are formal documents and are read for
    facts only; feeding them in as style is what makes an application read like
    every other application.
    """
    if kind not in ("background", "voice"):
        raise HTTPException(400, "kind must be 'background' or 'voice'")

    stored, total = [], 0
    for file in files:
        data = await file.read()
        text = _read_upload(file, data).strip()
        if not text:
            continue
        total += len(text)
        if total > MAX_UPLOAD:
            raise HTTPException(
                413, f"that is more than {MAX_UPLOAD // 1000} KB of text; upload the few "
                     "documents that matter most rather than everything"
            )

        # The gate at the input end. A voice profile built from generated text
        # teaches the drafting agent to sound generated, and the applicant ends up
        # with a machine imitating a machine imitating them.
        if kind == "voice" and len(text) > 200:
            verdict = await authenticity.judge(file.filename or "sample", text)
            if not verdict.human_written:
                raise HTTPException(422, {
                    "error": "ai_generated",
                    "file": file.filename,
                    "explanation": verdict.explanation,
                    "markers": verdict.markers[:4],
                    "confidence": verdict.confidence,
                })

        stored.append({"label": file.filename or "untitled", "text": text})

    if not stored:
        raise HTTPException(400, "no readable text in those files")

    count = store.save_session_files(session_id, kind, stored)
    return {"kind": kind, "added": len(stored), "total": count,
            "labels": [f["label"] for f in stored]}


@router.post("/speak")
async def record_speaking(
    session_id: str = Form(...),
    prompt_asked: str = Form(""),
    file: UploadFile = File(...),
) -> dict:
    """How they sound out loud, which is not how they write.

    Scripts, talks and presentations are written to be said. The level recorded
    here is the point: a model asked to write a talk reaches for the most
    articulate phrasing it can, and hands a B1 speaker a C1 script they will
    stumble through in front of a room.
    """
    audio = await file.read()
    if not audio:
        raise HTTPException(400, "empty recording")

    mime = (file.content_type or "audio/webm").split(";")[0]
    try:
        profile = await speaking.profile(audio, mime, prompt_asked)
    except Exception as exc:  # noqa: BLE001 - the container is the likely culprit
        raise HTTPException(
            415,
            f"could not read that recording ({mime}). Try a different browser, or upload "
            f"an m4a, mp3 or wav file instead.",
        ) from exc

    store.save_speaking(session_id, profile.model_dump())
    return profile.model_dump()


@router.delete("/speak/{session_id}")
def forget_speaking(session_id: str) -> dict:
    """Throw away a recording. Redoing an answer replaces the profile; deleting one
    has to actually remove it, or a level they rejected keeps shaping the draft."""
    store.delete_speaking(session_id)
    return {"deleted": True}


@router.get("/corpus/{session_id}")
def read_corpus(session_id: str) -> dict:
    spoken = store.get_speaking(session_id)
    return {
        "background": [f["label"] for f in store.get_session_files(session_id, "background")],
        "voice": [f["label"] for f in store.get_session_files(session_id, "voice")],
        "speaking": {"cefr_level": spoken["cefr_level"], "guidance": spoken["guidance"]}
        if spoken else None,
    }


def _evidence_pool(session_id: str | None) -> dict:
    """What "your files" actually means on this run.

    The interface says a claim was "not found in your files". Which files that is
    was previously invisible, and a visitor who uploaded only a writing sample was
    silently checked against the bundled corpus -- someone else's history.
    """
    live = evidence.session_is_live(session_id)
    items = evidence.inventory(session_id)
    return {
        "source": "yours" if live else "bundled demo corpus",
        "count": len(items),
        "labels": [i.label for i in items][:12],
    }


def check(spec: dict, draft: dict, spec_id: str | None = None) -> dict:
    """Compliance, with everything the packet is allowed to have drawn on.

    Every path to a verdict goes through here, so neither the grounding rule nor
    his Gate 3 attestations can be honoured on one route and skipped on another.
    """
    session_id = spec.get("session_id")
    attested = evidence.attested_text(session_id)
    if spec_id:
        attested += "\n" + "\n".join(store.get_answers(spec_id).values())
    # What he vouched for stands as evidence, because he is the source of record
    # about his own life. The draft keeps the list, so the override is auditable.
    attested += "\n" + " ".join(draft.get("attested_claims") or [])
    return _check(spec, draft, attested=attested)


@router.get("/health")
def health() -> dict:
    return {
        "service": "berkas",
        "ok": True,
        "model": os.environ.get("MODEL_ID", "gemini-3.7-flash"),
        "evidence_files": len(evidence.inventory()),   # the bundled fallback corpus
        "default_recipient": os.environ.get("BERKAS_DEMO_RECIPIENT", ""),
    }


# --- Screen 1: read the call ---------------------------------------------------

@router.post("/extract")
async def extract(
    file: UploadFile = File(...),
    session_id: str | None = Form(None),
) -> dict:
    """Read a call document. Reports requirements; scores nothing."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty upload")

    reading = await perception.extract(data, file.content_type or "application/pdf")
    # The spec remembers whose corpus it was built against, so every step after
    # this one draws on the same evidence without being told again.
    spec = StoredSpec(**reading.model_dump(), extracted=reading, session_id=session_id)
    store.save_spec(spec)
    return {"spec_id": spec.spec_id, "spec": spec.model_dump()}


@router.get("/spec/{spec_id}")
def read_spec(spec_id: str) -> dict:
    spec = store.get_spec(spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")
    return spec.model_dump()


# --- Gate 1: correct it before it binds ----------------------------------------

def _normalise_deadline(value: str | None) -> str | None:
    """Accept what a person actually types. "2026-09-7" is a date; ISO says no.

    Only unambiguous repairs: zero-padding a month or day. Anything else is left
    exactly as typed, so compliance can show it back to them rather than a parser
    guessing what they meant.
    """
    if not value:
        return None
    text = str(value).strip()
    parts = text.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        y, m, d = parts
        if len(y) == 4:
            return f"{y}-{int(m):02d}-{int(d):02d}"
    return text


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
    corrected.deadline = _normalise_deadline(corrected.deadline)
    updated = StoredSpec(
        **corrected.model_dump(),
        spec_id=spec.spec_id,
        session_id=spec.session_id,
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
            "compliance": check(spec.model_dump(), draft.model_dump(), spec_id),
            "evidence": _evidence_pool(spec.session_id)}


class Attestation(BaseModel):
    claims: list[str] = Field(default_factory=list)


@router.post("/attest/{draft_id}")
def attest(draft_id: str, body: Attestation) -> dict:
    """GATE 3. He vouches for a claim the checker could not find in his files.

    The checker compares strings, so it cannot see through translation or a
    paraphrase. When it is wrong about him he overrules it -- and, as with Gate 1,
    the override is written down rather than silently allowed.
    """
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    if not body.claims:
        raise HTTPException(400, "nothing to attest")

    draft.attested_claims = sorted(set(draft.attested_claims) | set(body.claims))
    draft.attested_at = datetime.now(timezone.utc).isoformat()
    store.save_draft(draft)

    spec = store.get_spec(draft.spec_id)
    return {"draft": draft.model_dump(),
            "compliance": check(spec.model_dump(), draft.model_dump(), draft.spec_id),
            "evidence": _evidence_pool(spec.session_id if spec else None)}


class DraftEdit(BaseModel):
    sections: dict[str, str]


@router.put("/draft/{draft_id}")
def edit_draft(draft_id: str, body: DraftEdit) -> dict:
    """He fixes what the checker blocked. Re-checked on the way out."""
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    draft.sections = body.sections
    # Edited text is new text: what he vouched for before does not carry over.
    draft.attested_claims, draft.attested_at = [], None
    store.save_draft(draft)
    spec = store.get_spec(draft.spec_id)
    return {"draft": draft.model_dump(),
            "compliance": check(spec.model_dump(), draft.model_dump(), draft.spec_id),
            "evidence": _evidence_pool(spec.session_id if spec else None)}


@router.post("/check/{draft_id}")
def run_check(draft_id: str) -> dict:
    """Plain Python. No model runs in this path."""
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "no such draft")
    spec = store.get_spec(draft.spec_id)
    if not spec:
        raise HTTPException(404, "no such spec")
    return check(spec.model_dump(), draft.model_dump(), draft.spec_id)


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

    verdict = check(spec.model_dump(), draft.model_dump(), draft.spec_id)
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
            human_attested=draft.attested_claims,
        )
    )
    return receipt.model_dump()
