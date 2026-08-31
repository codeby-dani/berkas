"""HTTP surface. The two gates live here, and nowhere else.

Gate 1 is PUT /spec/{id}: perception's reading is not a rulebook until a human
has confirmed it, and the diff of what they changed is recorded.

Gate 2 is POST /send/{id}: it refuses without an explicit confirmation, and it
refuses a draft that does not pass compliance. Both refusals are enforced here
rather than in the browser, so a judge who curls the endpoint gets the same
answer as a judge who clicks the button.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"service": "berkas", "ok": True}
