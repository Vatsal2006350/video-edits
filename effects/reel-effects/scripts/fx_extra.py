#!/usr/bin/env python3
"""Extra talking-head effects that plug into the vendored claude-video-effects engine.

Same CLI as fx.py (one effect, --plan, --still, --list). The vendored pack is NOT edited:
this file imports it, registers more effects with its @effect decorator, then runs its main().

  spotify-scroll   tilted lyric-style list scrolls behind you, the active row lights up
  tech-widgets     iOS calendar widget + black "reel views" widget pop in above your head
  glass-tunnel     reel cards fly outward past you like a tunnel, behind your head
  notes-app        Apple Notes card types a checklist and ticks it off
  story-portal     orange dot portal, then your clip lands inside an Instagram feed + story row
  yap-headline     bubbly pink headline pops in letter by letter with sticker stars and a cursor
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude-video-effects', 'scripts'))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import fx
from fx import (effect, clamp, ease_out, ease_back, ease_inout, font, text_img, rrect, shadowed, place, comp,
                card, vary, cached, to_np, heart, star, cursor, tick, above_head, face_chip)

INK, WHITE = (22, 22, 24), (255, 255, 255)
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
try:
    import json as _json
    FACTS = _json.load(open(os.path.join(REPO, 'channel-facts.json')))
except Exception:
    FACTS = {}
def fact(key, default=''):
    v = FACTS.get(key, {})
    if isinstance(v, dict) and v.get('use_on_screen') is False: return default
    return v.get('value', default) if isinstance(v, dict) else (v or default)
fx.CARD_FX = tuple(fx.CARD_FX) + ('glass-tunnel', 'story-portal', 'spotify-scroll', 'orbit-3d')
fx.ALIASES.update({'spotify': 'spotify-scroll', 'lyrics': 'spotify-scroll', 'widgets-ios': 'tech-widgets',
                   'tunnel': 'glass-tunnel', 'notes': 'notes-app', 'portal': 'story-portal', 'yap': 'yap-headline'})


def opts(e, **dflt):
    return {k: e.o.get(k, v) for k, v in dflt.items()}


def fade_io(c, e, tin=0.25, tout=0.25):
    return clamp(c.lt / tin) * clamp((e.d - c.lt) / tout)


# ------------------------------------------------------------------ spotify-scroll
def _thumb(i, s):
    """A little square 'album art' with a hue per row."""
    import colorsys
    r, g, b = [int(255 * v) for v in colorsys.hsv_to_rgb((i * 0.173 + 0.02) % 1, 0.55, 0.95)]
    r2, g2, b2 = [int(255 * v) for v in colorsys.hsv_to_rgb((i * 0.173 + 0.12) % 1, 0.7, 0.55)]
    grad = np.linspace(0, 1, s)[None, :, None]
    base = np.array([r, g, b], np.float32) * (1 - grad) + np.array([r2, g2, b2], np.float32) * grad
    im = Image.fromarray(np.repeat(base, s, 0).astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (s, s), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], int(s * 0.16), fill=255); im.putalpha(m)
    return im


@effect('spotify-scroll', 'a tilted Spotify-style list scrolls behind you, the active row glows')
def fx_spotify_scroll(c, e):
    o = opts(e, text='Notes App|Story Portal|Yap Headline|UGC Spin|Pull-back Reveal|Wiggle Type|Paper Labels|AI Video Studio|Bubble Script|Editorial Trio|Yellow Block|Crayon Mix',
             sub='Studio · new', speed=1.5, side='auto')
    names = str(o['text']).split('|'); n = len(names); sub = str(o['sub']); speed = float(o['speed'])
    colw = int(c.W * 0.62); rowh = int(c.W * 0.115); win_h = int(c.H * 0.80)
    rows = cached(e, 'rows', lambda: [_row(names[i], sub, i, colw, rowh) for i in range(n)])
    pos = c.lt * speed + 0.0                                   # in rows
    active = int(round(pos + 3.5)) % n                        # row sitting at the bright spot
    strip = np.zeros((win_h, colw, 4), np.float32)
    for k in range(-1, int(win_h / rowh) + 2):
        idx = int(math.floor(pos)) + k
        y = int(round((k - (pos - math.floor(pos))) * rowh))
        row = rows[idx % n]
        is_on = (idx % n) == active
        dist = abs((y + rowh / 2) / win_h - 0.55)
        a = (1.0 if is_on else 0.80) * (1 - clamp(dist * 1.05))
        lay = to_np(row)
        if y + rowh <= 0 or y >= win_h: continue
        y0, y1 = max(0, y), min(win_h, y + rowh); sl = lay[y0 - y:y1 - y]
        sl = sl.copy(); sl[..., 3] *= a
        dst = strip[y0:y1]
        ao = sl[..., 3:4] + dst[..., 3:4] * (1 - sl[..., 3:4])
        strip[y0:y1, :, :3] = np.where(ao > 1e-4, (sl[..., :3] * sl[..., 3:4] + dst[..., :3] * dst[..., 3:4] * (1 - sl[..., 3:4])) / np.maximum(ao, 1e-4), 0)
        strip[y0:y1, :, 3:4] = ao
    left = (c.fx > c.W * 0.5) if o['side'] == 'auto' else (o['side'] == 'left')
    left = not left if o['side'] == 'auto' else left          # list goes on the side with more room
    pre = strip.copy(); pre[..., :3] *= pre[..., 3:4]
    # perspective: far (top) edge shrinks and the whole block rakes upward toward the inside
    s0 = np.float32([[0, 0], [colw, 0], [colw, win_h], [0, win_h]])
    top_in = colw * 0.10
    if left: d0 = np.float32([[colw * 0.08, c.H * 0.16], [colw * 0.88, c.H * 0.10], [colw * 0.98, c.H * 0.86], [-colw * 0.04, c.H * 0.92]])
    else:    d0 = np.float32([[c.W - colw * 0.88, c.H * 0.10], [c.W - colw * 0.08, c.H * 0.16], [c.W + colw * 0.04, c.H * 0.92], [c.W - colw * 0.98, c.H * 0.86]])
    M = cv2.getPerspectiveTransform(s0, d0)
    out = cv2.warpPerspective(pre, M, (c.W, c.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = out[..., 3:4]; rgbv = np.where(a > 1e-3, out[..., :3] / np.maximum(a, 1e-3), 0)
    lay = np.concatenate([rgbv, a * fade_io(c, e, 0.35, 0.3)], -1)
    # dark scrim behind the list so it reads on any background
    scrim = np.clip(cv2.GaussianBlur(a[..., 0], (0, 0), c.W * 0.05) * 3.0, 0, 1) * 0.80 * fade_io(c, e, 0.35, 0.3)
    c.img = c.img * (1 - (scrim * (1 - c.m))[..., None])
    comp(c, lay.astype(np.float32), 0, 0, 1.0, behind=True)


def _row(name, sub, i, w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ts = int(h * 0.74); im.alpha_composite(_thumb(i, ts), (int(h * 0.08), (h - ts) // 2))
    x = int(h * 0.08) + ts + int(h * 0.20)
    d.text((x, int(h * 0.15)), name, font=font('uib', h * 0.31), fill=(255, 255, 255, 255))
    d.text((x, int(h * 0.55)), sub, font=font('uim', h * 0.21), fill=(200, 205, 200, 255))
    d.ellipse([w - h * 0.50, h * 0.40, w - h * 0.50 + h * 0.18, h * 0.40 + h * 0.18], fill=(30, 215, 96, 255) if i % 3 == 0 else (0, 0, 0, 0), outline=(235, 235, 235, 255), width=2)
    return im


# ------------------------------------------------------------------ tech-widgets
@effect('tech-widgets', 'an iOS calendar widget and a black reel-views widget pop in above your head')
def fx_tech_widgets(c, e):
    o = opts(e, day='FRIDAY', date='30', note='Post at 7pm', label='Views / 30 days', value=fact('views_last_30d', ''))   # never fall back to the flagged 8M (use_on_screen:false)
    s = int(c.W * 0.24)                                   # 0.24W at 0.28/0.72W keeps both inside the IG safe box (x 59-918)
    cal = rrect(s, s, s * 0.22, (252, 252, 250, 255)); d = ImageDraw.Draw(cal)
    d.text((s * 0.10, s * 0.09), str(o['day']).upper(), font=font('uib', s * 0.095), fill=(232, 56, 48, 255))
    d.text((s * 0.07, s * 0.20), str(o['date']), font=font('uib', s * 0.46), fill=INK + (255,))
    d.rounded_rectangle([s * 0.10, s * 0.72, s * 0.82, s * 0.90], s * 0.04, fill=(255, 232, 230, 255))
    d.text((s * 0.14, s * 0.735), str(o['note']), font=font('uim', s * 0.095), fill=(200, 60, 50, 255))
    vw = rrect(s, s, s * 0.22, (14, 14, 16, 255)); d = ImageDraw.Draw(vw)
    d.text((s * 0.10, s * 0.10), str(o['label']), font=font('uim', s * 0.10), fill=(170, 170, 176, 255))
    vs = fx.lines_fit([str(o['value'])], s * 0.80, 'uib', int(s * 0.34))
    d.text((s * 0.10, s * 0.28), str(o['value']), font=font('uib', vs), fill=WHITE + (255,))
    pts = [(0.10, .86), (.28, .78), (.42, .82), (.60, .62), (.78, .66), (.90, .46)]
    d.line([(s * x, s * y) for x, y in pts], fill=(52, 199, 89, 255), width=max(3, int(s * 0.03)), joint='curve')
    cy = above_head(c, s); fo = fade_io(c, e, 0.12, 0.25)
    for k, (im, x) in enumerate(((cal, c.W * 0.28), (vw, c.W * 0.72))):
        t0 = 0.0 + k * 0.18
        p = ease_back((c.lt - t0) / 0.38) if c.lt > t0 else 0
        bob = math.sin(c.lt * 2.2 + k * 1.7) * c.H * 0.004
        place(c, shadowed(im, 18, 12, 110), x, cy + bob + (1 - clamp(p)) * 40, 0.75 + 0.25 * p, (-3.5 if k == 0 else 3.5) * p, clamp(p) * fo, behind=True)


# ------------------------------------------------------------------ glass-tunnel
@effect('glass-tunnel', 'reel cards fly outward past you like a tunnel, behind your head')
def fx_glass_tunnel(c, e):
    o = opts(e, count=34, life=1.9)
    n = int(o['count']); life = float(o['life'])
    def setup():
        rnd = random.Random(11)
        return [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.30, 1.0), rnd.uniform(0.5, 1.0), rnd.uniform(0, life), rnd.randrange(10 ** 6)) for _ in range(n)]
    P = cached(e, 'P', setup)
    base = int(c.W * 0.20)
    cache = cached(e, 'cards', lambda: {})
    cx, cy = c.fx, c.fy + c.fw * 0.5
    fo = fade_io(c, e, 0.2, 0.3)
    order = sorted(P, key=lambda p: -(((c.lt - p[3]) % life) / life))
    for ang, rad, sz, off, seed in order:
        u = ((c.lt + off) % life) / life                       # 0 at the centre, 1 past the edge
        gate = clamp((c.lt + off) / 0.2)                       # no pop before the effect has started
        r = (u ** 1.6) * rad * c.W * 1.15
        sc = 0.18 + u * 1.5 * sz
        x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r * 1.35
        k = seed % max(1, len(e.cards))
        key = (k, int(base * 1.2))
        if key not in cache: cache[key] = fx.card(vary(e.cards[k], k) if e.cards else Image.new('RGB', (90, 160), (60, 60, 60)), key[1], 0.06)
        im = cache[key]
        a = clamp(u / 0.05) * (1 - clamp((u - 0.88) / 0.12)) * fo * gate
        rim = Image.new('RGBA', im.size, (0, 0, 0, 0))
        place(c, im, x, y, sc, math.degrees(math.atan2(y - cy, x - cx)) * 0.04, a, behind=True)


# ------------------------------------------------------------------ notes-app
@effect('notes-app', 'an Apple Notes card types a checklist and ticks it off')
def fx_notes_app(c, e):
    o = opts(e, text='Hook by second 3|Film one take|Claude edits, I approve|Post at 7pm', title='Tomorrow’s reel',
             date='30 October 2026 at 7:12 am', cps=17)
    items = str(o['text']).split('|'); cps = float(o['cps']); yel = (226, 160, 12, 255)
    W = int(c.W * 0.80); pad = int(W * 0.055); lh = int(W * 0.125)
    H = pad * 2 + int(W * 0.30) + lh * len(items) + int(W * 0.02)
    im = rrect(W, H, W * 0.05, (253, 251, 243, 255)); d = ImageDraw.Draw(im)
    d.text((pad, pad * 0.9), '‹ Notes', font=font('uib', W * 0.045), fill=yel); d.text((W - pad, pad * 0.9), 'Done', font=font('uib', W * 0.045), fill=yel, anchor='ra')
    d.text((pad, pad * 0.9 + W * 0.085), str(o['title']), font=font('uib', W * 0.083), fill=INK + (255,))
    d.text((pad, pad * 0.9 + W * 0.19), str(o['date']), font=font('uim', W * 0.032), fill=(150, 150, 150, 255))
    y0 = pad + int(W * 0.285)
    t = 0.45; f = font('uim', W * 0.062); bx = W * 0.062
    for i, it in enumerate(items):
        typed_n = int(clamp((c.lt - t) * cps / max(1, len(it)) * 1.0, 0, 1) * len(it)) if c.lt > t else 0
        done_at = t + len(it) / cps + 0.35
        y = y0 + i * lh; cyc = y + lh * 0.5
        done = c.lt >= done_at
        box = [pad, cyc - bx / 2, pad + bx, cyc + bx / 2]
        if c.lt > t - 0.1:
            if done:
                k = ease_back((c.lt - done_at) / 0.25)
                d.ellipse(box, fill=yel); tick(d, pad + bx * 0.24, cyc - bx * 0.32, bx * 0.55, WHITE + (255,), 4)
            else: d.ellipse(box, outline=(190, 190, 190, 255), width=3)
            txt = it[:typed_n]
            col = (140, 140, 140, 255) if done else INK + (255,)
            d.text((pad + bx * 1.6, cyc), txt, font=f, fill=col, anchor='lm')
            if done:
                d.line([(pad + bx * 1.6, cyc + 2), (pad + bx * 1.6 + f.getlength(it), cyc + 2)], fill=(140, 140, 140, 255), width=3)
            elif typed_n < len(it) or int(c.lt * 2.2) % 2 == 0:
                cx_ = pad + bx * 1.6 + f.getlength(txt) + 4
                d.line([(cx_, cyc - bx * 0.55), (cx_, cyc + bx * 0.55)], fill=yel, width=3)
        t = done_at + 0.12
    p = ease_back(c.lt / 0.4)
    cy = max(H / 2 + c.H * 0.045, min(c.fy - c.fw * 1.05 - H / 2, c.H * 0.30))
    cy = max(cy, H / 2 + c.H * 0.145)                           # stay below the IG top bar (y 278 is the box edge)
    place(c, shadowed(im, 20, 12, 100), 495 * c.W / 1080, cy - (1 - clamp(p)) * 60, 0.9 + 0.1 * p, 0, fade_io(c, e, 0.12, 0.25), behind=True)


# ------------------------------------------------------------------ story-portal
def _dots(c, prog, W, H, cell, col):
    """Orange halftone: dot radius follows a wave out from the centre; prog 0..1 sweeps through and back."""
    gx, gy = np.meshgrid(np.arange(0, W, cell), np.arange(0, H, cell))
    dist = np.hypot(gx - W / 2, (gy - H / 2) * 0.62) / (W * 0.85)
    r = np.clip((prog * 1.5 - dist) * 2.2, 0, 1) * cell * 0.62
    lay = np.zeros((H, W, 4), np.float32)
    for x, y, rr in zip(gx.ravel(), gy.ravel(), r.ravel()):
        if rr > 0.6: cv2.circle(lay, (int(x + cell / 2), int(y + cell / 2)), int(round(rr)), (*[v / 255 for v in col], 1.0), -1, cv2.LINE_AA)
    return lay


@effect('story-portal', 'an orange dot portal, then your clip lands inside an Instagram feed with a story row')
def fx_story_portal(c, e):
    o = opts(e, handle=FACTS.get('handle', 'your.handle'), caption='one clip, seven different edits...', likes=fact('max_likes_single_reel', ''), comments='', shares='', cell=38)
    t = c.lt; W, H = c.W, c.H
    wave = clamp(t / 0.75) if t < 0.75 else clamp(1 - (t - 0.75) / 0.6)
    in_ui = t > 0.75 and (e.d - t) > 0.0
    if in_ui:
        base = c.img.copy()
        ui = np.zeros_like(base) + np.array([0.04, 0.04, 0.05], np.float32)
        pw = W; ph = int(W * 1.10)
        top = int(H * 0.245)
        # post (the clip itself, centre-cropped to 4:5, person kept at the top of the crop)
        src = cv2.resize(base, (W, H)); y0 = int(H * 0.12); crop = src[y0:y0 + ph]
        ui[top:top + ph] = crop
        pil = Image.fromarray((np.clip(ui, 0, 1) * 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(pil)
        d.text((W * 0.5, H * 0.045), 'Instagram', font=font('serif', W * 0.09), fill=WHITE + (255,), anchor='mm')
        d.text((W * 0.06, H * 0.045), '+', font=font('uib', W * 0.09), fill=WHITE + (255,), anchor='mm')
        pil.alpha_composite(heart(int(W * 0.07), (255, 255, 255)), (int(W * 0.89), int(H * 0.028)))
        # story row: your face + cover rings
        face = face_chip(c, e, W * 0.17)
        ring_y = int(H * 0.062); rx = [W * 0.14, W * 0.34, W * 0.54, W * 0.74, W * 0.94]
        for k, x in enumerate(rx):
            r = W * 0.095
            if k == 0: pil.alpha_composite(face, (int(x - face.width / 2), int(ring_y + H * 0.01)))
            else:
                src_im = e.cards[k % len(e.cards)] if e.cards else None
                if src_im is not None:
                    ph_ = card(src_im, int(W * 0.13), 0.5).crop((0, 0, 1, 1)) and None
                d.ellipse([x - r, ring_y + H * 0.010, x + r, ring_y + H * 0.010 + 2 * r], outline=(255, 140, 60, 255), width=5)
                if e.cards:
                    cc = e.cards[k % len(e.cards)].convert('RGB').resize((int(2 * r - 14), int(2 * r - 14)), Image.LANCZOS).convert('RGBA')
                    mk = Image.new('L', cc.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, cc.width - 1, cc.height - 1], fill=255); cc.putalpha(mk)
                    pil.alpha_composite(cc, (int(x - r + 7), int(ring_y + H * 0.010 + 7)))
            nm = ['Your story', 'cover.studies', 'ugc.club', 'daily.reels', 'edits'][k]
            d.text((x, ring_y + H * 0.010 + 2 * r + H * 0.012), nm, font=font('uim', W * 0.028), fill=(200, 200, 205, 255), anchor='mm')
        d.ellipse([W * 0.03, top - H * 0.052, W * 0.03 + W * 0.07, top - H * 0.052 + W * 0.07], fill=(120, 120, 130, 255))
        d.text((W * 0.12, top - H * 0.040), str(o['handle']), font=font('uib', W * 0.036), fill=WHITE + (255,), anchor='lm')
        d.text((W * 0.12, top - H * 0.022), 'Original audio', font=font('uim', W * 0.028), fill=(190, 190, 196, 255), anchor='lm')
        fy_ = top + ph + H * 0.022
        pil.alpha_composite(heart(int(W * 0.05)), (int(W * 0.035), int(fy_ - W * 0.025)))
        d.text((W * 0.095, fy_), str(o['likes']), font=font('uib', W * 0.036), fill=WHITE + (255,), anchor='lm')
        bx_ = W * 0.30; d.ellipse([bx_, fy_ - W * 0.022, bx_ + W * 0.044, fy_ + W * 0.022], outline=WHITE + (255,), width=4)
        if str(o['comments']): d.text((W * 0.355, fy_), str(o['comments']), font=font('uib', W * 0.036), fill=WHITE + (255,), anchor='lm')
        px_ = W * 0.52 if str(o['comments']) else W * 0.42; d.polygon([(px_, fy_ - W * 0.002), (px_ + W * 0.05, fy_ - W * 0.025), (px_ + W * 0.032, fy_ + W * 0.026)], outline=WHITE + (255,), width=4)
        if str(o['shares']): d.text((px_ + W * 0.065, fy_), str(o['shares']), font=font('uib', W * 0.036), fill=WHITE + (255,), anchor='lm')
        d.text((W * 0.04, fy_ + H * 0.030), str(o['handle']) + ' ' + str(o['caption']), font=font('uim', W * 0.034), fill=WHITE + (255,), anchor='lm')
        k_in = ease_out((t - 0.75) / 0.35); k_out = clamp((e.d - t) / 0.2)
        arr = np.asarray(pil.convert('RGB'), np.float32) / 255
        a = min(k_in, k_out)
        c.img = base * (1 - a) + arr * a
    if wave > 0:
        lay = cached(e, 'dots%d' % int(wave * 14), lambda: _dots(c, wave, W, H, int(o['cell']), (255, 128, 48)))
        a = lay[..., 3:4]; c.img = c.img * (1 - a * 0.97) + lay[..., :3] * a * 0.97


# ------------------------------------------------------------------ yap-headline
@effect('yap-headline', 'a bubbly pink headline pops in letter by letter with sticker stars and a cursor click')
def fx_yap_headline(c, e):
    o = opts(e, text='YAP STYLE|CONTENT', sub='(for when you…)', color='ff9fc8', stroke='ffd9ea')
    lines = str(o['text']).split('|'); pink = fx.rgb(o['color'], (255, 159, 200)); edge = fx.rgb(o['stroke'], (255, 217, 234))
    size = fx.lines_fit(lines, c.W * 0.80, 'bold', int(c.W * 0.20))
    lh = size * 1.08; cy0 = max(c.H * 0.20, above_head(c, 0) - lh * len(lines) * 0.2) if False else min(c.fy - c.fw * 1.25, c.H * 0.34) - lh * (len(lines) - 1) / 2
    cy0 = max(cy0, c.H * 0.235)
    fo = fade_io(c, e, 0.05, 0.25); n_before = 0; last = None
    for li, line in enumerate(lines):
        f = font('bold', size); tw = f.getlength(line); x = c.W / 2 - tw / 2 + (li - (len(lines) - 1) / 2) * size * 0.05
        for ch in line:
            adv = f.getlength(ch); 
            if ch != ' ':
                t0 = 0.10 + n_before * 0.045; p = ease_back((c.lt - t0) / 0.28) if c.lt > t0 else 0
                if p > 0:
                    gi = text_img(ch, size, 'bold', fill=pink, stroke=int(size * 0.045), stroke_fill=edge, shadow=int(size * 0.05), glow=((255, 120, 190), int(size * 0.10)))
                    wob = math.sin(c.lt * 5 + n_before) * 1.2
                    place(c, gi, x + adv / 2, cy0 + li * lh + (1 - clamp(p)) * -size * 0.5, 0.4 + 0.6 * p, wob + (1 - clamp(p)) * 18 * (1 if n_before % 2 else -1), clamp(p) * fo, behind=True)
                    last = (x + adv / 2, cy0 + li * lh)
            x += adv; n_before += 1
    t_all = 0.10 + n_before * 0.045 + 0.2
    sub = str(o['sub'])
    if sub:
        p = clamp((c.lt - t_all) / 0.3)
        im = text_img(sub, int(size * 0.26), 'serif', fill=(255, 235, 245), shadow=int(size * 0.02))
        place(c, im, c.W / 2, cy0 + lh * (len(lines) - 0.2) + size * 0.2, 1, 0, p * fo, behind=True)
    sx = [(0.10, -0.55, 'star', (255, 150, 200), 0.20), (0.07, 0.70, 'star', (190, 160, 255), 0.17), (0.90, 0.78, 'heart', (255, 120, 190), 0.14), (0.935, -0.42, 'heart', (255, 140, 200), 0.10)]
    for k, (fx_, fy_, kind, col, sz) in enumerate(sx):
        t0 = 0.25 + k * 0.17; p = ease_back((c.lt - t0) / 0.35) if c.lt > t0 else 0
        if p <= 0: continue
        s = int(c.W * sz); im = star(s, col) if kind == 'star' else heart(s, col)
        place(c, im, c.W * fx_, cy0 + lh * (len(lines) - 1) / 2 + fy_ * lh * 1.1, 0.5 + 0.5 * p, math.sin(c.lt * 3 + k) * 8 + (-12 if k % 2 else 12), clamp(p) * fo)
    if last and c.lt > t_all:
        q = ease_inout((c.lt - t_all) / 0.55)
        cs = int(c.W * 0.055); sx0, sy0 = c.W * 0.72, cy0 + lh * (len(lines) - 1) + size * 0.9
        cx_ = sx0 + (last[0] + size * 0.15 - sx0) * q; cy_ = sy0 + (last[1] - size * 0.1 - sy0) * q
        place(c, cursor(cs), cx_ + cs * 0.4, cy_ + cs * 0.6, 1.0 - 0.15 * math.sin(clamp((c.lt - t_all - 0.55) / 0.2) * math.pi), 0, fo)


import fx_world  # 12 world-bending effects (halo-rays ... shockwave); registers on the same engine
if os.environ.get('FX_MATTE'):     # HQ RVM cut-out + decontaminated edges for every effect (fx_hq.py)
    import fx_hq; fx_hq.wrap_all()


def _check_mode():
    """--check: render a still at the middle of every effect in the plan and tile them into one sheet to Read."""
    import json
    a = sys.argv; a.remove('--check')
    if '--plan' in a: plan = json.load(open(a[a.index('--plan') + 1])); plan = plan.get('effects', plan) if isinstance(plan, dict) else plan
    else:
        st = float(a[a.index('--start') + 1]) if '--start' in a else 0.0; en = float(a[a.index('--end') + 1]) if '--end' in a else st + 3
        plan = [{'start': st, 'end': en}]
    mids = ','.join(f"{(float(d['start']) + min(float(d['end']), float(d['start']) + 6)) / 2:.2f}" for d in plan)
    dst = a[-1]
    if not dst.endswith('.png'): sys.exit('--check needs a .png output path (the sheet is written next to it)')
    a += ['--still', mids]
    fx.main()
    import glob
    base = dst[:-4]; fs = sorted((f for f in glob.glob(base + '_*.png') if not f.endswith('_sheet.png')), key=lambda f: float(f[len(base) + 1:-4])) or [dst]
    ims = [Image.open(f).convert('RGB') for f in fs]; h = 640; ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    sheet = Image.new('RGB', (sum(i.width for i in ims) + 8 * (len(ims) - 1), h), (20, 20, 20)); x = 0
    for i in ims: sheet.paste(i, (x, 0)); x += i.width + 8
    sheet.save(base + '_sheet.png'); print('CHECK SHEET:', base + '_sheet.png')


if __name__ == '__main__':
    if '--check' in sys.argv: _check_mode()
    else: fx.main()
