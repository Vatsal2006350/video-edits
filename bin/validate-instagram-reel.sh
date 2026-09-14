#!/usr/bin/env bash
set -euo pipefail

publish_dir="${1:-}"

if [[ -z "$publish_dir" || ! -d "$publish_dir" ]]; then
  echo "Usage: $0 publishing/queue/REEL_NAME" >&2
  exit 2
fi

video="$publish_dir/reel.mp4"
caption="$publish_dir/caption.txt"
metadata="$publish_dir/publish.json"

for required in "$video" "$caption" "$metadata"; do
  if [[ ! -f "$required" ]]; then
    echo "Missing required file: $required" >&2
    exit 1
  fi
done

read -r codec width height duration < <(
  ffprobe -v error \
    -select_streams v:0 \
    -show_entries stream=width,height,codec_name:format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$video" | paste -sd ' ' -
)

audio_streams="$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$video" | wc -l | tr -d ' ')"
caption_chars="$(wc -m < "$caption" | tr -d ' ')"

if (( width >= height )); then
  echo "Video is not vertical: ${width}x${height}" >&2
  exit 1
fi

if [[ "$codec" != "h264" && "$codec" != "hevc" ]]; then
  echo "Unexpected video codec: $codec" >&2
  exit 1
fi

if (( audio_streams < 1 )); then
  echo "Video has no audio stream" >&2
  exit 1
fi

if (( caption_chars > 2200 )); then
  echo "Caption exceeds 2200 characters: $caption_chars" >&2
  exit 1
fi

echo "Ready for Instagram"
echo "Video: ${width}x${height}, ${codec}, ${duration}s"
echo "Audio streams: $audio_streams"
echo "Caption characters: $caption_chars"
