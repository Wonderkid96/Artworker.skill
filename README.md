# Artworking

A Claude Code skill for checking print artwork before it goes to press.

Point Claude at a PDF or InDesign file and it works through a 13-domain artworking checklist — bleed, colour, resolution, typography, copy accuracy, print engineering — then renders a **marked-up PDF** with every fault boxed tight to the exact characters and labelled with what is wrong.

![severity](https://img.shields.io/badge/BLOCK%20%C2%B7%20RISK%20%C2%B7%20CRAFT%20%C2%B7%20NOTE-graded-informational)

## Install

**1. Add the plugin** — in Claude Code:

```
/plugin marketplace add Wonderkid96/Artworker.skill
/plugin install artworking
```

**2. Restart Claude Code.** Plugins load at session start, so the skill will not appear until you do.

**3. Check the environment.** This is the step people skip, and it matters: a missing dependency does not fail loudly, it makes whole checks silently unavailable while the report still looks complete.

```bash
python3 ~/.claude/plugins/cache/artworking/artworking/*/skills/artworking/tools/doctor.py
```

It prints what is present, what is missing, and the exact commands to fix it — using the path of the Python you actually ran it with, which avoids the usual "installed it, still not found" trap.

Expect something like:

```
  [  ok  ] PyMuPDF                reads and marks up PDFs
  [ miss ] PyObjC / spellcheck    spelling and grammar will NOT run
  [  ok  ] InDesign               Adobe InDesign 2026

  Recommended:
    /opt/homebrew/bin/python3 -m pip install pyobjc-framework-Cocoa zxing-cpp
```

**4. Install what it asks for.**

| | Needed for | Install |
|---|---|---|
| **PyMuPDF** | everything — required | `pip install pymupdf` |
| **pyobjc-framework-Cocoa** | spelling, en_GB locale, grammar | `pip install pyobjc-framework-Cocoa` |
| **zxing-cpp** | barcode and QR scan-testing | `pip install zxing-cpp` |
| **ghostscript** | total ink coverage | `brew install ghostscript` |
| **poppler**, **exiftool** | text extraction, PDF metadata | `brew install poppler exiftool` |
| **verapdf** | PDF/X conformance | `brew install verapdf` |
| **Adobe InDesign** | `.indd` source checks — overset, swatches, links | macOS only; PDFs audit without it |

Nothing except PyMuPDF is mandatory. Anything missing is reported in the audit under "what was not checked", never silently skipped.

**5. Use it.**

```
/artwork ~/Work/brochure.pdf
```

Or just ask — "check this artwork before it goes to print", "is this print ready", "mark up the errors".

## What it does

**Audits.** Works the checklist in `skills/artworking/reference/artworking-functions.md`: spec intake, document construction, typography, copy and factual accuracy, brand compliance, colour, images, layout, print engineering, output, proofing, versioning.

**Marks up.** Produces two PDFs:

- `*_MARKED.pdf` — artwork on an oversized sheet, every instance of every fault boxed and named, findings column alongside, summary page with a verdict
- `*_COMMENTS.pdf` — original geometry with native annotations, so it opens in Acrobat's comment list and a printer or client can tick them off

**Is honest about its limits.** Every report ends with what was *not* checked and why. A clean report that quietly skipped half the checklist is worse than no report.

## What it catches well

The deterministic layer, which is where most reprint-grade errors actually originate:

- Copy: spelling, grammar, locale drift, double spaces, straight quotes, soft hyphens, hyphen/en-dash misuse
- Facts: date/day-of-week mismatches, arithmetic that does not add up, contradictions between pages, dead URLs
- Structure: trim/bleed boxes, page count vs binding, safety-margin violations
- Colour: stray RGB, spot-name mismatches (`PANTONE 485 C` vs `Pantone 485 C`), registration black in artwork, rich-black builds
- Images: effective resolution at placed size, colour space, upscaling
- Type: font embedding, substitution, minimum sizes, hairline strokes
- Barcodes and QR codes: decoded and scan-tested at true size

## What it does not do

- **Judge taste.** Optical alignment, whether a Pantone will sit right on uncoated stock, whether a fold will crack.
- **Approve regulatory copy.** Allergens, claims, certification wording, financial warnings — flagged for a human specialist, never signed off.
- **Replace a proof.** It is a thorough first pass, not a second pair of eyes and not a press pass.

## The one idea worth stealing

**Grade against what the file is for, not against print-readiness by default.**

A proof PDF has no bleed, downsampled images and RGB throughout. That is correct — it is a file for reading, not for printing. Marking those as blockers inflates the count with things nobody needs to act on and buries the findings that matter.

The skill identifies the file type by looking at it (`MediaBox = TrimBox = BleedBox`, uniform low ppi, sRGB throughout → proof) and states it up front before any tally.

## Requirements

- Python 3 with [PyMuPDF](https://pymupdf.readthedocs.io/) — `pip install pymupdf`
- Optional: `ghostscript` (ink coverage), `zxing-cpp` (barcode/QR decode), `verapdf` (PDF/X conformance)
- Optional: Adobe InDesign on macOS, for checks no PDF can answer — overset text, link status, swatch names as authored, font substitution

## Try it

```bash
python3 examples/make_sample.py                       # A5 flyer with 11 seeded errors
python3 skills/artworking/tools/mark.py \
    examples/sample_flyer.pdf examples/findings.json -o examples/out
```

## Roadmap

Auditing works. Fixing does not yet — `docs/specs/execute-mode-design.md` designs EXECUTE mode: apply the mechanical fixes to a *copy* of an InDesign file, then prove nothing regressed by re-auditing and diffing. The original is never opened, and that is asserted with a hash rather than promised.

## Licence

MIT
