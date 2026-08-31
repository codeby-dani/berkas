# The four minutes

Only the first four minutes are judged. Use all of them — the field median is 3:35 and a third come
in under 3:00, which leaves score on the table.

**Record one continuous take and speed it up uniformly.** Put a note on screen saying it is unedited
apart from speed. That is worth more than a polished cut, because the thing being demonstrated is
that the system actually works.

---

## Before you press record

- [ ] `https://berkas-jprtd3yasa-uc.a.run.app` opened once already, so the container is warm.
      **Cold start is ~14 seconds.** Hit it, wait, then reload before recording.
- [ ] The IISMA call document on your desktop, ready to drag.
- [ ] `dani.muhammad.k@gmail.com` open in a second tab, inbox visible, **already scrolled to top**.
- [ ] Firestore console open on the `receipts` collection, in a third tab.
- [ ] Cloud Run console on the `berkas` service, fourth tab.
- [ ] Browser zoom at 125%. The word counts must be legible after compression.
- [ ] Close every notification. A Slack toast mid-take costs you the take.

**Two places the model thinks and the screen sits still:** after *"These are correct — continue"*
(~15–30s while it works out what your files don't answer) and after *"Write the packet"* (~30–60s).
Speed those through hard. Do not cut them out — a visible wait is honest, a jump cut is not.

---

## 0:00 – 0:25 · The friction, with a date on it

Your call, deferred until now: your own recording, or the same words as text on screen. Either way
**the date must be visible**, because a dated friction that predates the hackathon is the one thing
nobody else in this field can produce.

> *"my English is not that good enough still… I feel like I need script when I try to present."*
> — 2026-07-14, three weeks before this hackathon opened

Say, over it:

> "I have made deals in English. I still open every application form the same way. The problem was
> never grammar. It is that I cannot tell what a specific institution will reject me for."

## 0:25 – 1:00 · Drop the call document

Drag the IISMA call onto the drop zone. Click **Read the requirements**.

> "Berkas reads the call and reports what it requires. It does not score me, it does not tell me my
> chances. It reads a document."

Screen 2 appears. Point at what it got right:

> "Deadline. Two essays, five hundred words and three hundred. And this one" — the Short Bio —
> "the call caps at seven hundred and fifty *characters*, not words. It refused to convert that into
> a word count and put the real rule in the requirements list instead. If it had guessed, the
> checker would have blocked the wrong thing later."

## 1:00 – 1:40 · Correct it. This is the whole project.

**Change the Statement of Motivation cap from 500 to 150.**

The field turns amber. The note underneath updates live:

```
You corrected 1 thing:
Statement of Motivation: 500 → 150 words
```

> "This is the part that matters. What the model read is not the rulebook yet. I correct it first,
> and what I changed gets recorded — the original reading is kept next to my correction, so anyone
> can see which of us decided what."

Click **These are correct — continue**.

> "And until I do that, the drafting endpoint returns a 409. Not a disabled button. The API refuses."

## 1:40 – 2:30 · It asks, then it blocks itself

Interview questions appear. **Answer two of them, honestly and briefly. Leave one blank on purpose.**

> "It only asks what my own files don't already answer. I've written eleven applications; it doesn't
> make me retype any of it."

Click **Write the packet**. *(speed through the wait)*

Screen 4. Two different kinds of violation, which is the point:

> "Two blocks, for two different reasons. This one is over the cap I just set — two hundred and
> eleven words against my hundred and fifty. And this one" — the `[NEEDS:]` section — "is the one I
> actually care about. I left that question blank, so it refused to invent an answer. It wrote down
> exactly what it would need and stopped. A packet with an invented claim in it cannot be sent."

Point at the button: **Cannot submit — 2 violations**, greyed out.

> "Not 'consider shortening this'. Cannot submit."

## 2:30 – 3:00 · Fix it, confirm it, send it

Trim the long section. Delete the `[NEEDS:]` sentence. Click **Re-check**.

Everything goes green. The button becomes **Send it**.

> "The recipient is here on screen so you can see where this goes. It's my own second inbox, because
> I'm not sending a real scholarship application to a real committee at midnight for a demo. But the
> send is the real Gmail API — real message id, real receipt. Nothing about it is mocked."

Click **Send it**. The receipt panel appears.

**Switch to the inbox tab. Refresh. The email is there.** Open it.

## 3:00 – 3:30 · Where it lands, and what ran

Firestore tab, `receipts` collection. Open the document.

> "Gmail message id, the timestamp I confirmed at, and the timestamp it sent at. This row is why the
> outbound action is checkable rather than claimed."

Open the `specs` collection, show `corrected_fields` and `extracted`.

> "And here is my correction. The model said five hundred. I said a hundred and fifty. Both are kept."

Cloud Run console — the service, the region. Then the architecture diagram.

> "One Cloud Run service. Gemini through Vertex at the global endpoint. And the checker is plain
> Python with no model in it, which is the whole design: the model perceives, code decides."

## 3:30 – 4:00 · The honest close

> "Thirty tests. The ones I care about assert what does *not* happen: on a blocked send the
> transport is never called and no receipt is written."

One line on what's next:

> "Next is Indonesian-language calls. LPDP, Beasiswa Unggulan, the campus forms that are still PDFs.
> The people who need the gate most are the ones filing in a second language."

**Then say it, clearly, to camera:**

> "This project was created for the purposes of entering the All Things Agentic Hackathon."

---

## If something breaks on camera

Keep rolling. A recovery is worth more than a clean take — under 63% of demos in this field even
mention failure. If the send fails, show the 409 or the error, say what it means, fix it, run it
again. The one thing that is not recoverable is claiming something works that does not.

## Do not

- Do not say "AI-powered", "seamless", or "revolutionary".
- Do not read the architecture diagram aloud box by box. Point at two things and move.
- Do not apologise for the interface. It is deliberately plain.
- Do not skip the bonus sentence. Three of forty-six videos contain it.
