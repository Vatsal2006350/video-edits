#!/bin/bash
# Travel story reel: quiet opening line, then a beat-cut montage.
# Format after @swayamj.joshi (IG DcA6l7eMTK-): milestone line -> "since then I travelled" montage.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
B="$HOME/Downloads/photos-broll"
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/travel"
rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/travel_reel.mp4}"
AUDIO="${AUDIO:-$HOME/Downloads/music-rf/travel_trend.mp3}"
AUDIO_SS="${AUDIO_SS:-0}"
OPEN_D="${OPEN_D:-2.50}"
L1="${L1-2 years ago i moved}"; L2="${L2-to the us for my bachelors}"
E1="${E1-make the most}"; E2="${E2-of the one you get}"
DUR="${DUR:-14.05}"
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30
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

# open|clip|seek   then  montage rows "clip|seek|cut_out"  (cut_out = beat from bin/beats.py)
OPEN="${OPEN:-$B/aura-new/0614_120534_video-6838_singular_display.mov.mov|1.2}"
SHOTS="${SHOTS:-$B/aura-new/0618_140349_IMG_2447.MOV.MOV|1.0|3.181
$B/aura-new/0614_113007_video-6811_singular_display.mov.mov|2.0|4.040
$B/aura-new/0614_124437_IMG_2297.MOV.MOV|1.5|5.364
$B/aura-new/0618_140154_IMG_2442.MOV.MOV|1.0|5.921
$B/kerala-scenic/0820_171934_IMG_4332.MOV.MOV|1.0|6.780
$B/kerala-scenic/0820_182543_IMG_4392.MOV.MOV|1.0|8.057
$B/kerala-scenic/0820_182523_IMG_4391.MOV.MOV|1.6|8.777
$B/broll/0522_192342_video-4382_singular_display.mov.mov|6.0|9.752
$B/broll/0523_182630_video-4501_singular_display.mov.mov|2.0|10.704
$B/broll/0606_175232_IMG_1863.MOV.MOV|3.6|11.587
$B/broll/0523_182647_video-4503_singular_display.mov.mov|2.0|12.446
$B/broll/0523_185029_IMG_1003.MOV.MOV|3.0|14.05}"

echo "[1/4] opening line 0 -> 2.50s"
python3 "$ROOT/bin/hero-type.py" "{\"dur\":${OPEN_D},\"face\":\"$ROOT/fonts/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":112,\"top\":760,\"x\":88,\"lead\":1.10,\"fade\":0.26,\"shadow\":0.9,\"scrim\":${SCRIM:-0.34},\"ghost\":${GHOST:-0.52},\"lines\":[{\"t\":\"${L1}\",\"at\":0.10},{\"t\":\"${L2}\",\"at\":0.85}],\"outdir\":\"$W/t_open\"}" >/dev/null
IFS='|' read -r osrc oss ostab <<< "$OPEN"
OPRE="$(source_vf "$osrc"),scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
if [ "${ostab:-0}" = "1" ]; then
  ffmpeg -nostdin -v error -ss "$oss" -t "$OPEN_D" -i "$osrc" -vf "$OPRE,vidstabdetect=shakiness=9:accuracy=15:result=$W/op.trf" -f null - 2>/dev/null
  OPRE="$OPRE,vidstabtransform=input=$W/op.trf:smoothing=24:zoom=3:optzoom=1:interpol=bicubic,unsharp=5:5:0.5"
fi
ffmpeg -nostdin -v error -ss "$oss" -t "$OPEN_D" -i "$osrc" -framerate 30 -i "$W/t_open/h_%04d.png" \
  -filter_complex "[0:v]${OPRE},fps=30[bg];[bg][1:v]overlay=0:0:shortest=1[v]" \
  -map "[v]" -an "${enc[@]}" "$W/s000.mp4" -y

echo "[2/4] montage"
prev="$OPEN_D"; i=1
while IFS='|' read -r src ss cut stab; do
  [ -z "$src" ] && continue
  d=$(python3 -c "print(f'{float('$cut')-float('$prev'):.3f}')"); n=$(printf "s%03d" $i)
  PRE="$(source_vf "$src"),scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
  printf "    %6.2f -> %6.2f  (%4.2fs)  %s\n" "$prev" "$cut" "$d" "$(basename "$src")"
  if [ "${stab:-0}" = "1" ]; then
    # two-pass stabilisation, then a slight zoom so the warped edges stay off-frame
    ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
      -vf "$PRE,vidstabdetect=shakiness=9:accuracy=15:result=$W/$n.trf" -f null - 2>/dev/null
    ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
      -vf "$PRE,vidstabtransform=input=$W/$n.trf:smoothing=24:zoom=3:optzoom=1:interpol=bicubic,unsharp=5:5:0.5,fps=30" \
      -an "${enc[@]}" "$W/$n.mp4" -y
  else
    ffmpeg -nostdin -v error -ss "$ss" -t "$d" -i "$src" \
      -vf "$PRE,fps=30" \
      -an "${enc[@]}" "$W/$n.mp4" -y
  fi
  prev="$cut"; i=$((i+1))
done <<< "$SHOTS"

echo "[3/4] closing line"
LASTD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$(ls "$W"/s0*.mp4 | tail -1)")
python3 "$ROOT/bin/hero-type.py" "{\"dur\":${LASTD},\"face\":\"$ROOT/fonts/AvenirNext-Regular.ttf\",\"face_index\":0,\"size\":104,\"top\":800,\"x\":88,\"lead\":1.10,\"fade\":0.28,\"shadow\":0.9,\"scrim\":${SCRIM:-0.34},\"ghost\":${GHOST:-0.52},\"lines\":[{\"t\":\"${E1}\",\"at\":0.05},{\"t\":\"${E2}\",\"at\":0.55}],\"outdir\":\"$W/t_end\"}" >/dev/null
LAST=$(ls "$W"/s0*.mp4 | tail -1)
ffmpeg -nostdin -v error -i "$LAST" -framerate 30 -i "$W/t_end/h_%04d.png" \
  -filter_complex "[0:v]fps=30[bg];[bg][1:v]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/last.mp4" -y
mv "$W/last.mp4" "$LAST"

echo "[4/4] join + music"
for f in "$W"/s0*.mp4; do printf "file '%s'\n" "$f"; done > "$W/l.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/l.txt" -ss "$AUDIO_SS" -i "$AUDIO" \
  -filter_complex "[1:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-0.45}'):d=0.45,loudnorm=I=-13:TP=-1.0:LRA=11[a]" \
  -map 0:v -map "[a]" -t "$DUR" "${enc[@]}" -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
