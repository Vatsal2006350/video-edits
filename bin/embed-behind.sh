#!/usr/bin/env bash
# embed-behind.sh <in.mp4> <out.mp4> <start> <end> <text-png>
# Mattes the speaker in that window and composites the PNG BEHIND them.
set -euo pipefail
IN="${1:?in}"; OUT="${2:?out}"; S="${3:?start}"; E="${4:?end}"; TXT="${5:?text png}"
HF="${HYPERFRAMES_ROOT:-$HOME/Downloads/hyperframes}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
DUR=$(python3 -c "print(round($E-$S,3))")
ffmpeg -nostdin -y -v error -ss "$S" -t "$DUR" -i "$IN" -an -c:v libx264 -crf 14 "$T/win.mp4"
node "$HF/packages/cli/dist/cli.js" remove-background "$T/win.mp4" -o "$T/fg.mov" >/dev/null 2>&1
mkdir -p "$T/bg" "$T/fg"
ffmpeg -nostdin -y -v error -i "$T/win.mp4" "$T/bg/f_%04d.png"
ffmpeg -nostdin -y -v error -i "$T/fg.mov" -pix_fmt rgba "$T/fg/f_%04d.png"
python3 - "$T" "$TXT" <<'PY'
from PIL import Image
import sys, glob, os
T,txt=sys.argv[1],sys.argv[2]
overlay=Image.open(txt).convert('RGBA')
bgs=sorted(glob.glob(f'{T}/bg/*.png')); fgs=sorted(glob.glob(f'{T}/fg/*.png'))
os.makedirs(f'{T}/out',exist_ok=True)
for i,b in enumerate(bgs):
    bg=Image.open(b).convert('RGBA')
    if overlay.size!=bg.size: ov=overlay.resize(bg.size, Image.LANCZOS)
    else: ov=overlay
    comp=Image.alpha_composite(bg, ov)                  # text sits on the background
    if i < len(fgs):
        fg=Image.open(fgs[i]).convert('RGBA')
        if fg.size!=bg.size: fg=fg.resize(bg.size, Image.LANCZOS)
        comp=Image.alpha_composite(comp, fg)            # subject back on top
    comp.convert('RGB').save(f'{T}/out/f_{i+1:04d}.png')
print(f'composited {len(bgs)} frames')
PY
ffmpeg -nostdin -y -v error -framerate 30 -i "$T/out/f_%04d.png" -r 30 -fps_mode cfr \
  -c:v libx264 -crf 17 -pix_fmt yuv420p "$OUT"
echo "[embed-behind] -> $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
