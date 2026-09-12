#!/usr/bin/env bash
# yc-trend-variant.sh <variant> <output.mp4>
# Builds one of the September 2026 YC trend tests with locally archived audio.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VARIANT="${1:?variant: professional|friends|push}"
OUT="${2:?output mp4}"
WORK="$ROOT/.work/yc-trends"
FACE="$WORK/face-709.mp4"
YC="$ROOT/receipts/yc_fullbleed.jpg"
EVENT="$ROOT/logos/jachacks/photo_DSC06792.png"
FONT="$ROOT/fonts/Montserrat-Bold.ttf"
AUDIO_ROOT="/Users/vatsalshah/Downloads/ig-trend-audio/2026-09-11"
mkdir -p "$WORK" "$(dirname "$OUT")"

if [ ! -s "$FACE" ]; then
  ffmpeg -nostdin -y -v error -i /Users/vatsalshah/Downloads/IMG_5407.MOV \
    -map 0:v:0 -map '0:a:0?' \
    -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
    -c:v libx264 -crf 17 -preset medium -c:a aac -b:a 160k -movflags +faststart "$FACE"
fi

case "$VARIANT" in
  professional)
    AUDIO="$AUDIO_ROOT/DaBDpRjMUZp.mp3"; TOTAL=13.9; A=6.41; B=9.65
    HOOK="college sophomore, but also..."; BRIDGE=""; PAYOFF="YC founder at 18"; END="180+ builders at Michigan"
    ;;
  friends)
    AUDIO="$AUDIO_ROOT/Db3n68GqpP9.mp3"; TOTAL=8.1; A=3.35; B=6.85
    HOOK="me in class vs. me after class"; BRIDGE=""; PAYOFF="YC founder at 18"; END="same kid. different shift."
    ;;
  push)
    AUDIO="$AUDIO_ROOT/DcL57x3xuBq.mp3"; TOTAL=5.5; A=3.55; B=4.58
    HOOK="just needed one little push"; BRIDGE=""; PAYOFF="YC founder at 18"; END="at 18."
    ;;
  *) echo "unknown variant: $VARIANT" >&2; exit 2;;
esac

draw() {
  local text="$1" y="$2"
  printf ",drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=60:borderw=3:bordercolor=black@0.72:shadowcolor=black@0.7:shadowy=4:x=(w-text_w)/2:y=%s" "$FONT" "$text" "$y"
}

HOOK_DRAW="$(draw "$HOOK" 285)"
BRIDGE_DRAW=""; [ -z "$BRIDGE" ] || BRIDGE_DRAW="$(draw "$BRIDGE" 285)"
PAYOFF_DRAW="$(draw "$PAYOFF" 310)"
END_DRAW="$(draw "$END" 310)"

# Every source is deliberately neutral Rec.709. There is no contrast, saturation,
# vignette, or skin-tone effect in this graph.
ffmpeg -nostdin -y -v error \
  -ss 0.4 -t "$A" -i "$FACE" \
  -loop 1 -t "$(awk "BEGIN{print $B-$A}")" -i "$YC" \
  -loop 1 -t "$(awk "BEGIN{print $TOTAL-$B}")" -i "$EVENT" \
  -i "$AUDIO" \
  -filter_complex "\
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30${HOOK_DRAW}${BRIDGE_DRAW}[v0];\
    [1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30${PAYOFF_DRAW}[v1];\
    [2:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30${END_DRAW}[v2];\
    [v0][v1][v2]concat=n=3:v=1:a=0,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]" \
  -map '[v]' -map 3:a:0 -t "$TOTAL" \
  -af "afade=t=out:st=$(awk "BEGIN{print $TOTAL-0.18}"):d=0.18,aresample=44100:async=1,loudnorm=I=-14:TP=-2:LRA=11" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.0 -r 30 -g 60 \
  -c:a aac -b:a 160k -ac 2 -ar 44100 -movflags +faststart "$OUT"

echo "[$VARIANT] $OUT ($TOTAL s; reveal $A s)"
