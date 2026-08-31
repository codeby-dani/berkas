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


# --- unverified claims ---------------------------------------------------------
#
# The promise at the top of the README, made checkable. Before this rule the
# drafting agent fabricated "2,000 USD" of household income in the same sentence
# where it marked a different gap, and only the marker blocked the packet. A
# fabrication written cleanly would have been submitted.

CORPUS = (
    "Telkom University, D3 in Applied Information Systems, GPA 3.83 out of 4.00. "
    "Anagata, AI engineer. Apple Developer Academy. EVE reminder assistant. "
    "IEEE SOFTT 2025 paper on energy forecasting. Universitas Terbuka."
)


def _spec1(name="motivation", cap=None):
    return spec([{"name": name, "word_cap": cap, "required": True}])


def test_a_fabricated_place_blocks():
    result = check(
        _spec1(),
        draft(motivation="I will study at the Massachusetts Institute of Technology."),
        attested=CORPUS,
    )
    violation = next(v for v in result["violations"] if v["rule"] == "unverified_claim")
    assert "Massachusetts" in violation["actual"]
    assert not result["passed"]


def test_a_fabricated_number_blocks():
    """The exact failure observed: an invented income beside a marked gap."""
    result = check(
        _spec1(),
        draft(motivation="My household income is approximately 2,000 per month."),
        attested=CORPUS,
    )
    assert [v["rule"] for v in result["violations"]] == ["unverified_claim"]
    assert "2000" in result["violations"][0]["actual"]


def test_claims_that_are_in_the_corpus_pass():
    result = check(
        _spec1(),
        draft(motivation="I finished a D3 at Telkom University with a GPA of 3.83. "
                         "I built agent pipelines at Anagata."),
        attested=CORPUS,
    )
    assert result["passed"], result["violations"]


def test_sentence_initial_capitals_are_not_claims():
    """Capitalisation at a sentence start is a rule of English, not evidence."""
    result = check(
        _spec1(),
        draft(motivation="Working there taught me a lot. Building things is how I learn. "
                         "Nothing here names a place."),
        attested=CORPUS,
    )
    assert result["passed"], result["violations"]


def test_small_numbers_are_rhetoric_not_evidence():
    result = check(
        _spec1(),
        draft(motivation="There are three reasons, and I will give two of them."),
        attested=CORPUS,
    )
    assert result["passed"], result["violations"]


def test_the_spec_attests_its_own_terms():
    """He confirmed the spec at Gate 1, so what it names is not an invention."""
    s = spec([{"name": "motivation", "word_cap": None, "required": True}])
    s["programme"] = "Beasiswa Mobilitas Internasional"
    result = check(s, draft(motivation="I am applying to Beasiswa Mobilitas Internasional."),
                   attested=CORPUS)
    assert result["passed"], result["violations"]


def test_digit_grouping_does_not_defeat_the_check():
    assert check(_spec1(), draft(motivation="It saved 1,250 hours."), attested="saved 1250 hours")["passed"]


def test_without_attested_evidence_the_rule_is_silent():
    """Grounding needs something to ground against; absent it, the rule cannot fire."""
    result = check(_spec1(), draft(motivation="I studied at Hogwarts in 1997."))
    assert result["passed"]


# --- a total function ----------------------------------------------------------

@pytest.mark.parametrize("bad", ["2026-09-7", "next friday", "14 September 2026", "2026/09/07", ""])
def test_an_unreadable_deadline_is_a_violation_not_a_crash(bad):
    """The deadline is a field a human edits, so it can hold anything they typed.

    "2026-09-7" raised ValueError out of date.fromisoformat, took down the whole
    draft request with a 500, and reached the user as an error message reading
    "{}". A checker that crashes on its own input is not a checker.
    """
    result = check(spec([{"name": "m", "word_cap": None, "required": False}], deadline=bad),
                   draft(m="text"), today=date(2026, 8, 31))
    if not bad:
        assert result["passed"]          # empty means "no deadline stated"
        return
    assert not result["passed"]
    assert result["violations"][0]["rule"] == "deadline_unreadable"
    assert "YYYY-MM-DD" in result["violations"][0]["message"]
