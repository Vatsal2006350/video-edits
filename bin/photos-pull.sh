#!/usr/bin/env bash
# Pull iCloud originals from Photos with no manual step: runs bin/photos-fetch.sh inside
# Terminal.app (which already holds the Photos permission) via a .command file, waits for
# it, and prints the log. Claude's own process cannot get Photos access; Terminal can.
#   bin/photos-pull.sh <uuid-file> <dest-dir> [timeout_s=1800]
# Denylisted UUIDs are refused. Transcription is skipped (do it afterwards).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
U="${1:?uuid file}"; D="${2:?dest dir}"; T="${3:-1800}"
mkdir -p "$D"
while read -r id; do [ -z "$id" ] && continue
  if grep -qi "$id" "$ROOT/FOOTAGE-DENYLIST.md"; then echo "DENYLISTED $id" >&2; exit 3; fi
done < "$U"
U="$(cd "$(dirname "$U")" && pwd)/$(basename "$U")"; D="$(cd "$D" && pwd)"
CMD="$D/.pull.command"; DONE="$D/.pull.done"; rm -f "$DONE"
cat > "$CMD" <<EOS
#!/bin/bash
PHOTOS_FETCH_TRANSCRIBE=0 "$ROOT/bin/photos-fetch.sh" "$U" "$D"
echo \$? > "$DONE"
osascript -e 'tell application "Terminal" to close (every window whose name contains ".pull.command")' >/dev/null 2>&1
EOS
chmod +x "$CMD"
open -a Terminal "$CMD"
echo "running in Terminal.app ... (waiting up to ${T}s)"
for ((i=0;i<T;i+=3)); do [ -f "$DONE" ] && break; sleep 3; done
[ -f "$DONE" ] || { echo "timeout; still running, see $D/photos-fetch.log"; exit 4; }
tail -8 "$D/photos-fetch.log"; echo "exit $(cat "$DONE")"; ls -la "$D" | grep -i -E "mov|mp4"
