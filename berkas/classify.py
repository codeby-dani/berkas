"""Gemma sorts the corpus by which section each file can actually speak to.

A second model, doing a job the first one should not: routing. Before this, the
drafting agent received the whole corpus -- 26 files, 119k characters -- for every
section, and had to work out for itself which of them bore on "financial need" and
which on "contribution plan". Now Gemma reads the corpus once and labels it, and
drafting receives only the files relevant to the section it is writing.

Gemma is reached through the Gemini API rather than Vertex, because it is
open-weights: there is no managed Vertex endpoint to call, and self-hosting needs
GPU quota this project does not have (measured: 0, on all 60 GPU types).

This is a routing improvement, not a correctness dependency. Every failure path
falls back to handing over the whole corpus, which is what the system did before
Gemma existed. A demo must not be able to break because a second model is having
a bad night.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from functools import lru_cache

from berkas.evidence import Item

log = logging.getLogger(__name__)

# Confirmed against ai.google.dev/gemma/docs/core/gemma_on_gemini_api
MODEL = os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it")

# Enough of each file for Gemma to tell what it is about, without shipping the corpus twice.
SNIPPET = 700

# Routing is worth a short wait and nothing more. Past this the whole corpus goes
# through and drafting proceeds; a packet is never held up by the optional step.
#
# 20s is deliberately tight. Gemma is served here through the Gemini API on a
# prepay account, and its latency has ranged from ~25s to not answering at all
# within ten minutes, for the same corpus and the same prompt. An optional
# improvement that is sometimes unavailable is fine; one that can hang a draft
# request is not.
TIMEOUT_S = float(os.environ.get("BERKAS_GEMMA_TIMEOUT", "20"))


@lru_cache(maxsize=1)
def _client():
    """Cached: a Client held only for the duration of an expression is garbage
    collected mid-request, and the call fails with "the client has been closed"."""
    from google import genai

    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("no GOOGLE_API_KEY; Gemma is reached through the Gemini API")
    return genai.Client(api_key=key, vertexai=False)


def _blocking_call(sections: list[str], items: list[Item]) -> str:
    reply = _client().models.generate_content(
        model=MODEL,
        contents=_prompt(sections, items),
        # Routing the same corpus twice should not give two answers.
        config={"temperature": 0},
    )
    return reply.text or ""


async def route_async(sections: list[str], items: list[Item]) -> dict[str, list[Item]] | None:
    """`route`, off the event loop and on a clock.

    google-genai's client is synchronous, so calling it directly from an async route
    blocks the whole event loop. Locally, with one request in flight, that is
    invisible. On Cloud Run it is not: a draft request sat blocked for 599 seconds
    and was killed by the request timeout.
    """
    if not items or not sections:
        return None
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(route, sections, items), timeout=TIMEOUT_S
        )
    except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
        log.warning("Gemma routing timed out or failed (%s); using the whole corpus", exc)
        return None


def _prompt(sections: list[str], items: list[Item]) -> str:
    catalogue = "\n\n".join(
        f"[{i}] {item.label}\n{item.text()[:SNIPPET]}" for i, item in enumerate(items)
    )
    return (
        "You are routing evidence to the section of an application it can support.\n\n"
        f"SECTIONS:\n" + "\n".join(f"- {s}" for s in sections) + "\n\n"
        f"FILES:\n{catalogue}\n\n"
        "For each section, list the indices of the files that contain evidence relevant to it. "
        "A file may serve several sections, or none. Be selective: a file that merely mentions "
        "the topic is not evidence for it.\n\n"
        "Reply with JSON only, no prose, in exactly this shape:\n"
        '{"<section name>": [0, 3, 7], "<section name>": [1]}'
    )


def _parse(text: str, sections: list[str], count: int) -> dict[str, list[int]]:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in Gemma's reply")
    raw = json.loads(match.group(0))
    out: dict[str, list[int]] = {}
    for section in sections:
        picked = raw.get(section, [])
        out[section] = [i for i in picked if isinstance(i, int) and 0 <= i < count]
    return out


def route(sections: list[str], items: list[Item]) -> dict[str, list[Item]] | None:
    """Map each section to the corpus files bearing on it. None means 'use everything'."""
    if not items or not sections:
        return None
    try:
        reply = _blocking_call(
            sections, items
        )
        picked = _parse(reply, sections, len(items))
    except Exception as exc:  # noqa: BLE001 - routing is an optimisation, never a dependency
        log.warning("Gemma routing unavailable (%s); using the whole corpus", exc)
        return None

    routed = {s: [items[i] for i in idx] for s, idx in picked.items()}
    if not any(routed.values()):
        log.warning("Gemma routed nothing; using the whole corpus")
        return None
    return routed
