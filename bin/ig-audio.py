#!/usr/bin/env python3
"""Extract local MP3 reference tracks from public Instagram Reel URLs.

Downloaded audio is for local analysis/editing. Keep provenance and attach licensed trend
audio natively in Instagram when publishing. This tool does not bypass private accounts,
login gates, or access controls.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def reel_url(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in {
        "instagram.com",
        "www.instagram.com",
    }:
        raise argparse.ArgumentTypeError(f"not an Instagram URL: {value}")
    if not (parsed.path.startswith("/reel/") or parsed.path.startswith("/reels/")):
        raise argparse.ArgumentTypeError(f"expected a public Reel URL: {value}")
    return value


def load_rows(paths: list[Path], urls: list[str]) -> list[tuple[str, str]]:
    rows = [("", reel_url(url)) for url in urls]
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                url = (row.get("url") or "").strip()
                if url:
                    rows.append(((row.get("name") or "").strip(), reel_url(url)))
    seen: set[str] = set()
    return [(name, url) for name, url in rows if not (url in seen or seen.add(url))]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="public Instagram Reel URLs")
    parser.add_argument("--input", action="append", type=Path, default=[], help="CSV with name,url")
    parser.add_argument("--output", type=Path, default=Path.home() / "Downloads" / "ig-audio")
    parser.add_argument("--limit", type=int, help="process only the first N unique URLs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.input, args.urls)
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        parser.error("provide a Reel URL or --input CSV")
    if not shutil.which("uvx"):
        parser.error("uvx is required (the repository uses `uvx yt-dlp`)")

    args.output.mkdir(parents=True, exist_ok=True)
    ledger_path = args.output / "ledger.jsonl"
    failures = 0
    for index, (name, url) in enumerate(rows, 1):
        print(f"[{index}/{len(rows)}] {name or url}")
        if args.dry_run:
            continue
        before = set(args.output.glob("*.mp3"))
        command = [
            "uvx",
            "yt-dlp",
            "--no-playlist",
            "--no-overwrites",
            "--write-info-json",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "--output",
            str(args.output / "%(id)s.%(ext)s"),
            url,
        ]
        result = subprocess.run(command, text=True)
        if result.returncode:
            failures += 1
            print(f"  failed: yt-dlp exited {result.returncode}", file=sys.stderr)
            continue
        created = sorted(set(args.output.glob("*.mp3")) - before, key=lambda p: p.stat().st_mtime)
        if not created:
            reel_id = urlparse(url).path.rstrip("/").split("/")[-1]
            created = [args.output / f"{reel_id}.mp3"] if (args.output / f"{reel_id}.mp3").exists() else []
        if not created:
            failures += 1
            print("  failed: downloader reported success but no MP3 was found", file=sys.stderr)
            continue
        audio = created[-1]
        info_path = audio.with_suffix(".info.json")
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
        record = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "label": name,
            "source_url": url,
            "reel_id": info.get("id") or audio.stem,
            "uploader": info.get("uploader") or info.get("uploader_id"),
            "title": info.get("title"),
            "duration_seconds": info.get("duration"),
            "file": str(audio),
            "sha256": sha256(audio),
        }
        with ledger_path.open("a", encoding="utf-8") as ledger:
            ledger.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"  -> {audio}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
