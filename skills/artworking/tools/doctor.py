#!/usr/bin/env python3
"""Check the environment and say exactly what is missing.

Run this first. A missing dependency does not break the skill loudly — it makes
whole checks silently unavailable, which is worse, because the report still
looks complete.

    python3 doctor.py
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

OK, WARN, BAD = "  ok  ", " miss ", " FAIL "


def check_import(mod: str):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def main() -> int:
    rows, missing_req, missing_opt = [], [], []

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    rows.append((OK if sys.version_info >= (3, 9) else BAD,
                 f"Python {py}", sys.executable))
    if sys.version_info < (3, 9):
        missing_req.append("Python 3.9 or newer")

    # --- required ---
    if check_import("fitz") or check_import("pymupdf"):
        rows.append((OK, "PyMuPDF", "reads and marks up PDFs"))
    else:
        rows.append((BAD, "PyMuPDF", "REQUIRED — nothing works without it"))
        missing_req.append("pymupdf")

    # --- spelling ---
    if check_import("AppKit"):
        try:
            from AppKit import NSSpellChecker
            langs = list(NSSpellChecker.sharedSpellChecker().availableLanguages())
            gb = "en_GB" in langs
            rows.append((OK if gb else WARN, "PyObjC / spellcheck",
                         f"{len(langs)} languages, en_GB {'yes' if gb else 'NOT INSTALLED'}"))
            if not gb:
                missing_opt.append("en_GB dictionary: System Settings > Keyboard > Text > Spelling")
        except Exception as e:
            rows.append((WARN, "PyObjC / spellcheck", str(e)[:50]))
    else:
        rows.append((WARN, "PyObjC / spellcheck",
                     "spelling and grammar will NOT run"))
        missing_opt.append("pyobjc-framework-Cocoa")

    # --- optional binaries ---
    for tool, why, pkg in [
        ("gs", "total ink coverage", "ghostscript"),
        ("pdftotext", "fast text extraction", "poppler"),
        ("exiftool", "PDF metadata and output intent", "exiftool"),
        ("verapdf", "PDF/X conformance", "verapdf"),
    ]:
        path = shutil.which(tool)
        rows.append((OK if path else WARN, tool, path or f"optional — {why}"))
        if not path:
            missing_opt.append(pkg)

    if check_import("zxingcpp"):
        rows.append((OK, "zxing-cpp", "barcode and QR decode"))
    else:
        rows.append((WARN, "zxing-cpp", "barcodes and QR codes will NOT be scan-tested"))
        missing_opt.append("zxing-cpp")

    # --- InDesign ---
    apps = sorted((p.name for p in Path("/Applications").glob("Adobe InDesign*")), reverse=True)
    if apps:
        rows.append((OK, "InDesign", apps[0]))
    else:
        rows.append((WARN, "InDesign",
                     "not found — PDFs still audit; .indd source checks will not run"))

    # --- report ---
    print("\n  ARTWORKING — environment check\n")
    for status, name, detail in rows:
        print(f"  [{status}] {name:<22} {detail}")

    brew = [p for p in missing_opt if p in ("ghostscript", "poppler", "exiftool", "verapdf")]
    pip = [p for p in missing_opt if p in ("pyobjc-framework-Cocoa", "zxing-cpp")]

    print()
    if missing_req:
        print("  REQUIRED — the skill cannot run without these:")
        print(f"    {sys.executable} -m pip install {' '.join(p for p in missing_req if p[0].islower())}")
        print()
    if pip:
        print("  Recommended:")
        print(f"    {sys.executable} -m pip install {' '.join(pip)}")
    if brew:
        print(f"    brew install {' '.join(brew)}")
    for note in missing_opt:
        if note.startswith("en_GB"):
            print(f"    {note}")

    if not missing_req and not missing_opt:
        print("  Everything present. Nothing to install.")
    elif not missing_req:
        print("\n  Nothing is broken — the checks above marked 'miss' simply will not run,")
        print("  and the report will list them under what was not checked.")

    print()
    return 1 if missing_req else 0


if __name__ == "__main__":
    raise SystemExit(main())
