#!/usr/bin/env python3
"""Per-frame head position from an alpha matte, for orbit / behind-head art.

Reads the alpha channel of a matte produced by `hyperframes remove-background`
(VP9/alpha WebM or ProRes 4444 MOV) and writes a JSON track of the speaker's
head: top edge, centre x and width, in full-frame pixels.

    bin/face-track.py <matte.webm|mov> <out.json> [--w 1080] [--h 1920]
                      [--offset 0] [--fps 30]

Output: {"fps":30,"w":1080,"h":1920,"offset":0.0,
         "frames":[{"t":0.0,"top":412,"cx":548,"width":296}, ...]}

`top` is the highest alpha row (hair line). `width`/`cx` are measured on the row
25% of the way down the head, which is the widest part of the skull and is not
contaminated by shoulders. Frames with no subject repeat the last good sample.
Why this and not a face detector: the matte already exists in the render chain,
so this adds no model, no download and no new dependency.
"""
import argparse, json, subprocess, sys
import numpy as np

SCALE_W, SCALE_H = 270, 480  # decode small; the metrics are scaled back up


def alpha_frames(path, w, h):
    cmd = ["ffmpeg", "-v", "error"]
    if path.endswith(".webm"):
        cmd += ["-c:v", "libvpx-vp9"]   # or ffmpeg silently drops the alpha
    cmd += ["-i", path, "-vf", f"alphaextract,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (w * h)
    if not n:
        sys.exit(f"no alpha frames decoded from {path}")
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("matte")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--offset", type=float, default=0.0, help="source time of this matte's first frame")
    ap.add_argument("--fps", type=float, default=30.0)
    a = ap.parse_args()

    frames = alpha_frames(a.matte, SCALE_W, SCALE_H)
    sx, sy = a.w / SCALE_W, a.h / SCALE_H
    out, last = [], None
    for i, f in enumerate(frames):
        m = f > 128
        rows = np.where(m.any(1))[0]
        if len(rows):
            top = int(rows[0])
            probe = min(SCALE_H - 1, top + max(2, int((SCALE_H - top) * 0.06)))
            cols = np.where(m[probe])[0]
            if len(cols) >= 2:
                last = dict(top=round(top * sy), cx=round((cols[0] + cols[-1]) / 2 * sx),
                            width=round((cols[-1] - cols[0] + 1) * sx))
        if last is None:
            last = dict(top=round(a.h * 0.22), cx=a.w // 2, width=round(a.w * 0.3))
        out.append(dict(t=round(a.offset + i / a.fps, 4), **last))

    tops = [f["top"] for f in out]
    widths = [f["width"] for f in out]
    json.dump(dict(fps=a.fps, w=a.w, h=a.h, offset=a.offset, frames=out), open(a.out, "w"))
    print(f"{len(out)} frames -> {a.out}  top {min(tops)}..{max(tops)}  width {min(widths)}..{max(widths)}")


if __name__ == "__main__":
    main()
