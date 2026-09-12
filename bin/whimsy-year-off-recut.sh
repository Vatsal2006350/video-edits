#!/usr/bin/env bash
# Recut the approved Whimsymaxxing concept to the canonical audio map.
# Audio anchors: SURGE 4.00; onsets 4.64, 4.92, 5.43, 5.94, 6.43.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-$ROOT/receipts/drop_story_b.mp4}"
OUT="${2:-$ROOT/receipts/whimsy_year_off_recut.mp4}"
AUDIO="${AUDIO:-$ROOT/.work/trend-audio/DcZseTIvgJX.mp3}"
FONT="$ROOT/fonts/Montserrat-Bold.ttf"
mkdir -p "$(dirname "$OUT")"

ffmpeg -nostdin -y -v error -i "$SRC" -i "$AUDIO" -filter_complex "
  [0:v]fps=60,scale=1080:1920,setsar=1,split=7[a][b][c][d][e][f][g];
  [a]trim=0:1.733333,setpts=(PTS-STARTPTS)*2.30769,
    drawbox=x=0:y=0:w=1080:h=278:color=black:t=fill,
    drawtext=fontfile='$FONT':text='POV\\: you disappeared':fontsize=50:fontcolor=white:borderw=2:bordercolor=black@0.55:x=(w-text_w)/2:y=1020,
    drawtext=fontfile='$FONT':text='for a year':fontsize=50:fontcolor=white:borderw=2:bordercolor=black@0.55:x=(w-text_w)/2:y=1080[setup];
  [b]trim=1.733333:2.949,setpts=(PTS-STARTPTS)*0.52644,
    scale=864:1536,pad=1080:1920:108:192:black[yc1];
  [c]trim=3.9:5.402,setpts=(PTS-STARTPTS)*0.18642,
    scale=864:1536,pad=1080:1920:108:192:black[school];
  [d]trim=6.166667:8.026,setpts=(PTS-STARTPTS)*0.27424[laptop];
  [e]trim=8.833333:12.1,setpts=(PTS-STARTPTS)*0.15612[event];
  [f]trim=12.1:14.1,setpts=(PTS-STARTPTS)*0.245[presentation];
  [g]trim=1.733333:2.949,setpts=(PTS-STARTPTS)*0.83059,
    scale=864:1536,pad=1080:1920:108:192:black[yc2];
  [setup][yc1][school][laptop][event][presentation][yc2]
    concat=n=7:v=1:a=0,fps=30,trim=0:7.44,format=yuv420p,
    setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709[v];
  [1:a]atrim=0:7.44,asetpts=PTS-STARTPTS,aresample=44100:async=1[a]
" -map '[v]' -map '[a]' -t 7.44 \
  -c:v libx264 -preset slow -crf 16 -profile:v high -level 4.0 -pix_fmt yuv420p \
  -r 30 -g 60 -keyint_min 60 -sc_threshold 0 \
  -c:a aac -b:a 160k -ar 44100 -ac 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -movflags +faststart+negative_cts_offsets -use_editlist 0 "$OUT"

echo "[whimsy-recut] YC reveal 4.00s; post-drop cuts 4.64/4.92/5.43/5.94/6.43 -> $OUT"
