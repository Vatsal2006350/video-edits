#!/bin/bash
# Find a talking-head clip by what is SAID in it.
#   find-clip.sh <uuid-file> <dest-dir> <regex>
# Exports the clips from Photos, transcribes each, and reports the ones whose speech
# matches the regex. Needs Photos access granted (System Settings > Privacy > Photos)
# because almost everything in this library is iCloud-only.
set -euo pipefail
UUIDS="${1:?uuid file}"; DEST="${2:?dest dir}"; PAT="${3:?search regex}"
mkdir -p "$DEST/transcripts"

echo "[1/3] exporting $(wc -l < "$UUIDS" | tr -d ' ') clips from Photos"
uvx --from osxphotos osxphotos export "$DEST" --uuid-from-file "$UUIDS" \
  --download-missing --use-photokit --skip-original-if-edited --retry 2 2>&1 | tail -3

N=$(find "$DEST" -maxdepth 1 -type f \( -iname '*.mov' -o -iname '*.mp4' \) | wc -l | tr -d ' ')
echo "    $N files on disk"
[ "$N" = "0" ] && { echo "    nothing exported -- grant Photos access and retry"; exit 1; }

echo "[2/3] transcribing"
for f in "$DEST"/*.MOV "$DEST"/*.mov "$DEST"/*.mp4 "$DEST"/*.MP4; do
  [ -f "$f" ] || continue
  b=$(basename "$f"); t="$DEST/transcripts/${b%.*}.txt"
  [ -s "$t" ] && continue
  ffmpeg -nostdin -v error -i "$f" -vn -ac 1 -ar 16000 "/tmp/_fc.wav" -y 2>/dev/null || continue
  ( cd /tmp && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
      --output-dir /tmp --output-format txt _fc.wav >/dev/null 2>&1 ) || continue
  [ -f /tmp/_fc.txt ] && mv /tmp/_fc.txt "$t" && echo "    $b"
done

echo "[3/3] matching /$PAT/"
grep -ril -E "$PAT" "$DEST/transcripts" 2>/dev/null | while read -r m; do
  echo "  === $(basename "$m")"
  grep -i -o -E ".{0,90}$PAT.{0,90}" "$m" | head -3 | sed 's/^/      /'
done
echo "done"
