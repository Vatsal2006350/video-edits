#!/bin/bash
# List / card reel: one line of hero type per shot, cut on the beat. No talking head.
#   CARDS = "path|seek|cut_out|line1|line2"   (line2 may be empty)
# Each card's text is laid over its own shot only, so a line never bleeds across a cut.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/cardreel"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/card_reel.mp4}"
AUDIO="${AUDIO:-$HOME/Downloads/music-rf/travel-documentary.mp3}"; AUDIO_SS="${AUDIO_SS:-0}"
SIZE="${SIZE:-100}"; TOP="${TOP:-1040}"; SCRIM="${SCRIM:-0.32}"
FACE="${FACE:-$ROOT/fonts/AvenirNext-Regular.ttf}"
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)
source "$(dirname "$0")/lib-still.sh"

prev=0; i=0; : > "$W/l.txt"
while IFS='|' read -r src ss cut l1 l2; do
  [ -z "$src" ] && continue
  i=$((i+1)); n=$(printf "c%02d" $i)
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  lower=$(printf %s "$src" | tr "[:upper:]" "[:lower:]")
  case "$lower" in
    *.jpg|*.jpeg|*.png|*.heic)
      # a still needs -loop/-frames, and a slow push so it does not sit dead on screen
      fr=$(awk -v d="$d" 'BEGIN{printf "%d", d*30}')
      ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$src" \
        -vf "$(still_vf 1080 1920 0.0012 1.14),eq=contrast=1.04:saturation=1.10" \
        -frames:v "$fr" -an "${enc[@]}" "$W/$n.mp4" -y ;;
    *)
      ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.04:saturation=1.10,fps=30" \
        -an "${enc[@]}" "$W/$n.mp4" -y ;;
  esac
  if [ -n "${l1// /}" ]; then
    LN="{\"t\":\"${l1}\",\"at\":0.06}"
    [ -n "${l2:-}" ] && [ -n "${l2// /}" ] && LN="$LN,{\"t\":\"${l2}\",\"at\":0.40}"
    python3 "$ROOT/bin/hero-type.py" "{\"dur\":${d},\"face\":\"${FACE}\",\"face_index\":0,\"size\":${SIZE},\"top\":${TOP},\"x\":88,\"lead\":1.12,\"fade\":0.22,\"shadow\":0.9,\"scrim\":${SCRIM},\"ghost\":0.55,\"lines\":[${LN}],\"outdir\":\"$W/t$i\"}" >/dev/null
    ffmpeg -nostdin -v error -i "$W/$n.mp4" -framerate 30 -i "$W/t$i/h_%04d.png" \
      -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/${n}t.mp4" -y
    mv "$W/${n}t.mp4" "$W/$n.mp4"
  fi
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/l.txt"
  printf "    %6.2f -> %6.2f  %-34s  %s\n" "$prev" "$cut" "$(basename "$src")" "$l1"
  prev="$cut"
done <<< "$CARDS"

DUR="$prev"
ffmpeg -v error -f concat -safe 0 -i "$W/l.txt" -ss "$AUDIO_SS" -i "$AUDIO" \
  -filter_complex "[1:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.8,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-1.0}'):d=1.0,loudnorm=I=-13:TP=-1.0:LRA=11[a]" \
  -map 0:v -map "[a]" -t "$DUR" "${enc[@]}" -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
