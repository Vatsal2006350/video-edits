#!/usr/bin/env python3
"""Build caption ASS from FORCE-ALIGNED word timings.

Read `aligned.json` (wav2vec2 forced alignment), not raw whisper output: whisper pins the
first word to 0.00 and jitters the rest by up to ~0.3s. Times are in the time base of the
video the subtitles get burned onto -- if an opening is prepended afterwards, open_d is 0.
"""
import json, sys

cfg   = json.loads(sys.argv[1])
W     = cfg['work']
OPEN  = cfg.get('open_d', 0.0)
FONT  = cfg.get('font', 'Poppins')
SZ    = cfg.get('size', 104)
MAXC  = cfg.get('max_chars', 15)
MAXW  = cfg.get('max_words', 3)
GAP   = cfg.get('gap', 0.34)
MARGV = cfg.get('margin_v', 500)   # keep burned captions above IG's own caption block
HILITE= cfg.get('highlight', '&H0005CBFF&')     # BGR: Michigan maize
SNAPW = cfg.get('snap_window', 0.28)
SKIP  = cfg.get('skip_before', 0.0)   # words before this are covered by a typed hook

SRC = cfg.get('words_json', 'aligned.json')
ws = [w for s in json.load(open(f'{W}/{SRC}')).get('segments', []) for w in s.get('words', [])]

words = [{'w': w['word'].strip(), 's': w['start'], 'e': max(w['end'], w['start']+0.08)} for w in ws if w['start'] >= SKIP]

groups, cur = [], []
for w in words:
    cand = ' '.join(x['w'] for x in cur+[w])
    gap = w['s']-cur[-1]['e'] if cur else 0
    if cur and (len(cand) > MAXC or len(cur) >= MAXW or gap > GAP):
        groups.append(cur); cur = [w]
    else:
        cur.append(w)
if cur: groups.append(cur)

for g in groups:
    for x in g: x['s'] += OPEN; x['e'] += OPEN

HDR = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,{FONT},{SZ},&H00FFFFFF,&H00FFFFFF,&H00000000,&H8C000000,0,0,0,0,100,100,0,0,1,7,5,2,60,60,{MARGV},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

def ts(t):
    h = int(t//3600); m = int((t % 3600)//60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

ON  = '{\\c' + HILITE + '}'
OFF = '{\\c&H00FFFFFF&}'
out = []
for gi, g in enumerate(groups):
    gend = groups[gi+1][0]['s'] if gi+1 < len(groups) else g[-1]['e']+0.30
    gend = min(gend, g[-1]['e']+0.26)
    for j, w in enumerate(g):
        wend = g[j+1]['s'] if j+1 < len(g) else gend
        if wend <= w['s']: wend = w['s']+0.08
        txt = ' '.join((ON+x['w']+OFF) if k == j else x['w'] for k, x in enumerate(g))
        out.append(f"Dialogue: 0,{ts(w['s'])},{ts(wend)},Cap,,0,0,0,,{txt}")
open(f'{W}/caps.ass', 'w').write(HDR+'\n'.join(out)+'\n')
print(f"    {len(words)} words, {len(groups)} groups, first caption {groups[0][0]['s']:.2f}s" if groups else f"    {len(words)} words, 0 groups (all covered by the hook)")
