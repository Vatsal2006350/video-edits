#!/bin/bash
# MUST RUN IN Terminal.app. Fetches the DM-inbox screen recording plus the 4 remaining
# purple-shirt clips, transcribes the talking heads, and reports which one says "DMs".
set -uo pipefail
D="$HOME/Downloads/photos-broll/purple"; mkdir -p "$D/transcripts"
echo "running under: $(ps -o comm= -p $PPID 2>/dev/null)"
echo "=== fetching 5 files (2.5 GB)"
uvx --from osxphotos osxphotos export "$D" \
  --uuid-from-file "$HOME/Code/video-edits/uuids/dm_and_purple.txt" \
  --download-missing --use-photokit --skip-original-if-edited --retry 2 2>&1 | tail -20
N=$(find "$D" -maxdepth 1 -type f \( -iname '*.MOV' -o -iname '*.mp4' \) | wc -l | tr -d ' ')
echo; echo "on disk: $N"
if [ "$N" -lt 3 ]; then
  echo "*** if you see 'could not get authorization', you are NOT in Terminal.app ***"
  exit 1
fi
echo; echo "=== transcribing talking heads"
for f in "$D"/IMG_*.MOV; do
  [ -f "$f" ] || continue
  b=$(basename "$f"); t="$D/transcripts/${b%.*}.txt"
  [ -s "$t" ] && continue
  ffmpeg -nostdin -v error -i "$f" -vn -ac 1 -ar 16000 /tmp/_d.wav -y 2>/dev/null || continue
  ( cd /tmp && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
      --output-dir /tmp --output-format txt _d.wav >/dev/null 2>&1 )
  [ -f /tmp/_d.txt ] && mv /tmp/_d.txt "$t" && echo "  $b"
done
echo; echo "=== clips mentioning DMs / messages"
grep -ril -E "\bDM|direct message|hundreds of|messages" "$D/transcripts" 2>/dev/null | while read -r m; do
  echo "  --- $(basename "$m")"
  grep -i -o -E ".{0,110}(DM|hundreds of|messages).{0,110}" "$m" | head -2 | sed 's/^/      /'
done
echo; echo "DONE -- tell Claude."
