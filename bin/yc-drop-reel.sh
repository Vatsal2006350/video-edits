#!/usr/bin/env bash
# yc-drop-reel.sh <out> <audio> <caption.png> <build_clip> <build_start> <yc_card>
# Structure: colour build -> greyscale freeze + skull on the drop -> YC card reveal.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?out}"; AUD="${2:?audio}"; CAP="${3:?caption}"; CLIP="${4:?clip}"; SS="${5:?start}"; YC="${6:?yc card}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
# find the drop: first beat >= 2.0s so the build has room
DROP=$(python3 "$WS/bin/beats.py" "$AUD" 12 | python3 -c "
import sys
bs=[float(l) for l in sys.stdin if l.strip()]
c=[b for b in bs if b>=2.0]
print('%.2f' % (c[0] if c else 2.4))")
bash "$WS/bin/greyscale-drop.sh" "$T/part1.mp4" "$CLIP" "$SS" "$DROP" 1.7 "$CAP" >/dev/null
# YC card: full-bleed, slow push, held
ffmpeg -nostdin -y -v error -framerate 30 -loop 1 -t 2.6 -i "$YC" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1.07,1+0.0009*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p" \
  -r 30 -fps_mode cfr -c:v libx264 -crf 17 -an "$T/yc.mp4"
P1=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/part1.mp4")
OFF=$(python3 -c "print(round($P1-0.3,3))")
ffmpeg -nostdin -y -v error -i "$T/part1.mp4" -i "$T/yc.mp4" \
  -filter_complex "[0:v][1:v]xfade=transition=fadeblack:duration=0.3:offset=$OFF,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 16 -r 30 -fps_mode cfr -an "$T/vid.mp4"
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/vid.mp4")
FO=$(python3 -c "print(round($VD-0.6,2))")
ffmpeg -nostdin -y -v error -stream_loop 3 -i "$AUD" -i "$T/vid.mp4" -map 1:v -map 0:a -t "$VD" \
  -c:v copy -c:a aac -b:a 192k -af "afade=t=out:st=$FO:d=0.6" -movflags +faststart "$OUT"
echo "[yc-drop] -> $OUT  ${VD}s  (drop @ ${DROP}s)"
