# Devpost submission copy

Paste-ready. Everything here is true of the build as it stands; nothing describes
work that was planned and not done.

---

## Elevator pitch (200 char limit)

Berkas reads a call for applications, lets you correct what it understood before that becomes the
rulebook, blocks the packet on any violation, and files it for real.

---

## Inspiration

In July I recorded myself saying I needed a script to present in English. I have made deals in
English and I still open every application form with the same tightness in my chest. The problem was
never grammar — tools solved grammar years ago. It is that I cannot tell what a specific institution
will reject me for, and no writing assistant knows that either.

So I stopped trying to build something that writes better. I built something that knows the rules,
lets me correct it when it reads them wrong, and refuses to submit when the rules are broken.

## What it does

Berkas reads a call for applications and reports what it actually requires — deadline, word caps,
mandatory sections, the register it is written in.

**You correct that reading before it becomes the rulebook.** This is the part I care about. The
model is allowed to be wrong; it is not allowed to be wrong *and* binding. Every correction is
recorded, and the drafting endpoint returns `409` on a spec no human has confirmed.

It then interviews you only for evidence the call demands and your own files do not already contain,
drafts against the spec in your documented voice, and a deterministic checker blocks the packet on
any hard violation. On your explicit confirmation it sends it for real and returns a timestamped
receipt carrying the Gmail message id.

**It never invents a claim about your experience.** Where a fact is missing, the drafting agent
writes `[NEEDS: the thing it would need]` instead of a plausible sentence — and the checker treats
that marker as a hard violation, so a packet built on an invented claim cannot be sent. On the very
first end-to-end run, with no interview answers given, it refused to invent a host university, a
household income and a community project, and blocked itself three times. That was not staged.

## How we built it

Google ADK in Python on Cloud Run, Gemini 3.7 Flash through Vertex AI at the global endpoint,
Firestore for specs, drafts and receipts, and the Gmail API for the send.

The spine is one decision: **the model perceives, code decides.** Gemini reports what the document
requires. `berkas/compliance.py` — plain Python, standard library only, no model in the path —
produces the pass/fail verdict. Same draft, same verdict, every time, and the rules are auditable by
reading them rather than by trusting them.

Four rules, all evaluated together so a fix-and-recheck cycle converges instead of playing
whack-a-mole: word caps (exceeds, not reaches — 500/500 is compliant), missing mandatory sections,
unresolved `[NEEDS:]` markers, and a passed deadline evaluated in the applicant's own timezone.

Both gates live in the API rather than in the browser, so `curl` gets the same answer as a click.
The tests assert the negatives that matter: on a blocked send, the transport is never called and no
receipt is written.

## Challenges we ran into

**Gemini 3.x is served only from `location=global`**, which is not obvious from a regional Cloud Run
deployment.

**The Gemini API-key route returns 429 from Indonesia** — prepayment credits, not a rate limit — so
the whole build runs on Vertex AI billing. This also killed the plan to use Gemma for evidence
classification: Gemma 4 is visible to the API key but 429s like everything else, and it is not a
managed publisher model on Vertex in either `global` or `us-central1`. Self-deploying it from Model
Garden needs GPU quota and hours I did not have. I cut it rather than fake it.

**Two bugs that only existed in production.** `gcloud run deploy --source .` falls back to
`.gitignore` when there is no `.gcloudignore` — and the evidence corpus is gitignored on purpose, so
the service deployed perfectly, reported healthy, and quietly drafted from nothing. It was caught
only because `/api/health` reports the corpus size; a health check that returns `ok` while the
product is hollow is not a health check. Separately, `access_secret_version(name={"name": ...})`
passes a dict where a string belongs. That branch only runs on Cloud Run, so it passed every local
test and then 500'd on the one request the entire project is about.

**And the honest one:** deciding what the agent is *not* allowed to do took longer than making it
write well.

## Accomplishments that we're proud of

The refusals work, and they are tested as refusals. A packet with a violation cannot be sent even by
someone who bypasses the interface entirely.

## What we learned

That a gate is only worth what it is tested at. "The button is disabled" is a claim about a browser.
"`POST /api/send` returns 409" is a claim about a system.

## What's next for Berkas

Indonesian-language calls first — LPDP, Beasiswa Unggulan, and the campus grant forms that are still
PDFs. The rulebook abstraction does not care what language the document is in, and the people who
need the gate most are the ones filing in a second language.

---

## Required disclosure — do not omit

The rules require disclosing pre-existing code. The ADK deployment skeleton (`agent/agent.py`,
`deploy.sh`, `fix-iam.sh`, `smoke_test.py` — the first commit in the repository) predates this idea
and exists to verify the deployment path. The application corpus is personal data used as demo
input, not code, and is not published. Everything else was built inside the submission window.

## Say this in the video

> "This project was created for the purposes of entering the All Things Agentic Hackathon."

## Built with

`google-adk` · `gemini-3.7-flash` · `vertex-ai` · `cloud-run` · `firestore` · `gmail-api` ·
`secret-manager` · `python` · `fastapi` · `pytest`
