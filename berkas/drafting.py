"""Writes the packet against the corrected spec, in Dani's documented voice.

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

from berkas import evidence
from berkas.models import Draft, StoredSpec
from berkas.runtime import model_id, run_json


class DraftedSection(BaseModel):
    name: str = Field(description="Exactly the section name given in the spec.")
    text: str


class DraftOutput(BaseModel):
    sections: list[DraftedSection] = Field(default_factory=list)


INSTRUCTION = """\
You are drafting an application packet on behalf of Muhammad Dani, writing to an
institution in English, which is his second language.

THE ONE RULE THAT OVERRIDES EVERYTHING ELSE:
Never invent a claim about his experience. Every factual sentence must trace to
something in his corpus or to an answer he gave you. When a section needs a fact
you do not have -- a number, a date, a name, an outcome -- do not write a
plausible one and do not write around it vaguely. Write the marker:

    [NEEDS: the specific thing you would need to finish this sentence]

The marker is not a failure. It is the system working. A packet carrying one
cannot be submitted, which is exactly the intended behaviour.

VOICE:
Write in his documented voice, in the polished register -- the one for emails and
formal writing, not the raw journaling register. Honest and direct, opens with the
actual point rather than a pleasantry, concrete over abstract. No corporate filler,
no em-dashes. He is not a native speaker and does not need to sound like one; he
needs to sound like himself, clearly.

REGISTER AND SECTIONS:
Write every required section the spec lists, using exactly the section names it
gives. Match the register the spec states. Aim to use the space the call allows
without padding: a section that says what it has to say in fewer words is finished.
Do not count your own words -- that is checked afterwards, deterministically.
"""

agent = Agent(
    name="drafting",
    model=model_id(),
    description="Drafts the packet against the corrected spec, grounded in the corpus.",
    instruction=INSTRUCTION,
    output_schema=DraftOutput,
)


async def write(spec: StoredSpec, answers: dict[str, str] | None = None) -> Draft:
    answered = "\n".join(f"Q: {q}\nA: {a}" for q, a in (answers or {}).items())
    prompt = (
        f"THE SPEC he corrected and confirmed. These are the rules:\n"
        f"{spec.model_dump_json(indent=2)}\n\n"
        f"HIS DOCUMENTED VOICE:\n{evidence.voice_profile()}\n\n"
        f"HIS CORPUS -- everything he has already written. This, and the answers "
        f"below, are the only things you may state as fact about him:\n"
        f"{evidence.as_prompt_block()}\n\n"
        f"WHAT HE TOLD YOU JUST NOW:\n{answered or '(nothing yet)'}\n\n"
        f"Draft the packet."
    )
    result = DraftOutput.model_validate(await run_json(agent, [types.Part(text=prompt)]))
    return Draft(
        spec_id=spec.spec_id,
        sections={s.name: s.text for s in result.sections},
    )
