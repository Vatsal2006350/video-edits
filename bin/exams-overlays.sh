#!/bin/bash
# Re-apply the two overlays to the exams reel. Keep this separate from the build so a
# rebuild never silently drops them -- run it after every build-story-reel.sh pass.
#   exams-overlays.sh <in.mp4> <out.mp4>
set -euo pipefail
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
IN="${1:?in}"; OUT="${2:?out}"
DM="$HOME/Downloads/photos-broll/purple/dm_screenrec.mp4"
CARD="$S/reel_card.png"          # the 119K "Studying till she replies" screenshot, pre-shadowed
SHADOW="$S/dm_shadow.png"
MASK="$S/dm_mask.png"
# DM inbox scrolls on "hundreds of DMs"; the viral reel card takes the same slot on
# "after I posted this reel" -- same position so they read as one panel handing off.
ffmpeg -nostdin -v error -i "$IN" -loop 1 -t 2.1 -i "$SHADOW" -i "$DM" -i "$MASK" -loop 1 -t 3.95 -i "$CARD" -filter_complex "
 [2:v]scale=281:611,setsar=1,fps=30[dmv];
 [3:v]scale=281:611,format=gray[msk];
 [dmv][msk]alphamerge[dmc];
 [1:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st=1.75:d=0.30:alpha=1,setpts=PTS-STARTPTS+3.85/TB[shd];
 [dmc]fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st=1.75:d=0.30:alpha=1,setpts=PTS-STARTPTS+3.85/TB[dmf];
 [4:v]format=rgba,fade=t=in:st=0:d=0.28:alpha=1,fade=t=out:st=3.55:d=0.35:alpha=1,setpts=PTS-STARTPTS+5.95/TB[cardf];
 [0:v][shd]overlay=0:0:eof_action=pass:enable='between(t,3.85,5.90)'[b1];
 [b1][dmf]overlay=714:134:eof_action=pass:enable='between(t,3.85,5.90)'[b2];
 [b2][cardf]overlay=0:0:eof_action=pass:enable='between(t,5.95,9.85)'[v]" \
 -map "[v]" -map 0:a -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a copy "$OUT" -y
echo "overlays applied -> $OUT"
