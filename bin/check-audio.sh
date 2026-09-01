#!/usr/bin/env bash
# check-audio.sh <video> [t0:t1 ...] — integrated LUFS + per-segment mean volume.
# Use to catch loudness jumps at cuts (e.g. raw iPhone outro vs amplified main).
# Segments >2 dB apart at a cut will be audible; report, don't silently fix.
set -euo pipefail
V="${1:?usage: check-audio.sh <video> [t0:t1 ...]}"; shift || true
echo "== integrated =="
ffmpeg -hide_banner -i "$V" -af loudnorm=print_format=summary -f null /dev/null 2>&1 \
  | grep -E "Input (Integrated|True Peak|LRA)"
[ $# -gt 0 ] && echo "== segments =="
for seg in "$@"; do
  t0="${seg%%:*}"; t1="${seg##*:}"
  printf "%-12s " "$seg"
  ffmpeg -hide_banner -ss "$t0" -t "$(python3 -c "print($t1-$t0)")" -i "$V" \
    -af volumedetect -f null /dev/null 2>&1 | grep -oE "mean_volume: [-0-9.]+ dB"
done
