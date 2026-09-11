#!/usr/bin/env bash
# embed-behind-seq.sh <in.mp4> <out.mp4> <start> <end> <png-seq-dir>
# Mattes the speaker across the window and composites an ANIMATED PNG sequence BEHIND them.
set -euo pipefail
IN="${1:?in}"; OUT="${2:?out}"; S="${3:?start}"; E="${4:?end}"; SEQ="${5:?png seq dir}"
HF="${HYPERFRAMES_ROOT:-$HOME/Downloads/hyperframes}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
DUR=$(python3 -c "print(round($E-$S,3))")
ffmpeg -nostdin -y -v error -ss "$S" -t "$DUR" -i "$IN" -an -r 30 -fps_mode cfr -c:v libx264 -crf 14 "$T/win.mp4"
node "$HF/packages/cli/dist/cli.js" remove-background "$T/win.mp4" -o "$T/fg.mov" >/dev/null 2>&1
mkdir -p "$T/bg" "$T/fg" "$T/out"
ffmpeg -nostdin -y -v error -i "$T/win.mp4" "$T/bg/f_%04d.png"
ffmpeg -nostdin -y -v error -i "$T/fg.mov" -pix_fmt rgba "$T/fg/f_%04d.png"
python3 - "$T" "$SEQ" <<'PY'
from PIL import Image
import sys, glob, os
T, seq = sys.argv[1], sys.argv[2]
ovs = sorted(glob.glob(f'{seq}/*.png'))
bgs = sorted(glob.glob(f'{T}/bg/*.png')); fgs = sorted(glob.glob(f'{T}/fg/*.png'))
for i, b in enumerate(bgs):
    bg = Image.open(b).convert('RGBA')
    ov = Image.open(ovs[min(i, len(ovs)-1)]).convert('RGBA')      # hold the last frame if short
    if ov.size != bg.size: ov = ov.resize(bg.size, Image.LANCZOS)
    comp = Image.alpha_composite(bg, ov)                          # type sits on the background
    if i < len(fgs):
        fg = Image.open(fgs[i]).convert('RGBA')
        if fg.size != bg.size: fg = fg.resize(bg.size, Image.LANCZOS)
        comp = Image.alpha_composite(comp, fg)                    # subject back on top
    comp.convert('RGB').save(f'{T}/out/f_{i+1:04d}.png')
print(f'    composited {len(bgs)} frames over {len(ovs)} type frames')
PY
ffmpeg -nostdin -y -v error -framerate 30 -i "$T/out/f_%04d.png" -r 30 -fps_mode cfr \
  -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT"
echo "[embed-behind-seq] -> $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
