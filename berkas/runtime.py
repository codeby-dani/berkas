"""Running an ADK agent once and getting its answer back.

Berkas drives the agents from its own HTTP routes rather than through the ADK web
server, because the product is three purpose-built screens, not a chat window.
The agents themselves are ordinary google.adk Agents.
"""

from __future__ import annotations

import json
import os

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

APP_NAME = "berkas"
USER_ID = "dani"


def model_id() -> str:
    # Gemini 3.x is served only from location "global"; see agent/.env.
    return os.environ.get("MODEL_ID", "gemini-3.7-flash")


async def run(agent: Agent, parts: list[types.Part]) -> str:
    """Send one turn to an agent and return the final text it produced."""
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    message = types.Content(role="user", parts=parts)

    final = ""
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    ):
        for part in event.content.parts if event.content and event.content.parts else []:
            if part.text:
                final = part.text
    return final


async def run_json(agent: Agent, parts: list[types.Part]) -> dict:
    """Same, for agents declared with an output_schema."""
    text = (await run(agent, parts)).strip()
    if text.startswith("```"):  # models occasionally fence structured output anyway
        text = text.split("```", 2)[1].removeprefix("json").strip()
    return json.loads(text)
