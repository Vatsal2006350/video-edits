#!/bin/bash
# "N things I did at N" — the dara.miao format (reel Dbt1qCpvcd_).
#
# One achievement per beat: a photo or clip of the thing, with a short line naming it.
# The hook is held over the opening shot, the list runs on the beat grid, and the final
# card lands ON the drop. That timing is the whole format -- the list has to feel relentless
# and then stop.
#
#   HOOK   = "line 1|line 2"          held over the opening shot
#   OPEN   = "path|seek"              the opening shot
#   ITEMS  = "path|seek|text|logo.png|cy|logo_y"  one per line (last three optional)
#   FINAL  = "path|seek|text"         lands on the drop
#   BEATS  = comma-separated cut times (from bin/beats.py); ITEMS are assigned in order
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; F="$ROOT/fonts"
source "$ROOT/bin/lib-still.sh"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/listreel"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/list_reel.mp4}"
AUDIO="${AUDIO:-$HOME/Downloads/music-good/hell_of_a_year.mp3}"
DUR="${DUR:-18.44}"; DROP="${DROP:-16.09}"; HOOK_T="${HOOK_T:-1.70}"
# still_black_vf = plain black bars; still_vf = blurred backdrop
STILL_MODE="${STILL_MODE:-still_vf}"
SIZE="${SIZE:-64}"; CY="${CY:-1180}"
# the payoff card sits lower so it clears a letterboxed photo instead of covering it
FINAL_SIZE="${FINAL_SIZE:-84}"; FINAL_CY="${FINAL_CY:-1430}"
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)

shot () { # shot <src> <seek> <dur> <out>
  local src="$1" ss="$2" d="$3" out="$4"
  local lower; lower=$(printf %s "$src" | tr "[:upper:]" "[:lower:]")
  case "$lower" in
    *.jpg|*.jpeg|*.png|*.heic)
      ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$d" -i "$src" \
        -vf "$(${STILL_MODE:-still_vf} 1080 1920 0.0022 1.10)" -frames:v "$(awk -v d=$d 'BEGIN{printf "%d", d*30}')" \
        -an "${enc[@]}" "$out" -y ;;
    *)
      ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
        -an "${enc[@]}" "$out" -y ;;
  esac
}

# text card: no scrim box -- see bin/list-label.py for why
label () { # label <text> <out.png>   (LOGO=path optional)
  python3 "$ROOT/bin/list-label.py" "$1" "$2" "$SIZE" "$CY" "$F" "${LOGO:-}" "${LOGO_Y:-}"
}

IFS=',' read -ra BT <<< "$BEATS"
prev=0; i=0; : > "$W/l.txt"

# opening shot with the hook held over it
IFS='|' read -r osrc oss <<< "$OPEN"
shot "$osrc" "${oss:-0}" "$HOOK_T" "$W/s000.mp4"
IFS='|' read -r h1 h2 <<< "$HOOK"
python3 "$ROOT/bin/hero-type.py" "{\"dur\":${HOOK_T},\"face\":\"$F/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":${HOOK_SIZE:-84},\"top\":${HOOK_TOP:-1040},\"x\":88,\"lead\":1.14,\"fade\":${HOOK_FADE:-0.30},\"shadow\":0.95,\"scrim\":0.34,\"ghost\":${HOOK_GHOST:-0.92},\"lines\":[{\"t\":\"${h1}\",\"at\":0.02},{\"t\":\"${h2}\",\"at\":${HOOK_AT2:-0.26}}],\"outdir\":\"$W/hook\"}" >/dev/null
ffmpeg -nostdin -v error -i "$W/s000.mp4" -framerate 30 -i "$W/hook/h_%04d.png" \
  -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/o.mp4" -y
mv "$W/o.mp4" "$W/s000.mp4"; printf "file '%s'\n" "$W/s000.mp4" >> "$W/l.txt"
prev="$HOOK_T"

while IFS='|' read -r src ss text ilogo icy ilogoy; do
  [ -z "$src" ] && continue
  cut="${BT[$i]:-}"; i=$((i+1))
  [ -z "$cut" ] && { echo "!! ran out of beats at item $i"; break; }
  d=$(awk -v a="$cut" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
  [ "$(awk -v d=$d 'BEGIN{print (d<=0.08)}')" = 1 ] && continue
  n=$(printf "s%03d" $i)
  shot "$src" "${ss:-0}" "$d" "$W/$n.mp4"
  # a per-item CY lets a caption dodge text already burned into the source image
  LOGO="${ilogo:-}" CY="${icy:-$CY}" LOGO_Y="${ilogoy:-}" label "$text" "$W/$n.png"
  ffmpeg -nostdin -v error -i "$W/$n.mp4" -i "$W/$n.png" \
    -filter_complex "[0:v][1:v]overlay=0:0,fps=30[v]" -map "[v]" -an "${enc[@]}" "$W/${n}t.mp4" -y
  mv "$W/${n}t.mp4" "$W/$n.mp4"
  printf "file '%s'\n" "$W/$n.mp4" >> "$W/l.txt"
  printf "  %5.2f->%5.2f  %s\n" "$prev" "$cut" "$text"
  prev="$cut"
done <<< "$ITEMS"

# the final card lands on the drop and holds to the end
IFS='|' read -r fsrc fss ftext <<< "$FINAL"
fd=$(awk -v a="$DUR" -v b="$prev" 'BEGIN{printf "%.3f", a-b}')
shot "$fsrc" "${fss:-0}" "$fd" "$W/z.mp4"
# An empty FINAL text means the payoff image carries the drop on its own -- often stronger
# than a closing line, which tends to read as a caption on something already obvious.
if [ -n "${ftext// /}" ]; then
  SIZE="$FINAL_SIZE" CY="$FINAL_CY" label "$ftext" "$W/z.png"
  ffmpeg -nostdin -v error -i "$W/z.mp4" -i "$W/z.png" \
    -filter_complex "[0:v][1:v]overlay=0:0,fps=30[v]" -map "[v]" -an "${enc[@]}" "$W/zt.mp4" -y
  mv "$W/zt.mp4" "$W/z.mp4"
fi
printf "file '%s'\n" "$W/z.mp4" >> "$W/l.txt"
echo "  final ${prev}->${DUR}  ${ftext}"

ffmpeg -v error -f concat -safe 0 -i "$W/l.txt" -i "$AUDIO" \
  -filter_complex "[1:a]atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-0.5}'):d=0.5,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -t "$DUR" "${enc[@]}" -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
