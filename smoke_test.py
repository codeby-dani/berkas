"""Local end-to-end check: ADK runner -> Gemini 3.x on Vertex -> tool call."""
import asyncio, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
for line in pathlib.Path(__file__).with_name(".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())

from google.adk.runners import InMemoryRunner
from google.genai import types
from agent.agent import root_agent


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="smoke")
    session = await runner.session_service.create_session(app_name="smoke", user_id="dani")
    msg = types.Content(role="user", parts=[types.Part(text="What time is it in Bali right now?")])
    async for ev in runner.run_async(user_id="dani", session_id=session.id, new_message=msg):
        for p in (ev.content.parts if ev.content and ev.content.parts else []):
            if p.function_call:
                print("TOOL CALL   :", p.function_call.name, dict(p.function_call.args))
            if p.function_response:
                print("TOOL RESULT :", p.function_response.response)
            if p.text:
                print("MODEL       :", p.text.strip())


asyncio.run(main())
