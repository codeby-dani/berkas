"""The frozen contracts from PRD.md section 4. Everything downstream reads these."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return uuid.uuid4().hex[:12]


class Section(BaseModel):
    name: str
    word_cap: int | None = Field(
        default=None, description="Maximum words. null means the call states no limit."
    )
    required: bool = True


class ExtractedSpec(BaseModel):
    """What perception reports. Becomes the rulebook only after a human corrects it."""

    programme: str
    deadline: str | None = Field(default=None, description="ISO-8601 date, YYYY-MM-DD.")
    sections: list[Section] = Field(default_factory=list)
    # Named voice_register, not register: a field called "register" shadows
    # BaseModel.register, and an unset default then serialises as a bound method.
    voice_register: str = ""
    extra_requirements: list[str] = Field(default_factory=list)


class StoredSpec(ExtractedSpec):
    spec_id: str = Field(default_factory=_id)
    # Whose uploaded corpus this packet draws on. None means the bundled one.
    session_id: str | None = None
    created_at: str = Field(default_factory=_now)

    # What perception originally said, kept immutable so the correction is auditable
    # afterwards: the diff between this and the live fields is the human's edit.
    extracted: ExtractedSpec | None = None

    # Gate 1. Until a human has been through it, this is a reading, not a rulebook.
    human_corrected: bool = False
    corrected_fields: list[str] = Field(default_factory=list)
    corrected_at: str | None = None


class Draft(BaseModel):
    draft_id: str = Field(default_factory=_id)
    spec_id: str
    sections: dict[str, str] = Field(default_factory=dict)
    # How many corpus files Gemma routed to each section. None when it was unavailable.
    routing: dict[str, int] | None = None

    # GATE 3. Claims the checker could not find in his files and he vouched for anyway.
    # The checker is string containment, so it cannot see through translation: a section
    # in Indonesian saying "Sistem Informasi" is flagged against a corpus that attests
    # the same credential in English. When the machine is wrong about him, he overrules
    # it -- and the override is recorded rather than merely permitted.
    attested_claims: list[str] = Field(default_factory=list)
    attested_at: str | None = None
    created_at: str = Field(default_factory=_now)


class Receipt(BaseModel):
    receipt_id: str = Field(default_factory=_id)
    sent_at: str = Field(default_factory=_now)
    gmail_message_id: str
    gmail_thread_id: str
    to: str
    subject: str
    spec_id: str
    draft_id: str
    compliance_passed: bool = True
    confirmed_by_human_at: str
    # Whatever he personally vouched for at Gate 3, carried onto the receipt so the
    # record of what was sent says who stood behind which claim.
    human_attested: list[str] = Field(default_factory=list)
