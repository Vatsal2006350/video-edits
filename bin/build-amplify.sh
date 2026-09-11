#!/bin/bash
# Rebuild the Amplify origin reel from amplify_base.mp4 (clean concat, no overlays/captions).
# Applies the tightening edit, re-lays overlays on the NEW timeline, regenerates karaoke captions.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FONTS="$ROOT/fonts"
cd "$ROOT/amplify"
BASE=amplify_base.mp4
W="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}/build"
mkdir -p "$W"

# ---- edit list (reel time on BASE) -------------------------------------
CUT_A=52.69      # after "...products that have done well"
CUT_B=56.39      # before "and also"   -> drops the weak supplier clause
TEMPO=1.14       # speed for the tail; he crawls there ("competitor" = 2.04s)
END=67.93

echo "[1/6] splice matted CAPS embeds into the base"
ffmpeg -v error -i "$BASE" -t 18.00                    -c:v libx264 -crf 16 -preset medium -c:a aac -ar 48000 "$W/a1.mp4" -y
ffmpeg -v error -ss 22.30 -i "$BASE" -t 8.25           -c:v libx264 -crf 16 -preset medium -c:a aac -ar 48000 "$W/a2.mp4" -y
ffmpeg -v error -ss 33.55 -i "$BASE"                   -c:v libx264 -crf 16 -preset medium -c:a aac -ar 48000 "$W/a3.mp4" -y
# the matted embeds are video-only -- pair each with the base audio for the window
# it covers, or the concat silently drops that speech and shifts everything after it.
ffmpeg -v error -i seg_excel_v2.mp4  -ss 18.00 -t 4.30 -i "$BASE" -map 0:v -map 1:a -shortest \
  -c:v libx264 -crf 16 -preset medium -c:a aac -ar 48000 -ac 1 "$W/seg_excel.mp4" -y
ffmpeg -v error -i seg_human_v2.mp4 -ss 30.55 -t 3.00 -i "$BASE" -map 0:v -map 1:a -shortest \
  -c:v libx264 -crf 16 -preset medium -c:a aac -ar 48000 -ac 1 "$W/seg_human2.mp4" -y
printf "file '%s'\n" "$W/a1.mp4" "$W/seg_excel.mp4" "$W/a2.mp4" "$W/seg_human2.mp4" "$W/a3.mp4" > "$W/sp.txt"
ffmpeg -v error -f concat -safe 0 -i "$W/sp.txt" -c copy "$W/spliced.mp4" -y

echo "[2/6] cut the weak clause + speed the crawl"
ffmpeg -v error -i "$W/spliced.mp4" -filter_complex "
 [0:v]trim=0:${CUT_A},setpts=PTS-STARTPTS[v1];
 [0:a]atrim=0:${CUT_A},asetpts=PTS-STARTPTS[a1];
 [0:v]trim=${CUT_B}:${END},setpts=(PTS-STARTPTS)/${TEMPO}[v2];
 [0:a]atrim=${CUT_B}:${END},asetpts=PTS-STARTPTS,atempo=${TEMPO}[a2];
 [v1][v2]concat=n=2:v=1:a=0[v];
 [a1][a2]concat=n=2:v=0:a=1[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 16 -preset medium -r 30 -c:a aac -ar 48000 "$W/tight.mp4" -y
echo "    tightened duration: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/tight.mp4")s"

echo "[3/6] regenerate karaoke captions on the remapped timeline"
python3 - "$W" <<'PY'
import json, sys, os
W = sys.argv[1]
T = os.path.expanduser('~/Downloads/photos-broll/transcripts')
hook = json.load(open(f'{T}/0706_223215_IMG_3010.MOV.words.json'))
orig = json.load(open(f'{T}/0706_223359_IMG_3016.MOV.words.json'))
SEG = [(hook,0.00,8.90,0.00),(orig,0.00,13.44,8.90),(orig,14.38,19.54,7.99),(orig,20.08,60.38,7.49)]
CUT_A, CUT_B, TEMPO = 52.69, 56.39, 1.14

def rs(t):                                         # word START
    if t < CUT_A: return t
    if t < CUT_B: return None                      # word begins inside the cut -> gone
    return CUT_A + (t - CUT_B) / TEMPO
def re_(t):                                        # word END: clamp to the cut, never drop
    if t <= CUT_A: return t
    if t <= CUT_B: return CUT_A
    return CUT_A + (t - CUT_B) / TEMPO

words = []
for tr, a, b, off in SEG:
    for w in tr['words']:
        if a <= w['start'] < b:
            s, e = rs(w['start'] + off), re_(w['end'] + off)
            if s is None or e is None: continue
            words.append({'w': w['w'], 's': s, 'e': max(e, s + 0.08)})
words.sort(key=lambda x: x['s'])

# group into caption lines (~24 chars, break on a real pause)
groups, cur = [], []
for i, w in enumerate(words):
    cand = ' '.join(x['w'] for x in cur + [w])
    gap = w['s'] - cur[-1]['e'] if cur else 0
    if cur and (len(cand) > 14 or gap > 0.45):
        groups.append(cur); cur = [w]
    else:
        cur.append(w)
if cur: groups.append(cur)

HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Kara,Montserrat ExtraBold,140,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC8000000,0,0,0,0,100,100,2,0,1,10,7,2,36,36,300,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
def ts(t):
    h = int(t//3600); m = int((t%3600)//60); s = t%60
    return f"{h}:{m:02d}:{s:05.2f}"

ON, OFF = r'{\c&H004AD2FF&\fscx114\fscy114}', r'{\c&H00FFFFFF&\fscx100\fscy100}'
lines = []
for g in groups:
    for j, w in enumerate(g):
        end = g[j+1]['s'] if j+1 < len(g) else g[j]['e']
        txt = ' '.join((ON + x['w'] + OFF) if k == j else x['w'] for k, x in enumerate(g))
        lines.append(f"Dialogue: 0,{ts(w['s'])},{ts(max(end, w['s']+0.08))},Kara,,0,0,0,,{txt}")
open(f'{W}/subs_tight.ass','w').write(HDR + '\n'.join(lines) + '\n')
print(f"    {len(words)} words, {len(groups)} caption groups, ends {words[-1]['e']:.2f}s")
PY

echo "[4/6] lay overlay cards on the new timeline"
# card windows re-aimed at the words they illustrate; ov_sales now exits before the cut
CARDS="ov_yc:1.90:5.20 ov_store:10.30:13.60 ov_landing:33.90:37.10 ov_marketplace:37.40:41.20 ov_dashboard:43.90:47.20 ov_sales:47.90:52.20"
INS=(-i "$W/tight.mp4"); FG=""; PREV="0:v"; i=1
for c in $CARDS; do
  IFS=: read -r png a b <<< "$c"
  d=$(echo "$b - $a" | bc); fo=$(echo "$d - 0.30" | bc)
  INS+=(-loop 1 -t "$d" -i "$png.png")
  FG+="[${i}:v]format=rgba,fade=t=in:st=0:d=0.30:alpha=1,fade=t=out:st=${fo}:d=0.30:alpha=1,setpts=PTS-STARTPTS+${a}/TB[o${i}];"
  FG+="[${PREV}][o${i}]overlay=0:0:eof_action=pass:enable='between(t,${a},${b})'[v${i}];"
  PREV="v${i}"; i=$((i+1))
done
ffmpeg -v error "${INS[@]}" -filter_complex "${FG%;}" -map "[${PREV}]" -map 0:a \
  -c:v libx264 -crf 16 -preset medium -r 30 -c:a copy "$W/carded.mp4" -y

echo "[5/6] burn karaoke captions"
ffmpeg -v error -i "$W/carded.mp4" \
  -vf "subtitles=$W/subs_tight.ass:fontsdir=$FONTS" \
  -c:v libx264 -crf 16 -preset medium -r 30 -c:a copy "$W/capped.mp4" -y

echo "[6/6] mix voice + music + clicks"
MUSIC="${MUSIC:-$HOME/Downloads/music-rf/winner_is.mp3}"
MUSIC_SS="${MUSIC_SS:-42}"       # this track is quiet till ~60s and lifts at ~70s
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/capped.mp4")

# one track of shutter clicks at each moment something appears on screen
CLICK_AT="${CLICK_AT:-1.90 10.30 18.40 30.55 33.90 37.40 43.90 47.90}"
python3 - "$W" "$DUR" $CLICK_AT <<'PYC'
import sys, subprocess, numpy as np, os
W, dur = sys.argv[1], float(sys.argv[2])
ats = [float(x) for x in sys.argv[3:]]
sr = 48000
raw = subprocess.run(['ffmpeg','-v','error','-i',os.path.expanduser('~/Code/video-edits/sfx/click.wav'),
                      '-f','s16le','-ac','2','-ar','48000','-'],capture_output=True).stdout
clk = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
buf = np.zeros((int(dur*sr)+sr, 2), dtype=np.float32)
for t in ats:
    i = int(t*sr)
    buf[i:i+len(clk)] += clk * 0.5
buf = np.clip(buf, -1, 1)
subprocess.run(['ffmpeg','-v','error','-f','s16le','-ar','48000','-ac','2','-i','pipe:0',
                '-c:a','pcm_s16le',f'{W}/clicks.wav','-y'],
               input=(buf*32767).astype(np.int16).tobytes(), check=True)
print(f"    {len(ats)} clicks placed")
PYC

ffmpeg -v error -i "$W/capped.mp4" -ss "$MUSIC_SS" -i "$MUSIC" -i "$W/clicks.wav" -filter_complex "
 [0:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,asplit=2[voice][vsc];
 [1:a]aformat=channel_layouts=stereo,atrim=0:${DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2.0,afade=t=out:st=$(echo "$DUR-3.0"|bc):d=3.0,volume=0.34[bed];
 [bed][vsc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=420[duck];
 [2:a]aformat=channel_layouts=stereo,volume=0.9[clk];
 [voice][duck][clk]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 amplify_v8.mp4 -y

cp amplify_v8.mp4 ~/Downloads/reel-exports/amplify_reel.mp4
echo "DONE  amplify_v8.mp4  $(ffprobe -v error -show_entries format=duration -of csv=p=0 amplify_v8.mp4)s"
