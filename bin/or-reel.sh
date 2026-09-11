#!/bin/bash
# "X OR Y" trend reel  (format decoded from @sanskartech / reel DZRjqRCxhKL)
#   0 -> CUT        full-bleed vertical shot + gold fisheye-warped "L1 / OR / L3"
#   CUT -> +DOTS    three-dot loading beat on black
#   then            letterboxed 16:9 receipt shots, cut on the music's beats
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${OUT:-$HOME/Downloads/reel-exports/or_reel.mp4}"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/orreel"
rm -rf "$W"; mkdir -p "$W" "$(dirname "$OUT")"

HOOK="${HOOK:-$HOME/Downloads/content/IMG_8286.mov}"; HOOK_SS="${HOOK_SS:-0.30}"
AUDIO="${AUDIO:-$HOME/Downloads/music-rf/yc_trend.mp3}"
L1="${L1:-Talk to her again}"; L2="${L2:-OR}"; L3="${L3:-Become a YC founder}"
CUT="${CUT:-4.75}"; DUR="${DUR:-9.53}"; DOTS="${DOTS:-1.0}"
TARGET_W="${TARGET_W:-670}"; CY="${CY:-1105}"; K="${K:--0.26}"
BAND_H="${BAND_H:-608}"                       # letterbox band height (16:9 at 1080 wide)

# receipt shots: "path|seek|end_time"  (end_time = reel time this shot cuts away, on a beat)
# "path|seek|end_time|caption"  — end_time is a beat from bin/beats.py; caption is optional
PAYOFFS="${PAYOFFS:-$HOME/Downloads/yc_announcement.JPG|0|6.502|Became a YC founder at 18
$HOME/Downloads/content/IMG_6946.MOV|0.30|7.848|
$HOME/Downloads/content/IMG_6946.MOV|7.30|9.53|}"

enc=(-c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -r 30)
source "$(dirname "$0")/lib-still.sh"

HOOK_D=$(echo "$CUT - $DOTS" | bc)          # dots occupy the last DOTS seconds before the beat
echo "[1/4] hook  0 -> ${HOOK_D}s"
python3 "$PWD/bin/fisheye-text.py" "{\"lines\":[{\"t\":\"${L1}\"},{\"t\":\"${L2}\",\"rel\":0.80},{\"t\":\"${L3}\"}],\"target_w\":${TARGET_W},\"cy\":${CY},\"k\":${K},\"out\":\"$W/text.png\"}"
ffmpeg -v error -ss "$HOOK_SS" -t "$HOOK_D" -i "$HOOK" -i "$W/text.png" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];[bg][1:v]overlay=0:0,fps=30[v]" \
  -map "[v]" -an "${enc[@]}" "$W/s00.mp4" -y

echo "[2/4] loading dots  ${HOOK_D} -> ${CUT}s"
python3 "$PWD/bin/loading-dots.py" "{\"outdir\":\"$W/dots\",\"dur\":${DOTS},\"cy\":960,\"r\":24,\"gap\":96}" >/dev/null
ffmpeg -v error -framerate 30 -i "$W/dots/d_%04d.png" -an "${enc[@]}" "$W/s01.mp4" -y

echo "[3/4] receipt shots (letterboxed, beat-cut)"
prev="$CUT"; i=2
while IFS='|' read -r src ss endt cap; do
  [ -z "$src" ] && continue
  d=$(echo "$endt - $prev" | bc); n=$(printf "s%02d" $i)
  echo "    ${prev}s -> ${endt}s  (${d}s)  $(basename "$src")"
  lower=$(printf %s "$src" | tr "[:upper:]" "[:lower:]")
  case "$lower" in
    *.jpg|*.jpeg|*.png|*.heic)
      fr=$(echo "$d * 30 / 1" | bc)
      ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$src" \
        -vf "$(still_vf 1080 ${BAND_H} 0.0011 1.16),pad=1080:1920:0:(1920-${BAND_H})/2:black" \
        -frames:v "$fr" -an "${enc[@]}" "$W/$n.mp4" -y ;;
    *)
      ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
        -vf "scale=1080:${BAND_H}:force_original_aspect_ratio=increase,crop=1080:${BAND_H},pad=1080:1920:0:(1920-${BAND_H})/2:black,fps=30" \
        -an "${enc[@]}" "$W/$n.mp4" -y ;;
  esac
  if [ -n "${cap// /}" ]; then
    python3 "$PWD/bin/fisheye-text.py" "{\"lines\":[{\"t\":\"${cap}\"}],\"target_w\":780,\"cy\":455,\"k\":-0.18,\"out\":\"$W/cap$i.png\"}" >/dev/null
    ffmpeg -nostdin -v error -i "$W/$n.mp4" -i "$W/cap$i.png" \
      -filter_complex "[0:v][1:v]overlay=0:0,fps=30[v]" -map "[v]" -an "${enc[@]}" "$W/${n}c.mp4" -y
    mv "$W/${n}c.mp4" "$W/$n.mp4"
  fi
  prev="$endt"; i=$((i+1))
done <<< "$PAYOFFS"

echo "[4/4] join + music"
for f in "$W"/s*.mp4; do printf "file '%s'\n" "$f"; done > "$W/l.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/l.txt" -i "$AUDIO" \
  -filter_complex "[1:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=out:st=$(echo "$DUR-0.35"|bc):d=0.35,loudnorm=I=-13:TP=-1.0:LRA=11[a]" \
  -map 0:v -map "[a]" -t "$DUR" "${enc[@]}" -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
