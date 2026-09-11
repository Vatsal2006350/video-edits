#!/usr/bin/env python3
"""Kinetic serif hook: words arrive where they are spoken, cascade around the frame, and the
whole layer is meant to be composited BEHIND the speaker's matte.

Why the layout is spec-driven and not automatic: the speaker's silhouette decides what is
readable. Anything centred at torso height loses ~370px of letters behind the body; the
band above the head loses nothing. So the hero word goes above the head, and the words that
are allowed to be partly hidden go behind the chest and legs -- that is the effect.

Spec (JSON argv[1]):
  {"outdir": "...", "dur": 5.6, "fps": 30, "fade_out": 0.3,
   "items": [
     {"t": "WE'RE HOSTING", "at": 0.00, "x": 80,  "y": 296, "size": 58, "align": "left",  "from": "left"},
     {"t": "JACHACKS",      "at": 2.38, "y": 365, "size": 120, "align": "center", "hero": true},
     {"t": "AT UMICH",      "at": 4.82, "y": 1400, "size": 74, "align": "center", "logo": "logos/umich_block_m.png"}
   ]}
Each item slides in from `from` (left/right/up/scale), eases out over `fade`, then settles to
`ghost` opacity once the next item lands. `hero` items punch (scale 1.18 -> 1.0) with a glow
flash. Everything fades together over `fade_out` at the end.
"""
import sys, json, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

c     = json.loads(sys.argv[1])
W, H  = c.get('w', 1080), c.get('h', 1920)
FPS   = c.get('fps', 30)
DUR   = c['dur']
OUT   = c['outdir']
FONT  = c.get('font', '/Users/vatsalshah/Code/video-edits/fonts/PlayfairDisplay-BlackItalic.ttf')
GOLD  = tuple(c.get('fill', [255, 216, 128]))
GLOW  = tuple(c.get('glow', [255, 185, 50]))
FADE_OUT = c.get('fade_out', 0.30)
SAFE_L, SAFE_R = 59, 918
SAFE_T, SAFE_B = 278, 1536
os.makedirs(OUT, exist_ok=True)

items = c['items']
for i, it in enumerate(items):
    it['out'] = items[i + 1]['at'] if i + 1 < len(items) else DUR   # when the next word lands
    it['fade'] = it.get('fade', 0.26)
    it['ghost'] = it.get('ghost', 0.72)
    it['face'] = it.get('face', FONT)
    it['fill_c']   = tuple(it.get('fill', GOLD))
    it['shadow_c'] = tuple(it.get('shadow', [0, 0, 0]))
    it['shadow_a'] = it.get('shadow_alpha', 0.65)
    it['glow_on']  = it.get('glow', True)
    it['track']    = it.get('track', 0)          # extra px between letters for the sans words
    it['layer']    = it.get('layer', 'behind')   # 'behind' = under the matte, 'front' = over it
    it['hold']     = it.get('hold', None)        # seconds to stay after the next word lands
    it['life']     = it.get('life', None)        # OR: seconds after arrival, whichever is sooner
    it['leave_fade'] = it.get('leave_fade', 0.25)  # 0.06 = a hard cut to the next word
    # A centred word is bounded by twice the centre-to-rail distance (724px), not the box
    # width. Long words (OPPORTUNITY, SAN FRANCISCO) get shrunk until they fit rather than
    # clamped into the like button.
    MAXW = 2 * (SAFE_R - W // 2) - 12
    if it.get('cap_h'):
        probe = ImageFont.truetype(it['face'], 200); ch = probe.getbbox('H')[3] - probe.getbbox('H')[1]
        it['size'] = int(200 * it['cap_h'] / max(1, ch))
    while True:
        f = ImageFont.truetype(it['face'], it['size'])
        bb = f.getbbox(it['t'])
        if it['track']:
            bb = (bb[0], bb[1], bb[2] + it['track'] * (len(it['t']) - 1), bb[3])
        if it.get('squash_to') or bb[2] - bb[0] <= MAXW or it['size'] <= 40:
            break
        it['size'] -= 4
    it['font'] = f; it['bb'] = bb; it['tw'] = bb[2] - bb[0]; it['th'] = bb[3] - bb[1]
    al = it.get('align', 'center')
    if it.get('y_bottom'):
        it['y'] = it['y_bottom'] - it['th']
    if al == 'left':    it['x0'] = it['x']
    elif al == 'right': it['x0'] = it['x'] - it['tw']
    else:               it['x0'] = (W - it['tw']) // 2
    # hard guarantee: never past the rail, whatever the spec asked for
    it['x0'] = max(SAFE_L + 6, min(it['x0'], SAFE_R - 6 - it['tw']))
    if it.get('logo') and os.path.exists(it['logo']):
        lg = Image.open(it['logo']).convert('RGBA')
        lh = int(it['size'] * 1.05)
        it['logo_im'] = lg.resize((int(lg.width * lh / lg.height), lh))

def ease_out(p):  # cubic
    p = max(0.0, min(1.0, p)); return 1 - (1 - p) ** 3

def tracked(d, xy, txt, f, fill, track):
    if not track:
        d.text(xy, txt, font=f, fill=fill); return
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + track

def draw_word(layer, glowl, it, x, y, alpha, scale):
    f = it['font'] if scale == 1.0 else ImageFont.truetype(it['face'], max(8, int(it['size'] * scale)))
    bb = f.getbbox(it['t'])
    if it['track']:
        bb = (bb[0], bb[1], bb[2] + int(it['track'] * scale) * (len(it['t']) - 1), bb[3])
    # keep the word's centre fixed while it scales
    cx = x + it['tw'] / 2; cy = y + it['th'] / 2
    px = int(cx - (bb[2] - bb[0]) / 2 - bb[0]); py = int(cy - (bb[3] - bb[1]) / 2 - bb[1])
    # Hard guarantee, independent of every upstream calculation: the drawn ink (plus its
    # shadow) is shrunk and shifted into the IG safe box. Upstream fits catch the settled
    # position; this catches the entrance frames, where scale, tracking and shadow combine.
    sx_, sy_ = it.get('shadow_off', [4, 7])
    tr0 = int(it['track'] * scale)
    w_ink = (bb[2] - bb[0]) + tr0 * (len(it['t']) - 1) + max(0, sx_)
    h_ink = (bb[3] - bb[1]) + max(0, sy_)
    box_w, box_h = SAFE_R - SAFE_L - 16, SAFE_B - SAFE_T - 16
    if not it.get('squash_to') and (w_ink > box_w or h_ink > box_h):
        k = min(box_w / max(1, w_ink), box_h / max(1, h_ink))
        scale *= k
        f = ImageFont.truetype(it['face'], max(8, int(it['size'] * scale)))
        bb = f.getbbox(it['t'])
        if it['track']:
            bb = (bb[0], bb[1], bb[2] + int(it['track'] * scale) * (len(it['t']) - 1), bb[3])
        px = int(cx - (bb[2] - bb[0]) / 2 - bb[0]); py = int(cy - (bb[3] - bb[1]) / 2 - bb[1])
        w_ink = (bb[2] - bb[0]) + max(0, sx_); h_ink = (bb[3] - bb[1]) + max(0, sy_)
    if not it.get('squash_to'):
        px = max(SAFE_L + 8 - bb[0], min(px, SAFE_R - 8 - w_ink - bb[0]))
    py = max(SAFE_T + 8 - bb[1], min(py, SAFE_B - 8 - h_ink - bb[1]))
    if it.get('squash_to'):
        nat_w = (bb[2] - bb[0]) + int(it['track'] * scale) * (len(it['t']) - 1)
        tgt_w = min(nat_w, it['squash_to'])
        gh = (bb[3] - bb[1]) + 6
        tmp = Image.new('RGBA', (nat_w + 8, gh + 8), (0, 0, 0, 0))
        tracked(ImageDraw.Draw(tmp), (4 - bb[0], 4 - bb[1]), it['t'], f, it['fill_c'] + (int(255 * alpha),), int(it['track'] * scale))
        if tgt_w < nat_w:
            tmp = tmp.resize((tgt_w + 8, gh + 8), Image.LANCZOS)
        cxw = W // 2 - (tgt_w + 8) // 2
        cyy = int(cy - (gh + 8) / 2)
        cyy = max(SAFE_T + 4, min(cyy, SAFE_B - 4 - (gh + 8)))   # header/footer still respected
        layer.alpha_composite(tmp, (cxw, cyy))
        if it.get('logo_im') is not None:
            lg = it['logo_im']; layer.alpha_composite(lg, (cxw + tgt_w + 34, int(cy - lg.height / 2)))
        return
    a = int(255 * alpha)
    tr = int(it['track'] * scale)
    if it['glow_on']:
        tracked(ImageDraw.Draw(glowl), (px, py), it['t'], f, GLOW + (int(a * 0.8),), tr)
    d = ImageDraw.Draw(layer)
    sx, sy = it.get('shadow_off', [4, 7])
    tracked(d, (px + sx, py + sy), it['t'], f, it['shadow_c'] + (int(a * it['shadow_a']),), tr)
    tracked(d, (px, py), it['t'], f, it['fill_c'] + (a,), tr)
    if it.get('logo_im') is not None:
        lg = it['logo_im'].copy()
        if alpha < 1.0:
            al = lg.getchannel('A').point(lambda v: int(v * alpha)); lg.putalpha(al)
        layer.alpha_composite(lg, (px + (bb[2] - bb[0]) + 26, int(cy - lg.height / 2)))

n = int(round(DUR * FPS))
for fi in range(n):
    t = fi / FPS
    layers = {'behind': Image.new('RGBA', (W, H), (0, 0, 0, 0)), 'front': Image.new('RGBA', (W, H), (0, 0, 0, 0))}
    glows  = {'behind': Image.new('RGBA', (W, H), (0, 0, 0, 0)), 'front': Image.new('RGBA', (W, H), (0, 0, 0, 0))}
    end_fade = 1.0 if t < DUR - FADE_OUT else max(0.0, (DUR - t) / FADE_OUT)
    for it in items:
        if t < it['at']:
            continue
        p = ease_out((t - it['at']) / it['fade'])
        # settle back once the next word has landed, so the newest word owns the frame
        settled = it['ghost'] if (t >= it['out'] and not it.get('hero')) else 1.0
        leave = 1.0
        leave_at = None
        if it['hold'] is not None: leave_at = it['out'] + it['hold']
        if it['life'] is not None: leave_at = min(leave_at, it['at'] + it['life']) if leave_at else it['at'] + it['life']
        if leave_at is not None and t > leave_at:
            leave = max(0.0, 1 - (t - leave_at) / max(0.01, it['leave_fade']))
        if leave <= 0:
            continue
        alpha = p * settled * end_fade * leave
        # entrance
        layer = layers[it['layer']]; glowl = glows[it['layer']]
        x, y = it['x0'], it['y']
        frm = it.get('from', 'scale')
        travel = int(90 * (1 - p))
        if frm == 'cut':     travel = 0; p = 1.0
        if frm == 'left':    x = max(SAFE_L + 8, x - travel)
        elif frm == 'right': x = min(x + travel, SAFE_R - 8 - it['tw'])
        elif frm == 'up':    y = max(SAFE_T + 6, y - travel)
        scale = 1.0
        if it.get('hero'):
            # punch in -- but the arrival scale must still fit the centred limit (twice the
            # centre-to-rail distance), or the first frames of the hero cross the like button
            # -44 leaves room for the glow halo, which reaches ~14px past the glyph box
            max_s = min(1.18, (2 * (SAFE_R - W // 2) - 44) / max(1, it['tw']))
            scale = max_s - (max_s - 1.0) * p
            if t - it['at'] < 0.35:                # glow flash on arrival
                flash = 1 - (t - it['at']) / 0.35
                gl2 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                draw_word(Image.new('RGBA', (W, H)), gl2, it, x, y, flash * end_fade, scale)
                layers[it['layer']] = Image.alpha_composite(layer, gl2.filter(ImageFilter.GaussianBlur(16)))
                layer = layers[it['layer']]
        elif frm == 'scale':
            scale = 0.86 + 0.14 * p
        elif frm == 'cut':
            scale = 1.0
        # a slow breathing drift so held words never sit dead
        y += int(2 * math.sin((t - it['at']) * 1.6))
        for k in range(it.get('echo', 1)):
            # Kumar's three stacked copies are all full red; echo_alpha<1 gives the falloff if wanted
            draw_word(layer, glowl, it, x, y + k * it.get('echo_gap', 310), alpha * (1.0 if k == 0 else it.get('echo_alpha', 1.0) ** k), scale)
    for name, tag in (('behind', 'k'), ('front', 'f')):
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for rad in (5, 12):
            out = Image.alpha_composite(out, glows[name].filter(ImageFilter.GaussianBlur(rad)))
        out = Image.alpha_composite(out, layers[name])
        out.save(f'{OUT}/{tag}_{fi:04d}.png')
print(json.dumps({'frames': n, 'items': len(items)}))
