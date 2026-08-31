"""Reads the call document and reports what it requires. It never scores anything.

The split matters: this agent is allowed to be wrong, because a human corrects it
before anything it says becomes binding. What it is not allowed to do is decide
whether a draft passes -- that lives in compliance.py, in plain Python.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.genai import types

from berkas.models import ExtractedSpec
from berkas.runtime import model_id, run_json

INSTRUCTION = """\
You are reading a call for applications on behalf of someone who is about to apply
to it in a language that is not their first.

Report ONLY what the document itself requires. Extract:

- programme: the name of the programme or role being applied to.
- deadline: the submission deadline as YYYY-MM-DD. null if the document states none.
- sections: every piece of writing the applicant must produce. For each, give the
  name as the document names it, its word_cap as an integer, and whether it is
  required. Set word_cap to null when the document states no limit -- never guess a
  limit, and never carry a limit over from another section.
- voice_register: how the document expects to be written to, in a short phrase
  (for example "formal, first person, academic").
- extra_requirements: any other stated rule you cannot express as a section --
  file formats, attachments, eligibility statements, signatures.

Rules you must follow:
- Report only what is on the page. If the document does not state a word limit,
  that is null, not a number you consider sensible.
- If a limit is given in characters or pages rather than words, put it in
  extra_requirements verbatim and leave word_cap null. Do not convert it.
- Do not evaluate, rank, advise, or judge the applicant's chances. You are reading
  a document, not assessing a candidate.
"""

agent = Agent(
    name="perception",
    model=model_id(),
    description="Reports what a call for applications requires.",
    instruction=INSTRUCTION,
    output_schema=ExtractedSpec,
)


async def extract(document: bytes, mime_type: str) -> ExtractedSpec:
    """Read a call document (PDF or photograph) and report its requirements."""
    parts = [
        types.Part.from_bytes(data=document, mime_type=mime_type),
        types.Part(text="Read this call for applications and report what it requires."),
    ]
    return ExtractedSpec.model_validate(await run_json(agent, parts))
