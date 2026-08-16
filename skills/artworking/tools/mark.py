#!/usr/bin/env python3
"""Render an artworking audit as a marked-up PDF.

Two outputs from one findings file:

  *_MARKED.pdf    Artwork placed on an oversized sheet with numbered callout
                  flags on the page and a findings column alongside. Read it
                  like a printer's markup. Opens anywhere.

  *_COMMENTS.pdf  The original PDF, geometry untouched, with native PDF
                  annotations. Opens in Acrobat's comment list so a printer or
                  client can tick findings off. Send this one out.

The findings column paginates: if a page has more findings than fit alongside
the artwork, additional sheets are emitted for that page. Nothing is ever
silently dropped.

Usage:
    mark.py <artwork.pdf> <findings.json> [-o OUTDIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz

# --- Constants -------------------------------------------------------------

PT = 1.0
MM = 72.0 / 25.4

COLUMN_W = 258 * PT
GUTTER = 26 * PT
PAD = 28 * PT
HEADER_H = 62 * PT
FLAG_R = 8.5 * PT
MIN_SHEET_H = 340 * PT
FLAG_GUTTER = 30 * PT      # reserved margin left of the artwork; flags live here, never on the page

# The base-14 fonts are Latin-1 only, which silently drops em dashes, curly
# quotes and the like. A typography tool cannot garble typography in its own
# report, so embed a Unicode TTF where one is available.
FONT = "helv"
FONT_B = "hebo"
FONT_FILES = {}

_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Arial.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("/System/Library/Fonts/Helvetica.ttc",
     "/System/Library/Fonts/HelveticaNeue.ttc"),
]

for _reg, _bold in _CANDIDATES:
    if Path(_reg).exists() and Path(_bold).exists():
        FONT, FONT_B = "artwork", "artworkb"
        FONT_FILES = {FONT: _reg, FONT_B: _bold}
        break


_MEASURE = {n: fitz.Font(fontfile=p) for n, p in FONT_FILES.items()}


def register_fonts(page):
    for name, path in FONT_FILES.items():
        page.insert_font(fontname=name, fontfile=path)


def text_len(s: str, font: str, size: float) -> float:
    f = _MEASURE.get(font)
    if f is not None:
        return f.text_length(s, size)
    return fitz.get_text_length(s, fontname=font, fontsize=size)

SEVERITIES = ("BLOCK", "RISK", "CRAFT", "NOTE")

# BLOCK uses the a strong red.
PALETTE = {
    "BLOCK": (0.902, 0.208, 0.165),
    "RISK":  (0.910, 0.569, 0.165),
    "CRAFT": (0.294, 0.510, 0.667),
    "NOTE":  (0.482, 0.463, 0.435),
}

INK = (0.039, 0.039, 0.039)
MUTED = (0.42, 0.39, 0.35)
LINE = (0.80, 0.78, 0.75)
PAPER = (1.0, 0.992, 0.973)
SHEET = (0.937, 0.929, 0.914)


def sev_colour(sev: str):
    return PALETTE.get(sev.upper(), PALETTE["NOTE"])


# --- Model -----------------------------------------------------------------


@dataclass
class Finding:
    id: int
    severity: str
    domain: str
    title: str
    detail: str
    action: str
    page: int = 0
    rects: list = None
    fixable: bool = False
    short: str = ""

    def label_text(self) -> str:
        """Two or three words naming the fault, shown on the mark itself."""
        if self.short:
            return self.short.upper()
        t = self.title.split(":")[0].split("—")[0].split("(")[0].strip()
        words = t.split()
        return " ".join(words[:3]).upper()

    @property
    def located(self) -> bool:
        return bool(self.rects) and self.page > 0

    @property
    def instances(self) -> int:
        return len(self.rects or [])


def load_findings(path: Path):
    data = json.loads(path.read_text())
    findings = []
    for raw in data.get("findings", []):
        # `rects` marks every instance; `rect` stays supported for single hits.
        rects = raw.get("rects")
        if rects is None:
            rects = [raw["rect"]] if raw.get("rect") else []
        findings.append(Finding(
            id=int(raw["id"]),
            severity=str(raw.get("severity", "NOTE")).upper(),
            domain=raw.get("domain", ""),
            title=raw.get("title", ""),
            detail=raw.get("detail", ""),
            action=raw.get("action", ""),
            page=int(raw.get("page", 0) or 0),
            rects=[tuple(r) for r in rects],
            fixable=bool(raw.get("fixable", False)),
            short=raw.get("short", ""),
        ))
    findings.sort(key=lambda f: (SEVERITIES.index(f.severity) if f.severity in SEVERITIES else 9, f.id))
    coverage = {
        "checks_run": data.get("checks_run", []),
        "checks_skipped": data.get("checks_skipped", []),
        "unverified": data.get("unverified", []),
    }
    return data.get("job", {}), findings, coverage


def tally(findings):
    return {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}


# --- Text measurement ------------------------------------------------------
# insert_textbox silently refuses to draw when the rect is too small, which is
# how findings go missing. Measure first, size the rect to fit, always.


def wrap(s: str, width: float, font: str, size: float) -> list[str]:
    out = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if not cur or text_len(trial, font, size) <= width:
                cur = trial
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


def block_h(s, width, font, size, leading=1.34) -> float:
    return max(1, len(wrap(s, width, font, size))) * size * leading


def put(page, x, y, width, s, size, colour=INK, font=FONT, leading=1.34) -> float:
    """Draw a wrapped block from a top-left origin. Returns height consumed."""
    lines = wrap(s, width, font, size)
    step = size * leading
    for i, ln in enumerate(lines):
        page.insert_text((x, y + size + i * step), ln, fontname=font, fontsize=size, color=colour)
    return max(1, len(lines)) * step


def put_right(page, x_right, y, s, size, colour=INK, font=FONT):
    w = text_len(s, font, size)
    page.insert_text((x_right - w, y), s, fontname=font, fontsize=size, color=colour)


def put_centre(page, cx, y, s, size, colour=INK, font=FONT):
    w = text_len(s, font, size)
    page.insert_text((cx - w / 2, y), s, fontname=font, fontsize=size, color=colour)


def label(page, x, y, s, size=6.2, colour=MUTED):
    page.insert_text((x, y), " ".join(s.upper()), fontname=FONT_B, fontsize=size, color=colour)


def chip(page, x, y, sev, w=44.0, h=11.0):
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=None, fill=sev_colour(sev), radius=0.14)
    put_centre(page, x + w / 2, y + h - 3.4, sev, 6.2, (1, 1, 1), FONT_B)


def flag(page, cx, cy, n, sev):
    c = sev_colour(sev)
    page.draw_circle(fitz.Point(cx, cy), FLAG_R + 1.6, color=None, fill=PAPER)
    page.draw_circle(fitz.Point(cx, cy), FLAG_R, color=None, fill=c)
    put_centre(page, cx, cy + 2.8, str(n), 7.8, (1, 1, 1), FONT_B)


# --- Findings column -------------------------------------------------------


def entry_h(f: Finding, w: float) -> float:
    h = FLAG_R * 2 + 5
    h += block_h(f.title, w, FONT_B, 8.8) + 4
    h += block_h(f.detail, w, FONT, 7.5) + 4
    if f.action:
        h += block_h(("MECHANICAL  " if f.fixable else "") + f.action, w - 8, FONT, 7.3) + 9
    return h + 15


def draw_entry(page, x, y, w, f: Finding) -> float:
    y0 = y
    flag(page, x + FLAG_R, y + FLAG_R, f.id, f.severity)
    chip(page, x + FLAG_R * 2 + 8, y + 3, f.severity)
    dom = f.domain.upper()
    if f.instances > 1:
        dom += f"   ·   {f.instances} INSTANCES"
    page.insert_text((x + FLAG_R * 2 + 60, y + 11.6), dom,
                     fontname=FONT_B, fontsize=6.2, color=MUTED)
    y += FLAG_R * 2 + 5

    y += put(page, x, y, w, f.title, 8.8, INK, FONT_B) + 4
    y += put(page, x, y, w, f.detail, 7.5, INK, FONT) + 4

    if f.action:
        txt = ("MECHANICAL  " if f.fixable else "") + f.action
        h = block_h(txt, w - 8, FONT, 7.3)
        page.draw_line(fitz.Point(x, y + 1), fitz.Point(x, y + h + 2),
                       color=sev_colour(f.severity), width=1.6)
        put(page, x + 8, y, w - 8, txt, 7.3, MUTED, FONT)
        y += h + 9

    page.draw_line(fitz.Point(x, y + 3), fitz.Point(x + w, y + 3), color=LINE, width=0.4)
    return (y + 15) - y0


def paginate(page_findings, column_h: float, w: float):
    """Pack findings into column-sized chunks. Never drops one."""
    if not page_findings:
        return [[]]
    chunks, cur, used = [], [], 0.0
    for f in page_findings:
        h = entry_h(f, w)
        if cur and used + h > column_h:
            chunks.append(cur)
            cur, used = [], 0.0
        cur.append(f)
        used += h
    chunks.append(cur)
    return chunks


# --- Marked-up sheet -------------------------------------------------------


def build_marked(src: fitz.Document, job, findings, coverage) -> fitz.Document:
    out = fitz.open()
    counts = tally(findings)
    add_summary_page(out, job, findings, coverage, counts)

    for pno in range(src.page_count):
        sp = src[pno]
        sw, sh = sp.rect.width, sp.rect.height
        scale = min(1.0, 620 * PT / sw, 780 * PT / sh)
        aw, ah = sw * scale, sh * scale

        sheet_w = PAD + FLAG_GUTTER + aw + GUTTER + COLUMN_W + PAD
        sheet_h = max(MIN_SHEET_H, PAD + HEADER_H + ah + PAD)
        column_h = sheet_h - PAD - HEADER_H - 26 - PAD

        # Order the column the way the eye moves down the page. Sorting by
        # severity instead makes the reader hunt for the mark they are looking at.
        page_findings = [f for f in findings if f.page == pno + 1]
        page_findings.sort(key=lambda f: (min(r[1] for r in f.rects), min(r[0] for r in f.rects))
                           if f.rects else (1e9, 1e9))
        chunks = paginate(page_findings, column_h, COLUMN_W)

        for ci, chunk in enumerate(chunks):
            page = out.new_page(width=sheet_w, height=sheet_h)
            register_fonts(page)
            page.draw_rect(page.rect, color=None, fill=PAPER)
            draw_header(page, job, sheet_w, pno + 1, src.page_count, counts,
                        ci + 1, len(chunks))

            art = fitz.Rect(PAD + FLAG_GUTTER, PAD + HEADER_H,
                            PAD + FLAG_GUTTER + aw, PAD + HEADER_H + ah)
            page.draw_rect(art + (-1, -1, 1, 1), color=None, fill=SHEET)
            page.show_pdf_page(art, src, pno)
            page.draw_rect(art, color=LINE, width=0.6)
            draw_trim(page, sp, art, scale)

            # Every finding on the page is flagged on every sheet, so the
            # artwork always shows the complete picture. Only the column splits.
            draw_callouts(page, page_findings, art, sp, scale, dim=chunk)

            col_x = PAD + FLAG_GUTTER + aw + GUTTER
            col_y = PAD + HEADER_H
            folio = job.get("page_labels", {}).get(str(pno + 1), str(pno + 1))
            hdr = f"findings on page {folio}"
            if len(chunks) > 1:
                hdr += f"  ({ci + 1} of {len(chunks)})"
            label(page, col_x, col_y + 6, hdr)
            page.draw_line(fitz.Point(col_x, col_y + 12),
                           fitz.Point(col_x + COLUMN_W, col_y + 12), color=LINE, width=0.6)
            y = col_y + 26

            if not chunk:
                page.insert_text((col_x, y + 4), "No findings on this page.",
                                 fontname=FONT, fontsize=8, color=MUTED)
            for f in chunk:
                y += draw_entry(page, col_x, y, COLUMN_W, f)

    return out


def draw_header(page, job, sheet_w, pno, total, counts, sheet_i, sheet_n):
    y = PAD
    page.draw_line(fitz.Point(PAD, y + HEADER_H - 14),
                   fitz.Point(sheet_w - PAD, y + HEADER_H - 14), color=INK, width=1.1)

    label(page, PAD, y + 8, "artwork audit")
    title = " / ".join(x for x in (job.get("client"), job.get("job"), job.get("item")) if x)
    page.insert_text((PAD, y + 27), title or "Untitled job", fontname=FONT_B, fontsize=14, color=INK)
    page.insert_text((PAD, y + 40), job.get("file", ""), fontname=FONT, fontsize=7.4, color=MUTED)

    x = sheet_w - PAD
    for sev in reversed(SEVERITIES):
        n = counts.get(sev, 0)
        c = sev_colour(sev) if n else LINE
        put_right(page, x, y + 21, str(n), 16, c, FONT_B)
        put_right(page, x, y + 32, sev, 5.8, MUTED, FONT_B)
        x -= 56

    # A document whose folios do not start at 1 (inners, sections) would
    # otherwise print a sheet number the designer cannot match to the artwork.
    folio = job.get("page_labels", {}).get(str(pno))
    tag = f"PAGE {folio} OF {total}" if folio else f"PAGE {pno} OF {total}"
    if sheet_n > 1:
        tag += f"   SHEET {sheet_i}/{sheet_n}"
    put_right(page, sheet_w - PAD, y + 44, f"{tag}   ·   {job.get('audited','')}", 6.2, MUTED, FONT_B)


def _map(r, sp, art, scale):
    return fitz.Rect(art.x0 + (r[0] - sp.rect.x0) * scale,
                     art.y0 + (r[1] - sp.rect.y0) * scale,
                     art.x0 + (r[2] - sp.rect.x0) * scale,
                     art.y0 + (r[3] - sp.rect.y0) * scale)


def draw_trim(page, sp, art, scale):
    try:
        trim = sp.trimbox
    except Exception:
        return
    if not trim or trim == sp.rect:
        return
    r = _map((trim.x0, trim.y0, trim.x1, trim.y1), sp, art, scale)
    page.draw_rect(r, color=(0.55, 0.55, 0.55), width=0.5, dashes="[2 2] 0")
    label(page, r.x0, r.y0 - 3, "trim", size=5)


def tag(page, x, y, n, sev, text=None):
    """Numbered chip beside a mark. Carries a short label on first use, so the
    reader can name the fault without cross-referencing the column."""
    body = f"{n}  {text}" if text else str(n)
    w = text_len(body, FONT_B, 6.4) + 7
    h = 9.8
    r = fitz.Rect(x, y, x + w, y + h)
    page.draw_rect(r, color=None, fill=sev_colour(sev), radius=0.2)
    page.insert_text((x + 3.5, y + h - 2.9), body, fontname=FONT_B, fontsize=6.4, color=(1, 1, 1))
    return r


def draw_callouts(page, page_findings, art, sp, scale, dim=None):
    """Mark every instance of every located finding.

    Each mark is a tight box on the exact glyphs, tagged with the finding
    number right beside it. No leader lines: on a dense page they cross the
    artwork and obscure more than they explain, and a reader matching a number
    to the column does not need one.
    """
    active = {f.id for f in (dim or page_findings)}
    taken: list[fitz.Rect] = []

    def place_tag(box, w):
        """Find a slot for the chip that does not cover another mark."""
        h = 9.8
        # Above and below first: they sit in the leading between lines, so they
        # obscure far less copy than a chip parked over the neighbouring words.
        options = [
            (box.x0, box.y0 - h - 1.0),                          # above
            (box.x0, box.y1 + 1.0),                              # below
            (box.x1 + 2.0, box.y0 + (box.height - h) / 2),       # right
            (box.x0 - w - 2.0, box.y0 + (box.height - h) / 2),   # left
        ]
        for x, y in options:
            r = fitz.Rect(x, y, x + w, y + h)
            if r.x0 < art.x0 - FLAG_GUTTER - 40 or r.x1 > art.x1 + 2:
                continue
            if r.y0 < art.y0 - 2 or r.y1 > art.y1 + 2:
                continue
            if any(r.intersects(t) for t in taken):
                continue
            return r
        return fitz.Rect(options[0][0], options[0][1],
                         options[0][0] + w, options[0][1] + h)

    for f in page_findings:
        if not f.located:
            continue
        c = sev_colour(f.severity)
        on = f.id in active
        op = 1.0 if on else 0.28

        for raw in f.rects:
            r = _map(raw, sp, art, scale)
            # A single space or one character is too small to see; grow the
            # mark to a legible minimum without shifting where it sits.
            if r.width < 5:
                r = fitz.Rect(r.x0 - (5 - r.width) / 2, r.y0, r.x1 + (5 - r.width) / 2, r.y1)
            if r.height < 5:
                r = fitz.Rect(r.x0, r.y0 - (5 - r.height) / 2, r.x1, r.y1 + (5 - r.height) / 2)
            r = fitz.Rect(r.x0 - 0.8, r.y0 - 0.8, r.x1 + 0.8, r.y1 + 0.8)

            # A tint over a whole page washes the artwork out and helps nobody.
            # Large marks get an outline only; the fill is for picking out words.
            big = r.get_area() > art.get_area() * 0.25
            if not big:
                page.draw_rect(r, color=None, fill=c, fill_opacity=0.18 * op)
            page.draw_rect(r, color=c, width=1.4 if big else 0.9, stroke_opacity=op)

            if on:
                first = raw is f.rects[0]
                words = f.label_text() if first else None
                w = text_len(f"{f.id}  {words}" if words else str(f.id), FONT_B, 6.4) + 7
                t = place_tag(r, w)
                tag(page, t.x0, t.y0, f.id, f.severity, words)
                taken.append(t)
            taken.append(r)


# --- Summary ---------------------------------------------------------------


def add_summary_page(out, job, findings, coverage, counts):
    W, H = 595.0, 842.0
    page = out.new_page(width=W, height=H)
    register_fonts(page)
    page.draw_rect(page.rect, color=None, fill=PAPER)
    m = 46.0
    cw = W - 2 * m

    label(page, m, m + 6, "artwork audit")
    title = " / ".join(x for x in (job.get("client"), job.get("job"), job.get("item")) if x)
    y = m + 16
    y += put(page, m, y, cw, title or "Untitled job", 20, INK, FONT_B, leading=1.15)
    page.insert_text((m, y + 10), job.get("file", ""), fontname=FONT, fontsize=8, color=MUTED)
    y += 18
    page.draw_line(fitz.Point(m, y), fitz.Point(W - m, y), color=INK, width=1.2)
    y += 20

    if job.get("spec"):
        label(page, m, y, "checked against")
        y += 8
        y += put(page, m, y, cw, job["spec"], 8.2, INK, FONT) + 14

    # What kind of file this is. Without it, format observations that are
    # normal for the supplied file type get read as faults in the artwork.
    if job.get("context"):
        h = block_h(job["context"], cw - 16, FONT, 7.6) + 14
        page.draw_rect(fitz.Rect(m, y, W - m, y + h), color=None, fill=(0.93, 0.94, 0.90))
        page.draw_rect(fitz.Rect(m, y, m + 3, y + h), color=None, fill=PALETTE["NOTE"])
        put(page, m + 12, y + 5, cw - 16, job["context"], 7.6, INK, FONT)
        y += h + 16

    bw = cw / 4
    for i, sev in enumerate(SEVERITIES):
        x = m + i * bw
        n = counts.get(sev, 0)
        c = sev_colour(sev) if n else LINE
        page.draw_rect(fitz.Rect(x, y, x + 26, y + 3), color=None, fill=c)
        page.insert_text((x, y + 34), str(n), fontname=FONT_B, fontsize=27, color=c)
        page.insert_text((x, y + 46), sev, fontname=FONT_B, fontsize=6.4, color=MUTED)
    y += 66

    if counts["BLOCK"]:
        verdict, bg, fg = "NOT PRINT READY", sev_colour("BLOCK"), (1, 1, 1)
    elif counts["RISK"]:
        verdict, bg, fg = "DECISIONS REQUIRED BEFORE PRINT", sev_colour("RISK"), (1, 1, 1)
    else:
        verdict, bg, fg = "NO BLOCKING ISSUES FOUND", (0.784, 0.859, 0.271), INK
    page.draw_rect(fitz.Rect(m, y, W - m, y + 26), color=None, fill=bg)
    page.insert_text((m + 10, y + 17.5), verdict, fontname=FONT_B, fontsize=9.5, color=fg)
    y += 44

    label(page, m, y, "all findings")
    page.draw_line(fitz.Point(m, y + 6), fitz.Point(W - m, y + 6), color=LINE, width=0.6)
    y += 20

    # Reserve room for the coverage block, which is mandatory.
    cov_lines = ([f"{c.get('check')}: {c.get('reason')}" for c in coverage.get("checks_skipped", [])]
                 + list(coverage.get("unverified", [])))
    cov_body = "\n".join(f"·  {ln}" for ln in cov_lines) or "·  Nothing. All checks in scope were run."
    cov_h = block_h(cov_body, cw, FONT, 7.2, leading=1.5) + 46
    limit = H - m - cov_h - 22

    for i, f in enumerate(findings):
        if y > limit:
            page.insert_text((m, y + 1), f"... and {len(findings) - i} more. All are marked up on the pages that follow.",
                             fontname=FONT, fontsize=7.4, color=MUTED)
            y += 15
            break
        page.draw_rect(fitz.Rect(m, y - 6, m + 3, y + 4), color=None, fill=sev_colour(f.severity))
        page.insert_text((m + 10, y + 1), f"{f.id:02d}", fontname=FONT_B, fontsize=7.6, color=MUTED)
        loc = f"p{job.get('page_labels', {}).get(str(f.page), f.page)}" if f.page else "doc"
        page.insert_text((m + 28, y + 1), loc, fontname=FONT, fontsize=7, color=MUTED)
        t = f.title
        while text_len(t, FONT_B, 7.8) > cw - 56 and len(t) > 8:
            t = t[:-2]
        page.insert_text((m + 52, y + 1), t, fontname=FONT_B, fontsize=7.8, color=INK)
        y += 15

    y = H - m - cov_h + 10
    page.draw_line(fitz.Point(m, y), fitz.Point(W - m, y), color=INK, width=1)
    y += 14
    label(page, m, y, "what was not checked")
    y += 10
    y += put(page, m, y, cw, cov_body, 7.2, MUTED, FONT, leading=1.5)

    put(page, m, H - m - 14, cw,
        "This is an automated first pass, not a sign-off. Artwork still needs a human read on paper before print.",
        6.6, sev_colour("BLOCK"), FONT_B)


# --- Acrobat comment layer -------------------------------------------------


def build_comments(src_path: Path, findings, job=None) -> fitz.Document:
    """Original geometry, native annotations.

    Located findings are annotated where they are. Document-level findings used
    to be stacked as loose icons on page 1, which made the comment list look
    like everything was wrong with the cover — they are now gathered into a
    single note instead.
    """
    doc = fitz.open(src_path)
    labels = (job or {}).get("page_labels", {})

    for f in findings:
        if not f.located:
            continue
        pno = f.page - 1
        if pno < 0 or pno >= doc.page_count:
            continue
        page = doc[pno]
        c = sev_colour(f.severity)
        body = f"{f.title}\n\n[{f.severity}] {f.domain}\n\n{f.detail}\n\nACTION: {f.action}"
        for j, r in enumerate(f.rects):
            a = page.add_rect_annot(fitz.Rect(*r))
            a.set_colors(stroke=c)
            a.set_border(width=1.2)
            suffix = f"  ({j + 1} of {len(f.rects)})" if len(f.rects) > 1 else ""
            a.set_info(title=f"{f.id:02d} · {f.severity} · {f.title}{suffix}", content=body)
            a.update()

    doc_level = [f for f in findings if not f.located]
    if doc_level:
        lines = []
        for f in doc_level:
            lines.append(f"{f.id:02d}  [{f.severity}] {f.title}\n     {f.detail}\n     ACTION: {f.action}\n")
        counts = tally(doc_level)
        head = "  ·  ".join(f"{s} {counts[s]}" for s in SEVERITIES if counts[s])
        note = doc[0].add_text_annot(
            fitz.Point(18, 18),
            "These apply to the document as a whole, not to this page.\n\n" + "\n".join(lines),
            icon="Note")
        note.set_colors(stroke=sev_colour(doc_level[0].severity))
        note.set_info(title=f"DOCUMENT-LEVEL · {len(doc_level)} findings · {head}",
                      content="These apply to the document as a whole, not to this page.\n\n"
                              + "\n".join(lines))
        note.update()
    return doc


# --- Entry point -----------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Render an artworking audit as a marked-up PDF.")
    ap.add_argument("artwork", type=Path)
    ap.add_argument("findings", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, default=None)
    args = ap.parse_args()

    for p in (args.artwork, args.findings):
        if not p.exists():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 1

    outdir = args.outdir or args.artwork.parent
    outdir.mkdir(parents=True, exist_ok=True)
    stem = args.artwork.stem

    job, findings, coverage = load_findings(args.findings)

    with fitz.open(args.artwork) as src:
        marked = build_marked(src, job, findings, coverage)
        marked_path = outdir / f"{stem}_MARKED.pdf"
        marked.save(marked_path, garbage=3, deflate=True)
        marked.close()

    comments = build_comments(args.artwork, findings, job)
    comments_path = outdir / f"{stem}_COMMENTS.pdf"
    comments.save(comments_path, garbage=3, deflate=True)
    comments.close()

    counts = tally(findings)
    print(f"  {marked_path}")
    print(f"  {comments_path}")
    print("  " + "   ".join(f"{s} {counts[s]}" for s in SEVERITIES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
