#!/bin/bash
# "how i got into a top 10 cs school" — talking-head reel.
# Captions are derived by re-transcribing the ASSEMBLED audio (never by mapping source
# timings: whisper anchors the first word to 0.00 and the real onset is ~0.5s later).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; F="$ROOT/fonts"
T="$HOME/Downloads/photos-broll/talking"
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
mkdir -p "$S"
W="$S/t20"; rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/t20_reel.mp4}"
A="$T/0525_183109_IMG_1093.MOV.MOV"; B="$T/0618_235128_IMG_2477.MOV.MOV"
MUSIC="${MUSIC:-$HOME/Downloads/music-rf/winner_is.mp3}"; MUSIC_SS="${MUSIC_SS:-42}"
CAPFONT="${CAPFONT:-Poppins}"; CAPSIZE="${CAPSIZE:-104}"
OPEN_D=3.00
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30)

echo "[1/7] speech segments"
i=0
add(){ i=$((i+1)); n=$(printf "p%02d" $i)
  # level each take on its own: these two clips differ by ~20 LUFS, and normalising
  # only the joined track leaves the quieter one buried. Denoise before boosting a
  # very quiet source or the noise floor comes up with the voice.
  LUFS=$(ffmpeg -nostdin -hide_banner -ss "$2" -to "$3" -i "$1" -map 0:a:0 \
        -af loudnorm=print_format=summary -f null - 2>&1 | awk '/Input Integrated/{print $3}')
  [ -z "$LUFS" ] && LUFS=-16
  DEN=""
  if [ "$(awk -v l="$LUFS" 'BEGIN{print (l < -30)}')" = "1" ]; then
    DEN="afftdn=nf=-20,highpass=f=75,"; echo "    quiet take ${LUFS} LUFS -> denoise + boost"
  fi
  ffmpeg -nostdin -v error -ss "$2" -to "$3" -i "$1" -map 0:v:0 -map 0:a:0 \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
    -af "${DEN}loudnorm=I=-16:TP=-1.5:LRA=11" \
    "${enc[@]}" -c:a aac -ar 48000 -ac 2 "$W/$n.mp4" -y
  echo "    ${LUFS} LUFS -> -16"; }
add "$A" 0.00 11.36; add "$A" 12.06 19.12; add "$A" 19.56 31.78
add "$B" 0.00 3.71;  add "$B" 4.94 10.70
for f in "$W"/p*.mp4; do printf "file '%s'\n" "$f"; done > "$W/sp.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/sp.txt" -c copy "$W/speech.mp4" -y
ffmpeg -nostdin -v error -i "$W/speech.mp4" -an -c:v copy "$W/vonly.mp4" -y
ffmpeg -nostdin -v error -i "$W/speech.mp4" -vn -c:a pcm_s16le "$W/voice.wav" -y
SD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/speech.mp4")

echo "[2/7] b-roll — the third one straddles the take change at 30.64s so the cut is hidden"
keep(){ ffmpeg -nostdin -v error -ss "$1" -to "$2" -i "$W/vonly.mp4" -an "${enc[@]}" "$W/k_$3.mp4" -y; }
still(){ ffmpeg -nostdin -v error -loop 1 -framerate 30 -t "$3" -i "$1" \
  -vf "scale=2400:-1,zoompan=z='min(1.0+0.0012*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x608:fps=30,pad=1080:1920:0:656:black,fps=30" \
  -frames:v $(awk -v d="$3" 'BEGIN{printf "%d", d*30}') -an "${enc[@]}" "$2" -y; }
clip(){ ffmpeg -nostdin -v error -ss "$3" -t "$4" -i "$1" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -an "${enc[@]}" "$2" -y; }
keep 0 16.66 a
still "$HOME/Downloads/yc_announcement.JPG" "$W/b1.mp4" 1.5
keep 18.16 25.56 b
clip "$HOME/Downloads/content/IMG_6946.MOV" "$W/b2.mp4" 0.3 1.5
keep 27.06 30.10 c
clip "$HOME/Downloads/photos-broll/aura-new/0614_113007_video-6811_singular_display.mov.mov" "$W/b3.mp4" 5.2 1.6
keep 31.70 "$SD" d
printf "file '%s'\n" "$W/k_a.mp4" "$W/b1.mp4" "$W/k_b.mp4" "$W/b2.mp4" "$W/k_c.mp4" "$W/b3.mp4" "$W/k_d.mp4" > "$W/v.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/v.txt" -c copy "$W/video.mp4" -y

echo "[3/7] transcribe the assembled audio for exact caption timings"
ffmpeg -nostdin -v error -i "$W/voice.wav" -ac 1 -ar 16000 "$W/vx.wav" -y
( cd "$W" && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
    --output-dir . --output-format json --word-timestamps True vx.wav >/dev/null 2>&1 )

echo "[3b/7] forced alignment (wav2vec2) — whisper word times jitter up to 0.5s"
WXPY="$S/wxenv/bin/python"
if [ -x "$WXPY" ]; then
  "$WXPY" "$ROOT/bin/force-align.py" "$W/vx.wav" "$W/vx.json" "$W/aligned.json" | sed 's/^/    /'
else
  echo "    whisperx venv missing -- falling back to raw whisper timings"; cp "$W/vx.json" "$W/aligned.json"
fi

echo "[4/7] captions"
python3 "$ROOT/bin/make-captions.py" "{\"work\":\"$W\",\"open_d\":0,\"font\":\"$CAPFONT\",\"size\":$CAPSIZE}"
ffmpeg -v error -i "$W/video.mp4" -vf "subtitles=$W/caps.ass:fontsdir=$F" "${enc[@]}" -an "$W/capped.mp4" -y

echo "[5/7] opening title"
python3 "$ROOT/bin/title-card.py" "{\"outdir\":\"$W/t_open\",\"dur\":${OPEN_D},\"fonts\":\"$F\",\"logo\":\"$S/umich_logo.png\"}" >/dev/null
OPENCLIP="${OPENCLIP:-$HOME/Downloads/content/IMG_8286.mov}"
ffmpeg -nostdin -v error -ss 1.6 -t "$OPEN_D" -i "$OPENCLIP" -framerate 30 -i "$W/t_open/h_%04d.png" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.05:saturation=0.95,fps=30[bg];[bg][1:v]overlay=0:0:shortest=1[v]" \
  -map "[v]" -an "${enc[@]}" "$W/open.mp4" -y

echo "[6/7] join"
printf "file '%s'\nfile '%s'\n" "$W/open.mp4" "$W/capped.mp4" > "$W/all.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/all.txt" -c copy "$W/final_v.mp4" -y

echo "[7/7] mix"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/final_v.mp4")
ffmpeg -v error -i "$W/final_v.mp4" -i "$W/voice.wav" -ss "$MUSIC_SS" -i "$MUSIC" -filter_complex "
 [1:a]aformat=channel_layouts=stereo,adelay=$(awk -v d=$OPEN_D 'BEGIN{printf "%d|%d", d*1000, d*1000}'),volume=2dB,alimiter=limit=0.97,asplit=2[voice][vsc];
 [2:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.2,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-2.5}'):d=2.5,volume=0.32[bed];
 [bed][vsc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=400[duck];
 [voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
 -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
