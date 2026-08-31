"""Writes the packet against the corrected spec, in the applicant's own voice.

This agent carries the product's one promise, and it carries it by being unable to
do otherwise: it sees the corpus and the interview answers, and nothing else. When
a sentence would need a fact it does not have, it writes a [NEEDS: ...] marker
instead of a plausible sentence -- and compliance.py treats that marker as a hard
violation, so a packet built on an invented claim cannot be sent.

It is not asked to count words. Models cannot count reliably, and a model that
polices its own compliance is a model marking its own homework. compliance.py
counts, in plain Python, afterwards.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.genai import types
from pydantic import BaseModel, Field

from berkas import classify, evidence
from berkas.models import Draft, StoredSpec
from berkas.runtime import model_id, run_json


class DraftedSection(BaseModel):
    name: str = Field(description="Exactly the section name given in the spec.")
    text: str


class DraftOutput(BaseModel):
    sections: list[DraftedSection] = Field(default_factory=list)


INSTRUCTION = """\
You are drafting an application packet on behalf of the applicant, who is writing
to an institution in a language that may not be their first.

## Rule 1 — never invent a claim about the applicant

Every factual sentence must trace to their corpus or to an answer they gave you. This
includes, and most often fails on:

- **Where they are applying TO.** The host university, city and country. This is the
  single most common invention and the most damaging one. A call for applications
  usually does NOT name the destination -- that is the applicant's choice, and it
  is theirs to state, not yours to supply. If the spec does not name it and they
  have not told you, write:

      [NEEDS: which host university and country you are applying to]

  Never write "MIT", "the United States", "Boston", or any other plausible
  destination. An application naming the wrong university is not a draft with a
  small error in it; it is an application to somewhere they never applied.

- **Other places.** Which employer, which campus, which city.
- **Numbers.** Income, salary, headcount, dates, percentages, durations.
- **Outcomes.** What a project achieved, who used it, what it saved.

When you need a fact you do not have, write the marker and nothing else:

    [NEEDS: the specific thing you would need]

Do not write a plausible value beside a marker. Do not write "approximately" and
then guess. A sentence that contains an invented number is worse than a sentence
that is missing, because it will be submitted and believed.

The packet is checked afterwards by code that verifies every number and every
proper noun against their files. An invented one is caught and the packet is
blocked, so guessing does not save you work -- it only wastes their time.

## Rule 2 — their corpus is evidence, not a style guide

You are given their CVs, cover letters and application answers. **Read them for
facts only.** Do NOT imitate how they are written. They are formal documents
written for machine screening, and they sound like it. The applicant does not.

## Rule 3 — write the way they write

This is not decoration. A packet that reads like every other AI-written
application has failed even if every fact in it is true.

**Do:**
- Open with the actual point, not a pleasantry or a restatement of the question.
- Concrete specifics over abstractions. The boiled-down number, the actual tool,
  the real constraint.
- Vary the rhythm. A short punchy sentence, then a longer flowing one. Not six
  sentences of identical length and shape.
- Say the uncomfortable thing plainly where it is relevant. Do not manage their
  image for them; state the position and move on.
- Plain words. "I built" not "I engineered". "Used" not "utilised". "So" not
  "thus". "But" not "however".

**Never write:**
- "I am applying for X to study Y at Z" as an opener. Every applicant writes that.
- "my objective is to", "my goal is to deepen", "I am passionate about",
  "I am delighted", "it is my firm belief".
- leverage, synergy, streamline, empower, endeavour, robust, cutting-edge,
  seamless, holistic, moreover, furthermore, thus, delve, underscore, pivotal.
- "academic rigor", "technical excellence", "invaluable experience",
  "comprehensive understanding", "significant impact".
- Em-dashes, unless their own writing uses them. A comma, a full stop or a colon.
- Three perfectly parallel clauses in a row. Two is a rhythm; three is a machine.
- A closing paragraph that summarises what you just said.

If a sentence could appear in any other applicant's essay with the name swapped,
delete it and write what is true only of them.

## Rule 4 — obey the spec

Write every required section, using exactly the section names the spec gives.
Match the register it asks for: formal means no slang and no contractions, it does
not mean corporate. A formal register written in their voice is direct, specific and
plain -- not stiff.

Do not count your own words. That is checked afterwards, deterministically.
"""


agent = Agent(
    name="drafting",
    model=model_id(),
    description="Drafts the packet against the corrected spec, grounded in the corpus.",
    instruction=INSTRUCTION,
    output_schema=DraftOutput,
)


async def _corpus_for(spec: StoredSpec) -> tuple[str, dict[str, int] | None]:
    """The corpus as drafting should see it: sent once, with Gemma's routing map.

    Routing narrows which files a section should lean on. It must not multiply how
    much text is sent: an earlier version flattened the corpus separately for each
    section, which turned a 119k-character corpus into a 716k-character prompt for
    a six-section call and timed the request out on Cloud Run.

    A section Gemma routes nothing to is pointed at the whole corpus rather than
    starved. Gemma answered 0 files for one section on one run and 11 on the next,
    from the same corpus; a flaky route is not allowed to gut part of a packet.
    Gemma perceives, it does not decide.
    """
    items = evidence.inventory(spec.session_id)
    names = [s.name for s in spec.sections]
    routed = await classify.route_async(names, items)

    if routed is None:
        return evidence.as_indexed_block(items)[0], None

    # Only the files Gemma actually cited, deduplicated across sections. A section it
    # routed nothing to still sees this pool -- narrowed, never starved.
    cited = {i.label: i for picks in routed.values() for i in picks}
    corpus, index = evidence.as_indexed_block(list(cited.values()) or items)

    lines = []
    for name in names:
        picked = [index[i.label] for i in routed.get(name, []) if i.label in index]
        lines.append(
            f"- {name}: " + (", ".join(f"[{n}]" for n in picked) if picked else
                             "nothing routed — consider the whole corpus for this one")
        )
    guide = (
        "WHICH FILES BEAR ON WHICH SECTION (routed by Gemma). Lean on these first; "
        "you may still use anything else if it is genuinely relevant:\n" + "\n".join(lines)
    )
    counts = {n: len(routed.get(n, [])) for n in names}
    return f"{corpus}\n\n{guide}", counts


async def write(spec: StoredSpec, answers: dict[str, str] | None = None) -> Draft:
    answered = "\n".join(f"Q: {q}\nA: {a}" for q, a in (answers or {}).items())
    corpus, routing = await _corpus_for(spec)
    prompt = (
        f"THE SPEC they corrected and confirmed. These are the rules:\n"
        f"{spec.model_dump_json(indent=2)}\n\n"
        f"THEIR CORPUS -- EVIDENCE ONLY, NOT A STYLE GUIDE. These are formal documents\n"
        f"written for machine screening; read them for facts and ignore how they are\n"
        f"written. This, and the answers below, are the only things you may state as\n"
        f"fact about them:\n{corpus}\n\n"
        f"WHAT THEY TOLD YOU JUST NOW:\n{answered or '(nothing yet)'}\n\n"
        f"HOW THEY WRITE. This comes last because it is what you must actually sound\n"
        f"like. Everything above is what you may say; this is how to say it:\n"
        f"{evidence.voice_profile(spec.session_id)}"
        f"{evidence.speaking_profile(spec.session_id)}\n\n"
        f"Now draft the packet. If nothing above tells you which university, city\n"
        f"or country they are applying TO, you do not know it -- write the marker, and\n"
        f"do not name a plausible one.\n\n"
        f"Before you write each sentence, ask: could this\n"
        f"sentence appear in any other applicant's essay with the name swapped? If\n"
        f"yes, write something true only of them instead. And: does this sentence\n"
        f"contain a place, number or outcome I was not given? If yes, write a\n"
        f"[NEEDS: ...] marker rather than a plausible value."
    )
    result = DraftOutput.model_validate(await run_json(agent, [types.Part(text=prompt)]))
    draft = Draft(
        spec_id=spec.spec_id,
        sections={s.name: s.text for s in result.sections},
    )
    draft.routing = routing
    return draft
