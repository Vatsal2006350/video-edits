#!/usr/bin/env bash
# receipt-reel.sh <manifest> <out.mp4> [total_dur]
# Mass-produce the "meme hook -> receipts" reel format (10.912s = the Wishes cut).
# Manifest: one scene per line:   type|src|focus|text
#   type:  video | photo
#   focus: left | center | right   (crop anchor for landscape video)
#   text:  hook/receipt line; use \n for a line break. Empty = no text.
# Scenes get equal time slices of total_dur (default 10.912 = Wishes segment).
# Output is SILENT by design: attach the trending audio in the IG composer.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MF="${1:?manifest}"; OUT="${2:?out.mp4}"; TOTAL="${3:-10.912}"
FONT="$WS/fonts/Montserrat-SemiBold.ttf"
W=1080; H=1920; FPS=30
N=$(grep -cv '^\s*$' "$MF")
DUR=$(python3 -c "print(round($TOTAL/$N,3))")
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
i=0
esc(){ printf '%s' "$1" | sed "s/'/’/g; s/:/\\\\:/g; s/%/\\\\%/g"; }
while IFS='|' read -r type src focus text ss; do
  SS="${ss:-0}"
  [ -z "${type// }" ] && continue
  i=$((i+1)); seg="$TMP/seg$i.mp4"
  TXT="$(esc "$text")"; TXT="$(printf '%b' "$TXT")"   # \n -> real newline
  FS=$(python3 -c "
import sys
lines=(sys.argv[1] or ' ').split(chr(10))
L=max(len(l) for l in lines)
print(min(68,max(42,int(1650/max(L,1)))))" "$TXT")
  if [ "$type" = photo ]; then
    srcpng="$src"
    case "$src" in *.HEIC|*.heic|*.JPG|*.jpg|*.jpeg)
      sips -s format jpeg "$src" --out "$TMP/p$i.jpg" >/dev/null
      python3 -c "from PIL import Image, ImageOps; ImageOps.exif_transpose(Image.open('$TMP/p$i.jpg')).save('$TMP/p$i.png')"
      srcpng="$TMP/p$i.png";; esac
    DRAW=""; [ -n "$text" ] && DRAW=",drawtext=fontfile=$FONT:text='$TXT':fontsize=$((FS>64?64:FS)):fontcolor=white:line_spacing=14:text_align=center:x=(w-text_w)/2:y='h*0.16-14*min(1\,t/0.3)':alpha='min(1\,t/0.28)':box=1:boxcolor=black@0.35:boxborderw=16:shadowcolor=black@0.5:shadowx=0:shadowy=2"
    ffmpeg -nostdin -y -v error -framerate $FPS -loop 1 -t "$DUR" -i "$srcpng" -filter_complex \
      "[0:v]scale=$W:-1,pad=$W:$H:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='min(1.06\,1+0.0006*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=$FPS$DRAW,format=yuv420p,fps=$FPS" \
      -t "$DUR" -c:v libx264 -crf 17 -preset fast -an "$seg"
  else
    case "$focus" in left) X=0;; right) X="iw-ow";; *) X="(iw-ow)/2";; esac
    DRAW=""; [ -n "$text" ] && DRAW=",drawtext=fontfile=$FONT:text='$TXT':fontsize=$FS:fontcolor=white:line_spacing=14:text_align=center:x=(w-text_w)/2:y='h*0.54-14*min(1\,t/0.3)':alpha='min(1\,t/0.28)':shadowcolor=black@0.55:shadowx=0:shadowy=3"
    ffmpeg -nostdin -y -v error -ss "$SS" -t "$DUR" -i "$src" -filter_complex \
      "[0:v]scale=-1:$((H+80)),crop='min(iw,ih*9/16)':ih:$X:0,scale=$W:$H,eq=contrast=1.04:saturation=1.10,vignette=PI/5.5$DRAW,format=yuv420p,fps=$FPS" \
      -t "$DUR" -c:v libx264 -crf 17 -preset fast -an "$seg"
  fi
  echo "file '$seg'" >> "$TMP/list.txt"
  echo "[scene $i/$N] $type $(basename "$src") ${DUR}s ${text:+\"${text:0:40}\"}"
done < "$MF"
ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart -an "$OUT"
echo "[receipt-reel] → $OUT ($(python3 -c "print($N)") scenes, ${TOTAL}s, silent — attach audio in the IG composer)"
