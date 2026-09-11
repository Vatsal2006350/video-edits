#!/bin/bash
# Glow-up / transformation reel: childhood stills cut hard on the beat, then a drop into
# present-day motion, then the payoff card.
#   STILLS  = "path|cut_out"   (cut_out = beat time, from bin/beats.py)
#   MOTION  = "path|seek|cut_out"
#   PAYOFF  = "path|cut_out|caption"
# Stills are pushed through a slow zoompan so a photo never sits dead on screen, and get a
# greyscale+contrast grade so the switch to colour at the drop reads as the turn.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; F="$ROOT/fonts"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/glowup"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/glowup.mp4}"
AUDIO="${AUDIO:-$HOME/Downloads/music-rf/phonk-hard.mp3}"; AUDIO_SS="${AUDIO_SS:-0}"
DUR="${DUR:-9.57}"
OPEN_T="${OPEN_T:-2018}"           # small stamp burned over the stills
NOW_T="${NOW_T:-2026}"
L1="${L1-nobody was betting}"; L2="${L2-on the fat kid}"
CAPY="${CAPY:-1120}"
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)
source "$(dirname "$0")/lib-still.sh"

echo "[1/4] stills (graded, slow push)"
prev=0; i=0; : > "$W/list.txt"
while IFS='|' read -r src cut; do
  [ -z "$src" ] && continue
  i=$((i+1)); n=$(printf "a%02d" $i)
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  fr=$(awk -v d="$d" 'BEGIN{printf "%d", d*30}')
  ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$src" \
    -vf "$(still_cover_vf 1080 1920 0.0016 1.20),hue=s=0.18,eq=contrast=1.18:brightness=-0.02" \
    -frames:v "$fr" -an "${enc[@]}" "$W/$n.mp4" -y
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/list.txt"
  printf "    %6.2f -> %6.2f  %s\n" "$prev" "$cut" "$(basename "$src")"
  prev="$cut"
done <<< "$STILLS"
STILL_END="$prev"

echo "[2/4] motion (colour returns at the drop)"
j=0
while IFS='|' read -r src ss cut; do
  [ -z "$src" ] && continue
  j=$((j+1)); n=$(printf "b%02d" $j)
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.06:saturation=1.14,fps=30" \
    -an "${enc[@]}" "$W/$n.mp4" -y
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/list.txt"
  printf "    %6.2f -> %6.2f  %s\n" "$prev" "$cut" "$(basename "$src")"
  prev="$cut"
done <<< "$MOTION"

echo "[3/4] payoff"
IFS='|' read -r psrc pcut pcap <<< "$PAYOFF"
d=$(awk -v a="$pcut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
fr=$(awk -v d="$d" 'BEGIN{printf "%d", d*30}')
lower=$(printf %s "$psrc" | tr "[:upper:]" "[:lower:]")
case "$lower" in
  *.jpg|*.jpeg|*.png|*.heic)
    ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$psrc" \
      -vf "$(still_vf 1080 1920 0.0012 1.14)" \
      -frames:v "$fr" -an "${enc[@]}" "$W/z.mp4" -y ;;
  *)
    ffmpeg -nostdin -v error -ss 0 -t "$d" -i "$psrc" \
      -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -an "${enc[@]}" "$W/z.mp4" -y ;;
esac
if [ -n "${pcap// /}" ]; then
  python3 "$ROOT/bin/glow-text.py" "{\"text\":\"${pcap}\",\"font\":\"$F/Montserrat-Bold.ttf\",\"size\":104,\"max_w\":690,\"y\":${CAPY},\"out\":\"$W/pc.png\"}" >/dev/null
  ffmpeg -nostdin -v error -i "$W/z.mp4" -i "$W/pc.png" \
    -filter_complex "[0:v][1:v]overlay=0:0,fps=30[v]" -map "[v]" -an "${enc[@]}" "$W/zc.mp4" -y
  mv "$W/zc.mp4" "$W/z.mp4"
fi
printf "file '%s'\n" "$W/z.mp4" >> "$W/list.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/list.txt" -c copy "$W/joined.mp4" -y

echo "[4/4] hero line over the stills + music"
python3 "$ROOT/bin/hero-type.py" "{\"dur\":${STILL_END},\"face\":\"$ROOT/fonts/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":104,\"top\":1060,\"x\":88,\"lead\":1.12,\"fade\":0.24,\"shadow\":0.9,\"scrim\":0.30,\"lines\":[{\"t\":\"${L1}\",\"at\":0.10},{\"t\":\"${L2}\",\"at\":0.80}],\"outdir\":\"$W/t\"}" >/dev/null
ffmpeg -nostdin -v error -i "$W/joined.mp4" -framerate 30 -i "$W/t/h_%04d.png" \
  -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/final_v.mp4" -y
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/final_v.mp4")
ffmpeg -v error -i "$W/final_v.mp4" -ss "$AUDIO_SS" -i "$AUDIO" \
  -filter_complex "[1:a]atrim=0:${D},asetpts=PTS-STARTPTS,afade=t=out:st=$(awk -v d=$D 'BEGIN{printf "%.2f", d-0.7}'):d=0.7,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -t "$D" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
