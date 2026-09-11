#!/bin/bash
# Then/now diptych: a childhood still fills the top half, present-day motion the bottom,
# both cut together on the beat. Reads instantly in a feed because the comparison is the frame.
#   PAIRS = "still|motion|seek|cut_out"
# Top is graded down (desaturated, cooler) so the eye lands on the bottom half.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; F="$ROOT/fonts"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/diptych"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/diptych.mp4}"
AUDIO="${AUDIO:-$HOME/Downloads/music-rf/phonk-hard.mp3}"; AUDIO_SS="${AUDIO_SS:-0}"
TOP_T="${TOP_T:-2018}"; BOT_T="${BOT_T:-now}"
L1="${L1-}"; L2="${L2-}"                 # optional hero line over the seam
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)
source "$(dirname "$0")/lib-still.sh"
HALF=960

prev=0; i=0; : > "$W/l.txt"
while IFS='|' read -r still motion ss cut; do
  [ -z "$still" ] && continue
  i=$((i+1)); n=$(printf "d%02d" $i)
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  fr=$(awk -v d="$d" 'BEGIN{printf "%d", d*30}')
  ffmpeg -nostdin -v error \
    -loop 1 -framerate 30 -t "$d" -i "$still" \
    -ss "$ss" -t "$d" -i "$motion" \
    -filter_complex "
      [0:v]$(still_cover_vf 1080 ${HALF} 0.0014 1.16),hue=s=0.20,eq=contrast=1.14:brightness=-0.03[t];
      [1:v]scale=1080:${HALF}:force_original_aspect_ratio=increase,crop=1080:${HALF},eq=contrast=1.05:saturation=1.16,fps=30[b];
      [t][b]vstack=2,drawbox=y=${HALF}-3:h=6:c=white@0.85:t=fill[v]" \
    -map "[v]" -frames:v "$fr" -an "${enc[@]}" "$W/$n.mp4" -y
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/l.txt"
  printf "    %6.2f -> %6.2f  %-30s / %s\n" "$prev" "$cut" "$(basename "$still")" "$(basename "$motion")"
  prev="$cut"
done <<< "$PAIRS"
ffmpeg -v error -f concat -safe 0 -i "$W/l.txt" -c copy "$W/joined.mp4" -y
DUR="$prev"

# year stamps sit just inside each half, clear of IG's chrome and of the seam
python3 "$ROOT/bin/glow-text.py" "{\"text\":\"${TOP_T}\",\"font\":\"$F/Montserrat-Bold.ttf\",\"size\":72,\"max_w\":620,\"x\":96,\"anchor\":\"lm\",\"y\":360,\"glow\":[255,255,255],\"fill\":[255,255,255],\"passes\":2,\"radius\":10,\"out\":\"$W/top.png\"}" >/dev/null
python3 "$ROOT/bin/glow-text.py" "{\"text\":\"${BOT_T}\",\"font\":\"$F/Montserrat-Bold.ttf\",\"size\":72,\"max_w\":620,\"x\":96,\"anchor\":\"lm\",\"y\":1440,\"glow\":[255,214,10],\"fill\":[255,255,255],\"passes\":3,\"radius\":16,\"out\":\"$W/bot.png\"}" >/dev/null
ffmpeg -nostdin -v error -i "$W/joined.mp4" -i "$W/top.png" -i "$W/bot.png" \
  -filter_complex "[0:v][1:v]overlay=0:0[a];[a][2:v]overlay=0:0[v]" -map "[v]" -an "${enc[@]}" "$W/stamped.mp4" -y

if [ -n "${L1// /}" ]; then
  python3 "$ROOT/bin/hero-type.py" "{\"dur\":${DUR},\"face\":\"$F/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":92,\"top\":${LTOP:-820},\"x\":88,\"lead\":1.12,\"fade\":0.24,\"shadow\":0.95,\"scrim\":0.34,\"lines\":[{\"t\":\"${L1}\",\"at\":0.10},{\"t\":\"${L2}\",\"at\":0.75}],\"outdir\":\"$W/t\"}" >/dev/null
  ffmpeg -nostdin -v error -i "$W/stamped.mp4" -framerate 30 -i "$W/t/h_%04d.png" \
    -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/final_v.mp4" -y
else
  cp "$W/stamped.mp4" "$W/final_v.mp4"
fi

ffmpeg -v error -i "$W/final_v.mp4" -ss "$AUDIO_SS" -i "$AUDIO" \
  -filter_complex "[1:a]atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-0.7}'):d=0.7,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
