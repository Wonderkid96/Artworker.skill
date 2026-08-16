#!/usr/bin/env python3
"""Generate a sample A5 flyer with deliberate artworking errors, for demoing mark.py.

Lines are placed explicitly rather than via text boxes, so the fixture geometry
is exact and reproducible.

Seeded errors (all real-world classics):
  - no bleed box at all, and a black band built to the trim edge
  - whole document in DeviceRGB
  - reversed body copy below minimum size
  - hyphen used for a date range
  - straight apostrophes
  - double space after a full stop
  - day of week does not match the date
  - bundle price does not add up
  - phone number differs between page 1 and page 2
  - hairline rule below 0.25pt
  - terms copy inside the safety margin
"""

from pathlib import Path
import fitz

MM = 72.0 / 25.4
W, H = 148 * MM, 210 * MM
OUT = Path(__file__).parent / "sample_flyer.pdf"

INK = (0.05, 0.05, 0.05)
RED = (0.902, 0.208, 0.165)
PAPER = (1.0, 0.992, 0.973)
WHITE = (1, 1, 1)

doc = fitz.open()


def line(p, x_mm, y_mm, s, size, colour=INK, font="helv"):
    p.insert_text((x_mm * MM, y_mm * MM), s, fontname=font, fontsize=size, color=colour)


# --- Page 1 ---
p = doc.new_page(width=W, height=H)
p.draw_rect(p.rect, color=None, fill=PAPER)
p.draw_rect(fitz.Rect(0, 0, W, 84 * MM), color=None, fill=INK)   # bleeds to trim, no bleed set

line(p, 14, 38, "SPRING", 44, WHITE, "hebo")
line(p, 14, 53, "SALE", 44, WHITE, "hebo")

# 5pt reversed body, and a hyphen where a date range needs an en dash
line(p, 14, 63, "Every item in store reduced. Members get first access", 5, WHITE)
line(p, 14, 66.5, "from the 3rd-14th of April, with early entry from 8am.", 5, WHITE)

# straight apostrophes, and a double space after 'run.'
line(p, 14, 96, "It's the biggest sale we've run.  Book your slot now", 10)
line(p, 14, 102, "and we'll hold your fitting room for a full hour.", 10)

# 4 April 2026 is a Saturday
line(p, 14, 130, "Launch night: Thursday 4 April 2026, 6pm", 11, RED, "hebo")

line(p, 14, 148, "Bundle offer", 9, INK, "hebo")
line(p, 14, 155, "Jacket", 9); line(p, 44, 155, "£45", 9)
line(p, 14, 161, "Shirt", 9);  line(p, 44, 161, "£30", 9)
line(p, 14, 167, "Belt", 9);   line(p, 44, 167, "£20", 9)
line(p, 14, 174, "Bundle price", 9, INK, "hebo"); line(p, 44, 174, "£90", 9, INK, "hebo")

# hairline at 0.15pt
p.draw_line(fitz.Point(14 * MM, 182 * MM), fitz.Point(W - 14 * MM, 182 * MM), color=INK, width=0.15)

line(p, 14, 190, "acmestores.co.uk   ·   01522 511 900", 8)

# --- Page 2 ---
p2 = doc.new_page(width=W, height=H)
p2.draw_rect(p2.rect, color=None, fill=PAPER)

line(p2, 14, 30, "Find us", 22, INK, "hebo")
for i, t in enumerate(["Acme Stores", "12 High Street", "Lincoln", "LN2 1AA"]):
    line(p2, 14, 48 + i * 6, t, 10)

line(p2, 14, 88, "01522 511 090", 12, INK, "hebo")   # differs from page 1

# 4mm from trim, inside the 5mm safety margin
line(p2, 4, 203, "Terms apply. Offer ends 14 April 2026. See website for full details.",
     6.5, (0.45, 0.43, 0.40))

doc.save(OUT, garbage=3, deflate=True)
doc.close()
print(f"wrote {OUT}  ({W/MM:.0f} x {H/MM:.0f} mm, no bleed)")
