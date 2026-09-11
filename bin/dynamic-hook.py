#!/usr/bin/env python3
"""Dynamic typed hook: short phrases that replace each other, with hero words blown up.

Fixes two problems with a plain word-by-word reveal: it accumulates until the block
covers the speaker's face, and every word is the same size so it reads as monotonous.
Here each phrase gets its own size, alignment and vertical position inside a safe band
measured from the subject matte, and one word per phrase can be scaled up hard.

Spec:
  {"aligned": "...json", "outdir": "...", "dur": 4.3,
   "safe_top": 60, "safe_bottom": 460,
   "phrases": [
     {"n": 3, "size": 84,  "align": "left",   "hero": null},
     {"n": 1, "size": 210, "align": "center", "hero": 0, "caps": true},
     ...]}
`n` is how many words from the aligned stream this phrase consumes.
"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

c        = json.loads(sys.argv[1])
W, H     = c.get('w', 1080), c.get('h', 1920)
FPS      = c.get('fps', 30)
DUR      = c['dur']
FONT     = c.get('font', '/Users/vatsalshah/Code/video-edits/fonts/DMSerifDisplay-Italic.ttf')
FONT_HERO= c.get('font_hero', FONT)
TOP      = c.get('safe_top', 60)
BOT      = c.get('safe_bottom', 460)
MARGIN   = c.get('margin', 70)
FADE     = c.get('fade', 0.16)
SHADOW   = c.get('shadow', 0.75)
GLOW     = c.get('glow')
OUT      = c['outdir']
os.makedirs(OUT, exist_ok=True)

ws = [w for s in json.load(open(c['aligned'])).get('segments', []) for w in s.get('words', [])]
ws = [{'w': w['word'].strip(), 's': w['start'], 'e': w['end']} for w in ws if w['start'] < DUR]

# slice the word stream into the phrases described in the spec
phrases, i = [], 0
for p in c['phrases']:
    n = p.get('n', 1)
    grp = ws[i:i+n]
    if not grp: break
    i += n
    phrases.append({**p, 'words': grp, 's': grp[0]['s'],
                    'e': grp[-1]['e']})
for a, b in zip(phrases, phrases[1:]):
    a['out'] = b['s']                      # a phrase clears when the next one starts
if phrases: phrases[-1]['out'] = DUR

def layout(ph):
    """positions for each word of one phrase, wrapped and aligned inside the safe band"""
    base = ph.get('size', 90)
    hero = ph.get('hero')
    caps = ph.get('caps', False)
    hero_scale = ph.get('hero_scale', 1.0)
    items = []
    for k, w in enumerate(ph['words']):
        t = w['w'].upper() if caps else w['w']
        sz = int(base*hero_scale) if hero == k else base
        f = ImageFont.truetype(FONT_HERO if hero == k else FONT, sz)
        bb = f.getbbox(t)
        items.append({'t': t, 'f': f, 'w': bb[2]-bb[0], 'h': sz, 'sw': w['s']})
    # wrap
    maxw = W - MARGIN*2
    lines, cur, cw = [], [], 0
    for it in items:
        adv = it['w'] + int(it['h']*0.28)
        if cur and cw + adv > maxw:
            lines.append(cur); cur = [it]; cw = adv
        else:
            cur.append(it); cw += adv
    if cur: lines.append(cur)
    lh = max(int(max(x['h'] for x in ln)*1.16) for ln in lines)
    total = lh*len(lines)
    y0 = ph.get('y', (TOP+BOT)//2 - total//2)
    y0 = max(TOP, min(y0, BOT-total))
    al = ph.get('align', 'center')
    out = []
    for li, ln in enumerate(lines):
        wide = sum(x['w'] + int(x['h']*0.28) for x in ln)
        if al == 'left':    x = MARGIN
        elif al == 'right': x = W - MARGIN - wide
        else:               x = (W - wide)//2
        for it in ln:
            out.append({**it, 'x': x, 'y': y0 + li*lh})
            x += it['w'] + int(it['h']*0.28)
    return out

for ph in phrases:
    ph['items'] = layout(ph)

n = int(round(DUR*FPS))
for fi in range(n):
    t = fi/FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)) if GLOW else None
    d, ds = ImageDraw.Draw(im), ImageDraw.Draw(sh)
    dg = ImageDraw.Draw(gl) if gl else None
    for ph in phrases:
        if t < ph['s'] or t >= ph['out']: continue
        fade_out = 1.0
        if ph['out'] - t < 0.14: fade_out = max(0.0, (ph['out']-t)/0.14)
        for it in ph['items']:
            if t < it['sw']: continue
            a = min(1.0, (t-it['sw'])/FADE); a = (1-(1-a)**3)*fade_out
            rise = int((1-min(1.0, (t-it['sw'])/FADE))*14)
            x, y = it['x'], it['y']-rise
            if dg is not None:
                dg.text((x, y), it['t'], font=it['f'], fill=tuple(GLOW)+(int(255*a),),
                        stroke_width=5, stroke_fill=tuple(GLOW)+(int(255*a),))
            ds.text((x+3, y+7), it['t'], font=it['f'], fill=(0, 0, 0, int(215*a*SHADOW)))
            d.text((x, y), it['t'], font=it['f'], fill=(255, 255, 255, int(255*a)))
    out = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(17)), im)
    if gl is not None:
        for k in range(3):
            out = Image.alpha_composite(gl.filter(ImageFilter.GaussianBlur(8*(k+1))), out)
        out = Image.alpha_composite(out, im)
    out.save(f"{OUT}/h_{fi:04d}.png")
print(json.dumps({"frames": n, "phrases": len(phrases)}))
