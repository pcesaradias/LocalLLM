#!/usr/bin/env python3
"""Guard against drift in vendored shared modules.

Services vendor byte-identical copies of the shared modules in common/
(each Docker build context only sees its own service directory). common/
is the source of truth: every file elsewhere in the repo whose name matches
a common/*.py module must be byte-identical to it.

Usage:
  python scripts/check_vendored_common.py         # report drift, exit 1 if any
  python scripts/check_vendored_common.py --fix   # overwrite copies from common/
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"__init__.py"}


def vendored_copies(name: str):
    copies = [p for p in ROOT.glob(f"*/{name}") if p.parent.name != "common"]
    root_copy = ROOT / name
    if root_copy.is_file():
        copies.append(root_copy)
    return copies


def main() -> int:
    fix = "--fix" in sys.argv
    masters = sorted(p for p in (ROOT / "common").glob("*.py") if p.name not in SKIP)
    drifted = []

    for master in masters:
        for copy in vendored_copies(master.name):
            if not filecmp.cmp(master, copy, shallow=False):
                drifted.append(copy)
                if fix:
                    shutil.copyfile(master, copy)

    if drifted:
        if fix:
            for copy in drifted:
                print(f"synced {copy.relative_to(ROOT)} from common/")
            return 0
        print("Vendored shared-module drift detected (common/ is the source of truth):")
        for copy in drifted:
            print(f"  {copy.relative_to(ROOT)} != common/{copy.name}")
        print("Fix: edit common/<file> first, then run: python scripts/check_vendored_common.py --fix")
        return 1

    total = sum(len(vendored_copies(m.name)) for m in masters)
    print(f"OK: {len(masters)} shared modules, {total} vendored copies all match common/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
