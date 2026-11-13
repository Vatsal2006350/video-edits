#!/usr/bin/env python3
"""Measure how a motion film moves, and compare it with a reference that has the taste you want.

    python3 bin/motion-stats.py out.mp4
    python3 bin/motion-stats.py out.mp4 --ref ~/Downloads/original.mp4

Per frame it measures the mean absolute change from the previous frame (greyscale, 160 px wide,
0-255). From that:
  hard jumps / s  frames whose change is far above their neighbours (a cut, a pop, a snap).
                  Motion design built from transforms should be near 0.
  still share     share of frames that barely change (< 0.4). Long holds read as dead air;
                  the drafting-inks rule is no hold over half a second.
  longest hold    the longest run of still frames, in seconds.
  mean motion     the average change per frame: the energy of the film.
  motion CV       how even the energy is (std / mean). Very low = monotonous, very high = jerky.
A reference row is printed under the film so the numbers are read side by side, with a verdict.
"""
import subprocess
import sys

import numpy as np

W = 160


def frames(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    w, h, r = p.stdout.strip().split(",")[:3]; num, den = r.split("/"); fps = float(num) / float(den)
    H = int(round(W * int(h) / int(w) / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vf", f"fps=30,scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32), 30.0


def stats(path):
    f, fps = frames(path)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    med = np.median(d) + 1e-3
    local = np.array([np.median(d[max(0, i - 6):i + 7]) for i in range(len(d))]) + 0.15
    jumps = int(np.sum((d > 6 * local) & (d > 4.0)))
    still = d < 0.4
    run = best = 0
    for s in still:
        run = run + 1 if s else 0; best = max(best, run)
    return {
        "file": path.split("/")[-1], "seconds": round(len(f) / fps, 2),
        "hard_jumps_per_s": round(jumps / (len(f) / fps), 3), "still_share": round(float(still.mean()), 3),
        "longest_hold_s": round(best / fps, 2), "mean_motion": round(float(d.mean()), 2),
        "motion_cv": round(float(d.std() / (d.mean() + 1e-6)), 2), "median_motion": round(float(med), 2),
    }


def row(s):
    return f"{s['file'][:34]:34s} {s['seconds']:6.1f}s  jumps/s {s['hard_jumps_per_s']:5.2f}  still {s['still_share']:5.1%}  hold {s['longest_hold_s']:4.1f}s  mean {s['mean_motion']:5.2f}  cv {s['motion_cv']:4.2f}"


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    film = stats(sys.argv[1]); print(row(film))
    if "--ref" in sys.argv:
        ref = stats(sys.argv[sys.argv.index("--ref") + 1]); print(row(ref))
        notes = []
        if film["hard_jumps_per_s"] > max(0.1, ref["hard_jumps_per_s"] * 2): notes.append("more snaps/pops than the reference: look for cuts, tl.call, layout snapping")
        if film["longest_hold_s"] > max(0.6, ref["longest_hold_s"] * 1.5): notes.append(f"a hold of {film['longest_hold_s']}s: something should happen on every beat")
        if film["mean_motion"] < ref["mean_motion"] * 0.5: notes.append("much calmer than the reference: more happens per beat in the reference")
        if film["mean_motion"] > ref["mean_motion"] * 2: notes.append("much busier than the reference: give moves room to land")
        print("verdict: " + ("moves like the reference" if not notes else "; ".join(notes)))


if __name__ == "__main__":
    main()
