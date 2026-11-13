#!/usr/bin/env bash
# Rebuild the supplied finished gym edit with measured, speech-synced stat typography.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$ROOT/videos/umich-gym-165m"
SOURCE="${SOURCE:?set SOURCE=/path/to/clip.mp4}"
OUT="${GYM_REEL_OUT:-$HOME/Downloads/reel-batch/umich-gym}"
# The source is intentionally pinned to the reviewed UUID/hash, not a folder scan.
actual=$(shasum -a 256 "$SOURCE" | awk '{print $1}')
if rg -qi -F "$actual" "$ROOT/FOOTAGE-DENYLIST.md" || rg -qi -F '781F2C32-82AC-474C-865D-0E26D2C116A9' "$ROOT/FOOTAGE-DENYLIST.md"; then
 echo 'Source is denylisted; refusing to stage or export.' >&2; exit 1
fi
[ "$actual" = 6a978194374206ef129ff9ff0ae0316a178c41841b4a17e49e422d64222fa43a ] || { echo 'Reviewed source hash changed; review footage and denylist before continuing.' >&2; exit 1; }
[ ! -e "$OUT/01_umich-gym-v2.mp4" ] || { echo 'Output exists; set GYM_REEL_OUT to a new directory.' >&2; exit 1; }
mkdir -p "$OUT/phone"
if [ ! -e "$PROJECT/composition/input.mp4" ]; then
 bash "$ROOT/bin/color-normalize.sh" raw "$SOURCE" "$PROJECT/normalized-full.mp4"
 ffmpeg -v error -i "$PROJECT/normalized-full.mp4" -vf 'fps=30,scale=1080:1920' -c:v libx264 -crf 16 -preset fast -g 30 -keyint_min 30 -sc_threshold 0 -an -movflags +faststart "$PROJECT/composition/input.mp4"
fi
[ -e "$PROJECT/composition/soundtrack.m4a" ] || ffmpeg -v error -i "$SOURCE" -map 0:a:0 -c:a copy "$PROJECT/composition/soundtrack.m4a"
python3 "$PROJECT/rebuild-v2-design.py"
(cd "$PROJECT/composition" && npx hyperframes@0.8.225 check . && npx hyperframes@0.8.225 render overlay-v2 -o "$PROJECT/overlay-v2.mov" --format mov --fps 30 --workers 2)
ffmpeg -v error -i "$PROJECT/composition/input.mp4" -i "$PROJECT/overlay-v2.mov" -i "$SOURCE" -filter_complex "[0:v][1:v]overlay=format=auto:shortest=1,format=yuv420p[v]" -map "[v]" -map 2:a:0 -c:v libx264 -preset slow -crf 15 -profile:v high -pix_fmt yuv420p -r 30 -fps_mode cfr -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart -t 36.416667 "$OUT/01_umich-gym-v2.mp4"
bash "$ROOT/bin/export-ig.sh" "$OUT/01_umich-gym-v2.mp4" "$OUT/01_umich-gym-v2_IG.mp4"
ffmpeg -v error -i "$OUT/01_umich-gym-v2_IG.mp4" -vf scale=608:1080 -c:v libx264 -crf 26 -preset fast -c:a aac -b:a 128k -movflags +faststart "$OUT/phone/01_umich-gym-v2.mp4"
python3 "$ROOT/bin/ig-safe.py" view "$OUT/01_umich-gym-v2_IG.mp4" "$OUT/01_umich-gym-v2-safe.jpg" 0.8 3.4 13.3 16.4 20.1 27.9 33.9
