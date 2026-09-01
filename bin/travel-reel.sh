#!/usr/bin/env bash
# travel-reel.sh <out.mp4> <caption.png> <transition> "<clip:start:dur>" ...
# Builds a scenery travel reel: fills 1080x1920, light grade, xfade transitions,
# persistent caption overlay. Silent by design.
set -euo pipefail
OUT="${1:?out}"; CAP="${2:?caption png}"; TR="${3:?transition}"; shift 3
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
i=0
for spec in "$@"; do
  IFS=':' read -r f ss dur <<<"$spec"
  i=$((i+1))
  ffmpeg -nostdin -y -v error -ss "$ss" -t "$dur" -i "$f" \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.12,format=yuv420p,fps=30" \
    -an -r 30 -fps_mode cfr -c:v libx264 -crf 17 -preset fast "$T/s$i.mp4"
done
X="$T/s1.mp4"
for n in $(seq 2 $i); do
  TOT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$X")
  OFF=$(python3 -c "print(round($TOT-0.45,2))")
  ffmpeg -nostdin -y -v error -i "$X" -i "$T/s$n.mp4" \
    -filter_complex "[0:v][1:v]xfade=transition=$TR:duration=0.45:offset=$OFF,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -crf 16 -r 30 -fps_mode cfr "$T/j$n.mp4"
  X="$T/j$n.mp4"
done
ffmpeg -nostdin -y -v error -i "$X" -i "$CAP" \
  -filter_complex "[0:v][1:v]overlay=0:0,format=yuv420p[v]" -map "[v]" \
  -c:v libx264 -crf 18 -preset slow -movflags +faststart -an "$OUT"
echo "[travel-reel] → $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
