#!/usr/bin/env python3
"""Character-exact location of text patterns in a PDF.

`page.search_for()` only finds literal strings and returns whole-word boxes, so
it cannot mark a double space, a soft hyphen, or one stray character. This
rebuilds each page's text from per-character boxes, keeps an index from string
offset back to bbox, and runs regex against it. A match maps back to the union
of its characters' boxes — so the mark sits on the exact glyphs, nothing more.

    from locate import PageIndex
    idx = PageIndex(page)
    for m in idx.finditer(r"\\S  +\\S"):
        print(m.rects)      # one rect per line the match spans
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf


@dataclass
class Hit:
    text: str
    start: int
    end: int
    rects: list
    context: str


class PageIndex:
    """Page text with a character-to-bbox map."""

    def __init__(self, page: pymupdf.Page):
        self.page = page
        chars: list[tuple[str, pymupdf.Rect, int]] = []   # (char, bbox, line_id)
        raw = page.get_text("rawdict")
        line_id = 0
        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_id += 1
                for span in line.get("spans", []):
                    for ch in span.get("chars", []):
                        chars.append((ch["c"], pymupdf.Rect(ch["bbox"]), line_id))
                chars.append(("\n", None, line_id))
        self.chars = chars
        self.text = "".join(c[0] for c in chars)

    def finditer(self, pattern: str, flags: int = 0):
        for m in re.finditer(pattern, self.text, flags):
            yield self._hit(m)

    def find_literal(self, needle: str):
        start = 0
        while True:
            i = self.text.find(needle, start)
            if i < 0:
                return
            yield self._hit_span(i, i + len(needle), needle)
            start = i + 1

    def _hit(self, m):
        return self._hit_span(m.start(), m.end(), m.group(0))

    def _hit_span(self, a: int, b: int, text: str):
        # Group the matched characters by line so a wrapped match gets one rect
        # per line rather than one box swallowing the whole paragraph.
        by_line: dict[int, pymupdf.Rect] = {}
        for ch, bbox, lid in self.chars[a:b]:
            if bbox is None or bbox.is_empty:
                continue
            by_line[lid] = bbox if lid not in by_line else by_line[lid] | bbox
        rects = [[round(r.x0, 2), round(r.y0, 2), round(r.x1, 2), round(r.y1, 2)]
                 for r in by_line.values()]
        s = max(0, a - 45)
        e = min(len(self.text), b + 45)
        ctx = self.text[s:e].replace("\n", " ")
        return Hit(text, a, b, rects, ctx)


def scan_document(doc, pattern: str, flags: int = 0, pages=None):
    """Return [(pdf_page_index_1based, Hit), ...] across the document."""
    out = []
    for i, page in enumerate(doc):
        if pages and (i + 1) not in pages:
            continue
        for hit in PageIndex(page).finditer(pattern, flags):
            out.append((i + 1, hit))
    return out
