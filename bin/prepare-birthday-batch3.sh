#!/usr/bin/env bash
set -euo pipefail
cd ${VIDEO_EDITS_ROOT:-$HOME/Code/video-edits}
mkdir -p .work/birthday-bowling/batch3-assets
task_assets=.work/birthday-bowling/batch3-assets
task_filter='zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p'
prepare() {
  local source="$1" start="$2" duration="$3" output="$4"
  if [[ ! -f "$task_assets/$output.mp4" ]]; then
    ffmpeg -hide_banner -loglevel error -ss "$start" -i "${DOWNLOADS_DIR:-$HOME/Downloads}/$source" -t "$duration" -vf "$task_filter" -r 30 -c:v libx264 -preset fast -crf 18 -an -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$task_assets/$output.mp4"
  fi
}
prepare 'IMG_5456 2.MOV' 0 15.98 bowling
prepare 'IMG_5460 2.MOV' 0 4.2 cake-table
prepare 'video-9224_singular_display 2.MOV' 11.45 7.9 unbox
prepare 'video-9245_singular_display 2.MOV' 16.2 7.9 candle-pov
prepare 'IMG_5461 2.MOV' 0 15.5 friends
prepare 'IMG_5444 2.MOV' 0 4.3 alley
cp videos/birthday-bowling/assets/candle-real.mp4 "$task_assets/candle.mp4"
cp videos/birthday-bowling/assets/feeling-good.wav "$task_assets/music.wav"
for task_project in birthday-full-roll birthday-main-character birthday-accessories birthday-cake-reveal birthday-wish-list birthday-camera-roll; do
  mkdir -p "videos/$task_project/assets"
  for task_asset in "$task_assets"/*; do
    ln -f "$task_asset" "videos/$task_project/assets/$(basename "$task_asset")"
  done
done
