#!/usr/bin/env python3
"""In-house procedural VFX: light, particles and camera artefacts drawn per frame (numpy + PIL, no stock packs).

Each generator is a pure function of local time, so a still at time t is exactly what the render shows.
Additive ones return an RGB float32 light layer (0-1) to SCREEN over the frame; `iris` returns a darkening
mask; `burn` returns (light, black) for a film-burn transition.

    python3 bin/vfx_lib.py list
    python3 bin/vfx_lib.py sheet out.jpg                      # one still of each, on a grey card
    python3 bin/vfx_lib.py render flare out.mp4 [--dur 0.8]   # overlay clip on black, for any editor (screen blend)

In code:  import vfx_lib as V;  img = V.screen(img, V.flare(lt, 540, 700, (1.0, 0.75, 0.45)))
Used by videos/effects-showcase/timeline2.py. Rule: VFX go on moments that earn them (a hit, a reveal, a
transition), never wall to wall. No SFX on talking heads (memory: no-sfx-on-talking-heads).
"""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
LIST = {
    'flare':  'anamorphic lens flare: horizontal streak, hot core and ghost rings; fast attack, 0.3 s decay',
    'sparks': 'spark burst from a point: radial sparks with gravity, drag and motion-blurred glow',
    'debris': 'paper/ash debris drifting up from a line (pairs with paper-tear)',
    'iris':   'camera iris shutter blink: 7 blades close to black and reopen (darkening mask)',
    'burn':   'film burn: a hot noisy edge eats the frame to black (transition)',
    'leak':   'light leak: large warm blobs drifting across the frame',
    'glint':  'diagonal glint sweep across a band (for titles)',
}


def screen(img, layer, a=1.0):
    """img, layer: float32 HxWx3 in 0-1."""
    return 1 - (1 - img) * (1 - np.clip(layer * a, 0, 1))


def _up(a, w=W, h=H):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255


def flare(lt, cx, cy, color=(1.0, 0.78, 0.5), dur=0.6, strength=1.0):
    if lt < 0 or lt > dur + 0.3: return np.zeros((H, W, 3), np.float32)
    env = (1 - math.exp(-lt / 0.025)) * math.exp(-lt / (dur * 0.45)) * strength
    s = 4; h, w = H // s, W // s
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); x, y = xx * s - cx, yy * s - cy
    streak = np.exp(-(y / 7) ** 2) * np.exp(-(x / (W * 0.55)) ** 2)
    core = np.exp(-(x * x + y * y) / (2 * 60 ** 2)) + 0.35 * np.exp(-(x * x + y * y) / (2 * 220 ** 2))
    ghosts = np.zeros_like(x); gx, gy = W / 2 - cx, H / 2 - cy
    for k, r, g in ((0.6, 40, 0.18), (1.1, 80, 0.10), (1.6, 26, 0.22), (2.0, 120, 0.06)):
        px, py = cx + gx * k, cy + gy * k; d = np.sqrt((xx * s - px) ** 2 + (yy * s - py) ** 2)
        ghosts += g * (np.exp(-((d - r) / 6) ** 2) + 0.5 * (d < r))
    c = np.float32(color)
    lay = (streak * 1.3)[..., None] * (c * 0.6 + 0.4 * np.float32([0.6, 0.8, 1.0])) + core[..., None] * c + ghosts[..., None] * np.float32([0.5, 0.8, 1.0])
    return _up(lay * env)


def _particles(lt, n, seed, spawn, vel, gravity, drag, life, colors, width, glow=4):
    rs = np.random.RandomState(seed); s = 2
    im = Image.new('RGB', (W // s, H // s), (0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x0, y0 = spawn(rs); vx, vy = vel(rs); L = life * rs.uniform(0.6, 1.0); t0 = rs.uniform(0, 0.08)
        tt = lt - t0
        if tt < 0 or tt > L: continue
        def pos(t_):
            k = (1 - math.exp(-drag * t_)) / drag
            return x0 + vx * k, y0 + vy * k + 0.5 * gravity * t_ * t_
        x1, y1 = pos(tt); x2, y2 = pos(max(0, tt - 0.035))
        fade = (1 - tt / L) ** 1.4; col = colors[i % len(colors)]
        d.line([(x2 / s, y2 / s), (x1 / s, y1 / s)], fill=tuple(int(255 * fade * c) for c in col), width=max(1, int(width * rs.uniform(0.6, 1.2))))
    a = np.asarray(im, np.float32) / 255
    g = np.asarray(im.filter(ImageFilter.GaussianBlur(glow)), np.float32) / 255
    return _up(a + g * 1.8)


def sparks(lt, cx, cy, n=110, seed=3, color='warm', spread=1.0):
    cols = {'warm': [(1, 0.95, 0.8), (1, 0.7, 0.3), (1, 0.55, 0.2)], 'cool': [(0.8, 0.95, 1), (0.4, 0.9, 1), (1, 0.5, 1)],
            'yc': [(1, 0.9, 0.7), (1, 0.45, 0.1), (1, 0.6, 0.2)]}[color]
    def vel(rs):
        a = rs.uniform(-math.pi, 0) if rs.uniform() < 0.8 else rs.uniform(0, math.pi); sp = rs.uniform(900, 2600) * spread
        return math.cos(a) * sp, math.sin(a) * sp
    return _particles(lt, n, seed, lambda rs: (cx + rs.normal(0, 14), cy + rs.normal(0, 14)), vel, 2600, 3.2, 0.9, cols, 3)


def debris(lt, y_line, n=60, seed=9):
    cols = [(0.97, 0.93, 0.86), (0.85, 0.8, 0.72), (1, 0.85, 0.6)]
    return _particles(lt, n, seed, lambda rs: (rs.uniform(60, W - 60), y_line + rs.normal(0, 10)),
                      lambda rs: (rs.normal(0, 220), rs.uniform(-900, -350)), 700, 1.4, 1.2, cols, 9, glow=2) * 1.1


def iris(lt, dur=0.26, blades=7):
    """Darkening mask (HxW float, 1 = black). Closes over the first half, reopens over the second."""
    p = lt / dur
    if p <= 0 or p >= 1: return np.zeros((H, W), np.float32)
    close = math.sin(math.pi * p) ** 0.7                      # 0 open -> 1 shut -> 0 open
    R = math.hypot(W, H) / 2; r = R * (1 - close) * 1.02; rot = 0.9 * p
    s = 2; im = Image.new('L', (W // s, H // s), 0); d = ImageDraw.Draw(im)
    cx, cy = W / 2 / s, H / 2 / s
    for k in range(blades):                                    # each blade is a big quad tangent to the opening
        a = rot + k * 2 * math.pi / blades; a2 = a + 2 * math.pi / blades * 1.35
        p1 = (cx + math.cos(a) * r / s, cy + math.sin(a) * r / s); p2 = (cx + math.cos(a2) * r / s, cy + math.sin(a2) * r / s)
        far = R * 2 / s
        p3 = (cx + math.cos(a2 + 0.5) * far, cy + math.sin(a2 + 0.5) * far); p4 = (cx + math.cos(a + 0.5) * far, cy + math.sin(a + 0.5) * far)
        d.polygon([p1, p2, p3, p4], fill=255)
    m = np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    return _up(m)


_N = {}
def _noise(seed, w=135, h=240):
    if seed not in _N:
        rs = np.random.RandomState(seed); acc = np.zeros((h, w), np.float32)
        for o, amp in ((6, 1), (12, 0.5), (24, 0.25), (48, 0.12)):
            g = rs.rand(o * h // w + 2, o + 2).astype(np.float32)
            acc += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        _N[seed] = (acc - acc.min()) / (acc.max() - acc.min())
    return _N[seed]


def burn(lt, dur=0.55, seed=5):
    """Film burn transition. Returns (light layer to screen, black mask 0-1 to multiply away)."""
    p = lt / dur
    if p <= 0: return np.zeros((H, W, 3), np.float32), np.zeros((H, W), np.float32)
    n = _noise(seed); h, w = n.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    field = 0.55 * n + 0.45 * (1 - np.sqrt(((xx - w * 0.15) / w) ** 2 + ((yy - h * 0.85) / h) ** 2) / 1.2)
    thr = 1.05 - 1.25 * min(1.0, p)
    edge = np.exp(-((field - thr) / 0.035) ** 2); black = np.clip((field - thr) / 0.02, 0, 1)
    hot = edge[..., None] * np.float32([1.0, 0.82, 0.55]) * 1.6 + np.exp(-((field - thr + 0.06) / 0.08) ** 2)[..., None] * np.float32([1.0, 0.35, 0.05])
    return _up(hot), _up(black)


def leak(lt, dur=1.2, seed=2, strength=0.55):
    if lt < 0 or lt > dur: return np.zeros((H, W, 3), np.float32)
    env = math.sin(math.pi * lt / dur) * strength; rs = np.random.RandomState(seed); s = 8
    h, w = H // s, W // s; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); lay = np.zeros((h, w, 3), np.float32)
    for c in ((1.0, 0.45, 0.15), (1.0, 0.2, 0.45), (1.0, 0.8, 0.3)):
        x0, y0 = rs.uniform(-0.2, 1.2) * w, rs.uniform(0, 1) * h; vx = rs.uniform(-0.6, 0.6) * w
        r = rs.uniform(0.35, 0.6) * w; x = x0 + vx * lt / dur
        lay += np.exp(-(((xx - x) ** 2 + (yy - y0) ** 2) / (2 * r * r)))[..., None] * np.float32(c)
    return _up(lay * env)


def glint(lt, y0, y1, dur=0.5):
    if lt < 0 or lt > dur: return np.zeros((H, W, 3), np.float32)
    p = lt / dur; s = 2; h, w = H // s, W // s
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); x = xx * s + (yy * s - y0) * 0.45
    pos = -300 + (W + 600) * p; band = np.exp(-((x - pos) / 70) ** 2) * ((yy * s >= y0) & (yy * s <= y1))
    return _up(band[..., None] * np.float32([1, 1, 1]) * 0.85)


# ---------------------------------------------------------------- CLI
def _demo(name, lt):
    if name == 'flare': return flare(lt, 540, 760)
    if name == 'sparks': return sparks(lt, 540, 960)
    if name == 'debris': return debris(lt, 1100)
    if name == 'leak': return leak(lt)
    if name == 'glint': return glint(lt, 300, 500)
    if name == 'iris': return np.repeat(iris(lt)[..., None], 3, 2) * 0.0 + (1 - iris(lt))[..., None] * 0.25
    if name == 'burn': l, b = burn(lt); return l + (1 - b)[..., None] * 0.18


def main():
    a = sys.argv[1:]
    if not a or a[0] == 'list':
        for k, v in LIST.items(): print(f'{k:8s} {v}')
        return
    if a[0] == 'sheet':
        at = {'flare': 0.08, 'sparks': 0.25, 'debris': 0.5, 'iris': 0.11, 'burn': 0.3, 'leak': 0.6, 'glint': 0.25}
        ims = [Image.fromarray((np.clip(_demo(k, t_), 0, 1) * 255).astype(np.uint8)).resize((270, 480)) for k, t_ in at.items()]
        sh = Image.new('RGB', (278 * len(ims), 510), (20, 20, 20)); d = ImageDraw.Draw(sh)
        for i, (k, im) in enumerate(zip(at, ims)): sh.paste(im, (i * 278, 30)); d.text((i * 278 + 6, 8), k, fill=(255, 255, 255))
        sh.save(a[1], quality=88); print(a[1]); return
    if a[0] == 'render':
        name, out = a[1], a[2]; dur = float(a[a.index('--dur') + 1]) if '--dur' in a else 1.0
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                                '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for i in range(int(dur * 30)):
            enc.stdin.write((np.clip(_demo(name, i / 30), 0, 1) * 255).astype(np.uint8).tobytes())
        enc.stdin.close(); enc.wait(); print('wrote', out, '(screen-blend it over your footage)')


if __name__ == '__main__':
    main()
