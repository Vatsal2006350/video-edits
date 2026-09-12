#!/usr/bin/env bash
# wishes-yc-reel.sh <manifest> <out.mp4>
# Proven Wishes structure: four equal 2.728-second scenes. Keep this visual
# grid unchanged and use the verified original reel audio.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MF="${1:?manifest}"; OUT="${2:?output}"
FONT="$ROOT/fonts/Montserrat-Bold.ttf"
AUDIO="${AUDIO:-$ROOT/assets/audio/wishes.mp3}"
AUDIO_SS="${AUDIO_SS:-0}"
TOTAL=10.912
SCENE=2.728
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$(dirname "$OUT")"

escape_text() { printf '%s' "$1" | sed "s/'/’/g; s/:/\\\\:/g; s/%/\\\\%/g"; }
i=0
while IFS='|' read -r TYPE SRC SS TEXT; do
  [ -n "${TYPE// }" ] || continue
  i=$((i+1)); SEG="$TMP/seg-$i.mp4"; TXT="$(escape_text "$TEXT")"
  FS=$(python3 - "$TEXT" "$FONT" <<'PY'
import sys
from PIL import ImageFont
text, font = sys.argv[1:]
size = 58
while size > 34 and max(ImageFont.truetype(font, size).getlength(x) for x in text.split('\\n')) > 720:
    size -= 2
print(size)
PY
)
  DRAW=""
  if [ -n "$TEXT" ]; then
    if [ "$TYPE" = video ]; then Y=1010; else Y=360; fi
    DRAW=",drawtext=fontfile='$FONT':text='$TXT':fontsize=$FS:fontcolor=white:line_spacing=10:text_align=center:borderw=2:bordercolor=black@0.58:shadowcolor=black@0.55:shadowy=3:x=(w-text_w)/2:y=$Y"
  fi
  if [ "$TYPE" = video ]; then
    ffmpeg -nostdin -y -v error -ss "${SS:-0}" -t "$SCENE" -i "$SRC" \
      -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30${DRAW},format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
      -t "$SCENE" -an -c:v libx264 -crf 17 -preset fast "$SEG"
  else
    ffmpeg -nostdin -y -v error -loop 1 -t "$SCENE" -i "$SRC" \
      -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30${DRAW},format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
      -t "$SCENE" -an -c:v libx264 -crf 17 -preset fast "$SEG"
  fi
  printf "file '%s'\n" "$SEG" >> "$TMP/list.txt"
done < "$MF"
[ "$i" -eq 4 ] || { echo "manifest must contain exactly four scenes, got $i" >&2; exit 2; }

ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" \
  -ss "$AUDIO_SS" -t "$TOTAL" -i "$AUDIO" -map 0:v:0 -map 1:a:0 -t "$TOTAL" \
  -af "aresample=44100:async=1,loudnorm=I=-14:TP=-2:LRA=11" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 -g 60 \
  -c:a aac -b:a 160k -ar 44100 -ac 2 -movflags +faststart "$OUT"
echo "[wishes-yc] cuts 0/2.728/5.456/8.184/10.912; verified Wishes audio -> $OUT"
