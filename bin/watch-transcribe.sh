#!/usr/bin/env bash
# watch-transcribe.sh <dir> [outdir] [max_idle_min]
# Transcribes clips as they appear. Exits after max_idle_min with no new files.
set -uo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${1:?dir}"; OUT="${2:-$HOME/Downloads/photos-broll/transcripts}"; IDLE="${3:-90}"
mkdir -p "$OUT"
last=$(date +%s)
while :; do
  new=0
  for f in "$DIR"/*.MOV "$DIR"/*.mov "$DIR"/*.mp4; do
    [ -e "$f" ] || continue
    b=$(basename "$f"); b="${b%.*}"
    [ -f "$OUT/$b.words.json" ] && continue
    # skip files still being written
    s1=$(stat -f%z "$f" 2>/dev/null || echo 0); sleep 2
    s2=$(stat -f%z "$f" 2>/dev/null || echo 0)
    [ "$s1" != "$s2" ] && continue
    [ "$s2" -lt 100000 ] && continue
    echo "[$(date +%H:%M:%S)] transcribing $b"
    if python3 "$WS/bin/transcribe-clips.py" "$f" "$OUT" 2>&1 | tail -1 | grep -q FAILED; then
      echo '{"failed":true}' > "$OUT/$b.words.json"   # tombstone so we don't retry forever
      echo "  -> unreadable, skipping permanently"
    fi
    new=1; last=$(date +%s)
  done
  done_n=$(ls "$OUT"/*.words.json 2>/dev/null | wc -l | tr -d ' ')
  [ "$new" = 0 ] && {
    idle=$(( ($(date +%s) - last) / 60 ))
    [ "$idle" -ge "$IDLE" ] && { echo "idle ${idle}m — done. $done_n transcripts."; break; }
    sleep 20
  }
done
