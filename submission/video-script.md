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
- [ ] `samples/hard-call-for-applications.pdf` on your desktop, ready to drag.
- [ ] A paragraph of text on your clipboard, for the word-cap demo at 2:15.
- [ ] `dani.muhammad.k@gmail.com` open in a second tab, inbox visible, **already scrolled to top**.
- [ ] Firestore console open on the `receipts` collection, in a third tab.
- [ ] Cloud Run console on the `berkas` service, fourth tab.
- [ ] Browser zoom at 125%. The word counts must be legible after compression.
- [ ] Close every notification. A Slack toast mid-take costs you the take.

**Measured latencies on the live service, so you know what to speed through:**

| Step | Time |
|---|---|
| Read the requirements | ~17s |
| These are correct → questions appear | ~23s |
| Write the packet | ~57s |
| Re-check | ~1s |
| Send | ~2s |

Speed those through hard. Do not cut them out — a visible wait is honest, a jump cut is not.

**On Gemma:** the routing panel on screen 4 may show per-section file counts, or it may say
*"Gemma did not answer in time — drafting used your whole corpus."* Both are true outcomes and the
packet is identical either way. If you get the fallback, say so plainly and move on — see 1:40.

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

Perception read the document correctly. **You are going to change it anyway**, and that is the point.

The call says the portal closes **14 September**. There is a clause further down: applicants under
the **Vocational (D3/D4) scheme** are assessed by an earlier panel and must submit by
**7 September**. Your completed credential is a D3.

**Change the deadline to 2026-09-07.**

```
You corrected 1 thing:
deadline: "2026-09-14" → "2026-09-07"
```

> "The model read this document perfectly. It picked up the fourteenth, and it kept the vocational
> clause in the requirements list, which is exactly right, because nothing in this PDF tells it which
> scheme I am in. But my completed qualification is a D3. So the deadline that actually binds me is
> the seventh, a week earlier, and I am the only one in this system who knows that."

> "That is the whole argument. It is not that the model is unreliable. It read it right. It just
> cannot know things about me that are not on the page — and if I had let its reading become the
> rulebook, I would have missed a deadline by seven days and never known why."

Click **These are correct — continue**.

> "My correction is recorded next to what it originally said. And until I do this, the drafting
> endpoint returns a 409. Not a disabled button. The API refuses."

## 1:40 – 2:30 · It asks, then it blocks itself

Three questions appear. **Answer two briefly. Leave the financial one blank on purpose.**

> "It only asks what my own files don't already answer. I've written eleven job applications; it
> doesn't make me retype any of them."

Click **Write the packet**. *(speed through ~57s)*

If the routing panel shows counts, point at it:

> "That's Gemma, a second model, sorting my files by which section each one can speak to."

If it shows the fallback, say that instead — it is a better line, not a worse one:

> "Gemma didn't answer in time, so it used my whole corpus instead. That path is deliberate. A
> second model making the packet better is worth having; a second model that can stop the packet
> existing is not."

Then the block:

> "Six sections. Two of them cannot be submitted."

Point at the `[NEEDS:]` marker:

> "I left the financial question blank, so it refused to invent an answer. Nothing in eleven job
> applications says anything about my household finances — why would it. So instead of writing
> something plausible, it wrote down exactly what it would need, and stopped."

Point at the greyed-out button:

> "Cannot submit. Not 'consider revising'. An unsupported claim is a hard violation, the same as a
> word count."

### The part I would not cut

Below the violations there is an amber panel listing claims Berkas could not find in your files.
Some are genuine inventions. Some are true things it cannot verify, like *Sistem Informasi* in the
Indonesian section, because your corpus states that credential in English.

> "And here is where my own checker is wrong about me. It compares text against my files, so when
> I write my degree in Indonesian it cannot match it against the English on my CV. It is not being
> stupid. It genuinely cannot tell the difference between a translation and something I made up."

Click **These are mine — I attest them**.

> "So I overrule it. And that gets written down too, with my name on it, onto the receipt. Same as
> when I corrected the deadline. The machine reports, I decide, and every time I decide, the system
> records that it was me."

**Then show the word cap too**, because it is the more legible of the two. Click into a section,
paste a paragraph, click **Re-check**.

> "Same gate, different rule, counted in plain Python. No model is asked whether this is short
> enough, because models cannot count and a good essay should not be able to argue past a hard limit."

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
