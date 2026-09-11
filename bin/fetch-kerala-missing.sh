#!/bin/bash
# RUN IN Terminal.app (Claude Code cannot touch the Photos library -- see memory photos-tcc-blocker).
# Re-exports every Kerala-trip video (19-22 Aug 2026) as ORIGINALS into a fresh folder:
#   - brings down IMG_4257-4314 (herbal garden, plantation walk, interview) that the first export skipped
#   - gets the un-muted originals of IMG_4391/4392/4405/4412/4532 (the earlier copies were the edited, muted versions)
set -uo pipefail
OSX="$HOME/Code/video-edits/.photoenv/bin/osxphotos"; D="$HOME/Downloads/photos-broll/kerala-missing"; mkdir -p "$D"
[ -x "$OSX" ] || OSX="uvx osxphotos"
$OSX export "$D" --only-movies --from-date 2026-08-19 --to-date 2026-08-23 \
  --download-missing --use-photokit --skip-edited --retry 2 --update 2>&1 | tail -15
echo; echo "on disk: $(find "$D" -maxdepth 1 -type f -iname '*.MOV' | wc -l | tr -d ' ') clips"
echo "audio check (RMS per file; -180 = still muted):"
for f in "$D"/*.MOV; do printf '%-22s ' "$(basename "$f")"; ffmpeg -nostdin -i "$f" -map 0:a:0 -af "astats=measure_perchannel=none:measure_overall=RMS_level" -f null - 2>&1 | grep 'RMS level' | tail -1 | sed 's/.*dB: //'; done
