"""The deterministic gate. No model runs in this path, ever.

Gemini reports what the call document requires. This module decides whether a
draft may be submitted. Keeping the verdict in plain Python is the whole point:
the same draft yields the same result every time, the rules are auditable by
reading them, and a well-written essay cannot argue its way past a word cap.

Standard library only, so the tests cannot fail for environmental reasons.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

# Dani files from Bali; "has the deadline passed" is a question about his calendar.
LOCAL_TZ = ZoneInfo("Asia/Makassar")

# The drafting agent emits this marker rather than inventing a claim it cannot
# ground in the corpus. A packet still carrying one is not ready to leave.
UNGROUNDED_MARKER = "[NEEDS:"


def count_words(text: str) -> int:
    """Words are whitespace-delimited tokens.

    Documented because it is the one number a judge could reasonably quibble
    with, and an undocumented count is indistinguishable from a fudged one.
    Hyphenated words count as one. Runs of whitespace collapse.
    """
    return len(text.split())


def _today() -> date:
    return datetime.now(LOCAL_TZ).date()


def check(spec: dict, draft: dict, today: date | None = None) -> dict:
    """Return {passed, checks, violations} for a draft against a corrected spec.

    Every rule is total: it either fires or it does not, for any input. Rules are
    all evaluated -- the caller is shown every violation at once, not the first
    one, so a fix-and-recheck cycle converges instead of playing whack-a-mole.
    """
    today = today or _today()
    bodies = draft.get("sections") or {}
    checks: list[dict] = []
    violations: list[dict] = []

    for section in spec.get("sections") or []:
        name = section["name"]
        cap = section.get("word_cap")
        required = bool(section.get("required"))
        body = (bodies.get(name) or "").strip()
        words = count_words(body)

        checks.append({"section": name, "words": words, "cap": cap, "ok": True})
        current = checks[-1]

        if required and not body:
            current["ok"] = False
            violations.append(
                {
                    "section": name,
                    "rule": "missing_section",
                    "actual": 0,
                    "limit": None,
                    "message": f"{name} is required and empty — cannot submit",
                }
            )
            continue

        if cap is not None and words > cap:
            current["ok"] = False
            violations.append(
                {
                    "section": name,
                    "rule": "word_cap",
                    "actual": words,
                    "limit": cap,
                    "message": f"{name} is {words} words against a {cap} cap — cannot submit",
                }
            )

        if UNGROUNDED_MARKER in body:
            current["ok"] = False
            violations.append(
                {
                    "section": name,
                    "rule": "ungrounded_claim",
                    "actual": body.count(UNGROUNDED_MARKER),
                    "limit": 0,
                    "message": f"{name} contains an unsupported claim — cannot submit",
                }
            )

    deadline = spec.get("deadline")
    if deadline:
        due = date.fromisoformat(deadline)
        if due < today:
            violations.append(
                {
                    "section": None,
                    "rule": "deadline_passed",
                    "actual": today.isoformat(),
                    "limit": deadline,
                    "message": f"the deadline was {deadline} — cannot submit",
                }
            )

    return {"passed": not violations, "checks": checks, "violations": violations}
