#!/usr/bin/env python3
"""Frame-exact compositor for layer PNGs + alpha mattes over a base clip.

    bin/composite-layers.py --base picture.mp4 --out master.mp4 --audio mix.m4a \
        --frames 1604 \
        --op layer:work/behind \
        --op matte:work/hook_fg.webm:0 \
        --op matte:work/gal_fg.webm:16.9 \
        --op layer:work/front

Ops are applied in the order given, over the base, per frame index.

Why this exists instead of a chain of ffmpeg `overlay` filters: with several
image2 sequences and `-itsoffset` alpha WebMs feeding one graph, overlay's
frame-sync pairs inputs by timestamp and can silently drop or duplicate a
single frame. That produced a one-frame hole in reel 08 at exactly 19.70s --
the layer PNGs were perfect, the composite was not. Here every stream is
indexed by frame NUMBER, so a frame cannot slip: layer PNG i is composited
onto base frame i, always. The repo's CLAUDE.md already called for PIL
compositing whenever a matte is involved; this is that, vectorised.

Alpha WebM needs the explicit libvpx-vp9 decoder or ffmpeg drops the alpha.
"""
import argparse, subprocess, sys
import numpy as np
from pathlib import Path

W, H = 1080, 1920


def base_reader(path, fps, n):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path),
           "-vf", f"scale={W}:{H}:flags=lanczos,setsar=1,fps={fps}",
           "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)


def matte_reader(path, fps):
    cmd = ["ffmpeg", "-v", "error"]
    if str(path).endswith(".webm"):
        cmd += ["-c:v", "libvpx-vp9"]
    cmd += ["-i", str(path), "-vf", f"scale={W}:{H},fps={fps}",
            "-f", "rawvideo", "-pix_fmt", "rgba", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 4 * 4)


def over(dst, src_rgb, a):
    """dst (float32 HxWx3, 0..255) <- src over dst, with alpha a (HxWx1 0..1)."""
    np.multiply(dst, 1.0 - a, out=dst)
    np.add(dst, src_rgb * a, out=dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--crf", default="15")
    ap.add_argument("--op", action="append", default=[],
                    help="layer:DIR | matte:FILE:START_SECONDS")
    a = ap.parse_args()

    ops = []
    for spec in a.op:
        kind, rest = spec.split(":", 1)
        if kind == "layer":
            files = sorted(Path(rest).glob("frame_*.png"))
            if len(files) < a.frames:
                sys.exit(f"layer {rest} has {len(files)} frames, need {a.frames}")
            ops.append(dict(kind="layer", files=files))
        elif kind == "matte":
            path, start = rest.rsplit(":", 1)
            ops.append(dict(kind="matte", path=path, start=float(start), proc=None, i0=None))
        else:
            sys.exit(f"unknown op {kind}")

    enc = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-"]
    if a.audio:
        enc += ["-i", a.audio]
    enc += ["-map", "0:v"]
    if a.audio:
        enc += ["-map", "1:a:0", "-c:a", "copy"]
    enc += ["-c:v", "libx264", "-crf", a.crf, "-preset", "slow", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(a.fps),
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "+faststart", a.out]
    out = subprocess.Popen(enc, stdin=subprocess.PIPE)

    base = base_reader(a.base, a.fps, a.frames)
    from PIL import Image
    nb = W * H * 3
    for i in range(a.frames):
        raw = base.stdout.read(nb)
        if len(raw) < nb:
            sys.exit(f"base ran out at frame {i}")
        frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)
        for op in ops:
            if op["kind"] == "layer":
                px = np.asarray(Image.open(op["files"][i]).convert("RGBA"), np.uint8)
                al = px[..., 3:4].astype(np.float32) / 255.0
                if al.max() == 0:
                    continue
                over(frame, px[..., :3].astype(np.float32), al)
            else:
                i0 = int(round(op["start"] * a.fps))
                if i < i0:
                    continue
                if op["proc"] is None:
                    op["proc"] = matte_reader(op["path"], a.fps)
                    op["i0"] = i0
                mraw = op["proc"].stdout.read(W * H * 4)
                if len(mraw) < W * H * 4:
                    continue                      # matte window finished
                px = np.frombuffer(mraw, np.uint8).reshape(H, W, 4)
                al = px[..., 3:4].astype(np.float32) / 255.0
                over(frame, px[..., :3].astype(np.float32), al)
        out.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if i % 300 == 0:
            print(f"  {i}/{a.frames}", flush=True)

    out.stdin.close()
    out.wait()
    base.stdout.close()
    for op in ops:
        if op["kind"] == "matte" and op["proc"]:
            op["proc"].stdout.close()
    print(a.out)


if __name__ == "__main__":
    main()
