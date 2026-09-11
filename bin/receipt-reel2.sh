#!/usr/bin/env bash
# receipt-reel2.sh <manifest> <out.mp4> [total_dur]
# The "meme hook -> receipts" format, matched to the 2026-09-06 viral (Dc8vZ0gOMF5):
#   photos on BLACK bars (fit to width, centred), no blurred glass; text = Montserrat Bold ~61px, white, soft shadow,
#   no box; receipt text block top at y=406 (in the top bar), hook text centred at 42% height over video.
# Manifest, one scene per line:   type|src|focus|text|ss|dur|tat   (tat = delay before the text appears, s)
#   type video|photo · focus left|center|right (landscape video crop anchor) · text (\n = line break, empty = none)
#   ss = seek into the source (s) · dur = this scene's length (s); scenes without dur share what is left of total_dur.
# AUDIO="path.mp3" AUDIO_SS=31.56  burns a music cut (the Wishes 10.912s cut: drop 40.36 -> 8.80 like the viral).
# Output: 1080x1920 30fps; if AUDIO is set the file is Instagram-spec (stereo 44.1k, -2 dBTP, level 4.0, no edit lists).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MF="${1:?manifest}"; OUT="${2:?out.mp4}"; TOTAL="${3:-10.912}"
FONT="$WS/fonts/Montserrat-Bold.ttf"; W=1080; H=1920; FPS=30
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
esc(){ printf '%s' "$1" | sed "s/'/’/g; s/:/\\\\:/g; s/%/\\\\%/g"; }
# durations: fixed ones first, the rest share the remainder
python3 - "$MF" "$TOTAL" > "$TMP/durs.txt" <<'PY'
import sys
rows=[l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]; total=float(sys.argv[2])
fixed=[float(r.split('|')[5]) if len(r.split('|'))>5 and r.split('|')[5].strip() else None for r in rows]
free=[i for i,d in enumerate(fixed) if d is None]; rem=total-sum(d for d in fixed if d)
for i,d in enumerate(fixed): print(round(d if d is not None else rem/max(1,len(free)),3))
PY
i=0
while IFS='|' read -r type src focus text ss dur tat; do
  [ -z "${type// }" ] && continue
  i=$((i+1)); seg="$TMP/seg$i.mp4"; DUR=$(sed -n "${i}p" "$TMP/durs.txt"); SS="${ss:-0}"; TAT="${tat:-0}"
  TXT="$(esc "$text")"; TXT="$(printf '%b' "$TXT")"
  FS=$(python3 - "$TXT" "$FONT" <<'PY'
import sys
from PIL import ImageFont
lines=(sys.argv[1] or ' ').split('\n'); sz=61
while sz>36:
    f=ImageFont.truetype(sys.argv[2],sz)
    if max(f.getlength(l) for l in lines)<=900: break
    sz-=2
print(sz)
PY
)
  if [ "$type" = photo ]; then
    srcpng="$src"
    case "$src" in *.HEIC|*.heic|*.JPG|*.jpg|*.jpeg)
      sips -s format jpeg "$src" --out "$TMP/p$i.jpg" >/dev/null
      python3 -c "from PIL import Image, ImageOps; ImageOps.exif_transpose(Image.open('$TMP/p$i.jpg')).save('$TMP/p$i.png')"; srcpng="$TMP/p$i.png";; esac
    DRAW=""; [ -n "$text" ] && DRAW=",drawtext=fontfile=$FONT:text='$TXT':fontsize=$FS:fontcolor=white:line_spacing=12:text_align=center:x=(w-text_w)/2:y=406:alpha='min(1\,max(0\,(t-$TAT))/0.25)':shadowcolor=black@0.6:shadowx=0:shadowy=3"
    # photo fitted to width on black, slow 3% push
    ffmpeg -nostdin -y -v error -framerate $FPS -loop 1 -t "$DUR" -i "$srcpng" -filter_complex \
      "[0:v]scale=$W:-2:flags=lanczos,pad=$W:$H:0:(oh-ih)/2:black,zoompan=z='1+0.03*on/($DUR*$FPS)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=$FPS$DRAW,format=yuv420p" \
      -t "$DUR" -c:v libx264 -crf 17 -preset fast -an "$seg"
  else
    case "$focus" in left) X=0;; right) X="iw-ow";; *) X="(iw-ow)/2";; esac
    DRAW=""; [ -n "$text" ] && DRAW=",drawtext=fontfile=$FONT:text='$TXT':fontsize=$FS:fontcolor=white:line_spacing=12:text_align=center:x=(w-text_w)/2:y=(h*0.42-text_h/2):alpha='min(1\,max(0\,(t-$TAT))/0.25)':borderw=2:bordercolor=black@0.55:shadowcolor=black@0.6:shadowx=0:shadowy=3"
    ffmpeg -nostdin -y -v error -ss "$SS" -t "$DUR" -i "$src" -filter_complex \
      "[0:v]scale=-1:$((H+80)),crop='min(iw,ih*9/16)':ih:$X:0,scale=$W:$H,eq=contrast=1.06:saturation=1.10:brightness=-0.05,vignette=PI/5$DRAW,format=yuv420p,fps=$FPS" \
      -t "$DUR" -c:v libx264 -crf 17 -preset fast -an "$seg"
  fi
  echo "file '$seg'" >> "$TMP/list.txt"
  echo "[scene $i] $type $(basename "$src") ${DUR}s ${text:+\"${text:0:44}\"}"
done < "$MF"
if [ -n "${AUDIO:-}" ]; then
  ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" -ss "${AUDIO_SS:-0}" -t "$TOTAL" -i "$AUDIO" \
    -map 0:v -map 1:a -af "aresample=44100:async=1,loudnorm=I=-14:TP=-2.0:LRA=11:linear=true,alimiter=limit=0.79:level=false" -ac 2 \
    -c:v libx264 -preset slow -profile:v high -level 4.0 -pix_fmt yuv420p -r $FPS -g 60 -keyint_min 60 -sc_threshold 0 -b:v 8000k -maxrate 9000k -bufsize 18000k \
    -c:a aac -b:a 160k -ar 44100 -movflags +faststart+negative_cts_offsets -use_editlist 0 -shortest "$OUT"
  echo "[receipt-reel2] -> $OUT (${TOTAL}s, music burned: $(basename "$AUDIO") @${AUDIO_SS:-0}, IG-spec)"
else
  ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart -an "$OUT"
  echo "[receipt-reel2] -> $OUT (${TOTAL}s, silent)"
fi
