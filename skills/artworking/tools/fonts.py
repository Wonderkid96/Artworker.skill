#!/usr/bin/env python3
"""Find font files by the names InDesign reports.

InDesign names a font by family and style — `Univers\\tBold Condensed`. The file
on disk is called `UniversLTStd-BoldCn.otf`. Filename matching therefore fails
constantly, so this reads the OpenType `name` table instead and indexes fonts by
what they actually call themselves.

Found fonts are copied into a `Document Fonts` folder beside the document.
InDesign activates that folder automatically, without installing anything
system-wide — the same mechanism `File > Package` uses.

    python3 fonts.py find "Univers\\tBold Condensed" --search ~/Library/Fonts
    python3 fonts.py index ~/Library/Fonts        # what is in a folder

Adobe Fonts cannot be collected this way. They are licensed per user and live
in an obfuscated CoreSync cache with no readable filenames. The only fix is for
the recipient to activate the family themselves.
"""

from __future__ import annotations

import argparse
import shutil
import struct
import sys
from pathlib import Path

FONT_EXTS = {".otf", ".ttf", ".ttc", ".otc", ".dfont"}

DEFAULT_SEARCH = [
    Path.home() / "Library/Fonts",
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path("/Library/Application Support/Adobe/Fonts"),
]

# name table IDs
FAMILY, SUBFAMILY, FULL_NAME, POSTSCRIPT, TYPO_FAMILY, TYPO_SUBFAMILY = 1, 2, 4, 6, 16, 17


def _decode(raw: bytes, platform: int, encoding: int) -> str:
    try:
        if platform == 3 and encoding in (1, 10):
            return raw.decode("utf-16-be", errors="ignore")
        if platform == 0:
            return raw.decode("utf-16-be", errors="ignore")
        return raw.decode("mac-roman" if platform == 1 else "latin-1", errors="ignore")
    except Exception:
        return ""


def read_names(path: Path, offset: int = 0) -> dict[int, str]:
    """Pull the OpenType name table. No dependency; the format is stable."""
    names: dict[int, str] = {}
    try:
        with path.open("rb") as fh:
            fh.seek(offset)
            tag = fh.read(4)
            if tag == b"ttcf":                      # collection: read the first face
                fh.seek(offset + 12)
                first = struct.unpack(">I", fh.read(4))[0]
                return read_names(path, first)
            if tag not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"typ1"):
                return names

            num_tables = struct.unpack(">H", fh.read(2))[0]
            fh.seek(offset + 12)
            name_off = name_len = None
            for _ in range(num_tables):
                entry = fh.read(16)
                if len(entry) < 16:
                    break
                t, _cs, off, ln = struct.unpack(">4sIII", entry)
                if t == b"name":
                    name_off, name_len = off, ln
                    break
            if name_off is None:
                return names

            fh.seek(name_off)
            _fmt, count, string_off = struct.unpack(">HHH", fh.read(6))
            records = [struct.unpack(">HHHHHH", fh.read(12)) for _ in range(count)]
            for platform, encoding, _lang, name_id, length, off in records:
                if name_id not in (FAMILY, SUBFAMILY, FULL_NAME, POSTSCRIPT,
                                   TYPO_FAMILY, TYPO_SUBFAMILY):
                    continue
                fh.seek(name_off + string_off + off)
                text = _decode(fh.read(length), platform, encoding).strip()
                if text and name_id not in names:
                    names[name_id] = text
    except Exception:
        pass
    return names


def font_keys(names: dict[int, str]) -> set[str]:
    """Every way InDesign might refer to this face, lowercased."""
    keys = set()
    fam = names.get(TYPO_FAMILY) or names.get(FAMILY)
    sub = names.get(TYPO_SUBFAMILY) or names.get(SUBFAMILY)
    if fam and sub:
        keys.add(f"{fam}\t{sub}".lower())
        keys.add(f"{fam} {sub}".lower())
    if fam:
        keys.add(fam.lower())
    for nid in (FULL_NAME, POSTSCRIPT):
        if names.get(nid):
            keys.add(names[nid].lower())
    # InDesign's plain "Regular" style is often just the family name
    if fam and sub and sub.lower() in ("regular", "roman", "book"):
        keys.add(fam.lower())
    return keys


def index_folder(folders) -> dict[str, list[Path]]:
    """Map every name a font answers to -> the files providing it."""
    idx: dict[str, list[Path]] = {}
    for folder in folders:
        folder = Path(folder).expanduser()
        if not folder.is_dir():
            continue
        for f in folder.rglob("*"):
            if f.suffix.lower() not in FONT_EXTS or not f.is_file():
                continue
            keys = font_keys(read_names(f))
            for k in keys:
                idx.setdefault(k, [])
                if f not in idx[k]:
                    idx[k].append(f)
    return idx


def normalise(indesign_name: str) -> list[str]:
    """InDesign reports 'Family\\tStyle'. Produce the variants to look up."""
    n = indesign_name.strip()
    out = {n.lower(), n.replace("\t", " ").lower()}
    if "\t" in n:
        fam, _, sub = n.partition("\t")
        out.add(f"{fam.strip()} {sub.strip()}".lower())
        if sub.strip().lower() in ("regular", "roman", "book"):
            out.add(fam.strip().lower())
    return [x for x in out if x]


def resolve(missing: list[str], search=None) -> dict:
    """Match reported font names against files on disk."""
    idx = index_folder(search or DEFAULT_SEARCH)
    found, ambiguous, not_found = {}, {}, []
    for name in missing:
        hits: list[Path] = []
        for key in normalise(name):
            for p in idx.get(key, []):
                if p not in hits:
                    hits.append(p)
        if not hits:
            not_found.append(name)
        elif len(hits) > 1:
            ambiguous[name] = [str(p) for p in hits]
        else:
            found[name] = str(hits[0])
    return {"found": found, "ambiguous": ambiguous, "notFound": not_found,
            "indexed": len(idx)}


def collect(found: dict[str, str], document: Path) -> list[str]:
    """Copy into `Document Fonts` beside the document. InDesign activates it
    automatically, with nothing installed system-wide."""
    dest = Path(document).expanduser().resolve().parent / "Document fonts"
    dest.mkdir(exist_ok=True)
    copied = []
    for name, src in found.items():
        target = dest / Path(src).name
        if not target.exists():
            shutil.copy2(src, target)
        copied.append(str(target))
    return copied


def main() -> int:
    ap = argparse.ArgumentParser(description="Find font files by InDesign's names.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find", help="locate named fonts")
    f.add_argument("names", nargs="+", help=r"e.g. 'Univers\tBold Condensed'")
    f.add_argument("--search", nargs="*", help="folders to search")

    i = sub.add_parser("index", help="list what a folder provides")
    i.add_argument("folders", nargs="+")

    args = ap.parse_args()

    if args.cmd == "index":
        idx = index_folder(args.folders)
        for k in sorted(idx):
            print(f"{k}\t{idx[k][0].name}")
        print(f"\n{len(idx)} names from {len(set(p for v in idx.values() for p in v))} files",
              file=sys.stderr)
        return 0

    names = [n.replace("\\t", "\t") for n in args.names]
    res = resolve(names, args.search)
    for n, p in res["found"].items():
        print(f"FOUND      {n!r}\n           -> {p}")
    for n, ps in res["ambiguous"].items():
        print(f"AMBIGUOUS  {n!r}")
        for p in ps:
            print(f"           -> {p}")
    for n in res["notFound"]:
        print(f"NOT FOUND  {n!r}")
    print(f"\nsearched {res['indexed']} font names", file=sys.stderr)
    return 0 if not res["notFound"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
