#!/bin/bash
set -uo pipefail
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
mkdir -p "$S"
V=$HOME/Code/video-edits; B=$HOME/Downloads/photos-broll; T=$B/travel2; C=$HOME/Downloads/content; YC=$HOME/Downloads/yc_announcement.JPG
W=$S/penn; rm -rf "$W"; mkdir -p "$W"
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)
source "$V/bin/lib-still.sh"
SPEECH=$S/penn_speech.mp4
ffmpeg -nostdin -v error -i "$SPEECH" -an -c:v copy "$W/a.mp4" -y
ffmpeg -nostdin -v error -i "$SPEECH" -vn -ac 2 -ar 48000 -c:a pcm_s16le "$W/speech.wav" -y

TAILS="$C/IMG_7152.MOV|0.5|2.40|that clip ends|right there
$T/IMG_2627.MOV|60.5|4.80|i built for|the next two years
$YC|0|8.20|the yes came later|from somewhere else"
prev=0; i=0; : > "$W/t.txt"
while IFS='|' read -r src ss cut l1 l2; do
  [ -z "$src" ] && continue
  i=$((i+1)); n=$(printf "z%02d" $i)
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  lower=$(printf %s "$src" | tr "[:upper:]" "[:lower:]")
  case "$lower" in
    *.jpg|*.jpeg|*.png)
      fr=$(awk -v d="$d" 'BEGIN{printf "%d", d*30}')
      ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$src" \
        -vf "$(still_vf 1080 1920 0.0012 1.14)" \
        -frames:v "$fr" -an "${enc[@]}" "$W/$n.mp4" -y ;;
    *)
      ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -an "${enc[@]}" "$W/$n.mp4" -y ;;
  esac
  python3 "$V/bin/hero-type.py" "{\"dur\":$d,\"face\":\"$V/fonts/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":100,\"top\":1250,\"x\":88,\"lead\":1.12,\"fade\":0.22,\"shadow\":0.9,\"scrim\":0.32,\"ghost\":0.55,\"lines\":[{\"t\":\"$l1\",\"at\":0.06},{\"t\":\"$l2\",\"at\":0.42}],\"outdir\":\"$W/h$i\"}" >/dev/null
  ffmpeg -nostdin -v error -i "$W/$n.mp4" -framerate 30 -i "$W/h$i/h_%04d.png" \
    -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/${n}t.mp4" -y
  mv "$W/${n}t.mp4" "$W/$n.mp4"
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/t.txt"
  echo "    tail ${prev}-${cut}s  $l1"
  prev="$cut"
done <<< "$TAILS"
ffmpeg -v error -f concat -safe 0 -i "$W/t.txt" -c copy "$W/tail.mp4" -y
printf "file '%s'\nfile '%s'\n" "$W/a.mp4" "$W/tail.mp4" > "$W/all.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/all.txt" -c copy "$W/video.mp4" -y
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/video.mp4")
echo "total ${DUR}s"
ffmpeg -v error -i "$W/video.mp4" -i "$W/speech.wav" -i "$HOME/Downloads/music-rf/winner_is.mp3" -filter_complex "
 [1:a]aformat=channel_layouts=stereo,apad=whole_dur=${DUR},volume=2dB,alimiter=limit=0.97,asplit=2[voice][vsc];
 [2:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.2,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-2.2}'):d=2.2,volume=0.30[bed];
 [bed][vsc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=400[duck];
 [voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
 -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$HOME/Downloads/reel-batch/5-talking-head/01_the_night_before.mp4" -y
echo "DONE  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$HOME/Downloads/reel-batch/5-talking-head/01_the_night_before.mp4")s"
