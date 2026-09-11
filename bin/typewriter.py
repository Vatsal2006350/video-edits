#!/usr/bin/env python3
"""Typewriter hook: a sentence split into short phrases, each typed character by character
into the same centred slot, held until the next phrase is due, then faded out.

Measured from IG reel Dcq29SSRGLV ("why I think everyone should live away from home"):
  - ~24 characters/second, revealed left to right INTO a line that is laid out and centred
    as a whole first (left edge fixed, right edge grows) -- not re-centred per character
  - hold until the next phrase's start time, then a 0.13s fade (ink lightens to the wall)
  - ink ~194px tall for a mixed-case line, top at y~325, centred on x=540
  - dark warm near-black (47,30,8) on a bright wall; the last phrase is upper-cased
  - no caret in the reference; `caret` is optional

Spec (JSON argv[1]):
  {"outdir": "...", "dur": 4.2, "fps": 30,
   "font": ".../InstrumentSerif-Regular.ttf", "size": 176, "fill": [47,30,8],
   "y_top": 325, "cps": 24, "fade": 0.13, "caret": false,
   "phrases": [{"t": "Why I think everyone", "at": 0.00},
               {"t": "should live away",     "at": 1.40},
               {"t": "from home at least",   "at": 2.33},
               {"t": "ONCE!",                "at": 3.27, "caps": true, "until": 3.86}]}
`at` comes from the aligned words (first word of each phrase). `until` on the last phrase.
If typing a phrase at `cps` would overrun the next `at`, the rate is raised to fit.
Writes t_%04d.png (transparent) for overlay with ffmpeg.
"""
import sys, json, os, math
from PIL import Image, ImageDraw, ImageFont

c      = json.loads(sys.argv[1])
W, H   = c.get('w', 1080), c.get('h', 1920)
FPS    = c.get('fps', 30)
DUR    = c['dur']
OUT    = c['outdir']
FONT   = c.get('font', '/Users/vatsalshah/Code/video-edits/fonts/InstrumentSerif-Regular.ttf')
SIZE   = c.get('size', 103)
FILL   = tuple(c.get('fill', [47, 30, 8]))
Y_TOP  = c.get('y_top', 325)
CPS    = c.get('cps', 24)
FADE   = c.get('fade', 0.13)
CARET  = c.get('caret', False)
SAFE_L, SAFE_R = 59, 918
MAXW   = c.get('max_w', 2 * (SAFE_R - W // 2) - 12)   # centred limit, not the box width
os.makedirs(OUT, exist_ok=True)

phrases = c['phrases']
for i, p in enumerate(phrases):
    p['text'] = p['t'].upper() if p.get('caps') else p['t']
    p['out'] = p.get('until', phrases[i + 1]['at'] if i + 1 < len(phrases) else DUR)
    # size: shrink only if the finished line would cross the rail
    sz = p.get('size', SIZE)
    while sz > 24:
        f = ImageFont.truetype(FONT, sz)
        bb = f.getbbox(p['text'])
        if bb[2] - bb[0] <= MAXW:
            break
        sz -= 4
    p['font'] = f; p['bb'] = bb
    p['x0'] = (W - (bb[2] - bb[0])) // 2 - bb[0]           # the whole line is centred once
    n = len(p['text'])
    avail = max(0.05, p['out'] - p['at'] - FADE - 0.05)   # never type into the fade
    p['cps'] = max(CPS, n / avail)                           # speed up only if it would overrun
    p['type_len'] = n / p['cps']

def caret_w(f): return max(3, int(f.size * 0.05))

events = []                                  # (time, phrase_index) for every character reveal
for pi, p in enumerate(phrases):
    for k in range(len(p['text'])):
        if p['text'][k] != ' ':
            events.append((round(p['at'] + k / p['cps'], 4), pi))
json.dump(events, open(f'{OUT}/keystrokes.json', 'w'))

n_frames = int(round(DUR * FPS))
for fi in range(n_frames):
    t = fi / FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for p in phrases:
        if t < p['at'] or t >= p['out'] + FADE:
            continue
        # how many characters are on screen
        k = min(len(p['text']), int((t - p['at']) * p['cps']) + 1)
        # fade: ink lightens toward the wall over FADE seconds after `out`
        a = 1.0 if t < p['out'] else max(0.0, 1 - (t - p['out']) / FADE)
        shown = p['text'][:k]
        y = Y_TOP - p['bb'][1]
        d.text((p['x0'], y), shown, font=p['font'], fill=FILL + (int(255 * a),))
        if CARET and t < p['at'] + p['type_len'] and int(t * 2) % 2 == 0:
            cw = caret_w(p['font']); x = p['x0'] + p['font'].getlength(shown) + 4
            d.rectangle([x, Y_TOP, x + cw, Y_TOP + (p['bb'][3] - p['bb'][1])], fill=FILL + (int(255 * a),))
    im.save(f'{OUT}/t_{fi:04d}.png')
print(json.dumps({'frames': n_frames, 'keystrokes': len(events), 'phrases': [(p['text'], round(p['cps'], 1)) for p in phrases]}))
