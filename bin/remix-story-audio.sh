#!/usr/bin/env bash
# Rebuild a story reel's soundtrack from its clean voice stem and music.
#
# Usage:
#   MUSIC=track.mp3 MUSIC_SS=20 bash bin/remix-story-audio.sh \
#     picture.mp4 voice.wav output.mp4
#
# Optional environment:
#   MUSIC_VOL=0.20       music-bed gain before ducking
#   MUSIC_TARGET_DBFS=   measure the selected song section and set its average
#                       level automatically (for example, -36 for a quiet bed);
#                       when set, this takes precedence over MUSIC_VOL
#   MUSIC_INTRO_GAIN=1.15 extra bed presence during the opening
#   MUSIC_INTRO_DUR=3.5  opening music window, seconds
#   DUCKING=1            set to 0 for a fixed bed that never rebounds in pauses
#   VOICE_GAIN=1.15      overall dialogue gain
#   INTRO_GAIN=1.35      extra dialogue gain during the opening window
#   INTRO_DUR=4.0        opening window, seconds
#   SFX_STEM=track.wav   full-length ambience/SFX stem to mix quietly
#   SFX_VOL=1.0          full-length SFX-stem gain
#   WHOOSH_TIMES=6,18    transition accents, seconds
#   WHOOSH_FILE=sfx/whoosh.wav
#   WHOOSH_GAIN=0.18
#   FORCE=1              replace an existing output
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: MUSIC=track.mp3 [MUSIC_SS=20] $0 picture.mp4 voice.wav output.mp4" >&2
  exit 2
fi

PICTURE=$1
VOICE=$2
OUT=$3
MUSIC=${MUSIC:?set MUSIC to the background track}
MUSIC_SS=${MUSIC_SS:-0}
MUSIC_VOL=${MUSIC_VOL:-0.20}
MUSIC_TARGET_DBFS=${MUSIC_TARGET_DBFS:-}
MUSIC_INTRO_GAIN=${MUSIC_INTRO_GAIN:-1.15}
MUSIC_INTRO_DUR=${MUSIC_INTRO_DUR:-3.5}
VOICE_GAIN=${VOICE_GAIN:-1.15}
INTRO_GAIN=${INTRO_GAIN:-1.35}
INTRO_DUR=${INTRO_DUR:-4.0}
SFX_STEM=${SFX_STEM:-}
SFX_VOL=${SFX_VOL:-1.0}
WHOOSH_TIMES=${WHOOSH_TIMES:-}
WHOOSH_FILE=${WHOOSH_FILE:-$(cd "$(dirname "$0")/.." && pwd)/sfx/whoosh.wav}
WHOOSH_GAIN=${WHOOSH_GAIN:-0.18}
DUCKING=${DUCKING:-1}

for f in "$PICTURE" "$VOICE" "$MUSIC"; do
  [ -f "$f" ] || { echo "missing input: $f" >&2; exit 1; }
done
if [ -e "$OUT" ] && [ "${FORCE:-0}" != 1 ]; then
  echo "refusing to overwrite $OUT (set FORCE=1)" >&2
  exit 1
fi

duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PICTURE")

if [ -n "$MUSIC_TARGET_DBFS" ]; then
  # Measure exactly the portion used by the reel.  This prevents differently
  # mastered songs from producing differently loud beds at the same volume.
  mean_db=$(ffmpeg -hide_banner -nostats -ss "$MUSIC_SS" -t "$duration" -i "$MUSIC" -map 0:a:0 \
    -af "aformat=sample_rates=48000:channel_layouts=stereo,volumedetect" -f null - 2>&1 \
    | awk '/mean_volume:/ { value=$5 } END { print value }')
  [ -n "$mean_db" ] || { echo "could not measure music level: $MUSIC" >&2; exit 1; }
  MUSIC_VOL=$(awk -v target="$MUSIC_TARGET_DBFS" -v measured="$mean_db" \
    'BEGIN { printf "%.8f", exp(log(10) * (target - measured) / 20) }')
  echo "music calibration: ${mean_db} dBFS -> ${MUSIC_TARGET_DBFS} dBFS (gain ${MUSIC_VOL})"
fi
args=(-i "$PICTURE" -i "$VOICE" -stream_loop -1 -ss "$MUSIC_SS" -i "$MUSIC")

# Dialogue gets gentle presence EQ, short-window normalization, compression, and
# a separate opening lift. The music starts at frame one, fades in over 120 ms,
# and side-chain ducks beneath speech instead of disappearing.
filter="[1:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=75,equalizer=f=3000:t=q:w=1:g=1.8,dynaudnorm=f=180:g=7:p=0.92:m=4,acompressor=threshold=0.075:ratio=2.5:attack=5:release=120:makeup=${VOICE_GAIN},volume='if(lt(t,${INTRO_DUR}),${INTRO_GAIN},1)'[voice];[2:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration=${duration},asetpts=PTS-STARTPTS,volume='${MUSIC_VOL}*if(lt(t,${MUSIC_INTRO_DUR}),${MUSIC_INTRO_GAIN},1)',afade=t=in:st=0:d=0.12[music]"
if [ "$DUCKING" = 0 ]; then
  filter+=";[voice]anull[voice_mix];[music]anull[bed]"
else
  filter+=";[voice]asplit=2[voice_mix][voice_key];[music][voice_key]sidechaincompress=threshold=0.020:ratio=5:attack=12:release=320:makeup=1[bed]"
fi
mix_inputs="[voice_mix][bed]"
mix_count=2
next_input=3

if [ -n "$SFX_STEM" ]; then
  [ -f "$SFX_STEM" ] || { echo "missing SFX_STEM: $SFX_STEM" >&2; exit 1; }
  args+=(-i "$SFX_STEM")
  filter+=";[${next_input}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration=${duration},volume=${SFX_VOL}[sfxstem]"
  mix_inputs+="[sfxstem]"
  mix_count=$((mix_count + 1))
  next_input=$((next_input + 1))
fi

if [ -n "$WHOOSH_TIMES" ]; then
  [ -f "$WHOOSH_FILE" ] || { echo "missing WHOOSH_FILE: $WHOOSH_FILE" >&2; exit 1; }
  IFS=',' read -r -a times <<< "$WHOOSH_TIMES"
  for i in "${!times[@]}"; do
    ms=$(awk -v t="${times[$i]}" 'BEGIN { printf "%d", t * 1000 }')
    args+=(-i "$WHOOSH_FILE")
    label="whoosh${i}"
    filter+=";[${next_input}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=${WHOOSH_GAIN},adelay=${ms}|${ms}[${label}]"
    mix_inputs+="[${label}]"
    mix_count=$((mix_count + 1))
    next_input=$((next_input + 1))
  done
fi

filter+=";${mix_inputs}amix=inputs=${mix_count}:duration=longest:normalize=0,atrim=duration=${duration},alimiter=limit=0.78:attack=5:release=80[mix]"

tmp="${OUT%.*}.tmp.$$.mp4"
trap 'rm -f "$tmp"' EXIT
ffmpeg -hide_banner -y "${args[@]}" -filter_complex "$filter" \
  -map 0:v:0 -map '[mix]' -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 \
  -movflags +faststart -shortest "$tmp"
mv "$tmp" "$OUT"
trap - EXIT

echo "wrote $OUT"
