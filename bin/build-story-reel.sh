#!/bin/bash
# Generic talking-head story reel.
#   SEGS   = newline-separated "src|start|end" speech cuts, concatenated in order
#   HOOK_T = seconds of the assembled speech that get the typed serif hook treatment
#   CUTS   = newline-separated "start|end|src|seek" b-roll cutaways (speech time)
#   TAIL   = newline-separated "src|seek|dur" b-roll appended after the speech (music only)
#   WORDFIX = "heard=meant,to#2=from,junk=" caption word corrections. `#N`
#             targets only the Nth occurrence; an empty right side drops it.
#   TONEMAP = auto (default: HLG/PQ sources tonemapped to Rec.709 with zscale+hable) | 1 | 0
#   HEAD   = newline-separated "src|seek|dur" b-roll BEFORE the speech (music/SFX/MIDTEXT only; everything else shifts)
#   SFX    = newline-separated "time|file.wav|gain_dB" sound cues, mixed with the bed (ducked under the voice)
#   BROLL_VF = extra filter chain applied to every cutaway/tail clip (a grade)
# Captions come from forced alignment of the ASSEMBLED audio, never from source timings,
# and are burned onto the speech video BEFORE any opening is prepended (see caps open_d=0).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; F="$ROOT/fonts"
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
mkdir -p "$S"
NAME="${NAME:-story}"; W="$S/$NAME"; rm -rf "$W"; mkdir -p "$W"
OUT="${OUT:-$HOME/Downloads/reel-exports/${NAME}.mp4}"
MUSIC="${MUSIC:-$HOME/Downloads/music-rf/travel-documentary.mp3}"; MUSIC_SS="${MUSIC_SS:-0}"
CAPFONT="${CAPFONT:-Poppins}"; CAPSIZE="${CAPSIZE:-104}"
HOOK_T="${HOOK_T:-0}"
HOOK_FONT="${HOOK_FONT:-$F/DMSerifDisplay-Italic.ttf}"
HOOK_SIZE="${HOOK_SIZE:-96}"
ZOOMS="${ZOOMS:-}"          # comma-separated per-segment scale, e.g. "1.0,1.0,1.07,1.0,1.06"
BROLL_VF="${BROLL_VF:-}"    # extra ffmpeg filters for every cutaway/tail clip (a grade), e.g. "eq=contrast=1.08:saturation=1.15"
TONEMAP="${TONEMAP:-auto}"  # auto|1|0: HLG/PQ sources get tonemapped to Rec.709 before scaling (iPhone "HDR video" = arib-std-b67)
TMF="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
tmpre(){ # prints the tonemap prefix if the file is HDR (or TONEMAP=1)
  case "$TONEMAP" in 1) printf '%s' "$TMF";; 0) ;; *) t=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$1" 2>/dev/null); case "$t" in arib-std-b67|smpte2084) printf '%s' "$TMF";; esac;; esac; }
BVF=""; [ -n "$BROLL_VF" ] && BVF=",$BROLL_VF"
# Every rendered frame is display-ready Rec.709. Explicit tags prevent an HLG
# source's metadata surviving the tonemap and being interpreted a second time.
enc=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1)

echo "[0/6] story-qa"
if ! python3 "$ROOT/bin/story-qa.py" --segs "$SEGS" --cuts "${CUTS:-}" --tail "${TAIL:-}"; then
  [ "${QA_FORCE:-0}" = "1" ] || { echo "story-qa found problems -- fix the spec or set QA_FORCE=1"; exit 2; }
fi
echo "[1/6] speech segments"
i=0
while IFS='|' read -r src a b; do
  [ -z "$src" ] && continue
  i=$((i+1)); n=$(printf "p%02d" $i)
  # Takes recorded on different days can differ by 20 LUFS. Normalising only the
  # concatenated track lets the loudest clip set the level and buries the others, so
  # level each segment on its own -- and denoise first when it needs a big boost,
  # since raising a quiet source also raises its noise floor.
  LUFS=$(ffmpeg -nostdin -hide_banner -ss "$a" -to "$b" -i "$src" -map 0:a:0 \
        -af loudnorm=print_format=summary -f null - 2>&1 \
        | awk '/Input Integrated/{print $3}')
  [ -z "$LUFS" ] && LUFS=-16
  DEN=""
  if [ "$(awk -v l="$LUFS" 'BEGIN{print (l < -30)}')" = "1" ]; then
    DEN="afftdn=nf=-20,highpass=f=75,"
    echo "    (quiet source ${LUFS} LUFS -> denoise + boost)"
  fi
  Z=$(echo "$ZOOMS" | cut -d, -f$i); [ -z "$Z" ] && Z=1.0
  ZF=$(awk -v z="$Z" 'BEGIN{printf "%d:%d", 1080*z, 1920*z}')
  ffmpeg -nostdin -v error -ss "$a" -to "$b" -i "$src" -map 0:v:0 -map 0:a:0 \
    -vf "$(tmpre "$src")scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,scale=${ZF},crop=1080:1920,fps=30" \
    -af "${DEN}loudnorm=I=-16:TP=-1.5:LRA=11" \
    "${enc[@]}" -c:a aac -ar 48000 -ac 2 "$W/$n.mp4" -y
  echo "    $(basename "$src")  $a -> $b   [${LUFS} LUFS -> -16]"
done <<< "$SEGS"
for f in "$W"/p*.mp4; do printf "file '%s'\n" "$f"; done > "$W/sp.txt"
ffmpeg -nostdin -v error -f concat -safe 0 -i "$W/sp.txt" -c copy "$W/speech.mp4" -y
ffmpeg -nostdin -v error -i "$W/speech.mp4" -an -c:v copy "$W/vonly.mp4" -y
ffmpeg -nostdin -v error -i "$W/speech.mp4" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$W/vx.wav" -y
ffmpeg -nostdin -v error -i "$W/speech.mp4" -vn -c:a pcm_s16le "$W/voice.wav" -y
SD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/speech.mp4")
echo "    speech ${SD}s"

echo "[2/6] transcribe + force-align"
( cd "$W" && uvx --from mlx-whisper mlx_whisper --model mlx-community/whisper-large-v3-turbo \
    --output-dir . --output-format json --word-timestamps True vx.wav >/dev/null 2>&1 )
WXPY="$S/wxenv/bin/python"
if [ -x "$WXPY" ]; then "$WXPY" "$ROOT/bin/force-align.py" "$W/vx.wav" "$W/vx.json" "$W/aligned.json" | sed 's/^/    /'
else echo "    no whisperx -- raw whisper timings"; cp "$W/vx.json" "$W/aligned.json"; fi

python3 - "$W/aligned.json" "$SD" <<'PYG'
import json, sys
p, sd = sys.argv[1], float(sys.argv[2]); d = json.load(open(p)); n = 0
for seg in d.get('segments', []):
    keep = [w for w in seg.get('words', []) if w['start'] < sd - 0.25]
    n += len(seg.get('words', [])) - len(keep); seg['words'] = keep
d['segments'] = [s for s in d['segments'] if s.get('words')]
json.dump(d, open(p, 'w')); print(f"    dropped {n} hallucinated tail words" if n else "    no tail hallucination")
PYG
if [ -n "${WORDFIX:-}" ]; then
  python3 - "$W/aligned.json" "$WORDFIX" <<'PYF'
import json, sys
p, fixes = sys.argv[1], sys.argv[2]; d = json.load(open(p)); n = 0
rules = []
for f in fixes.split(','):
    if '=' not in f: continue
    lhs, replacement = f.split('=', 1)
    base, sep, occurrence = lhs.rpartition('#')
    rules.append((base if sep and occurrence.isdigit() else lhs,
                  int(occurrence) if sep and occurrence.isdigit() else None,
                  replacement))
seen = {}
for seg in d.get('segments', []):
    out = []
    for w in seg.get('words', []):
        key = w['word'].strip().lower().strip('.,!?')
        seen[key] = seen.get(key, 0) + 1
        hit = next((r for r in rules if r[0].lower() == key and (r[1] is None or r[1] == seen[key])), None)
        if hit is None: out.append(w); continue
        n += 1
        if hit[2] == '': continue                      # "word=" drops the word
        w['word'] = ' ' + hit[2]; out.append(w)
    seg['words'] = out
json.dump(d, open(p, 'w')); print(f"    word fixes applied: {n}")
PYF
fi
echo "[3/6] b-roll cutaways"
if [ -n "${CUTS:-}" ]; then
  prev=0; j=0; : > "$W/v.txt"
  while IFS='|' read -r ca cb csrc cseek; do
    [ -z "$ca" ] && continue
    j=$((j+1))
    KF=$(awk -v a="$ca" -v b="$prev" 'BEGIN{printf "%d", (a-b)*30+0.5}')
    if [ "$KF" -gt 0 ]; then
      ffmpeg -nostdin -v error -ss "$prev" -i "$W/vonly.mp4" -frames:v "$KF" -an "${enc[@]}" "$W/k$j.mp4" -y
    else
      rm -f "$W/k$j.mp4"
    fi
    CF=$(awk -v a="$cb" -v b="$ca" 'BEGIN{printf "%d", (a-b)*30+0.5}')
    ffmpeg -nostdin -v error -ss "$cseek" -i "$csrc" -frames:v "$CF" \
      -vf "$(tmpre "$csrc")scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30$BVF" -an "${enc[@]}" "$W/c$j.mp4" -y
    [ -f "$W/k$j.mp4" ] && printf "file '%s'\n" "$W/k$j.mp4" >> "$W/v.txt"
    printf "file '%s'\n" "$W/c$j.mp4" >> "$W/v.txt"
    echo "    cutaway ${ca}-${cb}s  $(basename "$csrc")"
    prev="$cb"
  done <<< "$CUTS"
  ZF=$(awk -v a="$SD" -v b="$prev" 'BEGIN{printf "%d", (a-b)*30+0.5}')
  if [ "$ZF" -gt 0 ]; then
    ffmpeg -nostdin -v error -ss "$prev" -i "$W/vonly.mp4" -frames:v "$ZF" -an "${enc[@]}" "$W/kz.mp4" -y
    printf "file '%s'\n" "$W/kz.mp4" >> "$W/v.txt"
  fi
  ffmpeg -nostdin -v error -f concat -safe 0 -i "$W/v.txt" -c copy "$W/video.mp4" -y
else
  cp "$W/vonly.mp4" "$W/video.mp4"
fi

if [ -n "${TAIL:-}" ]; then
  echo "[3b/6] tail b-roll (after the speech, music only)"
  printf "file '%s'\n" "$W/video.mp4" > "$W/t.txt"; j=0
  while IFS='|' read -r tsrc tseek tdur; do
    [ -z "$tsrc" ] && continue
    j=$((j+1))
    ffmpeg -nostdin -v error -ss "$tseek" -t "$tdur" -i "$tsrc" \
      -vf "$(tmpre "$tsrc")scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30$BVF" -an "${enc[@]}" "$W/t$j.mp4" -y
    printf "file '%s'\n" "$W/t$j.mp4" >> "$W/t.txt"
    echo "    tail $(basename "$tsrc") @${tseek} ${tdur}s"
  done <<< "$TAIL"
  ffmpeg -nostdin -v error -f concat -safe 0 -i "$W/t.txt" -c copy "$W/video_t.mp4" -y && mv "$W/video_t.mp4" "$W/video.mp4"
  TD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/video.mp4")
  ffmpeg -nostdin -v error -i "$W/voice.wav" -af "apad=whole_dur=${TD}" "$W/voice_p.wav" -y && mv "$W/voice_p.wav" "$W/voice.wav"
fi
HD=0
if [ -n "${HEAD:-}" ]; then
  echo "[3c/6] head b-roll (before the speech)"
  : > "$W/h.txt"; j=0
  while IFS='|' read -r hsrc hseek hdur; do
    [ -z "$hsrc" ] && continue
    j=$((j+1)); HF=$(awk -v d="$hdur" 'BEGIN{printf "%d", d*30+0.5}')
    ffmpeg -nostdin -v error -ss "$hseek" -i "$hsrc" -frames:v "$HF" \
      -vf "$(tmpre "$hsrc")scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30$BVF" -an "${enc[@]}" "$W/h$j.mp4" -y
    printf "file '%s'\n" "$W/h$j.mp4" >> "$W/h.txt"; HD=$(awk -v a="$HD" -v b="$hdur" 'BEGIN{printf "%.3f", a+b}')
    echo "    head $(basename "$hsrc") @${hseek} ${hdur}s"
  done <<< "$HEAD"
  printf "file '%s'\n" "$W/video.mp4" >> "$W/h.txt"
  ffmpeg -nostdin -v error -f concat -safe 0 -i "$W/h.txt" -c copy "$W/video_h.mp4" -y && mv "$W/video_h.mp4" "$W/video.mp4"
  HMS=$(awk -v h="$HD" 'BEGIN{printf "%d", h*1000}')
  ffmpeg -nostdin -v error -i "$W/voice.wav" -af "adelay=${HMS}|${HMS}" "$W/voice_h.wav" -y && mv "$W/voice_h.wav" "$W/voice.wav"
  echo "    head ${HD}s -- voice, captions and hook shifted"
fi
echo "[4/6] captions (from forced alignment, speech time)"
python3 "$ROOT/bin/make-captions.py" "{\"work\":\"$W\",\"open_d\":$HD,\"font\":\"$CAPFONT\",\"size\":$CAPSIZE,\"skip_before\":$HOOK_T}"
ffmpeg -nostdin -v error -i "$W/video.mp4" -vf "subtitles=$W/caps.ass:fontsdir=$F" "${enc[@]}" -an "$W/capped.mp4" -y

echo "[5/6] typed serif hook 0 -> ${HOOK_T}s"
if [ "$(awk -v h="$HOOK_T" 'BEGIN{print (h>0)}')" = "1" ]; then
  if [ -n "${HOOK_PHRASES:-}" ]; then
    python3 "$ROOT/bin/dynamic-hook.py" "{\"aligned\":\"$W/aligned.json\",\"dur\":${HOOK_T},\"font\":\"${HOOK_FONT}\",\"safe_top\":${HOOK_SAFE_TOP:-1000},\"safe_bottom\":${HOOK_SAFE_BOT:-1380},\"outdir\":\"$W/hook\",\"phrases\":${HOOK_PHRASES}}" | sed 's/^/    /'
  else
    python3 "$ROOT/bin/typed-hook.py" "{\"aligned\":\"$W/aligned.json\",\"from\":0,\"to\":${HOOK_T},\"font\":\"${HOOK_FONT}\",\"size\":${HOOK_SIZE},\"cy\":${HOOK_CY:-1150},\"outdir\":\"$W/hook\"}" | sed 's/^/    /'
  fi
  ffmpeg -nostdin -v error -i "$W/capped.mp4" -framerate 30 -i "$W/hook/h_%04d.png" \
    -filter_complex "[1:v]setpts=PTS+${HD}/TB[hk];[0:v][hk]overlay=0:0:eof_action=pass[v]" -map "[v]" -an "${enc[@]}" "$W/final_v.mp4" -y
else
  cp "$W/capped.mp4" "$W/final_v.mp4"
fi

if [ -n "${MIDTEXT:-}" ]; then
  echo "[5b/6] mid-reel hero lines"
  k=0
  while IFS='|' read -r ms md msz mal my ml1 ml2; do
    [ -z "$ms" ] && continue
    k=$((k+1))
    python3 "$ROOT/bin/hero-type.py" "{\"dur\":${md},\"face\":\"${HOOK_FONT}\",\"face_index\":0,\"size\":${msz},\"top\":${my},\"x\":88,\"lead\":1.14,\"fade\":0.22,\"shadow\":0.85,\"scrim\":0.30,\"lines\":[{\"t\":\"${ml1}\",\"at\":0.05},{\"t\":\"${ml2}\",\"at\":0.55}],\"outdir\":\"$W/mid$k\"}" >/dev/null
    ffmpeg -nostdin -v error -i "$W/final_v.mp4" -framerate 30 -i "$W/mid$k/h_%04d.png" \
      -filter_complex "[1:v]setpts=PTS-STARTPTS+${ms}/TB[m];[0:v][m]overlay=0:0:eof_action=pass:enable='between(t,${ms},$(awk -v a=$ms -v b=$md 'BEGIN{printf "%.2f", a+b}'))'[v]" \
      -map "[v]" -an "${enc[@]}" "$W/mid_out.mp4" -y
    mv "$W/mid_out.mp4" "$W/final_v.mp4"
    echo "    ${ms}s  ${ml1} / ${ml2}"
  done <<< "$MIDTEXT"
fi

echo "[6/6] mix"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/final_v.mp4")
if [ -n "${SFX:-}" ]; then
  # build one SFX track: each line "t|file|gain_dB"
  j=0; inputs=(); fc=""; mix=""
  while IFS='|' read -r st sf sg; do
    [ -z "$st" ] && continue
    j=$((j+1)); inputs+=(-i "$sf"); ms=$(awk -v t="$st" 'BEGIN{printf "%d", t*1000}')
    fc+="[$((j-1)):a]aformat=channel_layouts=stereo:sample_rates=48000,volume=${sg:-0}dB,adelay=${ms}|${ms}[s$j];"; mix+="[s$j]"
  done <<< "$SFX"
  ffmpeg -nostdin -v error "${inputs[@]}" -filter_complex "${fc}${mix}amix=inputs=$j:duration=longest:normalize=0,apad=whole_dur=${DUR},atrim=0:${DUR}[o]" -map "[o]" -ar 48000 "$W/sfx.wav" -y
  echo "    sfx: $j cues"
  SFXIN=(-i "$W/sfx.wav"); SFXMIX="[3:a]aformat=channel_layouts=stereo[sfx];[bed][sfx]amix=inputs=2:duration=first:normalize=0[bed2];"; BEDLBL="[bed2]"
else
  SFXIN=(); SFXMIX=""; BEDLBL="[bed]"
fi
ffmpeg -nostdin -v error -i "$W/final_v.mp4" -i "$W/voice.wav" -ss "$MUSIC_SS" -i "$MUSIC" "${SFXIN[@]}" -filter_complex "
 [1:a]aformat=channel_layouts=stereo,volume=2dB,alimiter=limit=0.97,asplit=2[voice][vsc];
 [2:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.2,afade=t=out:st=$(awk -v d=$DUR 'BEGIN{printf "%.2f", d-2.5}'):d=2.5,volume=${MUSVOL:-0.26}[bed];
 ${SFXMIX}
 ${BEDLBL}[vsc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=400[duck];
 [voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
 -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT" -y
echo "DONE  $OUT  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
