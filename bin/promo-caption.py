#!/usr/bin/env python3
"""Burned captions in the JacHacks-reel style, plus logo cards that pop in on cue.

Style measured off "JacHacks in Mumbai.MOV" frame by frame:
  - Anton (heavy condensed), ALL CAPS, ~3 words per line
  - white fill with a thick black stroke so it survives any background
  - selected keywords in RGB(255, 64, 0)
  - the source sat its captions at y~1760, which is under IG's own caption block; we keep
    the look but move them to y~1430 so they clear the chrome (see bin/ig-safe.py)

Spec (JSON argv[1]):
  {"aligned": "aligned.json", "outdir": "...", "dur": 39.1,
   "highlight": ["YC","18","100,000","NVIDIA"],       # words drawn in orange-red
   "cards": [{"img": "logos/nvidia.png", "from": 19.6, "to": 22.9, "slot": 0}, ...]}
Cards stack in a row of up to 3 slots above the caption.
"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont

c        = json.loads(sys.argv[1])
W, H     = c.get('w', 1080), c.get('h', 1920)
FPS      = c.get('fps', 30)
DUR      = c['dur']
FDIR     = c.get('fontdir', '/Users/vatsalshah/Code/video-edits/fonts')
SIZE     = c.get('size', 96)
CY       = c.get('cy', 1430)
ANCHOR   = c.get('anchor', 'baseline')   # 'baseline' (Anton style) or 'top' (Kumar: block grows downward from CY)
PITCH    = c.get('line_pitch', 1.0)      # line spacing as a multiple of SIZE, for multi-line top-anchored blocks
MAXW     = c.get('max_words', 3)
FILL     = tuple(c.get('fill', [255, 255, 255]))
HL       = tuple(c.get('hl', [255, 64, 0]))
STROKE   = c.get('stroke', 9)
OUT      = c['outdir']
CARDS    = c.get('cards', [])
HLWORDS  = {w.upper().strip('.,!?') for w in c.get('highlight', [])}
SKIP     = c.get('skip_before', 0.0)   # words before this are handled by the kinetic hook
MUTE     = c.get('mute', [])           # [[from,to],...] windows where a hero graphic replaces the caption
os.makedirs(OUT, exist_ok=True)

FONTFILE = c.get('font', f'{FDIR}/Anton-Regular.ttf')   # the JacHacks-Mumbai style is Anton; the
                                                            # chess-reel style is a bold sans in solid red
font = ImageFont.truetype(FONTFILE, SIZE)
# centred text is limited by the distance from centre to IG's rail, not the box width
SAFE_R = 902
MAXPX = min(SAFE_R - 88, 2 * (SAFE_R - W // 2))

ws = [w for s in json.load(open(c['aligned'])).get('segments', []) for w in s.get('words', [])]
words = [{'w': w['word'].strip().upper(), 's': float(w['start']), 'e': float(w['end'])}
         for w in ws if w.get('word', '').strip() and float(w['start']) >= SKIP]

# group into short lines that fit, breaking on a real gap so lines follow the phrasing
groups, cur = [], []
for w in words:
    cand = cur + [w]
    txt = ' '.join(x['w'] for x in cand)
    gap = w['s'] - cur[-1]['e'] if cur else 0
    too_wide = font.getbbox(txt)[2] - font.getbbox(txt)[0] > MAXPX
    if cur and (too_wide or len(cur) >= MAXW or gap > 0.45):
        groups.append(cur); cur = [w]
    else:
        cur = cand
if cur:
    groups.append(cur)

cards = []
for cd in CARDS:
    if os.path.exists(cd['img']):
        im = Image.open(cd['img']).convert('RGBA')
        cards.append({**cd, 'im': im})

SAFE_L, SAFE_RR = 59, 902
PER_ROW  = c.get('per_row', 2)          # wordmarks are wide; two per row keeps them legible
BOX_W    = c.get('box_w', 344)          # each logo is fitted inside this box, aspect kept
BOX_H    = c.get('box_h', 116)
PHOTO_W  = c.get('photo_w', 660)
CARD_TOP = c.get('card_top')            # absolute y of the first logo row; default = stacked above the caption

def shadowed(im):
    """soft dark halo so a transparent logo reads on any background -- replaces the white
    panel, which Vatsal called out as a border that should not be there"""
    from PIL import ImageFilter
    pad = 18
    sh = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sil = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sil.putalpha(im.getchannel('A'))
    sh.alpha_composite(sil, (pad, pad + 4))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    sh.alpha_composite(im, (pad, pad))
    return sh

def fit(im, bw, bh):
    r = min(bw / im.width, bh / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))))

def draw_cards(canvas, t):
    live = [cd for cd in cards if cd['from'] <= t < cd['to']]
    if not live:
        return
    photos = [cd for cd in live if cd.get('photo')]
    logos  = [cd for cd in live if not cd.get('photo')]
    # centred content is limited by twice the centre-to-rail distance, not the box width
    usable = 2 * (SAFE_RR - W // 2)

    for cd in photos:
        im = fit(cd['im'], min(PHOTO_W, usable), 900)
        s = min(1.0, (t - cd['from']) / 0.20); s = 1 - (1 - s) ** 3
        s = 0.86 + 0.14 * s                       # pop from 86%, never a speck
        im2 = im.resize((int(im.width * s), int(im.height * s)))
        card = shadowed(im2)
        canvas.alpha_composite(card, ((W - card.width) // 2, 900 - card.height // 2))

    if logos:
        rows = [logos[i:i + PER_ROW] for i in range(0, len(logos), PER_ROW)]
        gap = 26
        row_h = BOX_H + 26
        y = CARD_TOP if CARD_TOP is not None else CY - 190 - row_h * len(rows)   # card_top pins the logo rows (e.g. below the face)
        for row in rows:
            fitted = [fit(cd['im'], BOX_W, BOX_H) for cd in row]
            total = sum(f.width for f in fitted) + gap * (len(fitted) - 1)
            sc = min(1.0, usable / total) if total else 1.0
            if sc < 1.0:
                fitted = [f.resize((int(f.width * sc), int(f.height * sc))) for f in fitted]
                total = sum(f.width for f in fitted) + gap * (len(fitted) - 1)
            x = (W - total) // 2
            for cd, f in zip(row, fitted):
                s = min(1.0, (t - cd['from']) / 0.20); s = 1 - (1 - s) ** 3
                s = 0.86 + 0.14 * s
                fs = f.resize((max(1, int(f.width * s)), max(1, int(f.height * s))))
                card = shadowed(fs)
                cx = x + (f.width - card.width) // 2
                cy = y + (BOX_H - card.height) // 2
                canvas.alpha_composite(card, (cx, cy))
                x += f.width + gap
            y += row_h

n_frames = int(round(DUR * FPS))
gi = 0
for fi in range(n_frames):
    t = fi / FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    g = None
    muted = any(a <= t < b for a, b in MUTE)
    for grp in ([] if muted else groups):
        if grp[0]['s'] <= t < grp[-1]['e'] + 0.22:
            g = grp; break
    if g:
        # only words already spoken are on screen, so the line builds as he says it
        shown = [x for x in g if t >= x['s']] or [g[0]]
        parts = [(x['w'], x['w'].strip('.,!?') in HLWORDS) for x in shown]
        space = font.getbbox(' ')[2] - font.getbbox(' ')[0]
        widths = [font.getbbox(p[0])[2] - font.getbbox(p[0])[0] for p in parts]
        if ANCHOR == 'top':
            # wrap the shown words into lines that fit, then stack them downward from CY
            lines, cur, curw = [], [], 0
            for (txt, hl), wpx in zip(parts, widths):
                if cur and curw + space + wpx > MAXPX:
                    lines.append(cur); cur, curw = [], 0
                cur.append(((txt, hl), wpx)); curw += (space if len(cur) > 1 else 0) + wpx
            if cur: lines.append(cur)
            for li, ln in enumerate(lines):
                total = sum(wp for _, wp in ln) + space * (len(ln) - 1)
                x = (W - total) // 2; y = CY + int(li * SIZE * PITCH)
                for (txt, is_hl), wpx in ln:
                    d.text((x, y), txt, font=font, fill=(HL if is_hl else FILL) + (255,),
                           stroke_width=STROKE, stroke_fill=(0, 0, 0, 255), anchor='la')
                    x += wpx + space
        else:
            total = sum(widths) + space * (len(parts) - 1)
            x = (W - total) // 2
            for (txt, is_hl), wpx in zip(parts, widths):
                d.text((x, CY), txt, font=font, fill=(HL if is_hl else FILL) + (255,),
                       stroke_width=STROKE, stroke_fill=(0, 0, 0, 255), anchor='ls')
                x += wpx + space

    draw_cards(im, t)
    im.save(f'{OUT}/c_{fi:04d}.png')

print(json.dumps({'frames': n_frames, 'lines': len(groups), 'cards': len(cards)}))
