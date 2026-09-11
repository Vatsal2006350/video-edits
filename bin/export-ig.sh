#!/usr/bin/env bash
# export-ig.sh <master.mp4> <name_IG.mp4>
# Encode a display-ready master to the Instagram upload contract. Raw HLG/PQ
# footage must be tonemapped by the builder first; this command also writes
# explicit Rec.709 VUI/container metadata so source HDR tags cannot leak through.
set -euo pipefail

IN="${1:?usage: export-ig.sh <master.mp4> <name_IG.mp4>}"
OUT="${2:?usage: export-ig.sh <master.mp4> <name_IG.mp4>}"
[ -f "$IN" ] || { echo "missing input: $IN" >&2; exit 1; }
[ "$IN" != "$OUT" ] || { echo "input and output must differ" >&2; exit 1; }
[ "${FORCE:-0}" = 1 ] || [ ! -e "$OUT" ] || { echo "refusing to overwrite: $OUT (set FORCE=1)" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"

video=(-map 0:v:0 -c:v libx264 -preset slow -profile:v high -level 4.0
  -pix_fmt yuv420p -r 30 -fps_mode cfr -g 60 -keyint_min 60 -sc_threshold 0
  -b:v 8000k -maxrate 9000k -bufsize 18000k
  -color_primaries bt709 -color_trc bt709 -colorspace bt709
  -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1)
mov=(-movflags +faststart+negative_cts_offsets -use_editlist 0)

if ffprobe -v error -select_streams a:0 -show_entries stream=index -of csv=p=0 "$IN" | grep -q .; then
  # Feed measured values back to loudnorm. A one-pass `linear=true` export can
  # undershoot by several LU on sparse speech/music mixes.
  analysis=$(ffmpeg -nostdin -hide_banner -i "$IN" -map 0:a:0 \
    -af "loudnorm=I=-14:TP=-2.2:LRA=11:print_format=json" -f null - 2>&1)
  measured=$(printf '%s' "$analysis" | python3 -c '
import json, re, sys
s = sys.stdin.read()
m = re.findall(r"\{[^{}]*\}", s, re.S)
if not m: raise SystemExit("loudnorm analysis did not return JSON")
d = json.loads(m[-1])
print(":measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}".format(**d))
')
  ffmpeg -nostdin -y -v error -i "$IN" "${video[@]}" -map 0:a:0 \
    -af "aresample=44100:async=1,loudnorm=I=-14:TP=-2.2:LRA=11${measured}:linear=true,alimiter=limit=0.77:level=false" \
    -c:a aac -b:a 160k -ar 44100 -ac 2 "${mov[@]}" -shortest "$OUT"
else
  ffmpeg -nostdin -y -v error -i "$IN" "${video[@]}" -an "${mov[@]}" "$OUT"
fi

echo "[export-ig] -> $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=profile,level,width,height,avg_frame_rate,color_space,color_transfer,color_primaries \
  -of default=nw=1 "$OUT"
