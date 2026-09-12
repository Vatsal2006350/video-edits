#!/usr/bin/env bash
# yc-diverse-reel.sh <professional|bad-dream|opportunity|tradeoff> <out.mp4>
# Four visually distinct YC-first reels built only from first-party footage/proof.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIND="${1:?variant}"; OUT="${2:?output}"
FONT="$ROOT/fonts/Montserrat-Bold.ttf"
AUDIO_DIR="/Users/vatsalshah/Downloads/ig-trend-audio/2026-09-11"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$(dirname "$OUT")"

case "$KIND" in
  professional)
    AUDIO="$AUDIO_DIR/DaBDpRjMUZp.mp3"; AUDIO_SS=0; TOTAL=13.90
    SCENES=(
      "video|$ROOT/0820/source.mp4|12.0|3.30|when you're a college sophomore"
      "video|$ROOT/0820/source.mp4|30.0|3.11|but you're also..."
      "photo|$ROOT/receipts/yc_fullbleed.jpg|0|3.00|"
      "photo|$ROOT/logos/jachacks/umich_winners.png|0|4.49|organized a 180+ person hackathon"
    );;
  bad-dream)
    AUDIO="$AUDIO_DIR/DbpuhiDv3UZ.mp3"; AUDIO_SS=0; TOTAL=7.20
    SCENES=(
      "photo|$ROOT/receipts/before_portrait.jpg|0|0.90|they called it delusion"
      "photo|$ROOT/receipts/yc_fullbleed.jpg|0|2.30|"
      "video|$ROOT/0820/source.mp4|30.0|2.00|I called it the plan"
      "video|$ROOT/0820/source.mp4|40.0|2.00|still building"
    );;
  opportunity)
    # Start later in the archived sound so its 8.48s impact lands at 4.50s.
    AUDIO="$AUDIO_DIR/DcJkva7turE.mp3"; AUDIO_SS=3.98; TOTAL=6.00
    SCENES=(
      "video|$ROOT/0820/source.mp4|30.0|2.50|when opportunity calls"
      "video|$ROOT/0820/source.mp4|40.0|2.00|you pick up"
      "photo|$ROOT/receipts/yc_fullbleed.jpg|0|1.50|"
    );;
  tradeoff)
    AUDIO="$AUDIO_DIR/DcA1vxCBLVH.mp3"; AUDIO_SS=0; TOTAL=9.30
    SCENES=(
      "video|$ROOT/0820/source.mp4|12.0|2.20|less of a normal college life"
      "video|$ROOT/0820/source.mp4|34.0|2.21|more of this..."
      "photo|$ROOT/receipts/yc_fullbleed.jpg|0|2.50|"
      "video|$ROOT/0820/source.mp4|40.0|2.39|worth it."
    );;
  *) echo "unknown variant: $KIND" >&2; exit 2;;
esac

escape_text() { printf '%s' "$1" | sed "s/'/’/g; s/:/\\\\:/g; s/%/\\\\%/g"; }
i=0
for row in "${SCENES[@]}"; do
  IFS='|' read -r TYPE SRC SS DUR TEXT <<< "$row"
  i=$((i+1)); SEG="$TMP/seg-$i.mp4"; TXT="$(escape_text "$TEXT")"
  DRAW=""
  if [ -n "$TEXT" ]; then
    DRAW=",drawtext=fontfile='$FONT':text='$TXT':fontsize=58:fontcolor=white:borderw=3:bordercolor=black@0.74:shadowcolor=black@0.65:shadowy=4:x=(w-text_w)/2:y=285"
  fi
  if [ "$TYPE" = video ]; then
    ffmpeg -nostdin -y -v error -ss "$SS" -t "$DUR" -i "$SRC" \
      -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30${DRAW},format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
      -t "$DUR" -an -c:v libx264 -crf 17 -preset fast "$SEG"
  else
    ffmpeg -nostdin -y -v error -loop 1 -t "$DUR" -i "$SRC" \
      -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30${DRAW},format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
      -t "$DUR" -an -c:v libx264 -crf 17 -preset fast "$SEG"
  fi
  printf "file '%s'\n" "$SEG" >> "$TMP/list.txt"
done

ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$TMP/list.txt" \
  -ss "$AUDIO_SS" -t "$TOTAL" -i "$AUDIO" -map 0:v:0 -map 1:a:0 -t "$TOTAL" \
  -af "aresample=44100:async=1,loudnorm=I=-14:TP=-2:LRA=11,afade=t=out:st=$(awk "BEGIN{print $TOTAL-0.16}"):d=0.16" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.0 -pix_fmt yuv420p -r 30 -g 60 \
  -c:a aac -b:a 160k -ar 44100 -ac 2 -movflags +faststart "$OUT"
echo "[$KIND] $OUT"
