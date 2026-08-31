# Berkas — Product Requirements

> **berkas** · Indonesian: the file, the dossier, the papers you submit.

An application-filing partner for someone writing to an institution in a language that is not
theirs. It reads the call document, lets you correct what it understood **before that becomes the
rulebook**, interviews you for the evidence the spec demands, blocks the packet on any hard
violation, and on your explicit confirmation sends it for real and hands back a receipt.

**All Things Agentic (Google × Devpost) · Collaborative Partner track.** Deadline 2026-09-01 08:00 WITA.

---

## 1. The line the product will not cross

> **Berkas never invents a claim about your experience. Every sentence in the packet traces to a
> file you wrote or an answer you gave.**

This is a product requirement, not a slogan. It has three enforceable consequences:

- The drafting agent receives **only** the evidence corpus and the interview answers. It is
  instructed to leave a gap marked rather than fill it.
- Any sentence the drafting agent cannot ground is emitted as `[NEEDS: <what it needs>]` and is
  treated by the compliance checker as a **hard violation**. An ungrounded packet cannot be sent.
- The interview agent exists precisely so the model asks instead of assuming.

## 2. Who it is for, and the one path we build

One programme, one form, one register. **Not** "any document, any institution" — that is how this
becomes Grammarly, and it will read that way to a judge.

**The user:** Muhammad Dani, 22, Bali. Documented on 2026-07-14, three weeks before the submission
window opened: *"my English is not that good enough still… I feel like I need script when I try to
present."* He has an 11-kit application corpus on disk and a written voice profile. The friction is
dated and real, and it is not grammar — it is not knowing what a specific institution will reject
him for.

**The path:** a public Indonesian scholarship call (IISMA guidebook — real stated word caps and
mandatory sections). Fallback input if sourcing stalls: the Mindrift kit already on disk. The
document is *input*; the build does not depend on which one.

## 3. Scope

**In.** Perception → editable spec (Gate 1) → interview → draft → deterministic block → explicit
confirmation (Gate 2) → real Gmail send → Firestore receipt. Three screens. Unit tests on the
checker. Architecture diagram. Reproducible README.

**Out, and stays out.** Multi-document or multi-institution generalisation; authentication or
accounts; streaming UI; retry/queue infrastructure;
mobile layout; any styling not visible on camera.

## 3a. Bring your own corpus

Berkas can only say what you have already said, so the first screen collects it. Two slots, and
the separation is load-bearing rather than cosmetic:

- **background** — CVs, past applications. Read for **facts**, never for style. Formal documents
  written for machine screening are exactly what makes an application sound like every other
  application, so drafting is told to read them for facts and ignore how they are written.
- **voice** — a long message, an email, a journal entry. Read for **style**, and never usable as
  evidence: a turn of phrase must not become a claim.

Held in Firestore against a client-generated session id. A session that uploads nothing falls back
to the bundled corpus, so the demo works on a fresh visit and a fork works for whoever cloned it.

## 4. Data contracts

These are frozen. Everything downstream is written against them.

### ExtractedSpec

What perception reports and what Gate 1 edits. Stored in Firestore `specs/{spec_id}`.

| Field | Type | Notes |
|---|---|---|
| `spec_id` | `str` | uuid4 |
| `programme` | `str` | e.g. "IISMA 2026" |
| `deadline` | `str \| None` | ISO-8601 date, `YYYY-MM-DD` |
| `sections` | `[Section]` | see below |
| `voice_register` | `str` | e.g. "formal, first person". Not `register`: that name shadows `BaseModel.register`. |
| `extra_requirements` | `[str]` | free-text rules perception found but cannot enforce |
| `human_corrected` | `bool` | `False` until Gate 1 |
| `corrected_fields` | `[str]` | dotted paths the human changed, e.g. `sections[1].word_cap` |
| `created_at` | `str` | ISO-8601 UTC |

**Section:** `{ name: str, word_cap: int | None, required: bool }`.
`word_cap: None` means unbounded, not zero.

`corrected_fields` is the highest-value field in the system. It is machine-readable evidence that a
human overruled the model, it is written before a single word is drafted, and it is what makes
Screen 2 a submission rather than a form.

### Draft

Stored in `drafts/{draft_id}`.

`{ draft_id, spec_id, sections: {<section name>: <text>}, created_at }`

### ComplianceResult

Produced by `berkas/compliance.py`. **Plain Python. No model in this path, ever.**

```
{
  "passed": bool,
  "checks":     [ {section, words, cap, ok} ],
  "violations": [ {section, rule, actual, limit, message} ]
}
```

### Receipt

Stored in `receipts/{receipt_id}`. Written only after a real Gmail send returns a message id.

`{ receipt_id, sent_at, gmail_message_id, gmail_thread_id, to, subject, spec_id, draft_id,
   compliance_passed: True, confirmed_by_human_at }`

## 5. Compliance rules

The deterministic core. Every rule is total, testable, and produces the same verdict for the same
input every time.

**Word counting is defined as `len(text.split())`** — whitespace-delimited tokens after stripping.
Hyphenated words count as one. This definition is documented because it is the one thing a judge
could reasonably quibble with, and an undocumented count is indistinguishable from a fudged one.

| Rule | Fires when | Message |
|---|---|---|
| `word_cap` | `section.word_cap is not None` and `count > cap` | `"{section} is {count} words against a {cap} cap — cannot submit"` |
| `missing_section` | `section.required` and the draft has no non-empty body for it | `"{section} is required and empty — cannot submit"` |
| `ungrounded_claim` | the draft body contains `[NEEDS:` | `"{section} contains an unsupported claim — cannot submit"` |
| `deadline_passed` | `spec.deadline` is before today in Asia/Makassar | `"the deadline was {deadline} — cannot submit"` |

`passed` is `len(violations) == 0`. A section under its cap is reported in `checks` but is not a
violation. **Hard constraints cap: a good essay cannot outrank a word-count violation.**

## 6. API surface

| Route | Does |
|---|---|
| `POST /api/extract` | multipart upload → perception → `{spec_id, spec}` |
| `PUT  /api/spec/{spec_id}` | **Gate 1.** Saves corrections, diffs `corrected_fields`, sets `human_corrected` |
| `POST /api/interview/{spec_id}` | evidence inventory vs. spec → only the questions the corpus cannot answer |
| `POST /api/answers/{spec_id}` | stores the human's answers |
| `POST /api/draft/{spec_id}` | drafting agent, against spec + voice profile + evidence |
| `POST /api/check/{draft_id}` | **no model.** Returns `ComplianceResult` |
| `POST /api/send/{draft_id}` | **Gate 2.** Requires `confirm: true`. Gmail send → receipt |

### Two invariants, enforced server-side

1. **`POST /api/send` returns `409` when `check()` does not pass.** The disabled button is UI; the
   block lives in the API. A judge who curls the endpoint directly gets the same answer as a judge
   who clicks.
2. **`POST /api/send` returns `400` without `confirm: true`.** Nothing auto-sends. There is no code
   path from draft to inbox that does not pass through a human.

A receipt is never written for a draft that failed compliance. Asserted in the send path.

## 7. Screens

Three. The middle one is the demo.

**Screen 1 · Drop it.** Upload or photograph the call document → "Read the requirements". The visual
event lands in the first ten seconds; vision is the *input*, not decoration.

**Screen 2 · Here is what I understood.** Requirements rendered as **editable fields** — deadline,
word caps, mandatory sections, register — above the line *"These become the rules. Nothing is
written until you agree."* He edits a cap the model misread; `corrected_fields` records it.
**Acceptance: no draft request can be issued against a spec where `human_corrected is False`.**

**Screen 3 · The packet.** Per-section counts against caps. The verdict renders as a **gate, not a
score**: *"impact — 611 / 500 ✗ BLOCK"* and a disabled *"Cannot submit — 1 violation"* button.
Never *"consider shortening section 3"*. The difference is legible in two seconds.

## 8. Stack

Mandatory stack satisfied by load-bearing components, not bolted on: **Gemini 3.7 Flash via Vertex
AI** (location `global` — Gemini 3.x is served nowhere else), **Google ADK** (Python), **Cloud Run +
Firestore**. Gemma classifies evidence into sections. Cloud Trace carries the reasoning spans.

## 9. Done

- [ ] A real email arrives in a real inbox, sent by the deployed service, with the Gmail message id
      recorded in a Firestore receipt.
- [ ] A spec correction made in the browser is visible in Firestore as `corrected_fields`.
- [ ] `POST /api/send` on a violating draft returns 409 from the live URL.
- [ ] `pytest tests/` is green.
- [ ] The README renders an architecture diagram on GitHub.
- [ ] A four-minute video exists.

## 10. Disclosure

Pre-existing work incorporated, per the rules: the ADK deployment skeleton (`agent/agent.py`,
`deploy.sh`, `fix-iam.sh`, `smoke_test.py`) predates the idea and exists to verify the deployment
path; the application corpus in `~/Documents/Career/` is personal data used as demo input, not code.
Everything else was built inside the submission window.
