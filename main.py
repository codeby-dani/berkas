"""Berkas — one Cloud Run service: the API, and the three screens it serves."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from berkas.api import router

app = FastAPI(title="Berkas", description="An application-filing partner.")
app.include_router(router, prefix="/api")

# Mounted last: the catch-all must not shadow /api.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")
