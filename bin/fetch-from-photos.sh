#!/bin/bash
# RUN THIS IN TERMY (not from Claude).
#
# Claude's shell runs under Claude.app, and the Photos request actually comes from
# uvx's cached (unsigned) python, which macOS denies without even prompting. Termy
# already has Full Access, so running it there just works.
#
#   bash ~/Code/video-edits/bin/fetch-from-photos.sh
#
# Pulls the three sets that are currently blocked, then transcribes the talking heads
# and reports which one is about clubs.
set -uo pipefail
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
mkdir -p "$S"
B="$HOME/Downloads/photos-broll"
OSX=(uvx --from osxphotos osxphotos)

grab () {  # grab <uuid-file> <dest> <label>
  local uf="$1" dest="$2" label="$3"
  [ -s "$uf" ] || { echo "!! missing $uf"; return; }
  mkdir -p "$dest"
  echo
  echo "=== $label  ($(wc -l < "$uf" | tr -d ' ') clips) -> $dest"
  "${OSX[@]}" export "$dest" --uuid-from-file "$uf" --download-missing --use-photokit \
      --skip-original-if-edited --retry 2 2>&1 | tail -3
  echo "    now on disk: $(find "$dest" -type f \( -iname '*.mov' -o -iname '*.mp4' \) | wc -l | tr -d ' ')"
}

grab "$S/bom_uuids.txt"        "$B/bom"         "BOM Terminal 2 + Dubai airport, 26 Aug"
grab "$S/uuids.txt"            "$B/travel2"     "Ladakh / Maldives / Kerala / Dubai / SF / NY"
grab "$HOME/Code/video-edits/talkhead_uuids.txt" "$B/talk-search" "May-June talking heads"

echo
echo "=== transcribing talking heads to find the clubs one"
mkdir -p "$B/talk-search/transcripts"
n=0
for f in "$B"/talk-search/*.MOV "$B"/talk-search/*.mov "$B"/talk-search/*.mp4 "$B"/talk-search/*.MP4; do
  [ -f "$f" ] || continue
  b=$(basename "$f"); t="$B/talk-search/transcripts/${b%.*}.txt"
  [ -s "$t" ] && continue
  ffmpeg -nostdin -v error -i "$f" -vn -ac 1 -ar 16000 /tmp/_fc.wav -y 2>/dev/null || continue
  ( cd /tmp && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
      --output-dir /tmp --output-format txt _fc.wav >/dev/null 2>&1 )
  [ -f /tmp/_fc.txt ] && mv /tmp/_fc.txt "$t" && n=$((n+1)) && printf '.'
done
echo
echo "    transcribed $n"

echo
echo "=== clips that talk about clubs / societies / extracurriculars"
grep -ril -E "club|societ|extracurric|frat" "$B/talk-search/transcripts" 2>/dev/null | while read -r m; do
  echo "  --- $(basename "$m")"
  grep -i -o -E ".{0,100}(club|societ|extracurric|frat).{0,100}" "$m" | head -2 | sed 's/^/      /'
done
echo
echo "ALL DONE -- tell Claude it finished and it will build the reels."
