# Print specs: the numbers

UK / Europe defaults. **Always defer to the printer's own spec sheet.** These are the values to assume when nobody has told you otherwise, and the values to challenge a file against.

---

## Bleed and margins

| Job type | Bleed | Safety margin from trim |
|---|---|---|
| Standard litho / digital print | 3mm | 3-5mm |
| Packaging / cartons | 3-5mm past the die | 3mm from any fold or cut |
| Large format | 5-10mm (more for hemmed or grommeted) | 25mm+ from edge |
| Perfect bound, inner gutter | n/a | 5mm+ additional grind-off clearance |
| US convention | 0.125in (3.175mm) | 0.125in |

Crop mark offset: 3-5mm, so marks sit clear of the bleed.

---

## Resolution

| Output | Effective resolution at final size |
|---|---|
| Litho and quality digital | 300 ppi |
| Newsprint / coarse screen | 200 ppi |
| Large format, close viewing (exhibition panel) | 150 ppi |
| Large format, distant viewing (billboard) | 30-72 ppi at final size |
| Bitmap / line art | 1200 ppi |

**Effective** resolution means after placement scaling. A 300 ppi image placed at 200% is a 150 ppi image.

Screen ruling relationship: ppi ≈ 2 × lpi. 150 lpi litho wants 300 ppi.

---

## Ink limits (Total Area Coverage)

| Process / stock | TAC limit |
|---|---|
| Sheetfed coated | 300-340% |
| Sheetfed uncoated | 260-300% |
| Web offset coated | 300% |
| Newsprint | 240% |
| Uncoated board / kraft | 240-280% |

Rich black builds (these are swatch recipes, not TAC limits):

| Use | Build |
|---|---|
| Large solid black areas, coated | C60 M40 Y40 K100 (240%) |
| Cooler rich black | C60 M40 Y40 K100 or C40 M30 Y30 K100 |
| Small text and fine rules | K100 only |
| Uncoated | Lighter build, e.g. C40 M30 Y30 K100 |
| Registration marks only | 100/100/100/100 — **never in artwork** |

---

## Minimum sizes

| Element | Litho (coated) | Uncoated | Flexo / screen |
|---|---|---|---|
| Positive line / rule | 0.25pt | 0.5pt | 0.5-1pt |
| Reversed line | 0.5pt | 0.75pt | 1pt+ |
| Positive type | 5pt | 6pt | 6-8pt |
| Reversed type | 6pt, bold-ish | 7pt | 8pt+, sans, no fine serifs |
| Reversed out of 4 colours | 8pt+, avoid fine serifs entirely | — | avoid |
| Minimum holdable tint | 2-3% | 5% | 5-10% |

Statutory: EU/UK food information regulations require a minimum x-height of **1.2mm** for mandatory particulars (0.9mm on packs with a largest surface under 80cm²).

---

## PDF/X

| Standard | Colour | Transparency | Use when |
|---|---|---|---|
| **PDF/X-1a:2001** | CMYK + spot only, no ICC-based colour | Must be flattened | Older RIPs, conservative printers, most UK trade printers still ask for this |
| **PDF/X-3:2002** | Allows ICC / device-independent colour | Flattened | Rare in practice |
| **PDF/X-4:2010** | ICC colour, device-independent | Live transparency preserved | Modern RIPs. Better for jobs with transparency, drop shadows, live effects. Smaller files. |

**Ask the printer which one.** Exporting X-4 to a printer expecting X-1a is a common and expensive mistake, and the reverse flattens work that didn't need flattening.

Output intent profiles:

| Region / stock | Profile |
|---|---|
| Europe, coated | FOGRA39 (ISO Coated v2) or FOGRA51 (PSO Coated v3) |
| Europe, uncoated | FOGRA47 / FOGRA52 (PSO Uncoated v3) |
| US, commercial | GRACoL 2013 (CRPC6) |
| US, web / publication | SWOP |
| Newsprint | ISOnewspaper26v4 |

---

## Binding and construction

| Binding | Page count rule | Notes |
|---|---|---|
| Saddle stitch | Multiple of 4 | Creep/shingling on thick stock; outer pages need trim compensation |
| Perfect bound / PUR | Multiple of 2, practical minimum ~40pp | 5mm+ grind-off; spine width = pages × caliper ÷ 2 (+ cover) |
| Wiro / spiral | Any | Punch zone clear of content, typically 10-12mm |
| Section sewn | Multiple of 16 (or 8) | — |

Fold panel shortening: each panel that tucks inside is **2-3mm shorter** than the one outside it. A 6pp rollfold has three different panel widths.

Spine text: only where the spine is **4-5mm or wider**.

---

## Barcodes

| Symbology | Use |
|---|---|
| EAN-13 / UPC-A | Retail consumer unit |
| EAN-8 | Small retail packs |
| ITF-14 | Outer case / carton |
| GS1-128 | Logistics, variable data |
| GS1 DataMatrix | Healthcare, small items, 2D |

- Nominal EAN-13 size: 37.29 × 25.93mm at 100% magnification
- Permitted magnification: **80% to 200%** for retail (below 80% will be rejected by GS1)
- Quiet zone: minimum 2.31mm left, 1.65mm right at nominal (scales with magnification). Never crop it.
- Bar Width Reduction: process-dependent. Litho ~0.01-0.02mm, flexo can need 0.03-0.08mm. **The printer specifies it.**
- Colour: dark bars on light ground. Black on white is safest. **Red bars are invisible to a red-light scanner.** No barcode on a dark, metallic or transparent ground without a solid white patch behind it.
- Orientation: picket fence (bars perpendicular to press direction) is more tolerant than ladder.
- Always scan-test at final printed size, not on screen.

QR codes: minimum 4-module quiet zone, high contrast, at least 2cm × 2cm in print for reliable phone scanning, never across a fold, crimp, seam or curve.

---

## Specials

| Special | Artwork requirement |
|---|---|
| Foil | 100% flat spot swatch, own layer, overprint on. No gradients, no tints, no fine detail below ~0.5pt. Allow registration tolerance against litho. |
| Spot UV / varnish | Same as foil. Keep off glue flaps and write-on areas. Allow 0.5mm registration pull-back from litho edges. |
| Emboss / deboss | Own spot layer. Avoid sharp internal corners. Generous registration tolerance. |
| White ink | Own spot layer, named per printer (often `White` or `Opaque White`). Underbase required on clear, metallic or dark substrates. Do **not** set to overprint. |
| Die cut | Own layer, spot swatch (commonly `CutContour` or `Die`), 0.25pt stroke, no fill, overprint on, non-printing. Artwork bleeds past the die. |

---

## File naming

```
Client_Job_Item_Size_vNN_YYYYMMDD_PRINT.pdf
Client_Job_Item_Size_vNN_YYYYMMDD_PROOF.pdf
```

Print files carry marks and bleed. Proof files carry neither, are downsampled, and are watermarked `PROOF - NOT FOR PRINT`.
