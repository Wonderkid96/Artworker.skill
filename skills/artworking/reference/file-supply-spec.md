# What to ask for

The blocker on the first live job was not the tooling. It was that a bare `.indd` arrived with no fonts and no images, so a third of the checks could not run. This page fixes that permanently. The section marked FORWARDABLE can be pasted straight into an email.

---

## First: work out what you were actually sent

People send what is easy to send, which is usually a proof. Identify it before grading anything.

| Signal | Proof / review PDF | Print PDF |
|---|---|---|
| Boxes | Media = Trim = Bleed, no crop marks | Bleed box 3mm outside trim, crop marks present |
| Images | all at the same low ppi (100, 96, 150) | mixed, mostly 300+ |
| Colour | sRGB / DeviceRGB throughout | CMYK, with separations |
| Standard | plain PDF, no output intent | PDF/X-1a or X-4, output intent embedded |
| Size | a few MB | tens to hundreds of MB |

**A proof is not a defective print file. It is a different file for a different job.** Grade its content, note its type once, and ask separately whether the print export has been made correctly. Full doctrine in `../CLAUDE.md`.

The same applies in reverse: a print PDF is a poor thing to read on screen, and nobody should be asked to proofread one.

---

## The two routes, and what each one actually buys

| | **A. InDesign Package** | **B. Print-ready PDF** |
|---|---|---|
| Overset text | **Yes** — only route that shows it | No, it is baked in |
| Rag, widows, line breaks | Yes, with correct fonts | **Yes** — exactly as it will print |
| Real image resolution | Yes, plus filenames and paths | Yes, embedded at true res |
| Colour spaces per image | Yes | Yes |
| Swatch names, spot names | **Yes, as authored** | Separation names only |
| Overprint / knockout | Intent only | **Yes, as it will output** |
| Total ink coverage | No | **Yes** (Ghostscript) |
| PDF/X conformance | n/a | **Yes** |
| Barcode / QR scan test | Rasterised guess | **Yes, at true size** |
| Styles, overrides, layers | Yes | No |
| Can I *fix* it | **Yes** | No, fixes belong at source |
| Typical size | 2–5 GB | 30–150 MB |

**They answer different questions.** The PDF audits *what will actually print*. The package audits *what can be corrected*. Neither is a superset of the other.

**If you can only get one: get the PDF.** It covers more of the checks, it is small enough to email, it raises no font-licensing problem, and it is the file the printer receives so it is the file that matters. Accept one blind spot: **overset text is invisible in a PDF** and it is the single most expensive thing to miss.

**Best practice: ask for both.** They cost the sender about ninety seconds combined.

---

## The Adobe Fonts trap

`File > Package` does **not** include fonts activated through Adobe Fonts. That is an Adobe licensing restriction, not an oversight, and no setting changes it.

Univers — the missing family on the first live job — is available on Adobe Fonts. So if the originating studio activates it through Creative Cloud, it will never travel in a package, no matter how carefully they package.

**Fix it at our end instead:** activate Univers from Adobe Fonts in Creative Cloud. It is included in the subscription. Adobe CoreSync is already running on this machine, so activated fonts appear to InDesign automatically.

Ask the sender which foundry or source their fonts come from. If the answer is "Adobe Fonts", stop asking them for fonts and activate them locally. If the answer is a purchased desktop licence (Linotype, Monotype), then the package will carry them and the Document Fonts folder auto-activates without installing anything.

---

## FORWARDABLE — paste this into an email

> Could you send the artwork two ways so I can check it properly?
>
> **1. A print-ready PDF** — ideally the exact export you would send the printer.
> - Adobe PDF Preset: **PDF/X-4:2010** (or PDF/X-1a:2001 if the printer has asked for that)
> - Pages, **not** spreads
> - Marks: **crop marks on**, offset 3mm
> - Bleed: **use document bleed settings** (3mm)
> - Output intent / destination: your normal print profile (FOGRA39 or FOGRA51 for UK coated)
> - Compression: **do not downsample images** — this one matters, a downsampled PDF hides resolution problems rather than showing them
> - No security or password
>
> **2. An InDesign package** — `File > Package`, with:
> - Copy fonts
> - Copy linked graphics
> - Update graphic links in package
> - Include IDML
> - Include PDF (print)
>
> Then zip the whole package folder. If your fonts come from Adobe Fonts they will not be included — that is normal, just tell me which family and I will activate it this end.
>
> If it is easier to send only one, send the PDF.

---

## Checks that stay unavailable regardless

Be straight about these in every report. No file format fixes them.

- **Image licensing and expiry** — a records question. Ask for the licence list separately, especially for anything named `_WM`, `comp`, or with a stock-library filename pattern.
- **Regulatory, certification and legal copy** — flagged, never approved.
- **Copy accuracy against intent** — needs the approved copy deck. Without it, only internal consistency can be checked.
- **Brand compliance** — needs the guidelines document.
- **Colour appearance on stock** — needs a proof.
- **The printer's own requirements** — needs their spec sheet. Ask for it every time; every printer differs on PDF standard, bleed, marks and spot naming.

---

## Note on ink coverage

Ghostscript is now installed, so total area coverage is measurable from a PDF. Two cautions:

1. `-sDEVICE=inkcov` reports **average** coverage per page, not peak. A page averaging 180% can still contain a 340% patch. Peak TAC needs per-pixel separation rendering.
2. Coverage measured on a PDF *we* exported reflects *our* conversion settings, not the sender's. Only measure the sender's own print export, or the number is fiction.
