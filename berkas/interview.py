"""Asks only for what the spec demands and the corpus cannot supply.

The point is not to conduct an interview. It is to make the system ask instead of
assume: every question here is a claim the drafting agent would otherwise have had
to invent.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.genai import types
from pydantic import BaseModel, Field

from berkas import evidence
from berkas.models import StoredSpec
from berkas.runtime import model_id, run_json


class Question(BaseModel):
    section: str = Field(description="Which required section this is needed for.")
    question: str = Field(description="One plain question, answerable in a sentence or two.")
    why: str = Field(description="What the call asks for that the corpus does not answer.")
    shape: str = Field(
        default="",
        description=(
            "The SHAPE of a usable answer, as a fill-in-the-blank pattern using "
            "angle-bracket placeholders. Never a specimen answer with invented facts "
            "in it, because a plausible example is something the applicant may simply "
            "accept. Example: '<university>, <country>. <what you would study there>.'"
        ),
    )


class Questions(BaseModel):
    questions: list[Question] = Field(default_factory=list)


INSTRUCTION = """\
You are preparing to help someone write an application. You have their spec (what
the institution requires) and their corpus (everything they have already written
about their own experience).

Ask ONLY for evidence that the spec demands and the corpus does not already
contain. Before asking anything, search the corpus properly -- if the answer is in
there in any form, do not ask for it. An application that asks a person to retype
what they have already written is worse than useless.

Ask at most five questions. Each must be:
- answerable from memory in a sentence or two, not an essay
- about their own experience, never about their opinion of the programme
- specific: "how many people were on the team" beats "tell me about teamwork"

For each question also give `shape`: a fill-in-the-blank pattern showing what a
usable answer looks like, using <angle bracket> placeholders.

    "<university>, <country>. <what you would study there>."
    "<who you would help>, <what you would build or teach for them>."

Write the pattern, never a specimen answer. A plausible-looking example answer is
something the applicant may simply accept, and then the packet contains your
invention wearing their name.

If the corpus genuinely covers everything the spec requires, return an empty list.
That is a real and good answer. Do not invent gaps to look useful.
"""

agent = Agent(
    name="interview",
    model=model_id(),
    description="Finds the gaps between what the call requires and what the corpus holds.",
    instruction=INSTRUCTION,
    output_schema=Questions,
)


async def ask(spec: StoredSpec) -> list[Question]:
    prompt = (
        f"THE SPEC (already corrected by the applicant, so it is authoritative):\n"
        f"{spec.model_dump_json(indent=2)}\n\n"
        f"THE CORPUS:\n{evidence.as_prompt_block(session_id=spec.session_id)}\n\n"
        f"What must you ask them that their own files do not already answer?"
    )
    result = await run_json(agent, [types.Part(text=prompt)])
    return Questions.model_validate(result).questions
