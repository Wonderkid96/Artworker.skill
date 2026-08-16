---
name: artworking
description: Use when checking a design file before it goes to print — proofreading artwork, running a preflight, marking up errors for a designer, or auditing a PDF or InDesign document for bleed, colour, resolution, typography and copy errors. Produces a marked-up PDF with every fault boxed and named. Triggers on "check this artwork", "preflight", "is this print ready", "proof this", "mark up the errors", "artwork audit".
---

# Artworking

Taking a signed-off design and checking it is genuinely ready to print. Read the file, find every fault, and produce a markup a designer can act on.

## First: what is this file FOR?

**Establish this before grading a single finding.** It is the most common way an artwork audit goes wrong.

| What arrived | For | Grade |
|---|---|---|
| **Proof / review PDF** | Reading and sign-off | Content only. No bleed, downsampled images, RGB and no PDF/X are **expected and correct**. Note the file type once. Do not grade them as defects. |
| **Print PDF** | Going to the printer | Everything. Here missing bleed really is a blocker. |
| **Source** (`.indd`, `.ai`) | Fixing | Everything, plus overset text, styles, swatches, layers — things no PDF can show. |
| **Package** | Fixing, with fonts and links | Everything. The only complete picture. |

Tell them apart by **looking, not by the filename**:

```
MediaBox = TrimBox = BleedBox, no crop marks   →  proof
every image at the same low ppi (100/96/150)   →  proof
sRGB or DeviceRGB throughout                   →  proof
no output intent, plain PDF                    →  proof
```

A proof is not a defective print file. It is a different file for a different job. Grading it as artwork inflates the blocker count with things nobody needs to act on and buries the findings that matter.

**Always state the file type in `job.context` before the tallies.** If you cannot tell what the file is for, ask.

## Workflow

1. **Identify the file type** (above) and get the spec — trim size, bleed, colour, stock, process, binding. Ask for the printer's own spec sheet; every printer differs. Without a spec, "correct" is undefined, so state the defaults you are assuming.
2. **Work the checklist** in `reference/artworking-functions.md`. 13 domains. Domains 9 and 10 (print engineering, output) apply only to a file actually going to press.
3. **Spellcheck the copy.** Not optional — it catches what attentive reading misses.
   ```bash
   python3 tools/spelling.py check <pages.json> --locale en_GB --words brand-terms.txt
   ```
   Run it on text extracted from a **PDF**, not from an InDesign audit: joining InDesign frames
   reconstructs word adjacencies that do not exist in the composed result, which invents
   run-together words. Verified on a live job — two of three were artefacts, one was real.

   Results are grouped by unique word with counts and folios, so a client's name appearing forty
   times is one line to dismiss. Keep the genuine ones and put the rest in a project wordlist.
   Needs `pip install pyobjc-framework-Cocoa`; if it is missing, say spelling was not checked
   rather than skipping it silently.

4. **Verify visually.** Render pages and look at them. Text extraction gives you frame order, not visual order — do not conclude anything about layout, caption pairing or reading order without seeing the page.
5. **Write `findings.json`** per `tools/findings_schema.md`.
6. **Render the markup:** `python3 tools/mark.py <artwork.pdf> <findings.json> -o <outdir>`

## Outputs

| File | For |
|---|---|
| `*_MARKED.pdf` | Markup sheets. Every instance boxed tight to the exact characters and labelled with what is wrong. Findings column alongside, summary page with a verdict and a mandatory "what was not checked" block. |
| `*_COMMENTS.pdf` | The original geometry with native annotations. Opens in Acrobat's comment list so a printer or client can tick them off. Send this one out. |
| `findings.json` | Machine-readable. |

## Severity

| | Meaning |
|---|---|
| `BLOCK` | Will produce a wrong or unusable print. Must fix. |
| `RISK` | Likely to cause a problem. Needs a decision. |
| `CRAFT` | Quality issue a good artworker would fix. |
| `NOTE` | Observation. No action required. |

Severity is **relative to what the file is for**. See the table at the top.

## Rules

1. **Never modify a supplied original.** Copy first, always.
2. **Every finding carries evidence** — page, measurement, value found vs value expected. "Resolution looks low" is not a finding. "p4, `hero.tif` placed at 168% giving 179ppi effective, spec requires 300ppi" is.
3. **Every report ends with what was NOT checked, and why.** A report implying coverage it did not achieve is worse than no report.
4. **Never say a check passed unless it ran.** If Ghostscript is not installed, the ink limit was not checked. Say so.
5. **Fix at source.** Copy and layout errors found in an exported PDF get reported, not patched in the PDF.
6. **This is not a sign-off.** It is a thorough first pass. Artwork still needs a human read on paper, and a proof, before print.
7. **Regulatory and legal copy is flagged, never approved.** Allergens, claims, financial warnings, statutory type sizes — flag for a human specialist.
8. **Defer to the printer's spec sheet** over any default in `reference/print-specs.md`.
9. **Mark every instance**, not just the first.

## Marking up well

A box the reader cannot identify is only half a markup. A designer on a live job put it exactly: *"unsure of which errors are on each page even if I can see there is an error there."*

- Give every finding a `short` label — `SOFT HYPHEN`, `DOUBLE SPACE`, `WRONG FIGURE`. It prints on the mark itself.
- Mark **every** instance. `tools/locate.py` finds text to the character, so a single double space or one soft hyphen can be boxed exactly.
- `page` in `findings.json` is the **PDF page index**, never the printed folio. Supply `job.page_labels` so headers show the folio the designer recognises. Getting this wrong puts every callout one sheet out, silently.

## Tools

| | |
|---|---|
| `tools/mark.py` | Renders `findings.json` into the marked PDF and comment layer |
| `tools/locate.py` | Character-exact text location. Rebuilds a page from per-character boxes so regex finds what `search_for()` cannot |
| `tools/spelling.py` | Spelling, en_GB/en_US locale consistency and targeted grammar rules, via the macOS dictionary |
| `tools/indesign.py` | Safe InDesign access: audit, geometry, package, relink, fonts |
| `tools/fonts.py` | Finds font files by the family+style names InDesign reports |
| `tools/findings_schema.md` | The contract. Read before writing a findings file. |

Requires PyMuPDF. Optional: `ghostscript` (ink coverage), `zxing-cpp` (barcode/QR decode), `verapdf` (PDF/X conformance).

## Reference

- `reference/artworking-functions.md` — the master checklist, 13 domains, ~200 checks
- `reference/print-specs.md` — bleed, ink limits, minimum sizes, PDF/X, ICC intents, binding maths, barcodes
- `reference/file-supply-spec.md` — what to ask a client for, with a forwardable email
- `reference/capability-matrix.md` — what can and cannot be checked, and by what means

## Reading InDesign (macOS)

InDesign answers things no PDF can: overset text, link status and true resolution, swatch names as authored, and whether fonts are **substituted** rather than present.

```bash
python3 tools/indesign.py --check              # is InDesign installed
python3 tools/indesign.py audit <file.indd>    # full read, JSON to stdout
```

**Never open the original by any other route.** InDesign writes to a document the moment it opens it — link records, version migration, a `.idlk` lock beside it. So "just reading" is not read-only.

`tools/indesign.py` handles that. Every session:

1. Refuses to run if the document is open in InDesign or a `.idlk` lock exists
2. Hashes the original, then sets it read-only for the duration
3. Copies it **beside itself** (so relative links and a sibling `Document Fonts` folder still resolve)
4. Opens only the copy, with `userInteractionLevel = NEVER_INTERACT` so a missing-link dialog cannot hang the run
5. Deletes the copy afterwards, unless `keep()` was called
6. **Re-hashes the original and raises if it changed by one byte**

Step 6 is the guarantee. It is an assertion that fails the run, not a promise.

### Reading the results

- `fonts[].status` — `fsIn` installed, **`fsSu` substituted**. If anything is substituted, every composition result (rag, widows, line breaks, and the overset count) was measured on the wrong metrics. Report those as unverified, not clean.
- `links[].status` — `lmis` missing. Missing links mean image quality and colour cannot be assessed.
- `overset.count` — the single most valuable thing here, and impossible to get from a PDF.
- `layers[].visible` — a hidden layer does not output. Watch for hidden special-finish layers (spot UV, foil) that the job is supposed to carry.

### Writing your own JSX

Put it in `tools/jsx/`. The bridge substitutes `__DOC_PATH__`, `__OUT_PATH__` and `__PARAMS__`, and expects JSON written to `__OUT_PATH__`.

ExtendScript is ES3 — no `JSON`, no modern syntax, and an exception inside a loop silently ends the loop. Wrap each section so a failure records itself and the rest still runs. `audit.jsx` shows the pattern.

**Use `allPageItems`, never `page.textFrames`** — the latter misses frames nested inside groups and will silently drop copy from your audit.
