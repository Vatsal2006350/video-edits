#!/usr/bin/env python3
"""Cinematic stacked word reveal: large light lowercase type, words arrive in sequence,
earlier lines settle back to a ghost opacity. Writes a PNG sequence (transparent)."""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

c    = json.loads(sys.argv[1])
W, H = c.get('w', 1080), c.get('h', 1920)
FPS  = c.get('fps', 30)
DUR  = c['dur']
FACE = c.get('face', '/System/Library/Fonts/HelveticaNeue.ttc')
IDX  = c.get('face_index', 7)               # 7 = Light, 12 = Thin, 5 = UltraLight
SZ   = c.get('size', 150)
X    = c.get('x', 96)
TOP  = c.get('top', 620)
LEAD = c.get('lead', 1.02)
GHOST= c.get('ghost', 0.34)                 # opacity earlier lines settle to
RISE = c.get('rise', 26)                    # px a line travels as it fades in
FADE = c.get('fade', 0.22)                  # seconds per line to arrive
LINES= c['lines']                           # [{"t": "word", "at": 0.0}, ...] at = seconds in
SHADOW = c.get('shadow', 0.0)      # 0 = none; ~0.55 for busy/bright backgrounds
SCRIM  = c.get('scrim', 0.0)       # soft dark band behind the text block (bright footage)
OUT  = c['outdir']
os.makedirs(OUT, exist_ok=True)

SAFE_R = c.get('safe_right', 902)           # rail starts at 918; leave a small gutter
MAXW = c.get('max_w', SAFE_R - X)           # never let a line reach the rail
while SZ > 20:
    f = ImageFont.truetype(FACE, SZ, index=IDX)
    if max(f.getbbox(L['t'])[2] - f.getbbox(L['t'])[0] for L in LINES) <= MAXW:
        break
    SZ -= 2
font = ImageFont.truetype(FACE, SZ, index=IDX)
lh   = int(SZ * LEAD)
n    = int(round(DUR * FPS))

def make_scrim(y0, y1, strength):
    # Smooth sky shows any hard-edged gradient as a band. Spread the falloff over ~3x
    # the text block with a raised-cosine so there is no discernible edge anywhere.
    import math
    band = Image.new('L', (1, H), 0)
    px = band.load()
    mid = (y0+y1)/2.0
    half = max(1.0, (y1-y0)/2.0) * 3.0
    for y in range(H):
        d = abs(y-mid)/half
        if d >= 1.0:
            px[0, y] = 0
        else:
            px[0, y] = int(255*strength*0.5*(1.0+math.cos(math.pi*d)))
    mask = band.resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    sc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sc.putalpha(mask)
    return sc

for f in range(n):
    t  = f / FPS
    im  = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh  = Image.new('RGBA', (W, H), (0, 0, 0, 0)) if SHADOW > 0 else None
    d   = ImageDraw.Draw(im)
    ds  = ImageDraw.Draw(sh) if sh else None
    # which line is newest so far
    live = [i for i, L in enumerate(LINES) if t >= L['at']]
    newest = live[-1] if live else None
    for i, L in enumerate(LINES):
        if t < L['at']:
            continue
        age = t - L['at']
        p   = min(1.0, age / FADE)                 # arrival progress
        ease = 1 - (1 - p) ** 3
        a    = ease if i == newest else GHOST + (1 - GHOST) * max(0.0, 1 - (t - LINES[newest]['at']) / FADE)
        a    = max(0.0, min(1.0, a * ease if i == newest else a))
        y    = TOP + i * lh + int((1 - ease) * RISE)
        if ds is not None:
            ds.text((X + 3, y + 5), L['t'], font=font, fill=(0, 0, 0, int(255 * a * SHADOW)))
        d.text((X, y), L['t'], font=font, fill=(255, 255, 255, int(255 * a)))
    if sh is not None:
        im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), im)
    if SCRIM > 0:
        y0 = TOP - 60; y1 = TOP + len(LINES)*lh + 60
        im = Image.alpha_composite(make_scrim(y0, y1, SCRIM), im)
    im.save(f"{OUT}/h_{f:04d}.png")
print(json.dumps({"frames": n, "size": SZ, "outdir": OUT}))
