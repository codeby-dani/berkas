<!-- Written in the polished register from Voice/My Writing Voice.md.
     Freeze the published version as the first polished voice sample in Voice/Samples/. -->

# I built an AI that refuses to send my application

In July I recorded myself saying my English is not good enough, and that I feel like I need a script
when I try to present. I was talking to myself, not to an audience. Three weeks later this hackathon
opened, and I kept coming back to that recording.

I'll be honest, my first idea was to build something that writes better English than me. Then I
looked at what actually goes wrong when I apply for things, and it was never the English. I have
closed deals in English. I have ten full application kits sitting on my laptop from this year alone,
CVs, cover letters, answer sheets. The grammar was never the problem. Grammarly solved grammar a
decade ago.

The real problem is that I cannot tell what one specific institution is going to reject me for. And
no writing assistant knows that either, because none of them have read the call document.

So I stopped trying to write better than myself. I built something that knows the rules.

## What it actually does

Berkas is Indonesian for the file, the dossier, the papers you hand in. You give it the call for
applications, a PDF or just a photo of the page. It reads it and tells you what it requires: the
deadline, the word caps, the sections you cannot skip, how formal the writing has to be.

Then it stops and makes you correct it.

That pause is the whole thing. The model is allowed to be wrong about what it read. What it is not
allowed to be is wrong and final at the same time. So the requirements come back as fields you can
edit, nothing gets written until you have been through them, and if you change a word cap from 500 to
150 that gets saved next to what the model originally said, so later anyone can see which of us
decided what.

After that it interviews you, but only about the things your own files do not already answer. Ten
kits sitting on my disk, and it does not make me retype any of them. Then it drafts against the spec,
in a writing voice I documented months ago for a completely different reason.

And then it checks the draft, and quite often it refuses to send it.

## The part I actually care about

There is one line I wrote before any of the code:

> It never invents a claim about your experience. Every sentence traces to a file you wrote or an
> answer you gave.

That is easy to put in a README and hard to make true. The way it is enforced is small and kind of
stupid, and somehow that is the part that works. The drafting agent sees my corpus and my interview
answers and nothing else. When it needs a fact it does not have, it is told to write a marker instead
of a sentence:

```
[NEEDS: the specific thing it would need to finish this sentence]
```

And the checker treats that marker as a hard violation. Not a warning. A packet with one in it cannot
be submitted.

The first time I ran the whole thing end to end I did not answer any of the interview questions. I
just wanted to see if the pipes connected. It drafted four sections and then blocked itself three
times, because it would not invent a host university, a household income, or a community project it
had no evidence for. It wrote down exactly what it would need instead. I did not stage that. It was
the first real run.

## Why the checker has no AI in it

The checker is plain Python. Standard library only. No model call anywhere in that path.

This was the main decision and everything else follows from it. The model perceives. Code decides.

If you ask a language model whether a draft is under 500 words, you are asking something that cannot
count to do the counting, and then trusting the answer. Worse than that, a good essay can talk its
way past a hard rule, because that is what fluent writing does to whoever is reading it. So the model
reports what the document says, and 263 lines of Python decide whether you are allowed to submit.
Same draft, same verdict, every time.

It is also the only part of the system I could write real tests for, and I did not expect that to
matter as much as it did.

## Two bugs that only existed in production

Neither of these could fail on my laptop.

The first one: `gcloud run deploy --source .` falls back to reading `.gitignore` when there is no
`.gcloudignore`. My evidence corpus is gitignored on purpose, because it is my personal career
history and I am not publishing it. So the service deployed cleanly, reported healthy, and quietly
drafted from nothing at all. No error, no crash, just a system that had forgotten who it was writing
for. I only caught it because the health endpoint reports how many corpus files it can see. A health
check that says ok while the product is empty is not a health check.

The second one: I called Secret Manager with `access_secret_version(name={"name": ...})`, which
passes a dictionary where a string belongs. That branch only runs on Cloud Run, because locally the
token is read off disk. So it passed every test I had, deployed fine, cleared both gates, and then
threw a protobuf error on the single request this whole project exists to make.

Both of them are written down in the README now, because they cost me time and they will cost someone
else time.

## What I would tell myself at the start

A gate is only worth what you tested it at. "The button is disabled" is a claim about a browser.
"POST /api/send returns 409" is a claim about a system. Those are not the same sentence, and only one
of them survives someone with curl.

And the hard part was never the writing. It was deciding what the thing is not allowed to do, and
then making that decision expensive to undo.

I built this for the All Things Agentic hackathon, on Google ADK, Gemini 3.7 Flash and Gemma 4
through Vertex AI, Cloud Run, Firestore and the Gmail API. But the reason I built it is smaller than
all of that. I wanted one thing in my applications that I would not have to be afraid of.

What's one thing you have sent that you wish something had checked first?

---

*I created this piece of content for the purposes of entering the All Things Agentic hackathon.
Repo: [link] · Live: [link] · Demo video: [link]*

*#AllThingsAgenticHackathon*
