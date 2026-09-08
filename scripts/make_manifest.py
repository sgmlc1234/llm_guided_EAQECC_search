#!/usr/bin/env python3
"""Write MANIFEST.sha256: one line per archived input, `<sha256>  <path>`.

The auditor's archive-integrity claim checks the archive against this file,
so regenerate it whenever the archive legitimately changes (a new snapshot,
a new certificate) and commit both together.

    python3 scripts/make_manifest.py            # write
    python3 scripts/make_manifest.py --check    # exit 1 on any difference
"""

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MANIFEST.sha256"
EXCLUDE_DIRS = {ROOT / "artifacts" / "reproduce_eaqecc"}


def entries():
    for f in sorted((ROOT / "artifacts").rglob("*")):
        if not f.is_file() or f.name == ".DS_Store":
            continue
        if any(d in f.parents for d in EXCLUDE_DIRS):
            continue
        yield hashlib.sha256(f.read_bytes()).hexdigest(), f.relative_to(ROOT).as_posix()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = "".join(f"{h}  {p}\n" for h, p in entries())
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit("MANIFEST.sha256 is stale; run scripts/make_manifest.py")
        print("manifest up to date")
        return
    OUT.write_text(text)
    print(f"{text.count(chr(10))} files -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
