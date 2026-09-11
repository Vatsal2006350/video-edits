#!/usr/bin/env python3
"""Serif opening hook that types out word by word, in sync with the speech.

Takes forced-aligned word timings and reveals each word at the moment it is spoken,
wrapping across lines. Writes a transparent PNG sequence for the hook window.

  typed-hook.py '{"work":..., "aligned":"aligned.json", "from":0.0, "to":5.3, ...}'
"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

c      = json.loads(sys.argv[1])
W, H   = c.get('w', 1080), c.get('h', 1920)
FPS    = c.get('fps', 30)
FONT   = c['font']
SZ     = c.get('size', 92)
MAXW   = c.get('max_w', W - 150)
CY     = c.get('cy', 900)
LEAD   = c.get('lead', 1.22)
SHADOW = c.get('shadow', 0.60)
GLOW   = c.get('glow')                      # e.g. [255,214,10] to bloom the words
FADE   = c.get('fade', 0.14)                # per-word fade-in
T0, T1 = c['from'], c['to']
OUT    = c['outdir']
os.makedirs(OUT, exist_ok=True)

ws = [w for s in json.load(open(c['aligned'])).get('segments', []) for w in s.get('words', [])]
ws = [{'w': w['word'].strip(), 's': w['start']} for w in ws if T0 <= w['start'] < T1]
if not ws:
    print(json.dumps({"frames": 0})); sys.exit(0)

font = ImageFont.truetype(FONT, SZ)
def wide(t): b = font.getbbox(t); return b[2]-b[0]

# lay the full sentence out once so words never reflow as they appear
lines, cur = [], []
for w in ws:
    trial = ' '.join(x['w'] for x in cur+[w])
    if cur and wide(trial) > MAXW:
        lines.append(cur); cur = [w]
    else:
        cur.append(w)
if cur: lines.append(cur)

lh = int(SZ*LEAD)
top = CY - (len(lines)*lh)//2
pos = {}
for li, ln in enumerate(lines):
    total = wide(' '.join(x['w'] for x in ln))
    x = (W-total)//2
    for w in ln:
        pos[id(w)] = (x, top + li*lh)
        x += wide(w['w']+' ')

n = int(round((T1-T0)*FPS))
for f in range(n):
    t = T0 + f/FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)) if GLOW else None
    d, ds = ImageDraw.Draw(im), ImageDraw.Draw(sh)
    dg = ImageDraw.Draw(gl) if gl else None
    for w in ws:
        if t < w['s']: continue
        a = min(1.0, (t-w['s'])/FADE) if FADE > 0 else 1.0
        a = 1-(1-a)**3
        x, y = pos[id(w)]
        if dg is not None:
            dg.text((x, y), w['w'], font=font, fill=tuple(GLOW)+(int(255*a),),
                    stroke_width=5, stroke_fill=tuple(GLOW)+(int(255*a),))
        ds.text((x+3, y+6), w['w'], font=font, fill=(0, 0, 0, int(200*a*SHADOW)))
        d.text((x, y), w['w'], font=font, fill=(255, 255, 255, int(255*a)))
    out = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(15)), im)
    if gl is not None:
        for i in range(3):
            out = Image.alpha_composite(gl.filter(ImageFilter.GaussianBlur(7*(i+1))), out)
        out = Image.alpha_composite(out, im)
    out.save(f"{OUT}/h_{f:04d}.png")
print(json.dumps({"frames": n, "lines": len(lines), "words": len(ws), "size": SZ}))
