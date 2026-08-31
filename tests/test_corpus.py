"""Bringing your own writing.

Berkas ships with the author's corpus baked in, which makes the demo work out of
the box and makes the app useless to anyone else. A visitor uploads their own, and
it is kept in two piles on purpose:

    background   what may be stated as fact about them
    voice        how it should sound

Mixing them is what produced the first draft's corporate slop -- background files
are formal documents written for screening, and a model handed them as
undifferentiated context imitates their register.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    from berkas import authenticity, store

    sessions: dict[str, dict] = {}

    # The authenticity gate calls a model; these tests are about plumbing, so it is
    # stubbed to "a person wrote this" and exercised on its own below.
    async def human(label, text):
        return authenticity.Verdict(
            human_written=True, confidence="high", markers=[], explanation="fine"
        )

    monkeypatch.setattr(authenticity, "judge", human)
    monkeypatch.setattr(store, "save_speaking", lambda s, p: sessions.setdefault(s, {}).__setitem__("speaking", p))
    monkeypatch.setattr(store, "get_speaking", lambda s: sessions.get(s, {}).get("speaking") or None)
    monkeypatch.setattr(store, "delete_speaking", lambda s: sessions.setdefault(s, {}).__setitem__("speaking", None))

    def save(session_id, kind, files):
        bucket = sessions.setdefault(session_id, {}).setdefault(kind, [])
        bucket.extend(files)
        return len(bucket)

    monkeypatch.setattr(store, "save_session_files", save)
    monkeypatch.setattr(
        store, "get_session_files",
        lambda session_id, kind: sessions.get(session_id, {}).get(kind, []),
    )
    import main

    c = TestClient(main.app)
    c.sessions = sessions
    return c


def upload(client, session, kind, name, body):
    return client.post(
        "/api/corpus",
        data={"session_id": session, "kind": kind},
        files=[("files", (name, io.BytesIO(body.encode()), "text/plain"))],
    )


def test_uploaded_background_replaces_the_bundled_corpus(client):
    from berkas import evidence

    upload(client, "s1", "background", "cv.md", "I worked at Kedai Kopi as a barista.")
    items = evidence.inventory("s1")
    assert [i.label for i in items] == ["cv.md"]
    assert "Kedai Kopi" in items[0].body


def test_a_session_that_uploaded_nothing_falls_back_to_the_bundled_corpus(client):
    """The demo has to work on a fresh visit, and a fork has to work for whoever cloned it."""
    from berkas import evidence

    assert evidence.inventory("never-uploaded") == evidence.inventory(None)


def test_voice_and_background_stay_in_separate_piles(client):
    """The whole reason the intake has two slots."""
    from berkas import evidence

    upload(client, "s2", "background", "cv.md", "Six years as a marine biologist.")
    upload(client, "s2", "voice", "dm.txt", "yeah so.. idk, kinda tired today ngl")

    facts = " ".join(i.body for i in evidence.inventory("s2"))
    style = evidence.voice_profile("s2")

    assert "marine biologist" in facts and "kinda tired" not in facts
    assert "kinda tired" in style and "marine biologist" not in style


def test_the_voice_sample_is_never_usable_as_evidence(client, tmp_path, monkeypatch):
    """Style must not launder itself into fact, or the packet can cite a turn of phrase.

    The bundled corpus is pointed at an empty directory here, because with a real
    one behind it the assertion passes for the wrong reason -- the author's own CVs
    mention half of Indonesia.
    """
    from berkas import evidence

    monkeypatch.setattr(evidence, "ROOT", tmp_path)
    upload(client, "s3", "background", "cv.md", "Six years as a marine biologist.")
    upload(client, "s3", "voice", "dm.txt", "honestly Kalimantan traffic ruined my whole week")

    assert "marine biologist" in evidence.attested_text("s3")
    assert "Kalimantan" not in evidence.attested_text("s3")


def test_uploads_accumulate_rather_than_overwrite(client):
    from berkas import evidence

    upload(client, "s4", "background", "cv.md", "One thing.")
    upload(client, "s4", "background", "letter.md", "Another thing.")
    assert len(evidence.inventory("s4")) == 2


def test_an_unreadable_upload_is_refused_not_silently_stored(client):
    r = client.post(
        "/api/corpus",
        data={"session_id": "s5", "kind": "background"},
        files=[("files", ("empty.txt", io.BytesIO(b"   "), "text/plain"))],
    )
    assert r.status_code == 400


def test_the_kind_must_be_one_of_the_two_piles(client):
    r = upload(client, "s6", "everything", "x.md", "text")
    assert r.status_code == 400


def test_listing_shows_what_a_session_holds(client):
    upload(client, "s7", "background", "cv.md", "text")
    upload(client, "s7", "voice", "dm.txt", "text")
    assert client.get("/api/corpus/s7").json() == {
        "background": ["cv.md"], "voice": ["dm.txt"], "speaking": None,
    }


# --- the gate at the input end -------------------------------------------------

def test_a_generated_voice_sample_is_refused(client, monkeypatch):
    """Garbage in, garbage out, and here the garbage is the whole point.

    A voice profile built from AI-generated text teaches the drafting agent to
    sound like an AI. The applicant would get a machine imitating a machine
    imitating them, and would have no way to tell.
    """
    from berkas import authenticity

    async def generated(label, text):
        return authenticity.Verdict(
            human_written=False, confidence="high",
            markers=["passionate about leveraging cutting-edge technology"],
            explanation="Corporate abstractions with nothing concrete underneath.",
        )

    monkeypatch.setattr(authenticity, "judge", generated)
    r = upload(client, "s8", "voice", "linkedin.md",
               "I am passionate about leveraging cutting-edge technology to drive impact. " * 8)

    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["error"] == "ai_generated"
    # The refusal must quote the sample, or the person cannot check it.
    assert detail["markers"]
    assert client.sessions.get("s8") is None, "a refused sample must not be stored"


def test_background_files_are_not_put_through_the_authenticity_gate(client, monkeypatch):
    """A CV is allowed to read like a CV. It is evidence, not a voice sample."""
    from berkas import authenticity

    async def boom(label, text):
        raise AssertionError("background must not be judged for authorship")

    monkeypatch.setattr(authenticity, "judge", boom)
    assert upload(client, "s9", "background", "cv.md", "Six years as a marine biologist. " * 20).status_code == 200


def test_a_very_short_voice_sample_skips_the_gate(client, monkeypatch):
    """No detector can judge two sentences. Refusing on a coin flip is worse than allowing."""
    from berkas import authenticity

    async def boom(label, text):
        raise AssertionError("too short to judge")

    monkeypatch.setattr(authenticity, "judge", boom)
    assert upload(client, "s10", "voice", "note.txt", "yeah ok sure").status_code == 200


def test_the_spoken_level_reaches_the_drafting_prompt(client, monkeypatch):
    """The reason the recording exists: a B1 speaker must not be handed a C1 script."""
    from berkas import evidence, store

    monkeypatch.setattr(store, "get_speaking", lambda s: {
        "cefr_level": "B1", "level_evidence": "short clauses, basic connectors",
        "sentence_style": "short, restarts often", "typical_words": ["tool", "stuff"],
        "avoid": ["subsequently", "initially conceived"],
        "guidance": "Short clauses. Plain everyday words.",
    })
    block = evidence.speaking_profile("s11")
    assert "B1" in block
    assert "subsequently" in block
    assert "Do not put these in their mouth" in block


def test_a_deleted_recording_stops_shaping_the_draft(client, monkeypatch):
    """Deleting has to actually remove it.

    Recording again replaces the profile, but deleting one must clear it: a level
    the applicant rejected that keeps steering every draft is worse than no level
    at all, because nothing on screen says it is still there.
    """
    from berkas import evidence, store

    store.save_speaking("s12", {"cefr_level": "B1", "guidance": "short clauses",
                                "avoid": ["subsequently"], "typical_words": [],
                                "level_evidence": "", "sentence_style": ""})
    assert "B1" in evidence.speaking_profile("s12")

    assert client.delete("/api/speak/s12").json() == {"deleted": True}
    assert store.get_speaking("s12") is None
    assert evidence.speaking_profile("s12") == "", "a deleted level must not reach drafting"


# --- whose files are "your files"? ---------------------------------------------

def test_a_session_with_only_a_voice_sample_gets_no_borrowed_background(client, monkeypatch):
    """The bug this test exists for: upload a writing sample and nothing else, and
    every claim was checked against the bundled corpus -- a stranger's CV, silently.
    The fallback is for an empty session, not an incomplete one."""
    from berkas import evidence

    upload(client, "s13", "voice", "curhat.txt", "yeah idk.. tired today, whatever")

    assert evidence.inventory("s13") == [], "no background given means no background"
    assert evidence.attested_text("s13") == "", "nothing to attest claims against"
    assert evidence.inventory(None), "the bundled corpus still serves a session that gave nothing"


def test_a_recording_alone_also_counts_as_a_live_session(client, monkeypatch):
    from berkas import evidence, store

    store.save_speaking("s14", {"cefr_level": "B1", "guidance": "", "avoid": [],
                                "typical_words": [], "level_evidence": "", "sentence_style": ""})
    assert evidence.session_is_live("s14")
    assert evidence.inventory("s14") == []


def test_an_untouched_session_still_falls_back(client):
    from berkas import evidence

    assert not evidence.session_is_live("never-seen")
    assert evidence.inventory("never-seen") == evidence.inventory(None)
