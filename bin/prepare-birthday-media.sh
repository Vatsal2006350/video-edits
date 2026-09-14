#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
downloads_dir="${1:-/Users/you/Downloads}"
bowling_source="$downloads_dir/IMG_5456 2.MOV"
candle_source="$downloads_dir/6685A3C8-C40A-450D-9978-ADE42C4C11A7.MP4"
main_assets="$repo_dir/videos/birthday-bowling/assets"
pov_assets="$repo_dir/videos/birthday-bowling-pov/assets"
[[ -f "$bowling_source" && -f "$candle_source" ]] || { echo 'Missing birthday source footage' >&2; exit 1; }
mkdir -p "$main_assets" "$pov_assets"
technical_sdr='zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,scale=1080:1920,setsar=1,format=yuv420p'
ffmpeg -hide_banner -loglevel error -y -ss 4 -i "$bowling_source" -t 3.3 -vf "$technical_sdr" -r 30 -c:v libx264 -preset fast -crf 18 -an -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$main_assets/bowling-sdr.mp4"
ffmpeg -hide_banner -loglevel error -y -ss 0.8 -i "$bowling_source" -t 7.9 -vf "$technical_sdr" -r 30 -c:v libx264 -preset fast -crf 18 -an -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$pov_assets/bowling-only-sdr.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$candle_source" -t 12.4 -vf 'scale=1080:1920:in_range=pc:out_range=tv,setsar=1,format=yuv420p' -c:v libx264 -preset fast -crf 18 -an -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$main_assets/candle-real.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$candle_source" -vn -t 15.466667 -c:a pcm_s16le "$main_assets/feeling-good.wav"
cp "$main_assets/feeling-good.wav" "$pov_assets/feeling-good.wav"
node "$repo_dir/.agents/skills/media-use/scripts/resolve.mjs" --adopt --project "$repo_dir/videos/birthday-bowling"
node "$repo_dir/.agents/skills/media-use/scripts/resolve.mjs" --adopt --project "$repo_dir/videos/birthday-bowling-pov"
