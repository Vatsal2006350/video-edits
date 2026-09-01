#!/usr/bin/env bash
# beat-reel.sh <out.mp4> <audio> <caption.png> <transition> "<clip:start>" ...
# Cuts each scene so transitions land on detected musical beats. bash 3.2 safe.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?out}"; AUD="${2:?audio}"; CAP="${3:?caption}"; TR="${4:?transition}"; shift 4
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
N=$#
python3 "$WS/bin/beats.py" "$AUD" 40 > "$T/beats.txt"
python3 "$WS/bin/pick_cuts.py" "$T/beats.txt" "$N" > "$T/cuts.txt"
CUTS=(); while IFS= read -r line; do CUTS+=("$line"); done < "$T/cuts.txt"
i=0
for spec in "$@"; do
  f="${spec%:*}"; ss="${spec##*:}"
  i=$((i+1))
  DUR=$(python3 -c "print(round(${CUTS[$i]}-${CUTS[$((i-1))]},3))")
  ffmpeg -nostdin -y -v error -ss "$ss" -t "$DUR" -i "$f" \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.12,format=yuv420p,fps=30" \
    -an -r 30 -fps_mode cfr -c:v libx264 -crf 17 -preset fast "$T/s$i.mp4"
  echo "  scene $i: ${DUR}s  (cut on beat ${CUTS[$i]}s)"
done
X="$T/s1.mp4"
for n in $(seq 2 $i); do
  TOT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$X")
  OFF=$(python3 -c "print(round($TOT-0.25,3))")
  ffmpeg -nostdin -y -v error -i "$X" -i "$T/s$n.mp4" \
    -filter_complex "[0:v][1:v]xfade=transition=$TR:duration=0.25:offset=$OFF,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -crf 16 -r 30 -fps_mode cfr "$T/j$n.mp4"
  X="$T/j$n.mp4"
done
ffmpeg -nostdin -y -v error -i "$X" -i "$CAP" -filter_complex "[0:v][1:v]overlay=0:0,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 -preset slow -an "$T/vid.mp4"
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/vid.mp4")
FO=$(python3 -c "print(round($VD-0.6,2))")
ffmpeg -nostdin -y -v error -stream_loop 3 -i "$AUD" -i "$T/vid.mp4" -map 1:v -map 0:a -t "$VD" \
  -c:v copy -c:a aac -b:a 192k -af "afade=t=out:st=$FO:d=0.6" -movflags +faststart "$OUT"
echo "[beat-reel] -> $OUT  ${VD}s"
