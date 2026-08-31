"""The corpus Berkas is allowed to draw on: things Dani has already written.

This is the whole basis of the promise in PRD.md section 1. The drafting agent
sees this and the interview answers, and nothing else. If a claim is not in here
and was not answered out loud, it does not go in the packet.

The corpus is personal career history, so it is baked into the container but kept
out of the public repository (gitignored, not dockerignored). Without it the app
still runs: the inventory comes back empty and the interview agent, finding
nothing, asks for everything. That degradation is deliberate -- a judge who clones
the repo gets a working system that simply knows nothing about the author yet.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("BERKAS_CORPUS", Path(__file__).resolve().parent.parent / "corpus"))

# Gemini 3.x has room for far more, but an unbounded prompt is an unpredictable
# one, and the newest material is the material worth keeping.
MAX_CHARS = 120_000


@dataclass(frozen=True)
class Item:
    label: str
    path: Path

    def text(self) -> str:
        return self.path.read_text(encoding="utf-8", errors="replace")


def inventory() -> list[Item]:
    """Everything the corpus holds, as (label, path). Empty is a valid state."""
    if not ROOT.exists():
        return []
    items = [
        Item(label=str(p.relative_to(ROOT)), path=p)
        for p in sorted(ROOT.rglob("*.md"))
        if p.is_file() and p.name != "My Writing Voice.md"
    ]
    return items


def voice_profile() -> str:
    """Dani's documented writing voice. Drafting reads this; nothing else does."""
    path = ROOT / "voice" / "My Writing Voice.md"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def as_prompt_block() -> str:
    """The corpus, flattened for a prompt, newest first, truncated at MAX_CHARS."""
    chunks: list[str] = []
    budget = MAX_CHARS
    for item in sorted(inventory(), key=lambda i: i.path.stat().st_mtime, reverse=True):
        body = item.text()
        if len(body) > budget:
            break
        chunks.append(f"--- {item.label} ---\n{body}")
        budget -= len(body)
    return "\n\n".join(chunks)
