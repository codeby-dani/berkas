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

**There are three gates, and all three record what you decided.**

**You correct that reading before it becomes the rulebook.** This is the part I care about. The
model is allowed to be wrong; it is not allowed to be wrong *and* binding. Every correction is
recorded, and the drafting endpoint returns `409` on a spec no human has confirmed.

It then interviews you only for evidence the call demands and your own files do not already contain,
drafts against the spec in your documented voice, and a deterministic checker blocks the packet on
any hard violation. On your explicit confirmation it sends it for real and returns a timestamped
receipt carrying the Gmail message id.

The third gate is the one I did not plan. The checker verifies every number and every named
institution against your files — and it compares text, so it cannot see through translation. It
flags *Sistem Informasi* in an Indonesian section against a corpus that attests the same degree in
English. The claim is true and the checker is wrong. So you can attest it, and who vouched for what
is written to the receipt. It is Gate 1 again, pointed at the system's own checker.

**It never invents a claim about your experience.** Where a fact is missing, the drafting agent
writes `[NEEDS: the thing it would need]` instead of a plausible sentence — and the checker treats
that marker as a hard violation, so a packet built on an invented claim cannot be sent. On the very
first end-to-end run, with no interview answers given, it refused to invent a host university, a
household income and a community project, and blocked itself three times. That was not staged.

## How we built it

Google ADK in Python on Cloud Run, Gemini 3.7 Flash through Vertex AI at the global endpoint,
Gemma 4 through the Gemini API, Firestore for specs, drafts and receipts, and the Gmail API for
the send.

The spine is one decision: **the model perceives, code decides.** Gemini reports what the document
requires. `berkas/compliance.py` — plain Python, standard library only, no model in the path —
produces the pass/fail verdict. Same draft, same verdict, every time, and the rules are auditable by
reading them rather than by trusting them.

Four rules, all evaluated together so a fix-and-recheck cycle converges instead of playing
whack-a-mole: word caps (exceeds, not reaches — 500/500 is compliant), missing mandatory sections,
unresolved `[NEEDS:]` markers, and a passed deadline evaluated in the applicant's own timezone.

**Two models, doing different jobs.** Gemma 4 reads the corpus once and routes each file to the
sections it can support, so drafting sees the relevant files rather than all 26. On my real corpus
it puts the CVs behind the Short Bio, the application answers behind Motivation, and consistently
**nothing** behind Personal Statement of Financial Need — eleven job applications contain no
household finances, so there is nothing to route. That section is the one that ends up marked
`[NEEDS: ...]`, which is the system agreeing with itself from two directions.

Routing narrows but never starves, and it is honestly best-effort. Gemma answered 0 files for one
section on one run and 11 on the next; on the prepay route available to me the same call has taken
25 seconds, returned 429, and failed to answer within ten minutes. So routing runs on a 20-second
budget off the event loop, a section it routes nothing to falls back to the whole corpus, and the
interface tells you when it did not answer instead of quietly pretending it did. Same principle as
everywhere else here: Gemma perceives, it does not decide, and nothing it does is load-bearing.

Both gates live in the API rather than in the browser, so `curl` gets the same answer as a click.
The tests assert the negatives that matter: on a blocked send, the transport is never called and
no receipt is written.

## Challenges we ran into

**Gemini 3.x is served only from `location=global`**, which is not obvious from a regional Cloud Run
deployment.

**Getting Gemma at all.** Gemma is open-weights, so unlike Gemini there is no managed Vertex
endpoint to call — I got 404 on every Vertex model path. The documented route is the Gemini API,
which was returning 429 (prepayment credits, not rate limiting) from Indonesia. Self-hosting is the
other option, so I checked GPU quota through the Service Usage API: **zero, across all 60 GPU
types.** Credits pay the bill but they do not grant the quota, and a quota increase is a review
measured in days. I had written Gemma off entirely before the API route came back and I retried it.
The lesson I will keep: I declared something dead on one failed call.

**Two bugs that only existed in production, and a third that only existed under load.** A
synchronous client call inside an async route blocks the entire event loop — invisible locally with
one request in flight, and on Cloud Run a draft request sat blocked for 599 seconds until the
platform killed it. And routing per section, rather than once, turned a 119k-character corpus into
a 716k-character prompt.

**Two more that only existed in production.** `gcloud run deploy --source .` falls back to
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

And that the same rule has to apply to every model in the stack, not just the one you are
suspicious of. My first version of Gemma routing let a section with zero routed files be told
"nothing covers this" — which meant one flaky classification could quietly hollow out part of the
packet. I had built the exact thing the rest of the project argues against, and I only caught it
because the drafts got shorter between two runs.

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

`google-adk` · `gemini-3.7-flash` · `gemma-4` · `vertex-ai` · `cloud-run` · `firestore` ·
`gmail-api` · `secret-manager` · `python` · `fastapi` · `pytest`
