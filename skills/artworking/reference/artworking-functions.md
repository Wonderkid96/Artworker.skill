# Artworking: the full function taxonomy

What an artworker in a branding or packaging agency is actually responsible for, decomposed into checkable items. Use this as the master checklist. Domains 1-13.

A design is "signed off". Artworking is everything between that and a file a printer can run without phoning you.

**Before working this list, establish what the file is for.** Domains 1–8 and 11–13 apply to any file. Domains 9 and 10 — print engineering and output — only apply to a file that is actually going to press. Running them against a proof PDF produces findings nobody needs to act on and buries the ones they do. See "Grade against purpose" in `../CLAUDE.md`.

---

## 1. Spec intake

Before touching the file. Most artworking disasters are spec failures, not craft failures.

- Finished (trim) size, flat size, folded size
- Page count, and whether it divides correctly for the binding
- Print process: litho, digital, screen, flexo, gravure, letterpress, large format, DTG, embroidery
- Substrate: stock name, weight (gsm), caliper, coated/uncoated/board/synthetic/clear/kraft
- Colour spec: 4/4, 4/0, 1/1, CMYK + n spots, mono, duotone
- Specials: foil (which foil), spot UV, emboss/deboss, laminate (matt/gloss/soft-touch), varnish, white ink, die cut, perf, drill
- Binding: saddle stitch, perfect bound, wiro, PUR, section sewn, loop stitch
- **The printer's own artwork spec sheet.** Every printer differs on PDF preset, bleed, marks, spot naming, file delivery. Get it, don't assume.
- Quantity (affects process choice and therefore artwork constraints)
- Deadline, number of proof rounds, who signs off, in what form
- Delivery: portal, WeTransfer, file size cap, naming convention

**Deliverable:** a written spec sheet the artwork is checked against. Without one, "correct" is undefined.

---

## 2. Document construction

The mechanical setup. Get this wrong and everything downstream is wasted.

- Trim size exact, in the right units, no rounding drift
- Bleed applied and artwork genuinely extends into it (a bleed box with white in it is not bleed)
- Safety / quiet margin defined, and nothing critical inside it
- Correct document intent (Print), transparency blend space CMYK
- Colour settings and working spaces set before work starts, not after
- Page order correct; reader spreads, not printer spreads (do not impose unless explicitly asked; imposition is the printer's job and doing it uninvited causes chaos)
- Creep / shingling allowance for saddle stitch on bulky stock
- Grind-off allowance on perfect binding: keep content clear of the inner edge
- Spine width calculated from actual stock caliper and page count, not guessed
- Cover wrap, turn-in and hinge score allowances on cased work
- Die line on its own layer, named, set as a spot colour, overprint on, non-printing at output
- Fold, crease, perf and glue marks on separate named layers
- Layer discipline and naming: an artworker's file should be navigable by someone else
- Master pages / templates used, so a spec change is one edit not fifty
- Paragraph and character styles applied throughout, no local overrides
- Object styles for repeated elements
- No stray items on the pasteboard shipping in the package

---

## 3. Typography

The largest single category of artworking craft.

**Mechanical**
- No missing fonts; no font substitution
- No fake bold or fake italic (synthetic styling)
- Fonts licensed for embedding and, if handing over, for the client's use
- No overset text anywhere (the single most common catastrophic miss)
- Correct language and hyphenation dictionary (en-GB, not en-US)
- Live text vs outlined text decision made deliberately and documented

**Craft**
- Consistent leading, tracking, kerning; optical kerning on display sizes
- Widows and orphans eliminated
- Rags checked: no rivers, no stepped or sawtooth rags, no more than two consecutive hyphenations
- Hanging punctuation / optical margin alignment on justified and ranged text
- Justification settings sane (no gappy word spacing)
- Baseline grid adherence where the design uses one
- Real small caps, real ligatures, real fractions, correct figure style (lining vs oldstyle, tabular vs proportional in tables)

**Character-level**
- Typographer's quotes ' ' " ", never primes " ′
- Apostrophes not foot marks
- En dash for ranges, em dash for parenthetical (or spaced en per house style), hyphen for compounds
- Single ellipsis character, not three full stops
- Non-breaking spaces in units (10 kg), dates, initials, and before short trailing words
- Correct symbols: ® ™ © ° × ÷ – — £ € not lookalikes
- No double spaces after full stops
- No manual line breaks that survive a copy edit and break the rag

**Production-aware**
- Minimum type size for the process (flexo and screen need more than litho)
- Reversed-out type: heavier weight, avoid fine serifs and hairline stems, avoid four-colour reverse where registration is loose
- Type crossing folds, creases, perfs or die lines
- Type too close to trim, gutter, drill hole or glue flap
- Statutory minimum sizes where they apply (e.g. EU food information x-height 1.2mm)

---

## 4. Copy, content and factual accuracy

Proofreading is artworking. This is where agencies get sued and reprinted.

**Language**
- Spelling, against the correct locale, consistently (organise vs organize, one or the other throughout)
- Grammar and punctuation
- House style: capitalisation, serial comma, number style, date format, time format
- Consistency of terminology across the whole set, not just within one item

**Verification** (check against source, never against the previous artwork)
- Verbatim diff against the approved copy deck
- Names, spellings of names, job titles, qualifications, honorifics
- Phone numbers (dial them), emails (send to them), URLs (load them)
- Addresses and postcodes
- Dates: is the date real, does the stated day-of-week match, is the year right
- Prices, totals, percentages, VAT statements, currency symbols, decimal places
- Product codes, SKUs, batch references
- Cross-references, contents page numbers, folios, section numbers
- Captions matched to the correct image
- Sequence: no repeated or missing list items, correct alphabetical or numerical ordering

**Legal and regulatory**
- ® ™ © used correctly, on correct first use, on the correct marks
- Copyright line, year, company registration number, VAT number
- Promotion mechanics, closing dates, "no purchase necessary", odds statements
- Food: ingredients declaration, allergen emphasis, nutrition panel, net quantity, country of origin, storage, use-by format
- Recycling and disposal marks, packaging waste marks
- CE / UKCA, safety marks, age warnings
- Financial promotions wording and risk warnings
- Accessibility and contrast statements where contracted

**Consistency across a set**
- Business card, letterhead, comp slip, email signature all state the same phone number
- Every item in a campaign carries the same offer, dates and legal line

---

## 5. Brand compliance

- Correct logo **master file**, never redrawn, retyped, restretched or recoloured
- Correct variant for the context: primary, stacked, mono, reversed, single-colour
- Clear space / exclusion zone respected
- Minimum reproduction size respected for the process
- Logo not scaled non-proportionally; check for 99.7% scale accidents
- Brand colours specified in the right system for the job (Pantone for spot, the brand's approved CMYK breakdown for process, never a converted-on-the-fly RGB value)
- Brand typefaces, correct weights, correct hierarchy
- Photography treatment, crop rules, subject conventions
- Iconography, graphic devices, pattern usage per guidelines
- Tone of voice and written style per the brand's voice guidance
- Co-branding and endorsement lockups: correct relative sizing, order, separator, clear space
- Sub-brand and product-brand rules
- Sign-off against the brand guidelines document, cited by section

---

## 6. Colour

**Inventory**
- No stray RGB, Lab or ICC-based colours in a CMYK job
- No unused swatches; no duplicate swatches under different names
- Spot colour count matches the spec and the budget
- Spot names byte-identical across InDesign, Illustrator, Photoshop and every placed file (`PANTONE 485 C` ≠ `Pantone 485 C` ≠ `PANTONE 485 CV`)
- Correct Pantone library: Coated vs Uncoated vs Bridge, and matched to the substrate
- Approved Pantone-to-CMYK conversions where the job runs process-only

**Build**
- Rich black to the printer's formula (commonly 60/40/40/100 or 40/30/30/100), used on large solid areas
- 100K only for small text and fine rules
- Registration black (100/100/100/100) never used in artwork, only on marks
- Total Area Coverage within the process/stock limit (see `print-specs.md`)
- Tints achievable by the process (flexo cannot hold very light tints)
- Duotone / greyscale conversions done deliberately with correct curves

**Overprint and separation**
- Black text set to overprint (usually), white **never** set to overprint
- Overprint intent checked in Overprint Preview, on the exported PDF
- Separations Preview checked plate by plate, on the exported PDF
- Knockouts correct; no unintended white knockout of a spot varnish or foil layer
- Trapping: confirm whether the printer traps in RIP or expects it in the file

**Specials as separations**
- Foil, spot UV, varnish, white ink, emboss each on their own spot swatch
- Named exactly as the printer requires
- Set to 100% flat tint, overprint on, top layer
- Free of any gradient or transparency unless the process supports it
- Varnish-free zones for glue lines, address panels and write-on areas

**Management**
- Correct ICC output intent for the region and stock (FOGRA39/51 coated, PSO Uncoated, GRACoL/SWOP for US)
- No unexpected profile conversion on export
- Colour consistency across a set that runs on different processes and stocks (this needs deliberate compensation, not copy-paste)

---

## 7. Images and links

- All links present, current, none missing or modified
- Effective resolution at final placed size meets the process requirement
- No upscaled images, no web-sourced images, no screengrabs
- No visible JPEG artefacts, banding or posterisation
- Correct colour space per image, converted deliberately with the right profile, not silently on export
- Clipping paths and alpha channels clean; no white fringing or halo
- No stray white boxes from mishandled Photoshop transparency
- Retouching complete: dust, blemishes, join lines, mismatched skies
- Rights cleared: licence type, usage scope, territory, term, expiry date recorded
- No comp or watermarked stock anywhere in the file
- Model and property releases where people or private property appear
- Placed PDFs and AI files: check nested links, embedded fonts, and their own colour spaces
- Vector art: no stray points, no open paths where fills are intended, no redundant clipping masks, no unnecessary live effects
- Transparency and drop shadows in a spot-colour job (they flatten badly; usually need rebuilding)
- Transparency flattener resolution set correctly if flattening at all

---

## 8. Layout and alignment

The artworker's eye. Partly measurable, partly judgement.

- Grid adherence: columns, margins, baseline
- Consistent gutters and vertical rhythm
- Optical alignment where mathematical alignment looks wrong (round shapes, punctuation, wedge letterforms)
- Objects on whole-number coordinates; no fractional positioning causing soft edges
- Repeated elements in identical positions page to page (folios, running heads, logos)
- Consistent image sizes and crops across a series
- Stroke alignment (inside / centre / outside) accounted for in true dimensions
- Scaled groups: stroke weights scaled with them, or deliberately not
- Corner radii consistent
- Spacing consistent between like elements, and hierarchical (more space above a heading than below)
- Spread balance; no accidental trapped white space
- Nothing accidentally nudged: compare against the approved visual

---

## 9. Print engineering and feasibility

Where artworking stops being tidying and becomes production knowledge.

**Folding and construction**
- Panel sizes on rollfold / gatefold shortened progressively (typically 2-3mm per tucked panel)
- Elements that cross folds: will they align after fold tolerance, and will heavy ink crack on the crease
- Score direction with the grain
- Spine text only where the spine is wide enough to hold it
- Gutter loss on perfect binding: nothing critical, no cross-gutter type
- Glue flaps and seams free of ink and varnish
- Die line registered to the artwork, artwork bleeding past the die by the required amount

**Codes**
- Barcode type correct (EAN-13 retail, ITF-14 outer case, GS1-128 logistics, GS1 DataMatrix)
- Magnification within tolerance for the process
- Bar Width Reduction applied per the printer's requirement
- Quiet zones intact, human-readable numerals present and correct
- Orientation: picket fence vs ladder relative to press direction
- Contrast: bars dark, background light; never red bars, never on dark or metallic ground without a white patch
- Barcode **scan-tested** at final size, not eyeballed
- QR codes: quiet zone, contrast, adequate module size, tested, and not landing on a fold, curve, crimp or seam
- Destination URL of every QR code loaded and verified

**Process limits**
- Minimum stroke weight for the process (hairlines vanish)
- Minimum and maximum achievable tint
- Screen ruling vs image resolution
- Registration tolerance: avoid designs that need tight registration between litho and a foil or emboss pass
- Dot gain expectations on uncoated and board
- White ink underbase required on clear, metallic or dark substrates
- Substrate colour shifting perceived ink colour

**Format-specific**
- Large format: build scale (e.g. at 10%), viewing distance driving resolution, grommets, pole pockets, seam positions, wind slits, hem allowances
- Vehicle and window graphics: obstruction and door-line zones
- Screen print and embroidery: colour count, minimum line weight, stitch feasibility, underbase
- Mailing: Royal Mail clear zones, address panel position, PPI placement, machinability

---

## 10. Output and file delivery

- Correct PDF export preset for the printer (PDF/X-1a:2001 or PDF/X-4:2010; ask, don't guess)
- Correct output intent profile embedded
- Marks: crop marks on, offset clear of the bleed, no page information overlapping live area
- Bleed included at the specified amount
- Single pages or spreads exactly as the printer asked
- All fonts embedded
- Transparency flattened only if the standard requires it
- Layers preserved or flattened deliberately
- Image downsampling and compression settings appropriate
- **Re-check the exported PDF, not the source:** separations, overprint, ink limit, fonts, boxes, resolution. Export changes things.
- File naming convention: `Client_Job_Item_Size_vNN_YYYYMMDD_PRINT.pdf`
- Package / collect for output: links, fonts, IDML, and a plain-text instruction note
- A separate low-res, marks-free proof PDF for the client, watermarked "PROOF - NOT FOR PRINT"
- Correct number of files, correct versions, nothing extra, nothing stale

---

## 11. Proofing and sign-off

- **Second pair of eyes.** An artworker never signs off their own artwork. This is the single most effective control in the whole discipline.
- Read the hard copy, at actual size, on paper. Errors hide on screen.
- Proof type decided: soft proof, digital contract proof, wet proof, or press pass
- Colour proof viewed under D50 lighting, not office light
- Client sign-off obtained in writing, against the exact file that will be printed, with the filename recorded
- Amend rounds versioned and tracked; each round re-proofed in full, not just at the change
- Printer's own proof or plotter checked back against the approved artwork
- Approved artwork and the sign-off record archived together

---

## 12. Asset and version management

- One master source file. Forked copies are how the wrong version gets printed.
- Version numbering and date stamping convention, applied consistently
- Supplied assets archived separately from working files, unmodified
- Change log: what changed between versions and who asked for it
- Templates and style sheets maintained for repeat work
- Handover pack: working files, fonts (or font list and licence position), links, guidelines, print specs

---

## 13. Adjacent outputs

Often bundled into the artworking brief.

- Same content resized for digital and social formats, respecting safe areas
- Accessible PDF: tagged structure, logical reading order, alt text, PDF/UA compliance
- Screen versions with deliberate RGB conversion, not an accidental one
- Email signature, presentation template and document template versions

---

## The compressed version

If you only run ten checks before a file goes out:

1. Overset text anywhere
2. Missing or modified links, and effective resolution at final size
3. Missing fonts, or synthetic bold/italic
4. Stray RGB, stray spot colours, mismatched spot names
5. Bleed genuinely present, and nothing critical inside the safety margin
6. Overprint Preview and Separations Preview, on the exported PDF
7. Phone, email, URL, address, dates and prices verified against source
8. Logo is the master file, correct variant, correct clear space, correct minimum size
9. Barcode and QR scan-tested at final size
10. Someone other than you has read it on paper
