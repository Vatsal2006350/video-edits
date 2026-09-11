#!/usr/bin/env bash
# Slow opener, then hard-cut bounce between shots, one caption held the whole time.
# Decoded from IG DdHB2auJ5Fd ("My daily routine") + DblxlZ1TzCV (slower desk open).
#
#   SHOTS="path|seek|dur
#          path|seek|dur"
#   L1="switching between guitar" L2="and accepting on claude"
#   AUDIO=track.mp3 AUDIO_SS=0
#   OUT=... bash bin/bounce-reel.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/bounce"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:?set OUT}"
AUDIO="${AUDIO:?set AUDIO}"
AUDIO_SS="${AUDIO_SS:-0}"
L1="${L1:?set L1}"
L2="${L2-}"
FACE="${FACE:-$ROOT/fonts/PlayfairDisplay-BlackItalic.ttf}"
TOP="${TOP:-292}"
SIZE="${SIZE:-92}"
enc=(-c:v libx264 -crf 15 -preset slow -pix_fmt yuv420p -r 30
  -color_primaries bt709 -color_trc bt709 -colorspace bt709
  -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1)

source_vf () {
  local src=$1 transfer
  transfer=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=color_transfer -of default=nw=1:nk=1 "$src" \
    | head -n 1 | tr -d '\r,' | xargs)
  case "$transfer" in
    arib-std-b67|smpte2084)
      printf '%s' 'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'
      ;;
    *) printf '%s' 'format=yuv420p' ;;
  esac
}

python3 - "$W/caption.png" "$FACE" "$L1" "$L2" "$TOP" "$SIZE" <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
out, face, l1, l2, top, size = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
W, H = 1080, 1920
# centred text is bounded by 724px (2*(918-540)), not the full safe-box width
MAXW = 724
im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
lines = [l1] + ([l2] if l2 else [])
sz = size
while sz > 28:
    fonts = []
    widths = []
    for i, line in enumerate(lines):
        f = ImageFont.truetype(face, sz)
        fonts.append(f)
        widths.append(f.getbbox(line)[2] - f.getbbox(line)[0])
    if max(widths) <= MAXW:
        break
    sz -= 2
# soft scrim behind the block so white italic reads on a bright airport window
y0 = top - 70
y1 = top + (len(lines) * int(sz * 1.15)) + 80
scrim = Image.new('L', (1, H), 0)
px = scrim.load()
mid = (y0 + y1) / 2
half = max(1, (y1 - y0) / 2) * 2.6
import math
for y in range(H):
    d = abs(y - mid) / half
    px[0, y] = 0 if d >= 1 else int(140 * 0.5 * (1 + math.cos(math.pi * d)))
mask = scrim.resize((W, H)).filter(ImageFilter.GaussianBlur(36))
sc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sc.putalpha(mask)
im = Image.alpha_composite(im, sc)
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
ds = ImageDraw.Draw(sh)
y = top
for i, line in enumerate(lines):
    f = fonts[i]
    bb = f.getbbox(line)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2
    ds.text((x + 2, y + 4), line, font=f, fill=(0, 0, 0, 210))
    d.text((x, y), line, font=f, fill=(255, 255, 255, 255))
    y += int(sz * 1.18)
im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), im)
im.save(out)
print(f'caption {sz}px -> {out}')
PY

: > "$W/l.txt"
i=0
t0=0
while IFS='|' read -r src ss dur zoom; do
  [ -z "${src:-}" ] && continue
  i=$((i+1)); n=$(printf 's%02d' "$i")
  PRE="$(source_vf "$src"),scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.08:brightness=-0.02"
  if [ "${zoom:-0}" = "1" ]; then
    PRE="$PRE,scale=1188:2112,crop=1080:1920"
  fi
  printf '  %5.2f -> %5.2f  (%4.2fs)%s  %s @%s\n' "$t0" "$(python3 -c "print(round($t0+$dur,2))")" "$dur" \
    "$( [ "${zoom:-0}" = 1 ] && echo ' DROP' )" "$(basename "$src")" "$ss"
  ffmpeg -nostdin -y -v error -ss "$ss" -t "$dur" -i "$src" \
    -vf "$PRE,fps=30" -an "${enc[@]}" "$W/$n.mp4"
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/l.txt"
  t0=$(python3 -c "print(round($t0+$dur, 3))")
done <<< "$SHOTS"
DUR="$t0"

ffmpeg -nostdin -y -v error -f concat -safe 0 -i "$W/l.txt" \
  -loop 1 -framerate 30 -t "$DUR" -i "$W/caption.png" \
  -filter_complex "[1:v]fade=t=in:st=0:d=0.22:alpha=1,format=rgba[cap];[0:v][cap]overlay=0:0:format=auto:shortest=1[v]" \
  -map '[v]' -an "${enc[@]}" "$W/pic.mp4"

ffmpeg -nostdin -y -v error -i "$W/pic.mp4" -ss "$AUDIO_SS" -t "$DUR" -i "$AUDIO" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy \
  -af "aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.04,afade=t=out:st=$(python3 -c "print(max(0,$DUR-0.35))"):d=0.35,alimiter=limit=0.78" \
  -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart -shortest "$OUT"
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
