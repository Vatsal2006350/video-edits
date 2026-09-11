#!/bin/bash
# MUST RUN IN Terminal.app (Apple's). Claude's shell and other terminals are denied
# Photos access -- see anthropics/claude-code#55345 (closed as not planned).
set -uo pipefail
D="$HOME/Downloads/photos-broll/purple"; mkdir -p "$D/transcripts"
U="$HOME/Code/video-edits/uuids/purple.txt"

echo "running as: $(ps -o comm= -p $PPID 2>/dev/null)"
echo "=== downloading 6 clips (2.9 GB) from Photos"
uvx --from osxphotos osxphotos export "$D" --uuid-from-file "$U" \
  --download-missing --use-photokit --skip-original-if-edited --retry 2 2>&1 | tail -20

N=$(find "$D" -maxdepth 1 -type f -iname '*.MOV' | wc -l | tr -d ' ')
echo
echo "on disk: $N of 6"
if [ "$N" = "0" ]; then
  echo
  echo "*** NOTHING DOWNLOADED ***"
  echo "If the error above says 'could not get authorization', you are not in Terminal.app."
  echo "Open Spotlight, type Terminal, run this again there, and click Allow on the dialog."
  exit 1
fi

echo
echo "=== transcribing"
for f in "$D"/*.MOV; do
  [ -f "$f" ] || continue
  b=$(basename "$f"); t="$D/transcripts/${b%.*}.txt"
  [ -s "$t" ] && continue
  ffmpeg -nostdin -v error -i "$f" -vn -ac 1 -ar 16000 /tmp/_p.wav -y 2>/dev/null || continue
  ( cd /tmp && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
      --output-dir /tmp --output-format txt _p.wav >/dev/null 2>&1 )
  [ -f /tmp/_p.txt ] && mv /tmp/_p.txt "$t" && echo "  $b"
done

echo
echo "=== what each clip says"
for t in "$D"/transcripts/*.txt; do
  [ -f "$t" ] || continue
  echo "--- $(basename "$t" .txt)"
  head -c 260 "$t" | tr '\n' ' '; echo; echo
done
echo "DONE -- tell Claude."
