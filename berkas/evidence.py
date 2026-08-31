"""The corpus: things the applicant has already written.

This is the whole basis of the promise in PRD.md section 1. The drafting agent
sees this and the interview answers, and nothing else. If a claim is not in here
and was not answered out loud, it does not go in the packet.

Two kinds, doing two different jobs, and keeping them apart matters:

  background  what may be stated as fact about them
  voice       how it should sound

Mixing them is what produced the first draft's corporate slop: the background
files are formal CVs written for machine screening, and a model given them as
undifferentiated context imitates their register.

A corpus can come from either of two places. An uploaded one, held in Firestore
against a session, is what any visitor gets. The bundled one on disk is the
author's own, baked into the container and gitignored, and is used only when a
session has uploaded nothing -- so the demo works out of the box and a fork works
for whoever cloned it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("BERKAS_CORPUS", Path(__file__).resolve().parent.parent / "corpus"))

# Gemini 3.x has room for far more, but an unbounded prompt is an unpredictable
# one, and the newest material is the material worth keeping.
MAX_CHARS = 120_000

VOICE_FILENAME = "My Writing Voice.md"


@dataclass(frozen=True)
class Item:
    label: str
    body: str

    def text(self) -> str:
        return self.body


def _from_disk() -> list[Item]:
    """The bundled corpus. Empty is a valid state."""
    if not ROOT.exists():
        return []
    files = [p for p in ROOT.rglob("*.md") if p.is_file() and p.name != VOICE_FILENAME]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        Item(label=str(p.relative_to(ROOT)), body=p.read_text(encoding="utf-8", errors="replace"))
        for p in files
    ]


def _voice_from_disk() -> str:
    path = ROOT / "voice" / VOICE_FILENAME
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def session_is_live(session_id: str | None) -> bool:
    """Has this visitor given Berkas anything at all -- files, or a recording?

    The distinction matters more than it looks. Falling back per-pile means a
    visitor who uploads only a writing sample gets their claims checked against
    whoever's corpus happens to be bundled -- a stranger's CV, silently. The
    fallback is for an empty session, not an incomplete one.
    """
    if not session_id:
        return False
    from berkas import store

    return bool(
        store.get_session_files(session_id, "background")
        or store.get_session_files(session_id, "voice")
        or store.get_speaking(session_id)
    )


def inventory(session_id: str | None = None) -> list[Item]:
    """Background files: what may be stated as fact.

    Returns an EMPTY list for a session that gave something but no background.
    That is the honest answer: they have told Berkas how they write and how they
    sound, and nothing about what they have done. Every claim then gets marked,
    which is correct -- far better than borrowing somebody else's history.
    """
    if session_is_live(session_id):
        from berkas import store

        return [
            Item(label=f["label"], body=f["text"])
            for f in store.get_session_files(session_id, "background")
        ]
    return _from_disk()


def voice_profile(session_id: str | None = None) -> str:
    """How they write. Read by drafting, and by nothing else."""
    if session_is_live(session_id):
        from berkas import store

        uploaded = store.get_session_files(session_id, "voice")
        if uploaded:
            return "\n\n".join(
                f"--- something they wrote: {f['label']} ---\n{f['text']}" for f in uploaded
            )
        return ""
    return _voice_from_disk()


def as_indexed_block(items: list[Item]) -> tuple[str, dict[str, int]]:
    """The corpus once, numbered, plus a label -> index map.

    Routing must not mean sending the corpus once per section. Each file appears a
    single time and sections refer to it by number; six sections that each cite ten
    files cost one corpus, not six.
    """
    chunks: list[str] = []
    index: dict[str, int] = {}
    budget = MAX_CHARS
    for item in items:
        if len(item.body) > budget:
            break
        index[item.label] = len(chunks)
        chunks.append(f"[{len(chunks)}] {item.label}\n{item.body}")
        budget -= len(item.body)
    return "\n\n".join(chunks), index


def as_prompt_block(items: list[Item] | None = None, session_id: str | None = None) -> str:
    """The corpus flattened for a prompt, truncated at MAX_CHARS."""
    pool = inventory(session_id) if items is None else items
    return as_indexed_block(pool)[0]


def attested_text(session_id: str | None = None) -> str:
    """Everything the packet is allowed to draw facts from.

    The voice material is deliberately excluded: it governs how they write, not
    what is true about them, and letting it attest claims would launder its
    examples into evidence.
    """
    return "\n".join(i.body for i in inventory(session_id))


def speaking_profile(session_id: str | None = None) -> str:
    """How they sound out loud, folded into the voice guidance.

    Included even for written packets, because the level travels: an applicant who
    speaks at B1 is poorly served by a personal statement written at C1. They have
    to be able to defend every sentence of it in an interview.
    """
    if not session_id:
        return ""
    from berkas import store

    p = store.get_speaking(session_id)
    if not p:
        return ""
    return (
        f"\n\n## How they speak (recorded)\n"
        f"Level: **{p.get('cefr_level', '?')}**. {p.get('level_evidence', '')}\n"
        f"Sentence style: {p.get('sentence_style', '')}\n"
        f"Words they actually use: {', '.join(p.get('typical_words', [])[:20])}\n"
        f"**Do not put these in their mouth** (above their level): "
        f"{', '.join(p.get('avoid', [])[:20])}\n"
        f"{p.get('guidance', '')}\n"
        f"Write at their level. Not above it, and not a caricature below it either."
    )
