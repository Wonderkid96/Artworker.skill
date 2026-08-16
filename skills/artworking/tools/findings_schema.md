# Findings schema

The audit produces `findings.json`. Every output — marked PDF, Acrobat comment layer, written report — is generated from it. One source of truth, three renderings.

```jsonc
{
  "job": {
    "client":  "Acme",
    "job":     "Spring Campaign",
    "item":    "A5 Flyer, 2pp",
    "file":    "Acme_Spring_A5Flyer_v03.pdf",
    "spec":    "A5 148x210mm, 4/4, 3mm bleed, 300ppi, PDF/X-1a, FOGRA39, litho on 300gsm silk",
    "printer": "",
    "audited": "2026-08-16",

    // REQUIRED. What kind of file this is and how it is being graded.
    // Rendered as a banner above the tallies on the summary page.
    "context": "File supplied is a PROOF / review export, not print artwork. Format observations below describe the proof and are expected for this file type — they are not defects in the design.",

    // Maps PDF page index -> printed folio, for documents not starting at 1.
    "page_labels": { "1": "02", "2": "03", "5": "06" }
  },

  "checks_run":    ["structure", "fonts", "colour", "images", "text", "geometry"],
  "checks_skipped": [
    { "check": "total_ink_coverage", "reason": "proof copy is RGB — no separations to measure" }
  ],
  "unverified": [
    "Overset text — cannot be detected in a PDF. Check the InDesign source.",
    "Image licensing — no licence records supplied"
  ],

  "findings": [
    {
      "id":        1,
      "severity":  "BLOCK",              // BLOCK | RISK | CRAFT | NOTE
      "domain":    "Copy — factual",     // maps to artworking-functions.md
      "page":      5,                    // 1-based PDF page index. 0 = document-level.
      "rects":     [[490.4, 482.8, 523.0, 493.7]],   // every instance, source page points
      "title":     "Land Speed Record contradicts page 4",
      "detail":    "Reads 400mph. Page 4 gives 394.196 for the same record.",
      "action":    "Agree the figure with the client and make both pages match.",
      "short":     "wrong figure + wrong car",  // 2-4 words, printed ON the mark
      "fixable":   false                 // true = EXECUTE mode can apply it unattended
    }
  ]
}
```

## Severity

| | Meaning |
|---|---|
| `BLOCK` | Will produce a wrong or unusable print. Must fix. |
| `RISK` | Likely to cause a problem. Needs a decision. |
| `CRAFT` | Quality issue a good artworker would fix. |
| `NOTE` | Observation. No action required. |

**Severity is relative to what the file is for.** See "Grade against purpose" in `../CLAUDE.md`. Missing bleed in a print PDF is a BLOCK; missing bleed in a proof PDF is a NOTE, because a proof is not the file that goes to press. Grading a proof as though it were artwork produces a false BLOCK count and buries the findings that actually matter.

## Naming the fault on the mark

`short` is a two-to-four word label printed on the mark itself — `SOFT HYPHEN`, `DOUBLE SPACE`, `WRONG FIGURE + WRONG CAR`. Without it the reader sees a coloured box and has to cross-reference a number against the column to learn what is wrong with it. The designer on the first live job said exactly that: *"unsure of which errors are on each page even if I can see there is an error there."*

If `short` is absent the renderer derives one from the first few words of the title, but a hand-written one is better. Only the first instance on a page carries the words; the rest carry the number alone, so a page with forty soft hyphens stays readable.

The findings column is ordered by position down the page, not by severity, so the reader can work top to bottom against the artwork.

## Locating findings

`rects` marks **every instance**, not just the first. One finding covering thirteen double spaces carries thirteen rects, and the markup tags each one. `rect` (singular) is still accepted for single hits.

Coordinates are in **source page points**, top-left origin, matching PyMuPDF's page space. For character-exact positions — a double space, one soft hyphen, a single stray letter — use `tools/locate.py`, which rebuilds the page from per-character boxes so regex can find what `search_for()` cannot.

## Rules

- **`page` is the 1-based index into the supplied PDF, never the printed folio.** In a 22pp inners file folioed 02–23, the page folioed `06` is `page: 5`. Get this wrong and every callout lands one sheet out, silently — it happened on the first real job this tool ran. Always supply `job.page_labels` so headers and the summary list print the folio the designer recognises.
- **`job.context` is required.** A report without it invites the reader to grade a proof as though it were artwork.
- A finding with no `rects` is document-level and appears in the column without a mark.
- `checks_skipped` and `unverified` are **not optional**. A report that omits them overstates its own coverage.
- Give `checks_skipped` reasons that name the cause, not just the gap: "proof copy is RGB — no separations to measure" reads correctly; "no separations" reads like a fault.
- `fixable: true` means the correction needs **no design judgement** — a find/change, a property change, a swatch merge. It prints `MECHANICAL` on the markup so a designer can triage: these can be worked through quickly, the rest need thought.

  It does **not** mean anything was fixed, and it does not mean one click will fix it. No fixer exists yet; see `docs/specs/execute-mode-design.md`. Do not label it `AUTO-FIX` — on a report handed to a designer that reads as work already done.

  Do not set it on anything that moves geometry (extending a bleed, repositioning). Those trip the "no frame moved" gate in the EXECUTE design, so flagging them as mechanical is inconsistent with how they would actually be applied.
