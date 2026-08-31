"""The deterministic gate. No model runs in this path, ever.

Gemini reports what the call document requires. This module decides whether a
draft may be submitted. Keeping the verdict in plain Python is the whole point:
the same draft yields the same result every time, the rules are auditable by
reading them, and a well-written essay cannot argue its way past a word cap.

Standard library only, so the tests cannot fail for environmental reasons.
"""

from __future__ import annotations

import re
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


# Capitalised words that carry no claim: they are grammar, not evidence.
_HARMLESS = {
    "I", "A", "An", "The", "This", "That", "These", "Those", "My", "His", "Her",
    "Their", "Our", "It", "In", "On", "At", "As", "And", "But", "So", "If", "When",
    "While", "During", "After", "Before", "For", "From", "To", "With", "Without",
    "By", "Of", "Or", "Not", "No", "Yes", "Both", "Each", "Every", "Where", "What",
    "Which", "Who", "How", "Why", "There", "Here", "Then", "Now", "First", "Second",
    "Third", "Finally", "However", "Because", "Since", "Although", "Upon", "Over",
    "Under", "Between", "Within", "Through", "English", "Indonesian", "Indonesia",
    # Ubiquitous acronyms. They name a field, not a place he claims to have been.
    "AI", "ML", "API", "APIs", "IT", "UI", "UX", "PDF", "CV", "HR", "GPA", "USD",
    "IDR", "USA", "UK", "EU", "PhD", "BSc", "MSc", "IoT", "LLM", "LLMs",
}

# Structural numbers: list markers, "three ways", "two years" are rhetoric, not evidence.
_SMALL = 10


def _normalise(text: str) -> str:
    """Lowercased, with digit separators stripped, for containment tests."""
    return re.sub(r"[,\u202f\u00a0]", "", text.lower())


def _claimed_numbers(text: str) -> set[str]:
    """Numeric tokens a reader would take as fact. 1-10 are treated as rhetoric."""
    out = set()
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        clean = raw.replace(",", "")
        try:
            if float(clean) < _SMALL and "." not in clean:
                continue
        except ValueError:
            continue
        out.add(clean)
    return out


# Words that introduce a place or an affiliation. A capitalised run right after one
# of these is a claim about where he studied, worked, or is going -- the claims an
# institution acts on. Indonesian included, because a section may be written in it.
_LOCATORS = {
    "at", "in", "to", "from", "with", "for", "of", "into", "toward", "towards",
    "di", "ke", "dari", "pada", "menuju",
}
_ARTICLES = {"the", "a", "an", "my", "his", "her", "their", "our"}


def _claimed_names(text: str) -> set[str]:
    """Named places and institutions: a capitalised run introduced by a locator.

    Narrow on purpose, and narrowed by watching it fail. Flagging every capitalised
    phrase caught the real inventions -- MIT, Amerika Serikat, Coventry University --
    and also flagged "Public Relations", "Personal Productivity", "Assistive AI
    Tools" and "Media Documentation", which are ordinary English words in his own
    headings and claim nothing. Six blocks per run, mostly noise, is not a strict
    checker; it is a checker nobody reads.

    So the rule keys on grammar instead of capitalisation alone. "at MIT", "di
    Amerika Serikat", "from Telkom University" assert where he was. A title-case
    heading does not assert anything, and is left alone.
    """
    out: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        words = [w.strip(".,;:()'\u2019\"") for w in sentence.split()]
        i = 0
        while i < len(words):
            if words[i].lower() not in _LOCATORS:
                i += 1
                continue
            j = i + 1
            while j < len(words) and words[j].lower() in _ARTICLES:
                j += 1
            run: list[str] = []
            while j < len(words):
                word = words[j]
                if word and word[0].isupper() and word not in _HARMLESS and word[0].isalpha():
                    run.append(word)
                    j += 1
                elif run and word.lower() in {"of", "and", "the", "de", "dan"}:
                    j += 1
                else:
                    break
            # A single ordinary-looking capitalised word after a locator is usually a
            # sentence artefact; an acronym or a multi-word name is a claim.
            if len(run) >= 2 or (len(run) == 1 and run[0].isupper() and 2 <= len(run[0]) <= 6):
                out.update(run)
            i = max(j, i + 1)
    return out


def unverified(text: str, attested: str) -> list[str]:
    """Claims in `text` that do not appear anywhere in `attested`.

    This is the promise -- "never invents a claim about your experience" -- made
    checkable. Until this existed, the promise rested on the drafting agent
    choosing to mark its own gaps, which is a model marking its own homework: the
    exact thing the rest of this system refuses to do. It fabricated a household
    income of "2,000 USD" in the same sentence as a [NEEDS: ...] marker.

    Deliberately narrow. It checks places, names and numbers, because those are
    what an institution acts on and what a reader cannot verify. It does not try to
    judge whether a sentence is *true* -- only whether the specifics in it came
    from somewhere.
    """
    haystack = _normalise(attested)
    missing = [n for n in _claimed_numbers(text) if n not in haystack]
    missing += [w for w in _claimed_names(text) if w.lower() not in haystack]
    return sorted(set(missing))


def _today() -> date:
    return datetime.now(LOCAL_TZ).date()


def check(
    spec: dict,
    draft: dict,
    today: date | None = None,
    attested: str | None = None,
) -> dict:
    """Return {passed, checks, violations} for a draft against a corrected spec.

    Every rule is total: it either fires or it does not, for any input. Rules are
    all evaluated -- the caller is shown every violation at once, not the first
    one, so a fix-and-recheck cycle converges instead of playing whack-a-mole.
    """
    today = today or _today()
    bodies = draft.get("sections") or {}
    # The spec is attested by definition: he confirmed it at Gate 1.
    ground = None if attested is None else attested + " " + str(spec)
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

        if ground is not None and body:
            loose = unverified(body, ground)
            if loose:
                current["ok"] = False
                violations.append(
                    {
                        "section": name,
                        "rule": "unverified_claim",
                        "actual": loose[:6],
                        "limit": 0,
                        "message": (
                            f"{name} states something not found in your files: "
                            f"{', '.join(loose[:4])} — cannot submit"
                        ),
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
        try:
            due = date.fromisoformat(str(deadline).strip())
        except ValueError:
            # The deadline is a field a human edits at Gate 1, so it can be anything
            # they typed. An unreadable one is a violation to be shown, not an
            # exception that takes down the request: "2026-09-7" cost a 500 and an
            # error message that read "{}".
            violations.append(
                {
                    "section": None,
                    "rule": "deadline_unreadable",
                    "actual": deadline,
                    "limit": "YYYY-MM-DD",
                    "message": f'the deadline "{deadline}" is not a date — write it as '
                               f"YYYY-MM-DD, for example 2026-09-07",
                }
            )
            return {"passed": False, "checks": checks, "violations": violations}
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
