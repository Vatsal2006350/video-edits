#!/usr/bin/env bash
# Retimes an existing vertical edit so its primary visual transition lands on a
# measured audio drop. Usage: trend-remix.sh source audio output duration source_cut drop
set -euo pipefail
SRC="${1:?source mp4}"
AUDIO="${2:?audio file}"
OUT="${3:?output mp4}"
DUR="${4:?duration seconds}"
SRC_CUT="${5:?source payoff time}"
DROP="${6:?audio drop time}"
mkdir -p "$(dirname "$OUT")"

TAIL_SRC=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC" | awk -v c="$SRC_CUT" '{print $1-c}')
TAIL_OUT=$(awk -v d="$DUR" -v x="$DROP" 'BEGIN{print d-x}')
PRE_RATE=$(awk -v s="$SRC_CUT" -v d="$DROP" 'BEGIN{print s/d}')
POST_RATE=$(awk -v s="$TAIL_SRC" -v d="$TAIL_OUT" 'BEGIN{print s/d}')

ffmpeg -nostdin -y -hide_banner -loglevel error -i "$SRC" -i "$AUDIO" \
  -filter_complex "
    [0:v]fps=30,scale=1080:1920,setsar=1,split=2[va][vb];
    [va]trim=0:${SRC_CUT},setpts=(PTS-STARTPTS)/${PRE_RATE}[pre];
    [vb]trim=start=${SRC_CUT},setpts=(PTS-STARTPTS)/${POST_RATE}[post];
    [pre][post]concat=n=2:v=1:a=0,trim=0:${DUR},format=yuv420p[v];
    [1:a]atrim=0:${DUR},asetpts=PTS-STARTPTS[a]" \
  -map '[v]' -map '[a]' -t "$DUR" -c:v libx264 -preset slow -crf 16 -r 30 -g 60 \
  -c:a aac -b:a 256k -ar 44100 -ac 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -movflags +faststart "$OUT"
echo "[trend-remix] source ${SRC_CUT}s -> audio drop ${DROP}s -> $OUT"
