#!/usr/bin/env bash
# Build a 13.074s reaction meme from a vertical reaction clip, horizontal product
# footage, and a reference audio track. Cuts intentionally follow the reference
# grammar: reaction -> reveal -> reaction -> demonstrations -> reaction.
set -euo pipefail

REACTION="${1:?reaction mp4}"
PRODUCT="${2:?product mp4}"
AUDIO="${3:?audio file}"
OUT="${4:?output mp4}"
TOP1="${TOP1:-Me as a founder}"
TOP2="${TOP2:-realizing I}"
BOTTOM1="${BOTTOM1:-have to make my}"
BOTTOM2="${BOTTOM2:-website work on this}"
FONT="${FONT:-$(cd "$(dirname "$0")/.." && pwd)/fonts/Montserrat-Bold.ttf}"
mkdir -p "$(dirname "$OUT")"

# Reaction footage is supplied as clean creator footage; no product UI or prior
# burned copy is carried into the composition.
ffmpeg -nostdin -y -hide_banner -loglevel error \
  -i "$REACTION" -i "$PRODUCT" -i "$AUDIO" \
  -filter_complex "
    [0:v]fps=30,crop=iw:ih*0.55:0:0,
      scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:black,setsar=1,
      eq=contrast=1.04:saturation=0.94[person];
    [1:v]fps=30,scale=1080:608:force_original_aspect_ratio=decrease,
      pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1,setpts=PTS-STARTPTS[device];
    [person]trim=start=0.00:end=1.14,setpts=PTS-STARTPTS[p0];
    [device]trim=start=0.00:end=2.16,setpts=PTS-STARTPTS[p1];
    [person]trim=start=0.10:end=2.90,setpts=PTS-STARTPTS[p2];
    [device]trim=start=8.00:end=10.90,setpts=PTS-STARTPTS[p3];
    [person]trim=start=0.60:end=2.60,setpts=PTS-STARTPTS[p4];
    [device]trim=start=20.00:end=21.30,setpts=PTS-STARTPTS[p5];
    [person]trim=start=0.20:end=0.874,setpts=PTS-STARTPTS[p6];
    [person]trim=start=0.90:end=2.274,setpts=PTS-STARTPTS[p7];
    [p0][p1][p2][p3][p4][p5][p6][p7]concat=n=8:v=1:a=0,trim=0:13.074,
      drawtext=fontfile='${FONT}':text='${TOP1}':fontcolor=white:fontsize=52:
        borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=325,
      drawtext=fontfile='${FONT}':text='${TOP2}':fontcolor=white:fontsize=52:
        borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=385,
      drawtext=fontfile='${FONT}':text='${BOTTOM1}':fontcolor=white:fontsize=48:
        borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=1350,
      drawtext=fontfile='${FONT}':text='${BOTTOM2}':fontcolor=white:fontsize=48:
        borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=1408,
      format=yuv420p[v];
    [2:a]atrim=0:13.074,asetpts=PTS-STARTPTS[a]" \
  -map '[v]' -map '[a]' -t 13.074 \
  -c:v libx264 -preset slow -crf 15 -r 30 -g 60 \
  -c:a aac -b:a 256k -ar 44100 -ac 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -movflags +faststart "$OUT"

echo "[alternating-reaction-reel] -> $OUT"
