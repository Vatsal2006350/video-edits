#!/bin/bash
# RUN IN Terminal.app.  Uses a STABLE venv (~/Code/video-edits/.photoenv) instead of uvx,
# so the binary path never changes and the Photos permission only has to be granted once.
#   photos-fetch.sh <uuid-file> <dest-dir>
set -uo pipefail
OSX="$HOME/Code/video-edits/.photoenv/bin/osxphotos"
U="${1:?uuid file}"; D="${2:?dest dir}"; mkdir -p "$D/transcripts"
[ -x "$OSX" ] || { echo "missing $OSX"; exit 1; }
echo "binary: $OSX"
echo "=== fetching $(grep -c . "$U") files"
"$OSX" export "$D" --uuid-from-file "$U" --download-missing --use-photokit \
  --skip-original-if-edited --retry 2 2>&1 | tail -20
N=$(find "$D" -maxdepth 1 -type f \( -iname '*.MOV' -o -iname '*.mp4' \) | wc -l | tr -d ' ')
echo; echo "on disk: $N"
[ "$N" = "0" ] && { echo "*** still denied -- click Allow on the dialog, then re-run ***"; exit 1; }
echo; echo "=== transcribing talking heads"
for f in "$D"/IMG_*.MOV "$D"/*.mp4; do
  [ -f "$f" ] || continue
  case "$(basename "$f")" in ScreenRecording*) continue;; esac
  b=$(basename "$f"); t="$D/transcripts/${b%.*}.txt"
  [ -s "$t" ] && continue
  ffmpeg -nostdin -v error -i "$f" -vn -ac 1 -ar 16000 /tmp/_pf.wav -y 2>/dev/null || continue
  ( cd /tmp && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
      --output-dir /tmp --output-format txt _pf.wav >/dev/null 2>&1 )
  [ -f /tmp/_pf.txt ] && mv /tmp/_pf.txt "$t" && echo "  $b"
done
echo; echo "=== transcripts"
for t in "$D"/transcripts/*.txt; do
  [ -f "$t" ] || continue
  echo "--- $(basename "$t" .txt)"; head -c 240 "$t" | tr '\n' ' '; echo; echo
done
echo "DONE -- tell Claude."
