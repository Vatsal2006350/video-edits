"""World-bending effects: they change the ROOM (or the picture itself), not add a card on top.

Imported by fx_extra.py, registered on the same vendored engine. Every effect is a pure function
of the current frame + time (no frame history), so `--still` / `--check` show exactly what renders.

  halo-rays      gold light rays + embers burst from behind your head, the room dims
  neon-trace     a neon line draws itself around your outline, the room goes dark
  ascii-room     the room turns into live terminal ASCII, you stay real
  halftone-pop   comic halftone room in two inks, white sticker outline around you
  speed-lines    anime speed lines behind you with a punch-in
  teleport       the room behind you swaps place to place with a flash (needs images=folder)
  paper-tear     the picture rips open across the middle and a proof image / word shows in the gap
  chroma-quake   an RGB-split glitch hit that decays in a third of a second
  vhs-tape       VHS throwback: chroma bleed, tracking band, PLAY + your date stamp
  road-to-10k    follower progress card: real count from channel-facts, bar fills to the goal
  kaleido-room   the room folds into a slow kaleidoscope around your head
  shockwave      a ring ripples out from your chest and bends the room as it passes
"""
import os, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import fx
from fx import effect, clamp, ease_out, ease_back, ease_inout, font, text_img, rrect, shadowed, place, comp, cached, camera

MAIZE, BLUE, INK = (255, 203, 5), (0, 39, 76), (22, 22, 24)
LUM = np.float32([0.299, 0.587, 0.114])


def opts(e, **dflt): return {k: e.o.get(k, v) for k, v in dflt.items()}
def env(c, e, tin=0.25, tout=0.25): return clamp(c.lt / tin) * clamp((e.d - c.lt) / tout)
def col(v, d): return np.float32(fx.rgb(v, d)) / 255.0
def lum(img): return img @ LUM
def frame_seed(c, every=1): return int(round(c.t * c.fps)) // max(1, every)


def soft_matte(c, k=5):
    """The engine matte, feathered a touch so swapped rooms do not show a hard cut-out line.
    With the HQ RVM matte (fx_hq.py, FX_MATTE) it is already soft and strand-accurate: use it as is."""
    if hasattr(c, 'F'): return c.m[..., None]
    return cv2.GaussianBlur(c.m, (0, 0), k)[..., None]


def fg(c):
    """Foreground colour for the 'you' side of a matting composite: RVM's decontaminated F when the HQ
    matte is loaded, else the frame. Using the frame keeps wall colour in hair edges (white rim)."""
    return c.F if hasattr(c, 'F') else c.img


def set_bg(c, bg, a=1.0, feather=3):
    m = soft_matte(c, feather)
    c.img = c.img * (1 - a) + fg(c) * (m * a) + bg * ((1 - m) * a)


def clean_room(c):
    """The room with you painted out (normalised blur of everything that is not you), so warped rooms
    do not carry ghost copies of your head (first kaleido-room still, 2026-11-12)."""
    w = 1 - cv2.dilate(c.m, np.ones((25, 25), np.uint8)); s = c.W * 0.06
    fill = cv2.GaussianBlur(c.img * w[..., None], (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-3)[..., None]
    return c.img * w[..., None] + fill * (1 - w[..., None])


def polar(c, cx, cy, s=2):
    """Angle and radius maps at 1/s resolution (full-res arctan2 every frame is the slow part)."""
    h, w = c.H // s, c.W // s
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx * s - np.float32(cx), yy * s - np.float32(cy)        # c.fx is a float64 scalar: keep maps float32 for cv2.remap
    return np.arctan2(dy, dx).astype(np.float32), np.sqrt(dx * dx + dy * dy).astype(np.float32), (w, h)


def up(a, c): return cv2.resize(np.asarray(a, np.float32), (c.W, c.H), interpolation=cv2.INTER_LINEAR)


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * s + 0.5)), max(h, int(im.height * s + 0.5))), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def load_images(e):
    """images=<folder> or image=<file>. Returns PIL RGB list (may be empty)."""
    def go():
        out = []; p = e.o.get('image')
        if p and os.path.isfile(os.path.expanduser(p)): out.append(Image.open(os.path.expanduser(p)).convert('RGB'))
        d = e.o.get('images')
        if d and os.path.isdir(os.path.expanduser(d)):
            d = os.path.expanduser(d)
            for n in sorted(os.listdir(d)):
                if n.lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'webp'): out.append(Image.open(os.path.join(d, n)).convert('RGB'))
        return out
    return cached(e, 'imgs', go)


# ------------------------------------------------------------------ halo-rays
@effect('halo-rays', 'gold light rays and embers burst from behind your head while the room dims')
def fx_halo_rays(c, e):
    o = opts(e, color='ffb347', dim=0.72, embers=46, spin=0.22)
    a = env(c, e, 0.35, 0.4); tint = col(o['color'], (255, 198, 90))
    burst = 1 + 0.9 * math.exp(-c.lt / 0.25)                        # brighter on the hit, then settles
    th, r, _ = polar(c, c.fx, c.fy - c.fw * 0.1, 3)
    t = c.lt * float(o['spin'])
    rays = (0.5 + 0.5 * np.sin(th * 9 + t * 2.1)) ** 3 * 0.55 + (0.5 + 0.5 * np.sin(th * 23 - t * 3.3 + 1.7)) ** 6 * 0.6 \
        + (0.5 + 0.5 * np.sin(th * 5 + t)) ** 2 * 0.25
    fall = np.exp(-r / (c.W * 0.95)); core = np.exp(-(r / (c.fw * 1.9)) ** 2)
    light = np.clip(up((rays * fall * 0.50 + core * 0.45).astype(np.float32), c)[..., None] * a * burst, 0, 0.92)
    m = soft_matte(c, 4)
    g = lum(c.img)[..., None]
    room = (g + (c.img - g) * 0.55) * (1 - float(o['dim']) * a)   # dim + desaturate the room only
    c.img = c.img * m + room * (1 - m)
    lit = 1 - (1 - room) * (1 - light * tint)                      # screen, so a white wall cannot blow out
    c.img = fg(c) * m * (1 + 0.06 * a) + lit * (1 - m)
    rnd = random.Random(7); lay = np.zeros((c.H // 2, c.W // 2), np.float32)
    for i in range(int(o['embers'])):
        x0, sp, ph, sz = rnd.uniform(0, 1), rnd.uniform(0.05, 0.16), rnd.uniform(0, 1), rnd.uniform(1.2, 3.4)
        u = (ph + c.lt * sp) % 1
        x = (x0 + 0.03 * math.sin(c.lt * 1.3 + i)) * c.W / 2; y = (1.05 - u * 1.1) * c.H / 2
        cv2.circle(lay, (int(x), int(y)), int(sz + 0.5), float(math.sin(u * math.pi)) * (0.6 + 0.4 * math.sin(c.lt * 7 + i)), -1, cv2.LINE_AA)
    lay = up(cv2.GaussianBlur(lay, (0, 0), 2.2) * 1.6 + lay, c)[..., None] * a
    c.img += lay * np.float32([1.0, 0.78, 0.42]) * (1 - m * 0.75)
    fx.vignette(c, 0.30 * a)


# ------------------------------------------------------------------ neon-trace
@effect('neon-trace', 'a neon line draws itself around your outline and the room goes dark')
def fx_neon_trace(c, e):
    o = opts(e, color='39f6ff', color2='ff3df2', dim=0.72, draw=0.7, width=7)
    a = env(c, e, 0.15, 0.3)
    k = max(3, int(o['width']) | 1)
    # outline the SOLID silhouette: with the RVM matte, wispy curls sit at 0.3-0.7 alpha and a 0.5 cut
    # turned them into a white/neon blob beside the head (2026-11-12)
    mb = (cv2.GaussianBlur(c.m, (0, 0), 3) > (0.82 if hasattr(c, 'F') else 0.5)).astype(np.uint8)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    edge = (cv2.dilate(mb, ker) - cv2.erode(mb, ker)).astype(np.float32)
    ys, xs = np.nonzero(mb)
    cx, cy = (xs.mean(), ys.mean()) if len(xs) else (c.fx, c.fy)
    th, _, _ = polar(c, cx, cy, 2)
    ang = up(((th + math.pi * 1.5) % (2 * math.pi)) / (2 * math.pi), c)       # 0 at the top, clockwise
    p = ease_inout(c.lt / max(0.1, float(o['draw'])))
    edge = edge * np.clip((p * 1.04 - ang) / 0.03, 0, 1)                      # the line draws on round the body
    flick = 0.88 + 0.12 * math.sin(c.lt * 41) * math.sin(c.lt * 13)
    g1 = cv2.GaussianBlur(edge, (0, 0), 5); g2 = cv2.GaussianBlur(edge, (0, 0), 26)
    c1, c2 = col(o['color'], (57, 246, 255)), col(o['color2'], (255, 61, 242))
    mix = (0.5 + 0.5 * np.sin(ang * 2 * math.pi * 2 + c.lt * 1.4))[..., None]
    tint = c1 * mix + c2 * (1 - mix)
    m = soft_matte(c, 3); g = lum(c.img)[..., None]
    room = (g + (c.img - g) * 0.35) * (1 - float(o['dim']) * a)
    c.img = fg(c) * m * (1 - 0.18 * a) + room * (1 - m)
    c.img += ((g1 * 1.5 + g2 * 1.25)[..., None] * tint + (cv2.GaussianBlur(edge, (0, 0), 1.2) * 0.95)[..., None]) * a * flick


# ------------------------------------------------------------------ ascii-room
_RAMP = ' .,:;-~=+*xo%#&$@'
def _atlas(cell_w, cell_h):
    f = None
    for path, idx in (('/System/Library/Fonts/Menlo.ttc', 1), ('/System/Library/Fonts/Menlo.ttc', 0), (fx.FONT['mono'], 0)):
        try:
            from PIL import ImageFont
            f = ImageFont.truetype(path, int(cell_h * 0.95), index=idx); break
        except Exception: continue
    out = np.zeros((len(_RAMP), cell_h, cell_w), np.float32)
    for i, ch in enumerate(_RAMP):
        im = Image.new('L', (cell_w, cell_h), 0)
        ImageDraw.Draw(im).text((cell_w / 2, cell_h / 2), ch, font=f, fill=255, anchor='mm')
        out[i] = np.asarray(im, np.float32) / 255
    return out


@effect('ascii-room', 'the room turns into live terminal ASCII while you stay real')
def fx_ascii_room(c, e):
    o = opts(e, color='d97757', cols=58, bg='0d0d0f', wipe=0.45, you=0)
    cols = int(o['cols']); cw = c.W // cols; ch = int(cw * 1.8); rows = c.H // ch + 1; cols = c.W // cw + 1
    at = cached(e, 'atlas', lambda: _atlas(cw, ch))
    small = cv2.resize(lum(c.img), (cols, rows), interpolation=cv2.INTER_AREA)
    detail = np.abs(cv2.Laplacian(small, cv2.CV_32F, ksize=3)) * 3.0             # edges read even on a flat wall
    rank = np.argsort(np.argsort(small, axis=None)).reshape(small.shape) / small.size
    small = np.clip(0.55 * rank + 0.25 * small + detail, 0, 1) * 0.80
    rs = np.random.RandomState(frame_seed(c, 3))
    idx = np.clip((small * (len(_RAMP) - 1) + rs.uniform(-0.6, 0.6, small.shape)).round().astype(int), 0, len(_RAMP) - 1)
    glyph = at[idx].transpose(0, 2, 1, 3).reshape(rows * ch, cols * cw)[:c.H, :c.W]
    if glyph.shape != (c.H, c.W): glyph = cv2.copyMakeBorder(glyph, 0, c.H - glyph.shape[0], 0, c.W - glyph.shape[1], cv2.BORDER_CONSTANT, value=0)
    bright = cv2.resize(small, (c.W, c.H), interpolation=cv2.INTER_NEAREST)
    tint = col(o['color'], (217, 119, 87)); base = col(o['bg'], (13, 13, 15))
    art = base + glyph[..., None] * (tint * (0.45 + 0.75 * bright[..., None]) + 0.25 * bright[..., None] ** 3)
    art *= (0.90 + 0.10 * (np.arange(c.H) % 3 != 0))[:, None, None]             # faint scanlines
    p = ease_inout(c.lt / max(0.05, float(o['wipe']))) * clamp((e.d - c.lt) / 0.25)
    yy = np.arange(c.H, dtype=np.float32)[:, None, None] / c.H
    head = np.clip((p * 1.15 - yy) / 0.02, 0, 1)                               # top-to-bottom wipe with a bright scan head
    scan = np.exp(-((yy - p * 1.15) / 0.012) ** 2) * (p < 0.999)
    if str(o['you']) in ('1', 'true', 'yes'):
        c.img = c.img * (1 - head) + art * head
    else:
        m = soft_matte(c, 2); c.img = c.img * (1 - head) + fg(c) * (m * head) + art * (head * (1 - m))
    c.img += scan * tint * 0.9


# ------------------------------------------------------------------ halftone-pop
@effect('halftone-pop', 'the room becomes a two-ink comic halftone and you get a white sticker outline')
def fx_halftone_pop(c, e):
    o = opts(e, paper='ffcb05', ink='00274c', cell=22, outline=14, text='', angle=28)
    paper, ink = col(o['paper'], MAIZE), col(o['ink'], BLUE)
    s = float(o['cell']) * c.W / 1080; an = math.radians(float(o['angle']))
    def grid():
        yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
        u = xx * math.cos(an) + yy * math.sin(an); v = -xx * math.sin(an) + yy * math.cos(an)
        return np.sqrt(((u % s) - s / 2) ** 2 + ((v % s) - s / 2) ** 2) / (s * 0.5)
    d = cached(e, 'grid', grid)
    g = cv2.GaussianBlur(lum(c.img), (0, 0), s * 0.45)
    g = np.clip((g - 0.12) / 0.70, 0, 1)
    dots = np.clip((np.sqrt(1 - g) * 1.30 - d) / 0.10, 0, 1)[..., None]       # dark areas -> big ink dots
    art = paper * (1 - dots) + ink * dots
    pin = ease_back(c.lt / 0.32) * clamp((e.d - c.lt) / 0.2); a = clamp(c.lt / 0.10) * clamp((e.d - c.lt) / 0.2)
    c.img_src = fg(c).copy()
    c.img = c.img * (1 - a) + art * a
    txt = str(o['text'])
    if txt:
        lines = txt.split('|'); size = fx.lines_fit(lines, c.W * 0.66, 'anton', int(c.W * 0.42))   # 0.66W: centred text must fit 724 px (IG rail)
        y0 = max(c.H * 0.16 + size * 0.55, c.fy - c.fw * 1.9 - size * (len(lines) - 1) * 0.5)
        for i, ln in enumerate(lines):
            im = text_img(ln, size, 'anton', fill=tuple(int(v * 255) for v in ink), stroke=int(size * 0.035), stroke_fill=(255, 255, 255))
            place(c, im, c.W / 2, y0 + i * size * 1.02, 0.6 + 0.4 * pin, -4, a, behind=True)
    # outline the SOLID silhouette: with the RVM matte, wispy curls sit at 0.3-0.7 alpha and a 0.5 cut
    # turned them into a white/neon blob beside the head (2026-11-12)
    mb = (cv2.GaussianBlur(c.m, (0, 0), 3) > (0.82 if hasattr(c, 'F') else 0.5)).astype(np.uint8)
    k = max(3, int(float(o['outline']) * c.W / 1080 * max(0.01, pin)) * 2 + 1)
    ring = cv2.dilate(mb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(np.float32)
    ring = cv2.GaussianBlur(ring, (0, 0), 1.2)[..., None]
    sh = np.roll(np.roll(ring, int(c.W * 0.012), 0), int(c.W * 0.008), 1) * 0.55 * a
    c.img = c.img * (1 - sh) + ink * 0.25 * sh
    c.img = c.img * (1 - ring * a) + np.float32([1, 1, 1]) * ring * a
    m = soft_matte(c, 1.5)
    you = np.clip((c.img_src - 0.5) * 1.12 + 0.5, 0, 1)
    c.img = c.img * (1 - m) + you * m
    del c.img_src


# ------------------------------------------------------------------ speed-lines
@effect('speed-lines', 'anime speed lines shoot in behind you with a quick punch-in')
def fx_speed_lines(c, e):
    o = opts(e, color='auto', zoom=1.14, density=0.62, inner=1.7, dark=0.0)
    a = env(c, e, 0.08, 0.18)
    z = 1 + (float(o['zoom']) - 1) * ease_out(c.lt / 0.18) * clamp((e.d - c.lt) / 0.25)
    fx.face_cam(c, z, c.fy / c.H)
    th, r, _ = polar(c, c.fx, c.fy, 2)
    rs = np.random.RandomState(frame_seed(c, 1)); n = 420           # new lines every frame: every-2nd-frame read as a 15 fps strobe (motion-qc, 2026-11-12)
    on = (rs.uniform(0, 1, n) < float(o['density'])).astype(np.float32) * rs.uniform(0.5, 1, n)
    start = rs.uniform(0.75, 1.5, n) * c.fw * float(o['inner'])
    bi = ((th + math.pi) / (2 * math.pi) * n).astype(int) % n
    frac = ((th + math.pi) / (2 * math.pi) * n) % 1
    lines = on[bi] * np.clip((r - start[bi]) / (c.W * 0.10), 0, 1) * np.clip(1 - np.abs(frac - 0.5) * 2.4 * (1 - np.clip(r / (c.W * 1.4), 0, 0.75)), 0, 1)
    lines = up(lines.astype(np.float32), c)[..., None] * a
    m = soft_matte(c, 2)
    c.img *= 1 - float(o['dark']) * a * (1 - m)
    if str(o['color']) == 'auto':                                                 # white lines vanish on a white wall
        room = float((lum(c.img) * (1 - c.m)).sum() / max(1.0, float((1 - c.m).sum())))
        ink = np.float32([0.05, 0.05, 0.07]) if room > 0.55 else np.float32([1, 1, 1])
    else: ink = col(o['color'], (255, 255, 255))
    c.img = c.img * (1 - lines) + fg(c) * (lines * m) + ink * (lines * (1 - m))


# ------------------------------------------------------------------ teleport
@effect('teleport', 'the room behind you swaps from place to place with a white flash on each jump')
def fx_teleport(c, e):
    o = opts(e, text='', hold=0, flash=0.14, wrap=0.35)
    ims = load_images(e)
    if not ims:
        raise SystemExit("teleport needs real places: pass images=<folder of photos> (his own photos; never stock or someone else's reel)")
    n = len(ims); seg = float(o['hold']) or e.d / n
    i = min(n - 1, int(c.lt / seg)); u = (c.lt - i * seg) / seg; lt = c.lt - i * seg
    key = ('bg', i)
    if key not in e.state:
        e.state.clear() if False else None
        e.state[key] = np.asarray(cover(ims[i], int(c.W * 1.16), int(c.H * 1.16)), np.float32) / 255
    big = e.state[key]
    z = 1.16 - 0.10 * ease_out(lt / 0.5) - 0.05 * u                              # snap in, then a slow push
    w, h = int(c.W * z / 1.16 * 1.0), int(c.H * z / 1.16 * 1.0)
    w, h = min(big.shape[1], max(c.W // 2, int(big.shape[1] * (1 / z) * 1.0))), min(big.shape[0], max(c.H // 2, int(big.shape[0] * (1 / z))))
    x0, y0 = (big.shape[1] - w) // 2, (big.shape[0] - h) // 2
    bg = cv2.resize(big[y0:y0 + h, x0:x0 + w], (c.W, c.H), interpolation=cv2.INTER_LINEAR)
    m = soft_matte(c, 2.5)
    wrap = cv2.GaussianBlur(bg, (0, 0), 30) * float(o['wrap'])                    # light wrap: the new room's colour spills onto your edges
    edge = np.clip(cv2.GaussianBlur(c.m, (0, 0), 9)[..., None] * (1 - cv2.erode(c.m, np.ones((15, 15), np.uint8))[..., None]), 0, 1)
    tone = cv2.GaussianBlur(bg, (0, 0), 80).mean(axis=(0, 1))
    you = fg(c) * (0.86 + 0.28 * tone / max(1e-3, float(tone.mean())))           # nudge your colour toward the room
    c.img = bg * (1 - m) + (you * (1 - edge * 0.5) + wrap * edge) * m
    labels = [s for s in str(o['text']).split('|') if s]
    if i < len(labels):
        p = ease_back(lt / 0.3) * clamp((seg - lt) / 0.12)
        im = fx.fit_text(labels[i], c.W * 0.80, 'anton', int(c.W * 0.30), fill=(255, 255, 255), shadow=10)
        place(c, im, c.W / 2, max(c.H * 0.21, c.fy - c.fw * 1.85), 0.7 + 0.3 * p, 0, clamp(p), behind=True)
    f = math.exp(-lt / float(o['flash'])) if (i > 0 or c.lt < seg) else 0
    c.img += f * 0.95


# ------------------------------------------------------------------ paper-tear
def _jag(n, seed, amp):
    rs = np.random.RandomState(seed)
    coarse = np.interp(np.arange(n), np.linspace(0, n, 14), rs.uniform(-1, 1, 14))
    fine = np.interp(np.arange(n), np.linspace(0, n, 90), rs.uniform(-1, 1, 90))
    return ((coarse * 0.65 + fine * 0.35) * amp).astype(np.float32)


@effect('paper-tear', 'the picture rips open across the middle and a proof image or a word shows in the gap')
def fx_paper_tear(c, e):
    o = opts(e, at=0.5, open=0.26, text='', paper='f4ead8', ink='16161a', rip=0.38, tilt=1.2)
    ims = load_images(e)
    p = ease_out(c.lt / max(0.05, float(o['rip']))) * ease_inout((e.d - c.lt) / 0.3)
    gap = float(o['open']) * c.H * p
    if gap < 2: return
    cy = float(o['at']) * c.H; amp = c.H * 0.012
    j1, j2 = cached(e, 'j1', lambda: _jag(c.W, 3, amp)), cached(e, 'j2', lambda: _jag(c.W, 8, amp))
    r1, r2 = cached(e, 'r1', lambda: _jag(c.W, 5, amp * 0.5) + amp * 1.3), cached(e, 'r2', lambda: _jag(c.W, 9, amp * 0.5) + amp * 1.3)
    yy = np.arange(c.H, dtype=np.float32)[:, None]
    top_edge = cy - gap / 2 + j1[None, :]; bot_edge = cy + gap / 2 + j2[None, :]
    src = c.img; up_ = int(gap / 2); H = c.H
    top = np.zeros_like(src); top[:H - up_] = src[up_:]                           # top half slides up
    bot = np.zeros_like(src); bot[up_:] = src[:H - up_]                           # bottom half slides down
    # what is under the paper
    key = ('fill', int(float(o['open']) * 1000))
    if key not in e.state:
        gh = int(float(o['open']) * c.H + amp * 6)
        if ims: fill = cover(ims[0], c.W, gh)
        else:
            fill = Image.new('RGB', (c.W, gh), fx.rgb(o['paper'], (244, 234, 216)))
            if str(o['text']):
                lines = str(o['text']).split('|'); size = min(fx.lines_fit(lines, c.W * 0.60, 'anton', int(gh * 0.8)), int(gh * 0.78 / len(lines)))
                for i, ln in enumerate(lines):
                    im = text_img(ln, size, 'anton', fill=fx.rgb(o['ink'], INK))
                    fill.paste(im, (c.W // 2 - im.width // 2, int(gh / 2 + (i - (len(lines) - 1) / 2) * size * 1.02 - im.height / 2)), im)
        e.state[key] = np.asarray(fill, np.float32) / 255
    fill = e.state[key]; gh = fill.shape[0]
    under = np.zeros_like(src); y0 = int(cy - gh / 2); ya, yb = max(0, y0), min(H, y0 + gh)
    under[ya:yb] = fill[ya - y0:yb - y0]
    in_gap = ((yy > top_edge) & (yy < bot_edge)).astype(np.float32)
    sh = np.clip(1 - (yy - top_edge) / (c.H * 0.035), 0, 1) * 0.55 + np.clip(1 - (bot_edge - yy) / (c.H * 0.02), 0, 1) * 0.25
    under = under * (1 - np.clip(sh, 0, 0.7) * in_gap)[..., None]
    rim = (((yy <= top_edge) & (yy > top_edge - r1[None, :])) | ((yy >= bot_edge) & (yy < bot_edge + r2[None, :]))).astype(np.float32)
    rim = cv2.GaussianBlur(rim, (0, 0), 0.8)[..., None]
    out = np.where((yy <= top_edge)[..., None], top, np.where((yy >= bot_edge)[..., None], bot, under))
    grain = cached(e, 'grain', lambda: np.random.RandomState(2).uniform(0.94, 1.0, (c.H, c.W, 1)).astype(np.float32))
    c.img = out * (1 - rim) + np.float32([0.97, 0.95, 0.91]) * grain * rim
    c.m = np.where(yy <= top_edge, np.roll(c.m, -up_, 0), np.where(yy >= bot_edge, np.roll(c.m, up_, 0), 0)).astype(np.float32)


# ------------------------------------------------------------------ chroma-quake
@effect('chroma-quake', 'an RGB-split glitch hit that shakes the frame and decays in a third of a second')
def fx_chroma_quake(c, e):
    o = opts(e, amount=1.0, every=0, decay=0.16)
    lt = c.lt % float(o['every']) if float(o['every']) > 0 else c.lt
    k = math.exp(-lt / float(o['decay'])) * float(o['amount'])
    if k < 0.02: return
    rs = np.random.RandomState(frame_seed(c))
    dx = int(c.W * 0.022 * k) + 1
    img = c.img.copy()
    for _ in range(int(4 + 10 * k)):                                              # torn horizontal slices
        y = rs.randint(0, c.H - 8); h = rs.randint(c.H // 120, c.H // 14); s = int(rs.uniform(-1, 1) * c.W * 0.07 * k)
        img[y:y + h] = np.roll(img[y:y + h], s, axis=1)
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], dx, axis=1); out[..., 2] = np.roll(img[..., 2], -dx, axis=1)
    out[..., 1] = np.roll(img[..., 1], int(dx * 0.3), axis=0)
    out *= (1 - 0.22 * k * (np.arange(c.H) % 4 < 2))[:, None, None]
    if lt < 1.5 / c.fps: out = 1 - out * 0.9                                      # one inverted frame on the hit
    sh = int(rs.uniform(-1, 1) * c.W * 0.012 * k)
    c.img = np.roll(out, sh, axis=1)


# ------------------------------------------------------------------ vhs-tape
@effect('vhs-tape', 'a VHS throwback: colour bleed, a tracking band, PLAY and your date stamp')
def fx_vhs_tape(c, e):
    o = opts(e, text='', play='PLAY', strength=1.0)
    a = env(c, e, 0.12, 0.2) * float(o['strength'])
    rs = np.random.RandomState(frame_seed(c))
    src = c.img
    ycc = cv2.cvtColor(np.clip(src, 0, 1), cv2.COLOR_RGB2YCrCb)
    kx = int(c.W * 0.028) | 1
    ycc[..., 1] = np.roll(cv2.blur(ycc[..., 1], (kx, 1)), int(c.W * 0.006), 1)
    ycc[..., 2] = np.roll(cv2.blur(ycc[..., 2], (kx, 1)), -int(c.W * 0.004), 1)
    ycc[..., 0] = cv2.GaussianBlur(ycc[..., 0], (0, 0), 1.1)
    ycc[..., 0] = np.clip((ycc[..., 0] - 0.5) * 0.92 + 0.53, 0, 1)
    ycc[..., 1:] = 0.5 + (ycc[..., 1:] - 0.5) * 0.82
    out = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB)
    out += rs.normal(0, 0.035, (c.H // 2, c.W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1)[:c.H, :c.W, None]
    out *= (0.93 + 0.07 * (np.arange(c.H) % 4 < 2))[:, None, None]
    band_y = int((1.05 - (c.lt * 0.23) % 1.2) * c.H); bh = int(c.H * 0.035)        # tracking band drifting up
    if 0 <= band_y < c.H - bh:
        sl = out[band_y:band_y + bh]
        out[band_y:band_y + bh] = np.roll(sl, int(c.W * 0.03), 1) * 0.8 + rs.uniform(0, 0.45, (bh, c.W, 1)).astype(np.float32) * (rs.uniform(0, 1, (bh, 1, 1)) > 0.45)
    hb = int(c.H * 0.018)                                                          # head-switching noise at the very bottom
    for r in range(hb): out[c.H - 1 - r] = np.roll(out[c.H - 1 - r], int(c.W * 0.05 * (1 - r / hb) * (1 + 0.5 * math.sin(c.lt * 30 + r))), 0)
    c.img = src * (1 - a) + out * a
    fx.vignette(c, 0.25 * a)
    f = int(c.W * 0.047); jx = rs.randint(-1, 2)
    def osd(s, x, y, anchor='l'):
        if not s: return
        im = text_img(s, f, 'mono', fill=(245, 245, 245), shadow=2)
        comp(c, im, x + jx - (im.width if anchor == 'r' else 0), y, a * 0.95)
    if int(c.lt * 1.6) % 4 != 3 and str(o['play']):
        osd(str(o['play']), c.W * 0.075, c.H * 0.158)
        tx = int(c.W * 0.075 + font('mono', f).getlength(str(o['play'])) + f * 0.75 + jx); ty = int(c.H * 0.158 + f * 0.42); th_ = int(f * 0.62)
        tri = Image.new('RGBA', (th_, th_), (0, 0, 0, 0)); ImageDraw.Draw(tri).polygon([(0, 0), (th_ - 1, th_ // 2), (0, th_ - 1)], fill=(245, 245, 245, 255))
        comp(c, tri, tx, ty, a * 0.95)                                             # SpaceMono has no play glyph (it drew a box)
    osd('SP', c.W * 0.83, c.H * 0.158, 'r')
    osd(str(o['text']), c.W * 0.075, c.H * 0.755)


# ------------------------------------------------------------------ road-to-10k
def _followers():
    import json
    try:
        F = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'channel-facts.json')))
    except Exception: return None
    v = F.get('followers', {})
    if isinstance(v, dict) and v.get('use_on_screen') is not False and v.get('value'): return int(str(v['value']).replace(',', ''))
    return None


@effect('road-to-10k', 'a follower progress card: the real count ticks up and the bar fills toward the goal')
def fx_road_to_10k(c, e):
    o = opts(e, value='', goal=10000, label='ROAD TO 10K', day='', pos='bottom', accent='ffcb05', start='')
    val = int(str(o['value']).replace(',', '')) if str(o['value']) else _followers()
    if not val: raise SystemExit("road-to-10k: no verified follower count. Add `followers` to channel-facts.json (Graph API) or pass value=")
    goal = int(o['goal']); acc = fx.rgb(o['accent'], MAIZE)
    w, h = int(c.W * 0.64), int(c.W * 0.215); r = int(h * 0.22); S = 2
    a = clamp(c.lt / 0.2) * clamp((e.d - c.lt) / 0.25); pin = ease_back(c.lt / 0.4)
    q = ease_inout((c.lt - 0.25) / min(1.3, max(0.4, e.d - 1.0)))
    v0 = int(str(o['start']).replace(',', '')) if str(o['start']) else 0
    cur = int(v0 + (val - v0) * q)
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], r * S, fill=(16, 16, 20, 235), outline=(255, 255, 255, 38), width=2 * S)
    pad = int(h * 0.17) * S
    f1 = font('uib', int(h * 0.125) * S); f2 = font('anton', int(h * 0.40) * S); f3 = font('uim', int(h * 0.15) * S)
    d.text((pad, pad * 0.78), str(o['label']), font=f1, fill=(255, 255, 255, 170))
    if str(o['day']): d.text((w * S - pad, pad * 0.78), f"DAY {o['day']}", font=f1, fill=acc + (255,), anchor='ra')
    num = f'{cur:,}'; base_y = int(h * 0.70) * S
    d.text((pad, base_y), num, font=f2, fill=(255, 255, 255, 255), anchor='ls')
    nw = f2.getlength(f'{val:,}')
    d.text((pad + nw + 10 * S, base_y), f'/ {goal:,}', font=f3, fill=(255, 255, 255, 130), anchor='ls')
    pct = f'{100 * cur / goal:.0f}%'
    d.text((w * S - pad, base_y), pct, font=f3, fill=acc + (255,), anchor='rs')
    by0, by1 = int(h * 0.80) * S, int(h * 0.875) * S; bx0, bx1 = pad, w * S - pad
    d.rounded_rectangle([bx0, by0, bx1, by1], (by1 - by0) // 2, fill=(255, 255, 255, 40))
    fw_ = max(by1 - by0, int((bx1 - bx0) * min(1, cur / goal)))
    d.rounded_rectangle([bx0, by0, bx0 + fw_, by1], (by1 - by0) // 2, fill=acc + (255,))
    im = shadowed(im.resize((w, h), Image.LANCZOS), blur=22, dy=12, alpha=130)
    cy = c.H * 0.722 if str(o['pos']) == 'bottom' else max(c.H * 0.20, c.fy - c.fw * 1.9)
    place(c, im, c.W / 2, cy + (1 - clamp(pin)) * c.H * 0.03, 0.9 + 0.1 * pin, 0, a)


# ------------------------------------------------------------------ kaleido-room
@effect('kaleido-room', 'the room folds into a slow kaleidoscope around your head while you stay still')
def fx_kaleido_room(c, e):
    o = opts(e, slices=8, spin=0.25, zoom=1.0, tint=0.7, color='ff5e3a', color2='4028a0')
    a = env(c, e, 0.3, 0.3); n = int(o['slices'])
    cx, cy = c.fx, c.fy + c.fw * 0.6
    th, r, (w, h) = polar(c, cx, cy, 2)
    wedge = 2 * math.pi / n
    t = (th + c.lt * float(o['spin'])) % wedge
    t = np.where(t > wedge / 2, wedge - t, t) - math.pi / 2 + 0.25
    rr = r / float(o['zoom']) * (1 + 0.06 * math.sin(c.lt * 0.9))
    mx = np.clip(cx + np.cos(t) * rr, 0, c.W - 1).astype(np.float32); my = np.clip(cy + np.sin(t) * rr, 0, c.H - 1).astype(np.float32)
    k = cv2.remap(clean_room(c), cv2.resize(mx, (c.W, c.H)), cv2.resize(my, (c.W, c.H)), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = lum(k)[..., None]
    c1, c2, c3 = col(o['color'], (255, 94, 58)), col(o['color2'], (64, 40, 160)), np.float32([1.0, 0.86, 0.45])
    ph = up((0.5 + 0.5 * np.sin(r / c.W * 9 - c.lt * 1.2 + np.cos(t * n) * 1.5)).astype(np.float32), c)[..., None]
    pal = (c2 * (1 - ph) + c1 * ph) * (0.35 + 0.9 * g) + c3 * np.clip(g - 0.75, 0, 1) * 1.2
    k = np.clip(k * (1 - float(o['tint'])) + pal * float(o['tint']), 0, 1)
    set_bg(c, k, a, 3)


# ------------------------------------------------------------------ shockwave
@effect('shockwave', 'a ring ripples out from your chest and bends the room as it passes')
def fx_shockwave(c, e):
    o = opts(e, speed=1.25, amp=60, width=0.055, rings=2, gap=0.22, glow=0.6)
    cx, cy = c.fx, c.fy + c.fw * 1.6
    th, r, _ = polar(c, cx, cy, 2)
    off = np.zeros_like(r); glow = np.zeros_like(r); dark = np.zeros_like(r)
    for i in range(int(o['rings'])):
        lt = c.lt - i * float(o['gap'])
        if lt <= 0: continue
        R = lt * float(o['speed']) * c.W; wd = float(o['width']) * c.W * (1 + lt * 1.2)
        life = math.exp(-lt / 0.75)
        prof = np.exp(-((r - R) / wd) ** 2)
        off += prof * np.sign(r - R + 1e-3) * float(o['amp']) * c.W / 1080 * life * -1
        glow += np.exp(-((r - R - wd * 0.25) / (wd * 0.22)) ** 2) * life
        dark += np.exp(-((r - R + wd * 0.35) / (wd * 0.45)) ** 2) * life           # a lens has a dark inner rim: a bright-only ring vanished on a white wall
    if not off.any(): return
    yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
    ox, oy = up(off * np.cos(th), c), up(off * np.sin(th), c)
    room = clean_room(c)
    chans = [cv2.remap(np.ascontiguousarray(room[..., i]), xx + ox * s, yy + oy * s, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) for i, s in enumerate((1.12, 1.0, 0.88))]
    warped = np.stack(chans, -1) * (1 - 0.55 * np.clip(up(dark, c), 0, 1)[..., None]) + up(glow, c)[..., None] * float(o['glow']) * np.float32([0.75, 0.9, 1.0])
    set_bg(c, warped, 1.0, 2.5)



# ------------------------------------------------------------------ orbit-3d
@effect('orbit-3d', 'your reels orbit you in 3D: smooth behind-to-front crossing, depth dimming, no overlap')
def fx_orbit_3d(c, e):
    """The vendored `orbit` flips each card from behind to in-front in one frame as it crosses your
    shoulders, and its 6 large cards on a 0.38W ellipse overlap each other and you: that read as
    flicker (2026-11-12). Here the crossing happens outside the body (0.47W ellipse), the
    behind/front switch is a cross-fade over a depth band, rear cards shrink and dim, and the
    centre is low-passed so the ring does not jitter with face tracking."""
    o = opts(e, count=7, size=0.15, speed=1.25, rx=0.46, ry=0.13, band=0.22, tilt=-0.10)
    ims = load_images(e) or e.cards
    if not ims: return
    K = int(o['count']); cw = int(c.W * float(o['size']))
    cards = cached(e, 'cards3d', lambda: [fx.card(ims[i % len(ims)], cw) for i in range(K)])
    cx0, cy0 = cached(e, 'ctr', lambda: [c.fx, c.fy + c.fw * 0.45])
    e.state['ctr'] = [cx0 * 0.9 + c.fx * 0.1, cy0 * 0.9 + (c.fy + c.fw * 0.45) * 0.1]; cx, cy = e.state['ctr']
    intro = ease_out(c.lt / 0.45); out = clamp((e.d - c.lt) / 0.25)
    rx, ry = c.W * float(o['rx']) * (0.55 + 0.45 * intro), c.H * float(o['ry'])
    band = float(o['band']); items = []
    for i in range(K):
        th = i * 2 * math.pi / K + c.lt * float(o['speed']) + 0.4
        items.append((math.sin(th), th, i))
    for depth, th, i in sorted(items):                       # back to front
        x = cx + rx * math.cos(th); y = cy + ry * math.sin(th) + float(o['tilt']) * rx * math.cos(th) * 0.3
        sc = (0.72 + 0.30 * (depth + 1) / 2) * (0.6 + 0.4 * intro)
        im = cards[i]
        if depth < 0.3:                                      # rear cards sit in the room's light: darker
            k = 0.62 + 0.38 * clamp((depth + 1) / 1.3)
            arr = np.asarray(im, np.float32); arr[..., :3] *= k; im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        a = out * clamp(c.lt / 0.18)
        wf = clamp((depth + band) / (2 * band))              # 0 = fully behind you, 1 = fully in front
        rot = -5 * math.cos(th)
        if wf < 1: place(c, im, x, y, sc, rot, a * (1 - wf), behind=True)
        if wf > 0: place(c, im, x, y, sc, rot, a * wf, guard=True)


fx.ALIASES.update({'halo': 'halo-rays', 'rays': 'halo-rays', 'god-rays': 'halo-rays', 'neon': 'neon-trace', 'ascii': 'ascii-room',
                   'terminal': 'ascii-room', 'halftone': 'halftone-pop', 'comic': 'halftone-pop', 'anime': 'speed-lines',
                   'tear': 'paper-tear', 'rip': 'paper-tear', 'glitch': 'chroma-quake', 'vhs': 'vhs-tape', '10k': 'road-to-10k',
                   'kaleido': 'kaleido-room', 'ripple': 'shockwave', 'orbit3d': 'orbit-3d'})
