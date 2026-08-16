#!/usr/bin/env python3
"""Spelling, locale consistency and grammar for print copy.

Uses macOS's own spellchecker through NSSpellChecker. No dictionary files to
ship, and it knows en_GB properly — so `organize` and `colors` are flagged in a
British document, which is the single most common consistency failure in copy
that has passed through several hands.

The hard part is not finding misspellings. It is not drowning the report in
proper nouns. Every brand, product code and technical term is "misspelled", so
results are grouped by unique word with a count and page list: forty instances
of a client's name is one line to dismiss, not forty findings.

    python3 spelling.py check text.json --locale en_GB
    python3 spelling.py check text.json --words brand-terms.txt

`text.json` is `[{"folio": "02", "index": 1, "text": "..."}, ...]`.

**Prefer text extracted from a PDF over an InDesign audit.** InDesign's
`TextFrame.contents` returns each frame's logical text, and joining frames
reconstructs adjacencies that do not exist in the composed result — which
produces phantom run-together words like `forstraightforward`. A PDF is the
composed output, so word adjacency in it is real. Verified on a live job:
two of three run-together "errors" from an InDesign extraction were artefacts;
the third was genuine and appeared in the PDF too.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from AppKit import NSSpellChecker
    HAVE_APPKIT = True
except ImportError:
    HAVE_APPKIT = False

# Terms that are correct in print and design work but absent from a general
# dictionary. Extend per project with --words rather than editing this.
BUILTIN_WORDS = {
    "artwork", "artworker", "artworking", "bleed", "bleeds", "cmyk", "rgb", "pantone",
    "preflight", "prepress", "litho", "lithographic", "flexo", "flexographic", "gsm",
    "ppi", "dpi", "lpi", "spot", "duotone", "greyscale", "overprint", "knockout",
    "trapping", "imposition", "saddle", "perfect-bound", "wiro", "deboss", "debossed",
    "emboss", "embossed", "varnish", "laminate", "dieline", "die-line", "crease",
    "kerning", "leading", "tracking", "widow", "orphan", "rag", "recto", "verso",
    "folio", "folios", "colourway", "colourways", "mockup", "wordmark", "lockup",
    "fogra", "gracol", "swop", "icc", "pdf", "indesign", "illustrator", "photoshop",
    "eps", "tiff", "svg", "idml", "otf", "ttf", "opentype",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

# Patterns a spellchecker cannot see. Deliberately narrow: a grammar rule that
# fires on correct text is worse than no rule, because it trains people to skim.
GRAMMAR_RULES = [
    (r"\b(technolog(?:y|ies)|equipment|software|machinery|data)\s+that\s+meet\b",
     "subject/verb", "Singular subject with a plural verb — 'that meets'."),
    (r"\b(\w+)[ \t]+\1\b", "doubled word", "The same word twice in a row."),
    (r"\ba\s+([aeiouAEIOU]\w+)", "a/an", "'a' before a vowel sound — usually 'an'."),
    (r"\ban\s+([bcdfgjklmnpqrstvwxyzBCDFGJKLMNPQRSTVWXYZ]\w+)", "a/an",
     "'an' before a consonant sound — usually 'a'."),
    (r"\b(is|are|was|were)\s+consist\b", "verb form", "'consists of', not 'is consist'."),
    (r"\bcomprised of\b", "usage", "'comprises' or 'composed of'; 'comprised of' is disputed."),
    (r"\b(less)\s+(items|products|units|people|parts|components)\b", "usage",
     "'fewer' for countable nouns."),
    (r"\bamount of\s+(items|products|units|people|parts|components)\b", "usage",
     "'number of' for countable nouns."),
    (r"\bit's\b(?=\s+(own|design|performance|range|efficiency))", "its/it's",
     "Possessive takes 'its', with no apostrophe."),
    (r"\bthe[ \t]+the\b", "doubled word", "Repeated article."),
]


class Checker:
    def __init__(self, locale: str = "en_GB", extra_words: set[str] | None = None):
        if not HAVE_APPKIT:
            raise RuntimeError(
                "PyObjC not available. Install with: pip install pyobjc-framework-Cocoa\n"
                "Spelling is unchecked without it — report that, do not skip it silently.")
        self.checker = NSSpellChecker.sharedSpellChecker()
        available = list(self.checker.availableLanguages())
        if locale not in available:
            raise RuntimeError(f"locale {locale} not available. Have: {', '.join(available)}")
        self.locale = locale
        self.allow = {w.lower() for w in BUILTIN_WORDS} | {w.lower() for w in (extra_words or set())}

    def misspelled(self, text: str) -> list[tuple[str, int]]:
        """Return (word, offset) for each word the dictionary rejects."""
        out, i, guard = [], 0, 0
        n = len(text)
        while i < n and guard < 20000:
            guard += 1
            rng, _ = self.checker.\
                checkSpellingOfString_startingAt_language_wrap_inSpellDocumentWithTag_wordCount_(
                    text, i, self.locale, False, 0, None)
            if rng.length == 0 or rng.location >= n:
                break
            word = text[rng.location:rng.location + rng.length]
            out.append((word, rng.location))
            i = rng.location + rng.length
        return out

    def ignorable(self, word: str) -> bool:
        w = word.strip("'’-").lower()
        if len(w) < 2:
            return True
        if w in self.allow:
            return True
        if word.isupper():                       # acronyms and set-in-caps display type
            return True
        if any(c.isdigit() for c in word):       # NT2-26, PC10n-0076
            return True
        if "@" in word or "." in w or w.startswith(("www", "http")):
            return True                          # emails and URLs; checked separately
        return False


def check_pages(pages: list[dict], locale="en_GB", extra_words=None) -> dict:
    c = Checker(locale, extra_words)
    spelling: dict[str, dict] = defaultdict(lambda: {"count": 0, "folios": set(), "samples": []})
    grammar: list[dict] = []

    for pg in pages:
        folio = str(pg.get("folio") or pg.get("index") or "?")
        text = pg.get("text") or ""
        if not text.strip():
            continue

        for word, off in c.misspelled(text):
            if c.ignorable(word):
                continue
            e = spelling[word]
            e["count"] += 1
            e["folios"].add(folio)
            if len(e["samples"]) < 2:
                s = max(0, off - 40)
                e["samples"].append(text[s:off + len(word) + 40].replace("\n", " ").strip())

        for pattern, kind, why in GRAMMAR_RULES:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                s = max(0, m.start() - 45)
                grammar.append({"folio": folio, "kind": kind, "match": m.group(0).strip(),
                                "why": why,
                                "context": text[s:m.end() + 45].replace("\n", " ").strip()})

    words = []
    for w, e in sorted(spelling.items(), key=lambda kv: -kv[1]["count"]):
        words.append({"word": w, "count": e["count"],
                      "folios": sorted(e["folios"]), "samples": e["samples"],
                      "suggestions": suggest(c, w)})
    return {"locale": locale, "spelling": words, "grammar": grammar,
            "wordsChecked": sum(len(WORD_RE.findall(p.get("text") or "")) for p in pages)}


def suggest(c: Checker, word: str) -> list[str]:
    try:
        g = c.checker.guessesForWordRange_inString_language_inSpellDocumentWithTag_(
            (0, len(word)), word, c.locale, 0)
        return [str(x) for x in (g or [])][:3]
    except Exception:
        return []


def load_words(path: str | None) -> set[str]:
    if not path:
        return set()
    p = Path(path).expanduser()
    if not p.exists():
        return set()
    return {ln.strip() for ln in p.read_text().splitlines()
            if ln.strip() and not ln.startswith("#")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Spelling, locale and grammar for print copy.")
    ap.add_argument("command", choices=["check", "languages"])
    ap.add_argument("pages", nargs="?", help="JSON: [{folio, text}, ...]")
    ap.add_argument("--locale", default="en_GB")
    ap.add_argument("--words", help="newline-separated approved terms")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    if args.command == "languages":
        if not HAVE_APPKIT:
            print("PyObjC not installed: pip install pyobjc-framework-Cocoa", file=sys.stderr)
            return 1
        print(" ".join(NSSpellChecker.sharedSpellChecker().availableLanguages()))
        return 0

    if not args.pages:
        ap.error("check needs a pages JSON file")
    data = json.loads(Path(args.pages).read_text())
    pages = data["textByPage"] if isinstance(data, dict) and "textByPage" in data else data

    res = check_pages(pages, args.locale, load_words(args.words))
    text = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)

    print(f"{len(res['spelling'])} unique unrecognised words, "
          f"{len(res['grammar'])} grammar flags, "
          f"{res['wordsChecked']} words checked ({args.locale})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
