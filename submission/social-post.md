# Social post

## LinkedIn / X — primary

I built an AI application assistant whose main feature is refusing to send things.

Berkas reads a call for applications and reports what it requires. Then it stops and makes you
correct it, because a model that reads a document wrong should not also be the thing that binds you
to it. Your correction is recorded next to what the model originally said.

Then it drafts, and a plain-Python checker with no AI in it decides whether you may submit. Not
"consider shortening this section". Cannot submit.

The first time I ran it end to end I did not answer any of its questions. It drafted four sections
and then blocked itself three times, because it would not invent a host university, a household
income, or a project it had no evidence for. It wrote down exactly what it would need instead.

That was the first real run. I did not stage it.

Built for the All Things Agentic hackathon on Google ADK, Gemini 3.7 Flash via Vertex AI, Cloud Run,
Firestore and the Gmail API.

berkas · Indonesian for the file you submit.

🔗 [repo] · [demo] · [video]

---

## Shorter variant, if the first runs long

Spent the hackathon building an AI that refuses to send my application.

It reads the call document, makes me correct what it understood before that becomes the rulebook,
then a plain-Python checker with no model in it decides whether I am allowed to submit.

First real run, I answered none of its questions. It drafted four sections and blocked itself three
times rather than invent facts about me.

🔗 [repo] · [demo] · [video]

---

**Before posting:** fill in the three links, and add one screenshot. Use Screen 3 with the red BLOCK
badge and the greyed-out "Cannot submit" button. That image carries the whole idea without a caption.
