"""Placeholder root agent — proves the ADK + Gemini 3.x + Cloud Run path end to end.

The agent logic is deliberately trivial. It exists so the deployment pipeline is
verified before the real idea lands; only this file changes afterwards.
"""

import os
import datetime

from google.adk.agents import Agent

MODEL_ID = os.environ.get("MODEL_ID", "gemini-3.7-flash")


def current_time(timezone_offset_hours: int = 8) -> dict:
    """Return the current time at a UTC offset.

    Args:
        timezone_offset_hours: Hours ahead of UTC. Defaults to 8 (WITA, Bali).

    Returns:
        A dict with the ISO-8601 timestamp and the offset used.
    """
    tz = datetime.timezone(datetime.timedelta(hours=timezone_offset_hours))
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now(tz).isoformat(),
        "utc_offset_hours": timezone_offset_hours,
    }


root_agent = Agent(
    name="skeleton_agent",
    model=MODEL_ID,
    description="Deployment smoke-test agent.",
    instruction=(
        "You are a deployment smoke test. Answer briefly. "
        "When asked the time, call the current_time tool rather than guessing."
    ),
    tools=[current_time],
)
