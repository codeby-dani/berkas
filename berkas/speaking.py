"""Listens to someone talk, and writes down how they talk.

A writing sample cannot tell you how a person sounds out loud, and the two are not
the same register. Someone who writes carefully may speak in fragments; someone
fluent on the page may reach for simpler words when a room is looking at them.
Scripts, talks and presentations have to be written for the second one.

The part that matters most here is the level. A model asked to write a talk will
reach for the most articulate phrasing it can, which hands a B1 speaker a C1
script full of words they will stumble over on stage. So the profile records the
level the person actually speaks at, and drafting is told to write to it -- not
above it, and not in a caricature below it either.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.genai import types
from pydantic import BaseModel, Field

from berkas.runtime import model_id, run_json


class SpeakingProfile(BaseModel):
    transcript: str = Field(description="What they actually said, verbatim, including fillers and false starts.")
    cefr_level: str = Field(description="Their spoken level in this language: A1, A2, B1, B2, C1 or C2.")
    level_evidence: str = Field(description="What in the recording puts them at that level. Quote them.")
    typical_words: list[str] = Field(default_factory=list, description="Words and phrases they actually reached for.")
    fillers: list[str] = Field(default_factory=list, description="Their hesitations and connectors, verbatim.")
    sentence_style: str = Field(description="How their spoken sentences are built. Length, restarts, connectors.")
    avoid: list[str] = Field(
        default_factory=list,
        description="Words above their level that a script must not put in their mouth.",
    )
    guidance: str = Field(
        description="Two or three sentences telling a writer how to script for this speaker."
    )


INSTRUCTION = """\
You are listening to someone speak so that scripts can later be written for them
to say out loud. Report how they actually speak. Do not improve them.

Transcribe verbatim first, including "uh", false starts, repeated words and any
switching between languages. Those are the data, not noise to be cleaned up.

Then assess:

- **cefr_level**: the level they genuinely speak at, A1 to C2. Be accurate rather
  than generous. Getting this wrong in the flattering direction is the failure
  that matters: a B1 speaker handed a C1 script will stumble through it in front
  of a room, and it will be your fault.
- **typical_words**: what they actually reached for, not what they could have.
- **fillers**: their own hesitations, verbatim. "yeah", "like", "jadi", "gitu".
- **avoid**: words a script writer might reach for that sit above this speaker's
  level, that they would trip on. Be specific and concrete.
- **guidance**: how to write something for this person to say aloud and sound like
  themselves. Mention sentence length, rhythm, and level.

If they speak a language other than English, or switch between languages, say so
in `sentence_style` and assess the level of the language they mostly used.

Never flatter. A profile that overstates someone's level produces a script that
embarrasses them.
"""

agent = Agent(
    name="speaking",
    model=model_id(),
    description="Profiles how a person speaks, including the level they speak at.",
    instruction=INSTRUCTION,
    output_schema=SpeakingProfile,
)


async def profile(audio: bytes, mime_type: str, prompt_asked: str = "") -> SpeakingProfile:
    parts = [
        types.Part.from_bytes(data=audio, mime_type=mime_type),
        types.Part(text=(
            f"They were answering: {prompt_asked}\n\n" if prompt_asked else ""
        ) + "Transcribe them verbatim, then profile how they speak."),
    ]
    return SpeakingProfile.model_validate(await run_json(agent, parts))
