"""Gemma's routing, and the promise that it can always be absent.

Routing decides which corpus files drafting sees for each section. It makes the
packet better sourced; it is never allowed to make the packet impossible. Every
failure path here must return None, which the caller reads as "use everything" --
exactly what the system did before Gemma existed.
"""

from __future__ import annotations

import asyncio

import pytest

from berkas import classify


class FakeItem:
    def __init__(self, label): self.label = label
    def text(self): return f"contents of {self.label}"


ITEMS = [FakeItem("a.md"), FakeItem("b.md"), FakeItem("c.md")]
SECTIONS = ["motivation", "financial need"]


def _reply(monkeypatch, text=None, boom=None):
    class Models:
        def generate_content(self, **kw):
            if boom:
                raise boom
            return type("R", (), {"text": text})
    monkeypatch.setattr(classify, "_client", lambda: type("C", (), {"models": Models()}))


def test_routes_files_to_the_sections_they_bear_on(monkeypatch):
    _reply(monkeypatch, '{"motivation": [0, 2], "financial need": [1]}')
    routed = classify.route(SECTIONS, ITEMS)
    assert [i.label for i in routed["motivation"]] == ["a.md", "c.md"]
    assert [i.label for i in routed["financial need"]] == ["b.md"]


def test_a_section_with_no_supporting_evidence_gets_an_empty_list(monkeypatch):
    """The honest answer, and the one that makes the drafting agent mark a gap."""
    _reply(monkeypatch, '{"motivation": [0, 1, 2], "financial need": []}')
    routed = classify.route(SECTIONS, ITEMS)
    assert routed["financial need"] == []
    assert len(routed["motivation"]) == 3


def test_json_wrapped_in_prose_is_still_read(monkeypatch):
    """Gemma has no structured-output mode, so it sometimes explains itself first."""
    _reply(monkeypatch, 'Sure! Here you go:\n```json\n{"motivation": [1], "financial need": []}\n```')
    assert [i.label for i in classify.route(SECTIONS, ITEMS)["motivation"]] == ["b.md"]


def test_out_of_range_indices_are_dropped_not_crashed_on(monkeypatch):
    _reply(monkeypatch, '{"motivation": [0, 99, -1, "x"], "financial need": []}')
    assert [i.label for i in classify.route(SECTIONS, ITEMS)["motivation"]] == ["a.md"]


@pytest.mark.parametrize("bad", ['not json at all', '', '{"motivation": '])
def test_unparseable_replies_fall_back_to_the_whole_corpus(monkeypatch, bad):
    _reply(monkeypatch, bad)
    assert classify.route(SECTIONS, ITEMS) is None


def test_an_api_failure_falls_back_rather_than_propagating(monkeypatch):
    """A demo must not break because a second model is having a bad night."""
    _reply(monkeypatch, boom=RuntimeError("429 prepayment credits are depleted"))
    assert classify.route(SECTIONS, ITEMS) is None


def test_routing_nothing_at_all_falls_back(monkeypatch):
    _reply(monkeypatch, '{"motivation": [], "financial need": []}')
    assert classify.route(SECTIONS, ITEMS) is None


def test_an_empty_corpus_needs_no_routing(monkeypatch):
    assert classify.route(SECTIONS, []) is None
    assert classify.route([], ITEMS) is None


def test_a_section_routed_nothing_is_pointed_at_the_whole_corpus(monkeypatch, tmp_path):
    """Gemma routes; it does not decide. A miss must not starve a section.

    Gemma answered 0 files for "Contribution Plan" on one live run and 11 on the
    next, from the same corpus. If zero meant "write nothing", that flake would
    silently gut a section of the packet.
    """
    from berkas import drafting, evidence
    from berkas.models import Section, StoredSpec

    (tmp_path / "kits").mkdir()
    (tmp_path / "kits" / "one.md").write_text("evidence about his work")
    monkeypatch.setattr(evidence, "ROOT", tmp_path)

    spec = StoredSpec(programme="p", sections=[Section(name="motivation"), Section(name="plan")])
    async def fake(names, items): return {"motivation": items, "plan": []}
    monkeypatch.setattr(drafting.classify, "route_async", fake)
    corpus, routing = asyncio.run(drafting._corpus_for(spec))

    assert routing == {"motivation": 1, "plan": 0}, "the honest count is still reported"
    assert "nothing routed" in corpus, "a starved section is pointed at everything instead"
    assert "- motivation: [0]" in corpus, "a routed section cites the file by index"


def test_the_corpus_is_sent_once_however_many_sections_cite_it(monkeypatch, tmp_path):
    """Routing narrows which files a section leans on, not how much text is sent.

    Flattening the corpus per section turned a 119k-character corpus into a 716k
    prompt for a six-section call, and timed the request out on Cloud Run.
    """
    from berkas import drafting, evidence
    from berkas.models import Section, StoredSpec

    (tmp_path / "kits").mkdir()
    (tmp_path / "kits" / "one.md").write_text("UNIQUEMARKER evidence")
    monkeypatch.setattr(evidence, "ROOT", tmp_path)

    names = [f"section {i}" for i in range(6)]
    spec = StoredSpec(programme="p", sections=[Section(name=n) for n in names])
    async def fake(ns, items): return {n: items for n in ns}
    monkeypatch.setattr(drafting.classify, "route_async", fake)
    corpus, routing = asyncio.run(drafting._corpus_for(spec))

    assert corpus.count("UNIQUEMARKER") == 1, "the corpus was duplicated per section"
    assert all(routing[n] == 1 for n in names), "all six still cite it"
