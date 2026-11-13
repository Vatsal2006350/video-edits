#!/usr/bin/env python3
"""Refuse media whose basename or SHA-256 appears in FOOTAGE-DENYLIST.md."""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENYLIST = ROOT / "FOOTAGE-DENYLIST.md"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} MEDIA", file=sys.stderr)
        return 2
    media = Path(sys.argv[1]).expanduser().resolve()
    if not media.is_file():
        print(f"denylist check: no such file: {media}", file=sys.stderr)
        return 2
    if not DENYLIST.exists():
        return 0  # no local denylist: nothing is refused
    rows = DENYLIST.read_text(encoding="utf-8")
    cells = [cell.strip().strip("`") for row in rows.splitlines() if row.startswith("|") for cell in row.split("|")[1:-1]]
    forbidden_names = {cell for cell in cells if re.search(r"[A-Za-z0-9_-]+\.(?:mp4|mov|m4v|jpg|jpeg|heic|png|webp)(?:\.heic)?$", cell, re.I)}
    forbidden_ids = {cell for cell in cells if re.fullmatch(r"[0-9a-f-]{36}", cell, re.I)}
    forbidden_hashes = {cell.lower() for cell in cells if re.fullmatch(r"[0-9a-f]{64}", cell, re.I)}
    base = media.name.lower()
    if any(name.lower() == base for name in forbidden_names) or any(uid.lower() in base for uid in forbidden_ids):
        print(f"DENYLIST BLOCK: {media.name} matches a forbidden filename or UUID", file=sys.stderr)
        return 1
    digest = hashlib.sha256()
    with media.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() in forbidden_hashes:
        print(f"DENYLIST BLOCK: {media.name} SHA-256 is forbidden", file=sys.stderr)
        return 1
    print(f"denylist clear: {media.name} ({digest.hexdigest()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
