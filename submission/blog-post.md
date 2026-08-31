# I built an AI that refuses to send my application

*Written for the All Things Agentic hackathon. Draft in Dani's polished register: direct, concrete,
no em-dashes, no corporate filler. Edit freely, it should sound like you and not like me.*

---

In July I recorded myself saying my English is not good enough, and that I feel like I need a script
when I try to present. I was talking to myself, not to an audience. Three weeks later this hackathon
opened, and I kept coming back to that recording.

Here is the thing though. I have closed deals in English. I have written eleven job application kits
this year. The problem was never grammar. Grammarly solved grammar a decade ago. The problem is that
I cannot tell what a specific institution is going to reject me for, and no writing assistant knows
that either, because none of them have read the call document.

So I stopped trying to build something that writes better than me. I built something that knows the
rules.

## What it actually does

You give Berkas the call for applications. A PDF, or a photo of the page. It reads it and tells you
what it requires: the deadline, the word caps, which sections are mandatory, what register the thing
is written in.

Then it stops and asks you to correct it.

That pause is the whole product. The model is allowed to be wrong about what it read. What it is not
allowed to be is wrong *and* binding. So the requirements come back as editable fields, and nothing
gets written until you have been through them. If you change a word cap from 500 to 150, that gets
recorded, next to what the model originally said, so afterwards anyone can see which of you decided
what.

After that it interviews you, but only for things your own files do not already answer. I have
eleven application kits sitting on my disk. It does not make me retype any of them. Then it drafts
against the spec, in a writing voice I documented months ago for a completely different reason.

And then it checks the draft, and quite often it refuses to send it.

## The part I actually care about

There is one line I wrote before any of the code:

> It never invents a claim about your experience. Every sentence traces to a file you wrote or an
> answer you gave.

That is easy to put in a README and hard to make true. The way it is enforced is small and slightly
stupid, which is usually a good sign. The drafting agent sees my corpus and my interview answers and
nothing else. When it needs a fact it does not have, it is told to write a marker instead of a
sentence:

```
[NEEDS: the specific thing it would need to finish this sentence]
```

And the compliance checker treats that marker as a hard violation. Not a warning. A packet with one
in it cannot be submitted.

The first time I ran the whole thing end to end, I did not answer any of the interview questions. I
just wanted to see if the pipes connected. It drafted four sections, and then it blocked itself
three times, because it would not invent a host university, a household income, or a community
project it had no evidence for. I did not stage that. It was the first real run.

## Why the checker has no AI in it

The compliance checker is plain Python. Standard library only. No model call anywhere in that path.

This was the main design decision and everything follows from it. The model perceives. Code decides.

If you ask a language model whether a draft is under 500 words, you are asking something that cannot
count to do arithmetic, and then trusting the answer. Worse, you are letting a good essay argue its
way past a hard rule, because that is what fluent text does to an evaluator. So the model reports
what the document says, and 111 lines of Python decide whether you are allowed to submit. Same draft,
same verdict, every time.

It is also the only part of the system I could write real tests for, which turns out to matter more
than I expected.

## Two bugs that only existed in production

Neither of these could fail on my laptop, which is what made them interesting.

The first: `gcloud run deploy --source .` falls back to reading `.gitignore` when there is no
`.gcloudignore`. My evidence corpus is gitignored on purpose, because it is my personal career
history and I am not publishing it. So the service deployed cleanly, reported healthy, and quietly
drafted from nothing at all. No error. No crash. Just a system that had forgotten who it was writing
for. I only caught it because the health endpoint reports how many corpus files it can see. A health
check that says ok while the product is hollow is not a health check.

The second: I called Secret Manager with `access_secret_version(name={"name": ...})`, which passes a
dictionary where a string belongs. That branch only runs on Cloud Run, because locally the token is
read off disk. So it passed every test I had, deployed fine, cleared both gates, and then threw a
protobuf error on the single request the entire project exists to make.

Both of those are now written down in the README, because they cost me time and they will cost
someone else time.

## What I would tell myself at the start

A gate is only worth what it is tested at. "The button is disabled" is a claim about a browser.
"POST /api/send returns 409" is a claim about a system. Those are not the same sentence, and only
one of them survives someone with curl.

The hard part was never the writing. It was deciding what the thing is not allowed to do, and then
making that decision expensive to reverse.

---

*Berkas is Indonesian for the file, the dossier, the papers you submit. Built for All Things Agentic
on Google ADK, Gemini 3.7 Flash via Vertex AI, Cloud Run, Firestore and the Gmail API.*
