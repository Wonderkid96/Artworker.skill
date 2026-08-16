#!/usr/bin/env python3
"""Safe InDesign access.

InDesign writes to a document the moment it opens it — link records, version
migration, a `.idlk` lock file beside it. So "just reading" a file is not
read-only, and pointing this at someone's master document is not safe.

Every session therefore works on a **filesystem copy**, and the original is
hash-verified afterwards. If the original changed by a single byte the run
aborts and says so. The guarantee is an assertion, not a promise.

    from indesign import InDesignSession

    with InDesignSession("~/Work/brochure.indd") as s:
        data = s.run_jsx("audit.jsx")        # runs against the copy
        s.keep()                             # opt in to keeping the copy

Without `keep()` the copy is deleted on exit, so an audit leaves nothing behind.

CLI:
    python3 indesign.py --check                  # is InDesign available
    python3 indesign.py audit <file.indd>        # run the audit, print JSON
"""

from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

JSX_DIR = Path(__file__).parent / "jsx"

# Newest first. InDesign's AppleScript name includes the year.
KNOWN_APPS = [f"Adobe InDesign {y}" for y in range(2030, 2018, -1)] + ["Adobe InDesign"]


# Restored by atexit and by SIGINT/SIGTERM. Without this, a killed process
# leaves someone's master document chmod'd read-only, which is alarming and
# looks exactly like corruption.
_PENDING_RESTORE: dict = {}


def _emergency_restore(*_args):
    for path, mode in list(_PENDING_RESTORE.items()):
        try:
            os.chmod(path, mode)
        except OSError:
            pass
        _PENDING_RESTORE.pop(path, None)


atexit.register(_emergency_restore)
for _sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    try:
        signal.signal(_sig, lambda s, f: (_emergency_restore(), sys.exit(130)))
    except (ValueError, OSError):
        pass


class InDesignError(RuntimeError):
    pass


class OriginalModified(InDesignError):
    """The original file changed during a run. Always a bug in this tool."""


# --- discovery -------------------------------------------------------------


def find_indesign() -> str:
    """Return the AppleScript application name for the installed InDesign."""
    for base in ("/Applications", str(Path.home() / "Applications")):
        p = Path(base)
        if not p.is_dir():
            continue
        for entry in sorted(p.iterdir(), reverse=True):
            m = re.fullmatch(r"Adobe InDesign(?: (\d{4}))?", entry.name)
            if m and entry.is_dir():
                return entry.name
    for name in KNOWN_APPS:
        if Path(f"/Applications/{name}").exists():
            return name
    raise InDesignError(
        "Adobe InDesign not found in /Applications. "
        "This skill can still audit PDFs; only InDesign source checks need the app."
    )


def is_running(app_name: str) -> bool:
    out = subprocess.run(["pgrep", "-f", app_name], capture_output=True, text=True)
    return out.returncode == 0


# --- integrity -------------------------------------------------------------


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- session ---------------------------------------------------------------


class InDesignSession:
    """Opens a copy of a document. Never the original."""

    def __init__(self, doc: str | Path, app_name: str | None = None, timeout: int = 900):
        self.original = Path(doc).expanduser().resolve()
        self.app = app_name or find_indesign()
        self.timeout = timeout
        self.copy: Path | None = None
        self.warnings: list[str] = []
        self._keep = False
        self._ran_script = False
        self._orig_mode: int | None = None
        self._hash_before: str | None = None

    # -- guards --

    def _preflight(self) -> None:
        if not self.original.exists():
            raise InDesignError(f"no such file: {self.original}")
        if self.original.suffix.lower() not in (".indd", ".indt"):
            raise InDesignError(f"not an InDesign document: {self.original.name}")

        size = self.original.stat().st_size
        free = shutil.disk_usage(self.original.parent).free
        if free < size * 2.5:
            raise InDesignError(
                f"not enough free space to copy safely: need ~{size * 2.5 / 1e9:.1f}GB, "
                f"have {free / 1e9:.1f}GB on {self.original.parent}")

        # The copy has to sit beside the original so relative links resolve —
        # but in a synced folder it will upload before it is deleted, churning
        # version history and confusing anyone else in the folder.
        parts = {p.lower() for p in self.original.parts}
        synced = parts & {"dropbox", "egnyte", "onedrive", "google drive",
                          "googledrive", "box sync", "icloud drive", "cloudstorage"}
        if synced:
            self.warnings.append(
                f"{self.original.parent} looks like a synced folder ({', '.join(sorted(synced))}). "
                "A temporary copy will appear there and then be deleted, which may sync to "
                "colleagues and add version history. Consider copying the file somewhere local first.")

        lock = self.original.with_suffix(".idlk")
        if lock.exists():
            raise InDesignError(
                f"{self.original.name} is locked ({lock.name} present). "
                "It is open somewhere — close it before running."
            )
        if is_running(self.app) and self._open_in_app(self.original):
            raise InDesignError(
                f"{self.original.name} is currently open in InDesign. "
                "Close it first; this tool will not run alongside an open copy."
            )

    def _open_in_app(self, path: Path) -> bool:
        """True if InDesign already has this exact document open."""
        js = "var r=[]; for (var i=0;i<app.documents.length;i++){ " \
             "try { r.push(app.documents[i].fullName.fsName); } catch(e){} } r.join('\\n');"
        try:
            out = self._osascript(js, timeout=60)
        except InDesignError:
            return False
        return str(path) in out.splitlines()

    # -- lifecycle --

    def __enter__(self) -> "InDesignSession":
        self._preflight()
        self._hash_before = sha256(self.original)

        # Copy beside the original so relative links and a sibling
        # "Document Fonts" folder still resolve. A temp directory would
        # arrive with every link broken.
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.copy = self.original.with_name(f"{self.original.stem}_ARTWORKED_{ts}{self.original.suffix}")
        shutil.copy2(self.original, self.copy)

        # Belt and braces: even a bug in the JSX cannot write to the original.
        self._orig_mode = stat.S_IMODE(self.original.stat().st_mode)
        _PENDING_RESTORE[str(self.original)] = self._orig_mode
        os.chmod(self.original, self._orig_mode & ~0o222)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._ran_script:
            self._restore_interaction()

        if self._orig_mode is not None:
            _PENDING_RESTORE.pop(str(self.original), None)
            try:
                os.chmod(self.original, self._orig_mode)
            except OSError:
                pass

        if self.copy and self.copy.exists() and not self._keep:
            self.copy.unlink()

        after = sha256(self.original)
        if after != self._hash_before:
            raise OriginalModified(
                f"ORIGINAL WAS MODIFIED: {self.original}\n"
                f"  before {self._hash_before}\n  after  {after}\n"
                "This is a bug in the tool. Restore from backup and report it."
            )
        return False

    def keep(self) -> Path:
        """Retain the working copy after the session (used by fix mode)."""
        self._keep = True
        return self.copy

    # -- execution --

    def _restore_interaction(self) -> None:
        """Put the app's dialog setting back. NEVER_INTERACT is global and
        sticky — leaving it set would silently suppress prompts in whatever
        else the user has open."""
        try:
            self._osascript(
                "app.scriptPreferences.userInteractionLevel = "
                "UserInteractionLevels.INTERACT_WITH_ALL; 'ok';", timeout=60)
        except Exception:
            pass

    def _osascript(self, js: str, timeout: int | None = None) -> str:
        escaped = js.replace("\\", "\\\\").replace('"', '\\"')
        cmd = ["osascript", "-e", f'tell application "{self.app}" to do script "{escaped}" language javascript']
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout or self.timeout)
        if proc.returncode != 0:
            raise InDesignError(f"InDesign script failed:\n{proc.stderr.strip()}")
        return proc.stdout.strip()

    def run_jsx(self, script: str | Path, params: dict | None = None) -> dict:
        """Run a .jsx against the COPY and return whatever JSON it wrote."""
        if self.copy is None:
            raise InDesignError("session not started — use `with InDesignSession(...)`")

        path = Path(script)
        if not path.is_absolute():
            path = JSX_DIR / path
        if not path.exists():
            raise InDesignError(f"no such script: {path}")

        out_file = self.copy.with_suffix(f".{path.stem}.json")
        body = path.read_text()
        body = (body
                .replace("__DOC_PATH__", str(self.copy))
                .replace("__OUT_PATH__", str(out_file))
                .replace("__PARAMS__", json.dumps(params or {})))

        tmp = out_file.with_suffix(".jsx")
        tmp.write_text(body)
        try:
            # Bootstrap: read the file and eval it. Passing a long script
            # inline through osascript is a quoting minefield.
            boot = (f'var f=File("{tmp}"); f.open("r"); f.encoding="UTF-8"; '
                    f'var s=f.read(); f.close(); eval(s);')
            self._ran_script = True
            self._osascript(boot)
            if not out_file.exists():
                raise InDesignError(f"{path.name} produced no output")
            return json.loads(out_file.read_text())
        finally:
            tmp.unlink(missing_ok=True)
            out_file.unlink(missing_ok=True)


# --- CLI -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe InDesign access.")
    ap.add_argument("command", nargs="?", choices=["audit", "package"], help="what to run")
    ap.add_argument("document", nargs="?", help="path to .indd")
    ap.add_argument("--check", action="store_true", help="report whether InDesign is available")
    ap.add_argument("-o", "--out", help="write JSON here instead of stdout")
    ap.add_argument("--to", help="package: destination folder (default: alongside the document)")
    ap.add_argument("--pdf", action="store_true", help="package: include a print PDF")
    ap.add_argument("--hidden-layers", action="store_true", help="package: include hidden layers")
    args = ap.parse_args()

    if args.check:
        try:
            app = find_indesign()
        except InDesignError as e:
            print(f"unavailable: {e}", file=sys.stderr)
            return 1
        print(f"{app}   running={is_running(app)}")
        return 0

    if not args.command or not args.document:
        ap.print_help()
        return 2

    t0 = time.time()
    with InDesignSession(args.document) as s:
        for w in s.warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        print(f"working on a copy: {s.copy.name}", file=sys.stderr)
        if args.command == "audit":
            data = s.run_jsx("audit.jsx")
        else:
            dest = Path(args.to).expanduser().resolve() if args.to else \
                s.original.parent / f"{s.original.stem}_PACKAGE"
            data = s.run_jsx("package.jsx", {
                "outFolder": str(dest),
                "includeIdml": True,
                "includePdf": args.pdf,
                "hiddenLayers": args.hidden_layers,
            })
            # The packaged .indd carries the working copy's name. Put it back.
            if data.get("ok"):
                # .indd, .indt and .idml all carry the copy's name
                for f in dest.glob(f"{s.copy.stem}.*"):
                    f.rename(f.with_name(f"{s.original.stem}{f.suffix}"))
            for w in data.get("warnings", []):
                print(f"WARNING: {w}", file=sys.stderr)

    data["_meta"] = {"seconds": round(time.time() - t0, 1), "source": str(Path(args.document).resolve())}
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    print("original verified unchanged", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
