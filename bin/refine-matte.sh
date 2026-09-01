#!/usr/bin/env bash
# refine-matte.sh <project> <t0> <t1> [pad_px]
# Hi-res window re-matte: when the subject is small in frame (wide shot), the
# 320x320 segmentation model returns a blurry blob. This crops the subject
# region, upscales 4x, re-mattes, and pastes the sharp alpha back into
# frames_fg for exactly that window. Run AFTER prepare.sh, BEFORE make-theme.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
P="$(cd "${1:?usage: refine-matte.sh <project> <t0> <t1> [pad]}" && pwd)"
T0="${2:?t0}"; T1="${3:?t1}"; PAD="${4:-40}"
FPS="$(cat "$P/matte.fps" 2>/dev/null || echo 30)"
HF="${HYPERFRAMES_ROOT:-$HOME/Downloads/hyperframes}"

read S0 CNT CX CY CW CH SCALE <<<"$(python3 - "$P" "$T0" "$T1" "$PAD" "$FPS" <<'PY'
from PIL import Image
import sys, glob
p, t0, t1, pad, fps = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
fs = sorted(glob.glob(p + '/frames_fg/*.png'))
s0 = max(1, int(t0 * fps) + 1); s1 = min(len(fs), int(t1 * fps) + 1)
xs, ys = [], []
for i in range(s0 - 1, s1):
    bb = Image.open(fs[i]).convert('RGBA').getchannel('A').getbbox()
    if bb: xs += [bb[0], bb[2]]; ys += [bb[1], bb[3]]
if not xs: sys.exit("no subject found in window")
W, H = Image.open(fs[0]).size
x0 = max(0, min(xs) - pad); y0 = max(0, min(ys) - pad)
x1 = min(W, max(xs) + pad); y1 = min(H, max(ys) + pad)
cw = (x1 - x0) // 2 * 2; ch = (y1 - y0) // 2 * 2
scale = max(2, min(4, 1280 // cw))
print(s0, s1 - s0 + 1, x0, y0, cw, ch, scale)
PY
)"
echo "[refine] frames f_$(printf %04d "$S0")..+$CNT crop=${CW}x${CH}+${CX}+${CY} upscale=${SCALE}x"

TMP="$P/_refine"; rm -rf "$TMP"; mkdir -p "$TMP"
ffmpeg -y -v error -start_number "$S0" -i "$P/frames_bg/f_%04d.png" -frames:v "$CNT" \
  -vf "crop=${CW}:${CH}:${CX}:${CY},scale=$((CW*SCALE)):$((CH*SCALE)):flags=lanczos" \
  -r "$FPS" -c:v libx264 -crf 12 -pix_fmt yuv420p "$TMP/crop.mp4"
node "$HF/packages/cli/dist/cli.js" remove-background "$TMP/crop.mp4" -o "$TMP/matte.mov" >/dev/null 2>&1
ffmpeg -y -v error -i "$TMP/matte.mov" -pix_fmt rgba -start_number 0 "$TMP/a_%04d.png"

python3 - "$P" "$S0" "$CNT" "$CX" "$CY" "$CW" "$CH" <<'PY'
from PIL import Image
import numpy as np, sys
p, s0, cnt, cx, cy, cw, ch = sys.argv[1], *map(int, sys.argv[2:])
for k in range(cnt):
    hi = Image.open(f'{p}/_refine/a_{k:04d}.png').convert('RGBA').getchannel('A').resize((cw, ch), Image.LANCZOS)
    fn = f'{p}/frames_fg/f_{s0+k:04d}.png'
    im = Image.open(fn).convert('RGBA')
    a = np.zeros((im.height, im.width), dtype=np.uint8)
    a[cy:cy+ch, cx:cx+cw] = np.asarray(hi)
    im.putalpha(Image.fromarray(a)); im.save(fn)
print(f'[refine] {cnt} frames upgraded')
PY
rm -rf "$TMP"
