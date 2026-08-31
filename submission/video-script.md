# The four minutes

Scored as **Demo & Production Readiness — 30%**. Judged on three things, in the organisers' own
words: does the video *define the friction and explain the architecture*; is there **Proof of Action**
— live agent execution, **unedited**, visible as terminal logs, database updates or UI changes; and
is there **visual proof of deployment**.

They say explicitly that they are looking for raw execution, not a montage of results.

---

## Hard rules — breaking any of these costs the entry

| | |
|---|---|
| **Length** | Maximum 4:00. Past that, only the first four minutes are watched. |
| **Hosting** | YouTube or Vimeo, **public** — not unlisted, not private. Link goes in the Devpost form. |
| **Google Cloud proof** | **Mandatory, not optional.** Cloud Console, the Cloud Run dashboard, Vertex AI logs, or the `.run.app` URL visible in the address bar. |
| **Honesty** | The project must work as shown. A faked demo is grounds for disqualification. |
| **Language** | English narration, or English subtitles. |
| **Content** | No third-party logos, trademarks or slogans that imply sponsorship or endorsement. No content violating anyone's privacy, publicity or IP. |
| **After the deadline** | Do not edit the video, the repo or the live site until winners are announced. Editing during judging can void prize eligibility. |

**Narrate it.** The FAQ says voiceover — your own voice or AI TTS — guiding the judge is better than
background music. The narration must be accurate; do not describe anything the screen is not doing.

### The narration is written at your level, on purpose

Every line below is written the way you actually talk: short sentences, plain words, contractions,
and the openers you really use — *so*, *okay*, *and*, *look*. Your own app measured you at **B1**
tonight and listed the words to keep out of your mouth. An earlier draft of this script was C1 —
long subordinate clauses, no contractions — which is precisely what `speaking.py` exists to stop.

**Do not "improve" these lines while recording.** Reaching for a bigger word is what makes you
stumble, and a stumble costs more than a plain sentence ever will. If a line still feels too big in
your mouth, cut it shorter — never longer.

**Or narrate in Indonesian and add English subtitles.** The rules allow it, and it is worth
considering seriously: you would sound completely confident, and confidence reads on camera. The
cost is that a judge reads instead of listens. Your call — but do not pick English just because it
feels more professional. It does not, if you are fighting the sentences.

---

## On editing: the one thing to get right

The rubric objects to **cuts and montages**, not to speed. Removing a wait hides whether the thing
ran; a uniform speed-up of a wait still shows every frame of it. So:

| | |
|---|---|
| ❌ Cut the wait out | Hides the execution. This is the thing the criterion catches. |
| ❌ Jump-cut to the result | A montage. Same problem. |
| ✅ **Uniform 2× over the wait, with `⏩ 2× · no cuts` on screen** | Every frame still there. Standard practice, and defensible. |
| ✅ **Fill the wait with narration** | Best of all — you get Proof of Action *and* the architecture explanation in the same seconds. |

**The waits are ~113 seconds of your four minutes:** Gate 0 check 4s, speaking profile ~12s, read
requirements 17s, interview 23s, draft 55s, send 2s. At 1× that leaves only about two minutes for
everything you say and click, which is why a full read runs long.

### The rule that fixes the timing

**Narration over an unavoidable wait is free. Narration while you click is expensive.**

So the 55-second draft is where the architecture explanation goes, at **1× speed, uncut** — it costs
nothing, because you were waiting anyway. Speed the *other* two long waits (read requirements, and
the interview step) to 2× with the label. That alone gives back about **35 seconds**.

The remaining ~60 seconds come out of narration while clicking. Every line below is already cut for
that; do not add back.

**Measured latencies on the live service:**

| Step | Time |
|---|---|
| Read the requirements | ~17s → **2×, labelled** |
| Continue → questions appear | ~23s → **2×, labelled** |
| Write the packet | ~55s → **1×, narrate the architecture over it** |
| Attest / Re-check | ~1s |
| Send | ~2s |

---

## Before you press record

- [ ] `https://berkas-jprtd3yasa-uc.a.run.app` loaded once already so the container is warm.
- [ ] **The `.run.app` URL is visible in the address bar the whole time.** This is deployment proof
      running continuously in the background — do not full-screen the page.
- [ ] `samples/hard-call-for-applications.pdf` on the desktop, ready to drag.
- [ ] `samples/detector-test/A - linkedin post.md` on the desktop too, for Gate 0.
- [ ] A real writing sample of your own — an old journal entry or long message.
- [ ] A paragraph on the clipboard, for the word-cap block.
- [ ] `dani.muhammad.k@gmail.com` open in a second tab, inbox scrolled to top.
- [ ] Cloud Run console on the `berkas` service — third tab.
- [ ] Firestore console on `receipts` — fourth tab.
- [ ] Browser zoom 125%. Word counts must survive compression.
- [ ] Every notification closed.

**Record the Cloud Console proof in the same take.** You can scale the service down afterwards to
save money — the rules only require that the proof is captured in the video.

**One caution on trademarks:** the demo corpus lists real company names in file paths
(`kits/Accenture/…`, `kits/Bjak/…`). Do not linger or zoom on that list. Nothing there implies
endorsement, but there is no reason to put other companies' names on screen at all.

---

## The cut, section by section

Read straight through, this runs **4:00 at a careful pace**. It is 500 words. A full read of the
previous draft ran 5:34 — the difference is that the live recording step is gone and every line is at
its shortest. **Do not add words back while recording.**

Word budgets are given so you can tell mid-take whether you are running long.

---

## 0:00 – 0:18 · The friction *(48 words)*

On screen: your dated line, the date visible.

> *"my English is not that good enough still… I feel like I need script when I try to present."*
> — my own notes, 2026-07-14

> "I've closed deals in English. I still open every application form the same way, tight in my chest.
>
> It was never grammar. I don't know what *this* place will reject me for. ChatGPT doesn't either —
> it never read their document. Berkas reads it, and refuses to send if I break a rule."

## 0:18 – 0:36 · Gate 0 *(42 words)*

Drop **`A - linkedin post.md`** into *How you write*. Click **Continue**. Red panel in ~4s.

> "First it checks my writing sample is really mine. This one I made with ChatGPT. It says no, and
> shows me the lines.
>
> Because if I teach it with AI writing, it just learns to sound like AI."

Swap in your real sample and a background file. **Do not record live** — that costs 27 seconds you do
not have. If you recorded earlier in the session, let the level panel sit on screen for two seconds
and say nothing. It reads by itself.

## 0:36 – 0:52 · It reads the call *(18 words)*

Drag the PDF. **Read the requirements** — `⏩ 2× · no cuts` over the 17s.

> "Now the call document. Six sections, and it reports only what the document asks for — not my
> chances."

## 0:52 – 1:32 · Gate 1 — the whole project *(88 words)*

**Protect this section. If you are running long, cut elsewhere.**

Change the deadline to **2026-09-07**. Field turns amber.

> "It read this correctly. I'm going to change it anyway.
>
> It closes on the fourteenth. But down here — Vocational scheme submits by the seventh. My finished
> degree is a D3, so my real deadline is a week earlier. Nothing in this PDF says which scheme I'm in.
> The AI can't know that. I'm the only one who does."

Click **These are correct — continue**.

> "That's the whole point. The AI isn't bad — it read it right. It just can't know things about me
> that aren't on the page. And until I confirm, the API returns 409. Not a grey button. The server
> says no."

## 1:32 – 2:37 · Draft, and the architecture *(122 words — free time)*

Three questions. Answer two. **Leave the money one blank.** `⏩ 2×` over the 23s.

> "It only asks what my own files don't already answer."

Click **Write the packet**. **1× speed, no label, narrate the whole 55 seconds** — this costs nothing
because you are waiting anyway, and it is where the architecture score comes from.

> "While that runs — how it works.
>
> Gemini reads the call and says what it needs. Gemma, a second model, sorts my own files so each
> section only gets what helps it. The writing agent sees those files and my answers. Nothing else.
>
> Then a checker decides if I can submit, and there's no AI in that part at all. It's just Python.
> Same draft, same answer, every time — because AI can't count to three hundred fifty properly, and
> good writing shouldn't talk its way past a hard limit."

The packet appears, blocked.

> "I skipped the money question. It didn't guess — it wrote down what it needs and stopped. Earlier
> while building this, it invented two thousand dollars of family income. That's why there's a Python
> check on every number now."

## 2:37 – 3:02 · Attest, fix, send *(74 words)*

Tick one flagged claim that is genuinely yours.

> "Here my own checker is wrong about me. My degree written in Indonesian won't match the English on
> my CV. It can't tell a translation from an invention. So I overrule it, one at a time — and that's
> saved with my name on it."

Delete the `[NEEDS:]` sentence. Paste a long paragraph, **Re-check** — word cap fires — trim it back.
Green.

> "My own second email, because I'm not sending a real application to a real committee for a demo.
> But the sending is real. Real Gmail API, real message ID."

**Send it.** Switch to inbox. Refresh. Open it.

## 3:02 – 3:40 · Google Cloud proof *(62 words)*

**Mandatory. Do not shorten.**

Firestore → `receipts` → newest document.

> "Gmail message ID, the time I confirmed, the time it sent. So you can check it, not just believe me."

`specs` → `corrected_fields`.

> "And my correction, saved next to what the AI first read."

Cloud Run console → service, region, revision.

> "One Cloud Run service, us-central-one. Gemini through Vertex AI on the global endpoint, Gemma
> through the Gemini API, Firestore in Jakarta."

Architecture diagram. Point at two things.

> "Four gates. And the checker in the middle, with no AI in it."

## 3:40 – 4:00 · Close *(38 words)*

> "Seventy-eight tests. The ones I care about check what does *not* happen — when a packet is blocked,
> nothing sends and no receipt is written."

> "Next is Indonesian calls. LPDP, Beasiswa Unggulan. The people who need this most are applying in a
> second language."

**To camera:**

> "This project was created for the purposes of entering the All Things Agentic Hackathon."

---

## What I cut, and why

| Cut | Saved | Why it was safe |
|---|---|---|
| **Recording a spoken answer live** | ~27s | The feature still appears — the level panel is on screen and you name it in one line. Recording it live is the expensive part, not the proof. |
| Second half of the Gate 0 explanation | ~12s | The red panel quoting the file says it better than a sentence about it. |
| "machine copying a machine copying me" | ~6s | Good line, but the first sentence already made the point. |
| Half the block explanation | ~15s | The greyed-out button and the `[NEEDS:]` marker are visible. Do not narrate what the screen shows. |
| Doubled sentences throughout | ~34s | Every place the script said a thing twice. |

### Your actual pace

You read the 734-word draft in **5:34** — that is **132 words per minute**, which is a sensible,
unhurried pace and you should not try to speed it up. At 132 wpm, four minutes is about **528 spoken
words**. This cut is close to that.

**If a take still runs over, cut in this order:**

1. "Nothing else." in the architecture block — one line, nothing lost.
2. The whole second paragraph of 0:00 ("It was never grammar…"), keeping only the first and last.
3. The "Next is Indonesian calls" sentence at 3:45.

**Never cut:** Gate 1, the block, the send, the Cloud proof, or the last sentence. Those four are
where the 30% actually comes from, and the last one is worth 0.2 for four seconds.

**Do not solve an overrun by talking faster.** You will trip, and a stumble costs more than a cut
sentence. Cut, do not rush.

---

## If something breaks on camera

**Keep rolling.** A recovery is worth more than a clean take, and the rubric is explicitly looking for
raw execution. If the send fails, show the error, say what it means, fix it, run it again.

The one unrecoverable thing is claiming something works that does not — that is a disqualification
risk, not a scoring one.

## Do not

- Do not cut the waits out, and do not montage the results. That is the specific thing this criterion
  is written to catch.
- Do not full-screen the browser. The `.run.app` URL in the address bar is continuous deployment proof.
- Do not say "AI-powered", "seamless", or "revolutionary".
- Do not read the architecture diagram box by box. Point at two things and move.
- Do not linger on the corpus file list — other companies' names have no reason to be on screen.
- Do not skip the last sentence.

## After you upload

- [ ] YouTube or Vimeo, visibility **Public**. Not unlisted.
- [ ] English narration, or English subtitles uploaded.
- [ ] Link pasted into the Devpost submission form.
- [ ] **Then stop.** No edits to the video, the repo, or the live site until winners are announced.
      Editing during judging can void prize eligibility.

## Title, description, and the +0.2 content bonus

### Title

```
Berkas - an AI that refuses to send my application | All Things Agentic Hackathon
```

### Description — paste as one block

The first line must be the compliance sentence, because YouTube only shows two lines before
"...more" and that is the line the bonus depends on.

```
I created this video for the purposes of entering the All Things Agentic hackathon.

Berkas reads a call for applications and reports what it requires. Then it stops and makes you
correct it, because a model that reads a document wrong should not also be the thing that holds you
to it. It drafts only from files you wrote, and then a plain-Python checker with no model in it
decides whether the packet may be submitted.

First real run, I answered none of its questions. It drafted four sections and blocked itself three
times rather than invent a host university, a household income, or a project it had no evidence for.

Chapters
0:00  The friction
0:18  Gate 0 - is this call even real
0:36  It reads the call
0:52  Gate 1 - you correct what it understood
1:32  Drafting, and the architecture
2:37  Attest, fix, send
3:02  Google Cloud proof
3:40  Close

Repo:  [link]
Live:  [link]
Blog:  [link]

Built on Google ADK, Gemini 3.7 Flash and Gemma 4 through Vertex AI, Cloud Run, Firestore and the
Gmail API.

Berkas is Indonesian for the file, the dossier, the papers you hand in.

#AllThingsAgenticHackathon
```

**Fix the chapter timestamps from your editor timeline before you upload.** Those are the planned
beats from the script, not measured ones. Wrong chapters are worse than no chapters - delete the
whole block if the recording drifted and you have no time to check.

### Does this video claim the content bonus?

Treat it as **insurance, not the claim.** The bonus is Developer Content about *how you built it*,
scored separately from the demo, so a judge may decline to award it for an artifact you were already
required to submit. `blog-post.md` on dev.to is the unambiguous claim and it is written and ready.

The sentence in the description costs nothing and your scan found only **3 of 46** videos carry it,
so include it either way. If the judge counts it, good. If not, the blog already did.

**Upload Public, not Unlisted.** Both the submission rule and the bonus rule require public, and
Unlisted is the most common way this point is lost.
