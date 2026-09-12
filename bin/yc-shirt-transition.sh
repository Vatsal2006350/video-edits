#!/usr/bin/env bash
# Rebuild of the DY19PusoKRn hand-cover transition using Vatsal's two takes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/deliverables/yc-shirt-transition-2026-09-12/master/yc-shirt-transition.mp4}"
CLIP_A="${CLIP_A:-/Users/vatsalshah/Downloads/IMG_5421.MOV}"
CLIP_B="${CLIP_B:-/Users/vatsalshah/Downloads/IMG_5422.MOV}"
YC="${YC:-$ROOT/receipts/yc_fullbleed.jpg}"
AUDIO="${AUDIO:-$ROOT/.work/yc-shirt-transition/reference-audio.mp4}"
FONT="$ROOT/fonts/DMSerifDisplay-Regular.ttf"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$(dirname "$OUT")"

# Reference cut: full hand cover at 4.80s. Source A's matching cover is 5.55s;
# source B begins on its matching cover at 3.40s. Final YC proof lands at 8.17s.
VF="zscale=transfer=linear:npl=100,format=gbrpf32le,zscale=primaries=bt709,tonemap=tonemap=mobius:param=0.3:desat=0,zscale=transfer=bt709:matrix=bt709:range=tv,format=yuv420p,scale=1080:1920:flags=lanczos,setsar=1,fps=30"

ffmpeg -nostdin -y -v error -ss 0.75 -t 4.80 -i "$CLIP_A" \
  -vf "$VF,drawtext=fontfile='$FONT':text='Y Combinator':fontsize=60:fontcolor=0xF2C94C:borderw=1:bordercolor=black@0.3:shadowcolor=black@0.45:shadowy=2:x=(w-text_w)/2:y=1210:enable='between(t,1.45,4.80)'" \
  -an -c:v libx264 -crf 17 -preset fast "$TMP/a.mp4"

ffmpeg -nostdin -y -v error -ss 3.40 -t 3.37 -i "$CLIP_B" \
  -vf "$VF" -an -c:v libx264 -crf 17 -preset fast "$TMP/b.mp4"

ffmpeg -nostdin -y -v error -loop 1 -t 3.044 -i "$YC" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  -an -c:v libx264 -crf 17 -preset fast "$TMP/c.mp4"

printf "file '%s'\nfile '%s'\nfile '%s'\n" "$TMP/a.mp4" "$TMP/b.mp4" "$TMP/c.mp4" > "$TMP/list.txt"
ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" -i "$AUDIO" \
  -map 0:v:0 -map 1:a:0 -t 11.214 -af "aresample=44100:async=1,loudnorm=I=-14:TP=-2:LRA=11" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 -g 60 \
  -c:a aac -b:a 160k -ar 44100 -ac 2 -movflags +faststart "$OUT"
echo "[yc-shirt-transition] cover cut 4.80s; YC proof 8.17s -> $OUT"
