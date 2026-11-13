#!/usr/bin/env python3
"""Check a music-led HyperFrames reel against its analyzed source track.

Use the audiomap from .agents/skills/music-to-video/scripts/analyze-beatgrid.py.
This is a pre-render warning gate, not a substitute for watching the final MP4.
"""

from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path


class Clips(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"video", "img", "audio"}:
            self.items.append({"tag": tag, **{k: v or "" for k, v in attrs}})


def weighted_energy(phases: list[dict], begin: float, end: float) -> float:
    total = weight = 0.0
    for phase in phases:
        overlap = max(0.0, min(end, float(phase["end"])) - max(begin, float(phase["start"])))
        total += overlap * float(phase["energy"])
        weight += overlap
    return total / weight if weight else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("composition", type=Path)
    ap.add_argument("audiomap", type=Path)
    ap.add_argument("--mode", choices=["beat", "phrase"], default="beat")
    ap.add_argument("--tolerance", type=float, default=0.12)
    ap.add_argument("--allow-quiet-open", action="store_true")
    args = ap.parse_args()

    parser = Clips()
    parser.feed(args.composition.read_text())
    track = next((x for x in parser.items if x["tag"] == "audio" and x.get("id") == "music"), None)
    scenes = sorted(
        (x for x in parser.items if x["tag"] in {"video", "img"} and x.get("data-track-index") == "0"),
        key=lambda x: float(x.get("data-start", 0)),
    )
    if not track or not scenes:
        print("FAIL: expected #music and track-0 visual scenes")
        return 1

    amap = json.loads(args.audiomap.read_text())
    music_start = float(track.get("data-media-start", 0))
    music_duration = float(track["data-duration"])
    anchors = (
        amap["grid"]["beats_sec"] if args.mode == "beat"
        else [p["start"] for p in amap["phrases"]]
    )
    problems: list[str] = []
    phases = amap["energy_phases"]
    opening = weighted_energy(phases, music_start, music_start + min(1.5, music_duration))
    body = weighted_energy(phases, music_start, music_start + music_duration)
    if not args.allow_quiet_open and body > 0 and opening < 0.35 * body:
        problems.append(f"quiet opening: energy {opening:.2f} vs body {body:.2f}; choose a later music in-point")

    previous_end = 0.0
    for index, scene in enumerate(scenes):
        start = float(scene.get("data-start", 0))
        duration = float(scene.get("data-duration", 0))
        if abs(start - previous_end) > 0.035:
            problems.append(f"visual gap/overlap before {scene.get('id', index)}: {start - previous_end:+.3f}s")
        if index:
            source_time = music_start + start
            lyric_anchor = scene.get("data-audio-anchor")
            if lyric_anchor:
                delta = source_time - float(lyric_anchor)
                if abs(delta) > args.tolerance:
                    problems.append(f"off-lyric cut {scene.get('id', index)} at music {source_time:.3f}s: target {float(lyric_anchor):.3f}s ({delta:+.3f}s)")
                previous_end = start + duration
                continue
            nearest = min(anchors, key=lambda t: abs(t - source_time))
            delta = source_time - nearest
            if abs(delta) > args.tolerance:
                problems.append(f"off-{args.mode} cut {scene.get('id', index)} at reel {start:.3f}s / music {source_time:.3f}s: nearest {nearest:.3f}s ({delta:+.3f}s)")
        previous_end = start + duration
    if abs(previous_end - music_duration) > 0.035:
        problems.append(f"last scene ends at {previous_end:.3f}s, music at {music_duration:.3f}s")

    print(f"Music source {music_start:.3f}–{music_start + music_duration:.3f}s; opening energy {opening:.2f}, body {body:.2f}; {len(scenes)} scenes")
    if problems:
        for issue in problems:
            print("FAIL:", issue)
        return 1
    print(f"PASS: all {len(scenes) - 1} visual cuts within {args.tolerance:.3f}s of {args.mode} or explicit lyric anchors; no quiet opening")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
