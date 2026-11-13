#!/usr/bin/env python3
"""Fail an edit review when its visual claims lack frame-verified footage.

The manifest is intentionally human-verified, not an emotion-recognition model.
Run before rendering a project: python3 bin/shot-guard.py path/to/shot-manifest.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def duration(path: Path) -> float | None:
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".heic"}:
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"ffprobe could not read {path}: {result.stderr.strip()}")
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    root = args.manifest.resolve().parent
    data = json.loads(args.manifest.read_text())
    shots = data.get("shots", [])
    errors: list[str] = []
    ids: set[str] = set()
    tags: set[str] = set()

    for shot in shots:
        sid = shot.get("id", "<missing id>")
        if sid in ids:
            errors.append(f"duplicate shot id: {sid}")
        ids.add(sid)
        for required in ("asset", "subject", "visible_action", "emotion", "review_frame"):
            if not shot.get(required):
                errors.append(f"{sid}: missing {required}")
        asset = root / shot.get("asset", "")
        review = root / shot.get("review_frame", "")
        if not asset.is_file():
            errors.append(f"{sid}: missing asset {asset}")
            continue
        if not review.is_file():
            errors.append(f"{sid}: missing trim-review frame {review}")
        if not shot.get("human_verified", False):
            errors.append(f"{sid}: not marked human_verified")
        if shot.get("excluded", False):
            errors.append(f"{sid}: marked excluded")
        start = float(shot.get("source_in", 0))
        end = float(shot.get("source_out", 0))
        if end <= start:
            errors.append(f"{sid}: source_out must exceed source_in")
        elif asset.is_file():
            media_duration = duration(asset)
            if media_duration is not None and end > media_duration + 0.05:
                errors.append(f"{sid}: source_out {end:.2f}s exceeds asset duration {media_duration:.2f}s")
        tags.update(shot.get("action_tags", []))

    for claim in data.get("required_visual_claims", []):
        if claim not in tags:
            errors.append(f"No frame-verified shot supports required visual claim: {claim}")

    if errors:
        print("SHOT GUARD FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Shot guard passed: {len(shots)} reviewed shots, {len(tags)} action tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
