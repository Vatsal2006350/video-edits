#!/usr/bin/env bash
# cta-overlay.sh <in> <out> <start_sec> <line1> <line2> <line3> [--scrim png]
# Staggered Anton CTA (house style): lines rise+fade in 0.28s, 0.3s apart;
# line 2 is accent yellow. Video before <start_sec> is untouched.
set -euo pipefail
IN="${1:?in}"; OUT="${2:?out}"; T="${3:?start}"; L1="${4:?l1}"; L2="${5:?l2}"; L3="${6:?l3}"
SCRIM="${8:-}"; [ "${7:-}" = "--scrim" ] && SCRIM="$8"
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONT="$WS/fonts/Anton-Regular.ttf"
esc() { printf '%s' "$1" | sed "s/'/\\\\\\\\\\\\'/g; s/:/\\\\:/g"; }
D1=$(python3 -c "print($T+0.15)"); D2=$(python3 -c "print($T+0.45)"); D3=$(python3 -c "print($T+0.75)")
line() { # $1 text $2 y $3 color $4 t_in
  echo "drawtext=fontfile=$FONT:text='$(esc "$1")':fontsize=86:fontcolor=$3:borderw=6:bordercolor=black@0.85:x=(w-text_w)/2:y='$2-18*min(1\,max(0\,(t-$4)/0.28))':alpha='min(1,max(0,(t-$4)/0.28))':enable='gte(t,$T)'"
}
F="$(line "$L1" 1400 white "$D1"),$(line "$L2" 1518 0xFFD24A "$D2"),$(line "$L3" 1636 white "$D3"),format=yuv420p"
if [ -n "$SCRIM" ]; then
  ffmpeg -y -v error -i "$IN" -i "$SCRIM" -filter_complex "[0:v][1:v]overlay=0:0:enable='gte(t,$T)'[s];[s]$F[out]" \
    -map "[out]" -map 0:a -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -c:a copy "$OUT"
else
  ffmpeg -y -v error -i "$IN" -vf "$F" \
    -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -c:a copy "$OUT"
fi
echo "[cta] → $OUT"
