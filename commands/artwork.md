---
description: Audit a print artwork file (PDF or InDesign) and produce a marked-up PDF. Usage: /artwork <path to file>
argument-hint: <path to .pdf or .indd>
---

Audit the artwork file at: $ARGUMENTS

Use the `artworking` skill. Work through it in this order:

1. **Identify what the file is FOR** before grading anything — proof, print PDF, or source. Check the boxes, image ppi and colour space rather than trusting the filename. State it in `job.context`.

2. **If it is an InDesign file**, use the bridge:
   ```bash
   python3 <skill>/tools/indesign.py audit "<path>"
   ```
   It copies the file, opens only the copy, deletes it afterwards and hash-verifies the original. Never open the original by any other route.

3. **If it is a PDF**, read it directly with PyMuPDF. Use `tools/locate.py` for character-exact positions.

4. **Render the pages and look at them.** Text extraction gives frame order, not visual order — never conclude anything about layout or caption pairing without seeing the page.

5. **Write `findings.json`** per `tools/findings_schema.md`. Every finding needs evidence, a `short` label, and every instance in `rects`.

6. **Render the markup:**
   ```bash
   python3 <skill>/tools/mark.py "<artwork.pdf>" findings.json -o <outdir>
   ```

7. **Report**: the tallies, the blockers in plain language, and what could not be checked and why.

If no path was given, ask for one.
