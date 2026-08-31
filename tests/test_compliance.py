"""Tests for the gate.

This is the one module in Berkas whose verdict is not allowed to vary, so it is
the one module worth testing properly. No model, no network, no fixtures beyond
plain dicts.
"""

from datetime import date

import pytest

from berkas.compliance import check, count_words


def spec(sections, deadline=None):
    return {"programme": "IISMA 2026", "deadline": deadline, "sections": sections}


def draft(**bodies):
    return {"sections": bodies}


def words(n, word="alasan"):
    return " ".join([word] * n)


# --- word counting -------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("   \n\t  ", 0),
        ("one two three", 3),
        ("collapse   these    runs", 3),
        ("line one\nline two", 4),
        ("well-documented counts as one", 4),
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected


# --- word caps -----------------------------------------------------------------

def test_under_cap_passes():
    result = check(spec([{"name": "motivation", "word_cap": 500, "required": True}]),
                   draft(motivation=words(480)))
    assert result["passed"]
    assert result["checks"] == [
        {"section": "motivation", "words": 480, "cap": 500, "ok": True}
    ]


def test_exactly_at_cap_passes():
    """500 against a 500 cap is compliant. The rule is 'exceeds', not 'reaches'."""
    result = check(spec([{"name": "motivation", "word_cap": 500, "required": True}]),
                   draft(motivation=words(500)))
    assert result["passed"]


def test_over_cap_blocks_with_the_numbers_in_the_message():
    result = check(spec([{"name": "impact", "word_cap": 500, "required": True}]),
                   draft(impact=words(611)))
    assert not result["passed"]
    violation = result["violations"][0]
    assert violation["rule"] == "word_cap"
    assert (violation["actual"], violation["limit"]) == (611, 500)
    assert violation["message"] == "impact is 611 words against a 500 cap — cannot submit"


def test_no_cap_means_unbounded_not_zero():
    result = check(spec([{"name": "notes", "word_cap": None, "required": True}]),
                   draft(notes=words(5000)))
    assert result["passed"]
    assert result["checks"][0]["cap"] is None


# --- mandatory sections --------------------------------------------------------

def test_required_section_absent_blocks():
    result = check(spec([{"name": "plan", "word_cap": 500, "required": True}]), draft())
    assert not result["passed"]
    assert result["violations"][0]["rule"] == "missing_section"


def test_required_section_of_only_whitespace_blocks():
    result = check(spec([{"name": "plan", "word_cap": 500, "required": True}]),
                   draft(plan="   \n  "))
    assert result["violations"][0]["rule"] == "missing_section"


def test_optional_section_may_be_absent():
    result = check(spec([{"name": "extra", "word_cap": 200, "required": False}]), draft())
    assert result["passed"]


# --- ungrounded claims ---------------------------------------------------------

def test_ungrounded_marker_blocks():
    """The product's central promise, enforced rather than asserted."""
    result = check(spec([{"name": "impact", "word_cap": 500, "required": True}]),
                   draft(impact="I led [NEEDS: a team size you have not given me]."))
    assert not result["passed"]
    assert result["violations"][0]["rule"] == "ungrounded_claim"


# --- deadline ------------------------------------------------------------------

def test_past_deadline_blocks():
    result = check(spec([{"name": "m", "word_cap": None, "required": False}], deadline="2026-08-01"),
                   draft(), today=date(2026, 8, 31))
    assert [v["rule"] for v in result["violations"]] == ["deadline_passed"]


def test_deadline_day_itself_is_still_open():
    result = check(spec([{"name": "m", "word_cap": None, "required": False}], deadline="2026-08-31"),
                   draft(), today=date(2026, 8, 31))
    assert result["passed"]


def test_absent_deadline_is_not_a_violation():
    result = check(spec([{"name": "m", "word_cap": None, "required": False}]), draft())
    assert result["passed"]


# --- reporting behaviour -------------------------------------------------------

def test_every_violation_is_reported_not_just_the_first():
    """A fix-and-recheck cycle should converge, not play whack-a-mole."""
    result = check(
        spec(
            [
                {"name": "motivation", "word_cap": 500, "required": True},
                {"name": "impact", "word_cap": 500, "required": True},
                {"name": "plan", "word_cap": 500, "required": True},
            ],
            deadline="2026-08-01",
        ),
        draft(motivation=words(480), impact=words(611)),
        today=date(2026, 8, 31),
    )
    assert not result["passed"]
    assert sorted(v["rule"] for v in result["violations"]) == [
        "deadline_passed",
        "missing_section",
        "word_cap",
    ]
    # the compliant section is still reported, so the UI can show it green
    assert result["checks"][0] == {"section": "motivation", "words": 480, "cap": 500, "ok": True}


def test_verdict_is_stable_across_repeated_runs():
    """Same draft, same verdict, every time -- the reason the model is kept out."""
    s = spec([{"name": "impact", "word_cap": 500, "required": True}], deadline="2026-09-30")
    d = draft(impact=words(611))
    assert [check(s, d, today=date(2026, 8, 31)) for _ in range(5)].count(
        check(s, d, today=date(2026, 8, 31))
    ) == 5


# --- contract regression -------------------------------------------------------

def test_spec_with_defaults_is_serialisable():
    """A field named `register` shadows BaseModel.register and its unset default
    serialises as a bound method, which Firestore rejects at write time. Setting
    the field by hand hides this, so the regression test must not set it."""
    from berkas.models import StoredSpec

    dumped = StoredSpec(programme="anything").model_dump()
    assert all(not callable(v) for v in dumped.values()), dumped
