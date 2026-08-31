# Answer key — `hard-call-for-applications.pdf`

Ten traps, each one real call documents actually contain. Scored, not admired.

| # | Trap | Right answer | Tempting wrong answer |
|---|---|---|---|
| 1 | **Erratum supersedes the table.** Table says Component A = 500 words; an erratum below it reduces it to 350 and says the table was not reprinted. | `350` | `500` — read the table, stop reading |
| 2 | **Page limit, not words.** Component B: "maximum 2 pages (approximately 800 words)", and §3.5 says the word figure is indicative and unenforced. | `null` + the 2-page rule in `extra_requirements` | `800` |
| 3 | **Character limit.** Component C: 750 characters including spaces. | `null` + note | `750` |
| 4 | **Optional component.** Component D is marked Optional and §7 says it carries no weight. | `required: false`, cap `250` | `required: true` |
| 5 | **No limit stated.** Component E: "no prescribed limit". | `null` | a guessed number |
| 6 | **Withdrawn component.** Component F appears in the table with a 1,500-word limit, marked withdrawn, and §3.4 says it must not be submitted. | **absent from `sections`** | a 1,500-word section |
| 7 | **Second deadline.** Portal closes 14 Sep 2026; Vocational (D3/D4) applicants must submit by 7 Sep 2026. | `2026-09-14`, with the Vocational exception in `extra_requirements` | silently picking one, losing the other |
| 8 | **A section in Indonesian.** §4: Surat Pernyataan, mandatory, maksimal 300 kata, assessed separately. | present, cap `300`, required | missed because the heading is not English |
| 9 | **Mixed register.** Formal English first person, except the Surat Pernyataan in formal Indonesian. | both captured | only the English half |
| 10 | **Numeric distractors.** 30 credits, GPA 3.00 and 3.25, 24 years, 18 months, 2 MB, 10 MB, 200 dpi, 21 September, and five assessment percentages. | none become a `word_cap` | any of them does |

**Why trap 7 matters most.** Dani's completed credential is a D3, so the deadline that actually
binds him is 7 September, not 14. No extractor can know that. This is exactly what Gate 1 is for:
the model reports what the document says, he corrects it against what he knows about himself, and
the correction is recorded before anything is written.
