#!/usr/bin/env bash
# greyscale-drop.sh <out.mp4> <clip> <start> <build_dur> <freeze_dur> [caption.png]
# Colour build -> on beat: freeze frame, desaturate to greyscale, skull drops in.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?out}"; CLIP="${2:?clip}"; SS="${3:?start}"; BUILD="${4:-2.4}"; FRZ="${5:-1.6}"; CAP="${6:-}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
FILL="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p,fps=30"
# colour build section
ffmpeg -nostdin -y -v error -ss "$SS" -t "$BUILD" -i "$CLIP" -vf "$FILL,eq=contrast=1.06:saturation=1.1" \
  -an -r 30 -fps_mode cfr -c:v libx264 -crf 17 "$T/a.mp4"
# grab the exact drop frame, greyscale it, hold it
END=$(python3 -c "print(round($SS+$BUILD,3))")
ffmpeg -nostdin -y -v error -ss "$END" -i "$CLIP" -vframes 1 -vf "$FILL,hue=s=0,eq=contrast=1.22:brightness=-0.04" "$T/frz.png"
ffmpeg -nostdin -y -v error -framerate 30 -loop 1 -t "$FRZ" -i "$T/frz.png" -i "$WS/receipts/skull.png" \
  -filter_complex "[1:v]scale=iw*1.0:ih*1.0[s];[0:v][s]overlay=0:0:enable='gte(t,0.06)',zoompan=z='min(1.06,1+0.0016*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[v]" \
  -map "[v]" -r 30 -fps_mode cfr -c:v libx264 -crf 17 "$T/b.mp4"
printf "file '%s'\nfile '%s'\n" "$T/a.mp4" "$T/b.mp4" > "$T/l.txt"
ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$T/l.txt" -c:v libx264 -crf 16 -r 30 -fps_mode cfr -an "$T/c.mp4"
if [ -n "$CAP" ]; then
  ffmpeg -nostdin -y -v error -i "$T/c.mp4" -i "$CAP" -filter_complex "[0:v][1:v]overlay=0:0,format=yuv420p[v]" \
    -map "[v]" -c:v libx264 -crf 17 -preset slow -an "$OUT"
else cp "$T/c.mp4" "$OUT"; fi
echo "[grey-drop] -> $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
