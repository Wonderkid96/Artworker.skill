# Capability matrix: what Claude can actually do

Honest assessment, domain by domain, against `artworking-functions.md`.

Two modes are in scope:

- **AUDIT** — read the file, produce a full list of required adjustments. Report only.
- **EXECUTE** — make the adjustments in the file.

These have very different capability profiles. Auditing is largely solved. Executing depends entirely on file format.

Ratings: **Strong** (reliable, verifiable) / **Partial** (useful, needs human confirmation) / **Weak** (can flag, cannot conclude) / **No** (out of reach).

---

## Environment verified on this machine (2026-08-16)

| Tool | Status | Gives us |
|---|---|---|
| `pdftotext`, `pdfinfo`, `pdfimages` (poppler) | installed | text extraction, page boxes, image inventory |
| `exiftool` | installed | PDF metadata, output intent, producer |
| PyMuPDF (`fitz`) | installed | the workhorse: fonts, boxes, colour spaces, per-object geometry, text with coordinates, page rendering |
| Pillow, NumPy | installed | raster analysis, ink coverage estimation from rendered separations |
| Python 3, Node, Homebrew | installed | everything else is `brew install` away |
| Ghostscript 10.07.1 | **installed 2026-08-16** | total ink coverage (`-sDEVICE=inkcov`), separation rendering |
| zxing-cpp (in `demo/venv`) | **installed 2026-08-16** | barcode and QR decode — proven on the first live job |
| qpdf, mutool, ImageMagick, veraPDF | missing | PDF/X validation. Installable. |
| Adobe InDesign 2026, Illustrator 2026, Photoshop 2026, Acrobat DC | installed | the EXECUTE path for native files |
| Adobe scripting support | **proven 2026-08-16** — `osascript` > `do script ... language javascript` > InDesign 21.5.1 | full DOM read: fonts, swatches, links, overset, geometry, styles, layers, text. Also drives PDF export. |

---

## Before the domains: what is the file for

Every rating below assumes the file is being graded against its own purpose. A proof PDF cannot answer the production questions and should not be marked down for it — see "Grade against purpose" in `../CLAUDE.md`.

| Question | Proof PDF | Print PDF | Source | Package |
|---|---|---|---|---|
| Copy, grammar, facts | **yes** | yes | yes | yes |
| Composition (rag, widows) | **yes**, if fonts embedded | yes | only with fonts active | yes |
| Bleed, marks, boxes | no | **yes** | yes | yes |
| Ink coverage, overprint, separations | no | **yes** | no | no |
| True image resolution | no | **yes** | yes | yes |
| Overset text | no | no | **yes** | **yes** |
| Swatch and spot names as authored | no | partial | **yes** | **yes** |
| Can be corrected | no | no | **yes** | **yes** |

## AUDIT mode, by domain

| # | Domain | Rating | What Claude does well | Where it fails |
|---|---|---|---|---|
| 1 | Spec intake | **Strong** | Structures the spec sheet, interrogates gaps, flags what the printer hasn't told you | Cannot invent a spec you don't have |
| 2 | Document construction | **Strong** (PDF) | Reads MediaBox/TrimBox/BleedBox/CropBox exactly, verifies bleed amount, page count vs binding, checks content actually occupies the bleed area rather than sitting white | Cannot see native InDesign master pages or layer structure without an export or script bridge |
| 3 | Typography — mechanical | **Strong** | Font inventory with embedded/subset status, synthetic-style detection, minimum type size, language tag. From an InDesign source, also font *status* — the first live job showed all four Univers weights SUBSTITUTED. | Overset text does not exist in a PDF; it needs the source. And with a substituted font, every composition result is measured on the wrong metrics — treat rag, widows and overset as unverified, not clean. |
| 3 | Typography — craft | **Partial** | Widows and orphans, rag quality, consecutive hyphenation, and inconsistent leading are all computable from text-with-coordinates | Optical kerning judgement is taste. Flag, don't decide. |
| 3 | Typography — characters | **Strong** | Straight quotes, primes, double spaces, hyphen/en/em misuse, three-dot ellipses, missing non-breaking spaces, wrong symbols. Deterministic and complete. | — |
| 4 | Copy and language | **Strong** | Spelling, grammar, locale consistency, house style, terminology drift across a whole set | — |
| 4 | Factual verification | **Strong** | Date/day-of-week validation, price and VAT arithmetic, cross-reference and folio checking, sequence and ordering, URL loading and validation, phone/postcode format | Cannot dial a phone number. Format-checks only. |
| 4 | Copy deck diff | **Strong** | Verbatim diff of extracted PDF text against an approved copy deck. This alone catches most reprint-grade errors. | Needs the copy deck supplied |
| 4 | Legal and regulatory | **Weak** | Flags missing ® ™ ©, missing company number, missing allergen emphasis, implausible claims | **Cannot approve regulatory compliance.** Flags for a human, never signs off. |
| 5 | Brand compliance | **Partial** | With the brand guidelines supplied: colour values, typefaces, minimum size, clear space measured from geometry, lockup proportions. Rendered-page vision catches wrong or distorted logo variants. | Cannot confirm the logo is the master file rather than a good redraw without the original to diff against |
| 6 | Colour inventory | **Strong** | Full colour space inventory, stray RGB/Lab detection, separation names listed exactly as stored (catches `PANTONE 485 C` vs `Pantone 485 C`), spot count vs spec | Cannot judge whether a Pantone will look right on the actual stock |
| 6 | Colour build | **Partial** | Rich black formula, 100K-on-large-areas, registration black in artwork. Total ink coverage now measurable with Ghostscript, but `-sDEVICE=inkcov` gives page averages, not peak. | Dot gain and substrate interaction are experience, not maths |
| 6 | Overprint / separations | **Partial** | Overprint flags are readable from the PDF graphics state, including white-set-to-overprint (the classic disappearing-element bug) | Full separations preview reasoning is easier for a human with the plate view. Claude should render each plate and inspect. |
| 7 | Images and links | **Strong** | Effective resolution at final placed size, colour space per image, embedded profile, upscaling detection, compression artefact detection from render | Rights clearance and licence expiry are records, not file data. Must be supplied. |
| 8 | Layout and alignment | **Partial** | Measures object coordinates precisely: grid drift, inconsistent spacing, fractional positioning, repeated-element position drift page to page. This is genuinely good. | Optical vs mathematical alignment is judgement. Flag with the measurement, let a human rule. |
| 9 | Barcodes and QR | **Strong** once a decoder is installed | Decode, verify check digit, measure magnification and quiet zone from geometry, measure contrast, load QR destination URLs | Bar Width Reduction and press-direction orientation need the printer's spec |
| 9 | Print engineering | **Weak to Partial** | Checks the measurable rules: content across folds, panel shortening maths, spine width maths, gutter clearance, minimum stroke weight, glue-flap clearance | Whether ink will crack on a crease, whether registration will hold, whether the stock will take it. Experience. Not Claude's call. |
| 10 | Output and delivery | **Strong** | PDF version, output intent, embedded profile, font embedding, marks and bleed present, box relationships, filename convention, package completeness. Full PDF/X validation once veraPDF is installed. | — |
| 11 | Proofing | **No** | Can run a structured second pass and produce the proof report | **Cannot be the second pair of eyes.** Claude is a third pair, after the human. Cannot replace a contract proof or press pass. |
| 12 | Version management | **Strong** | Naming conventions, change logs, version diffs between two PDFs including a visual page-by-page diff | — |
| 13 | Accessible PDF | **Partial** | Tag structure, reading order, alt text presence, PDF/UA checks | Meaningful alt text quality still wants a human read |

---

## EXECUTE mode, by file format

This is where capability splits hard.

### PDF supplied (no source file)

**Partial.** Metadata, boxes, page order and simple structural fixes are editable programmatically. Text and layout edits in a final PDF are the wrong fix and should be refused — the correction belongs in the source. Correct output is a list of adjustments plus, where genuinely appropriate, a corrected export.

Safe to do: set/correct TrimBox and BleedBox, reorder or rotate pages, strip stray metadata, split spreads to singles, generate a watermarked proof PDF, produce annotated markup of every issue.

Not safe to do: retype copy, move type, recolour objects. Fix at source.

### InDesign / Illustrator source supplied

**Strong, but unproven here.** Both apps are installed and both ship scripting support. The route is ExtendScript driven over `osascript`, the same bridge pattern already used for After Effects on this machine. That gives full DOM access: styles, swatches, links, text, geometry, layers, export presets.

Realistically automatable in-app:
- Delete unused swatches, merge duplicate spot swatches, rename spots to the printer's exact string
- Convert stray RGB swatches to the approved CMYK or Pantone equivalents
- Set black text to overprint, clear overprint from white
- Apply or repair document bleed and slug
- Relink images, report and fix effective resolution failures
- Find/change across the document: straight quotes to typographer's quotes, double spaces, hyphen to en dash in ranges, three-dot ellipses
- Apply paragraph and character styles, clear local overrides
- Report every overset frame and every missing link, by page and frame
- Nudge objects onto whole-number coordinates and onto the grid
- Export to the correct PDF/X preset with the correct marks and bleed

Requires human judgement, so propose rather than apply:
- Fixing rags, widows and orphans (changes the copy fit)
- Any repositioning that changes the design
- Anything touching legal or regulatory copy
- Any colour decision not already specified

**Status: the bridge has not been built or tested in this session.** Treat as designed-not-proven until a round trip runs.

### Native Photoshop, Affinity, Figma, CorelDRAW

Photoshop: same ExtendScript route, viable. Affinity and CorelDRAW: no useful scripting bridge, audit-from-export only. Figma: API available, different problem.

---

## The honest summary

**Where Claude beats a tired human:** anything deterministic and repetitive. Copy diffing, factual verification, colour and font inventory, geometry measurement, spec compliance, and never once skipping an item because it's late on a Friday. Most reprint-grade errors live here.

**Where Claude is a useful assistant but not the decider:** typographic craft, optical alignment, brand-guideline interpretation, colour behaviour. It should present the measurement and the recommendation, and let you rule.

**Where Claude is no substitute:** production experience, physical proofing, and sign-off. It cannot be the second pair of eyes, because it is not a second pair of eyes — it is a very thorough first pass. And it cannot tell you a job will work on press.

**The failure mode to guard against:** a clean report reading as an approval. Every output must state what was checked, what was not checked, and what could not be checked. A silent pass is worse than no check at all.
