#!/usr/bin/env python3
"""Render stacked lines as gold outlined italic serif, barrel-warped (the IG 'fisheye' text look).
Writes a transparent RGBA PNG sized to the video frame."""
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont

cfg = json.loads(sys.argv[1])
FONT   = cfg.get('font', '/Users/vatsalshah/Code/video-edits/fonts/PlayfairDisplay-BlackItalic.ttf')
LINES  = cfg['lines']                      # [{"t":"...","rel":1.0}, ...]
W, H   = cfg.get('w', 1080), cfg.get('h', 1920)
TARGET = cfg.get('target_w', 840)          # widest line spans this many px
CY     = cfg.get('cy', 1120)               # vertical centre of the text block
GOLD   = tuple(cfg.get('gold', [255, 210, 60, 255]))
STROKE = cfg.get('stroke', 0.085)          # outline width as a fraction of font size
LEAD   = cfg.get('lead', 1.16)             # line height multiplier
K      = cfg.get('k', -0.17)               # barrel strength; negative bulges the centre
OUT    = cfg['out']
# The warp magnifies the centre, so the rendered block is ~20% wider than TARGET. The text
# is centred on W/2 while IG's safe box (59..918) is not, so the binding limit is the
# right-hand like/comment rail: 2*(918 - W/2).
MAXW   = cfg.get('max_w', 2 * (cfg.get('safe_right', 918) - cfg.get('w', 1080) // 2))

# --- fit the font so the widest full-size line hits TARGET ---
def widest(sz):
    w = 0
    for L in LINES:
        f = ImageFont.truetype(FONT, max(8, int(sz * L.get('rel', 1.0))))
        b = f.getbbox(L['t'], stroke_width=int(sz * L.get('rel', 1.0) * STROKE))
        w = max(w, b[2] - b[0])
    return w
def fit(target):
    lo, hi = 10, 400
    while hi - lo > 1:
        mid = (lo + hi) // 2
        (lo, hi) = (mid, hi) if widest(mid) < target else (lo, mid)
    return lo

# --- draw on a transparent canvas, block centred on (W/2, CY) ---
def render(target):
    SZ = fit(target)

    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    metrics = []
    for L in LINES:
        s = max(8, int(SZ * L.get('rel', 1.0)))
        metrics.append((ImageFont.truetype(FONT, s), int(s * STROKE), int(s * LEAD)))
    total = sum(m[2] for m in metrics)
    y = CY - total // 2
    for L, (f, sw, lh) in zip(LINES, metrics):
        d.text((W // 2, y + lh // 2), L['t'], font=f, fill=GOLD, anchor='mm',
               stroke_width=sw, stroke_fill=(0, 0, 0, 255))
        y += lh

    # --- barrel warp, centred on the text block ---
    a = np.array(canvas).astype(np.float32)
    pad = int(TARGET * 0.75)
    x0, x1 = max(0, W // 2 - pad), min(W, W // 2 + pad)
    y0, y1 = max(0, CY - pad), min(H, CY + pad)
    sub = a[y0:y1, x0:x1]
    sh, sw_ = sub.shape[0], sub.shape[1]
    yy, xx = np.mgrid[0:sh, 0:sw_].astype(np.float32)
    cx, cy = (sw_ - 1) / 2.0, (sh - 1) / 2.0
    nx, ny = (xx - cx) / cx, (yy - cy) / cy
    r = np.sqrt(nx * nx + ny * ny)
    scale = 1.0 + K * (r ** 2)                 # r_src = r_dst * scale ; K<0 magnifies the centre
    sx = np.clip(cx + nx * scale * cx, 0, sw_ - 1)
    sy = np.clip(cy + ny * scale * cy, 0, sh - 1)
    x0i, y0i = np.floor(sx).astype(int), np.floor(sy).astype(int)
    x1i, y1i = np.minimum(x0i + 1, sw_ - 1), np.minimum(y0i + 1, sh - 1)
    fx, fy = (sx - x0i)[..., None], (sy - y0i)[..., None]
    warped = (sub[y0i, x0i] * (1 - fx) * (1 - fy) + sub[y0i, x1i] * fx * (1 - fy) +
              sub[y1i, x0i] * (1 - fx) * fy       + sub[y1i, x1i] * fx * fy)
    a[y0:y1, x0:x1] = warped
    out = np.clip(a, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(out[:, :, 3] > 8)          # real extent AFTER warping
    return SZ, out, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())

# shrink until the warped block clears the rail -- measuring the pre-warp text would let
# the bloom of the magnified centre run under the like button
target = TARGET
while True:
    SZ, out, bx0, bx1, by0, by1 = render(target)
    if bx1 - bx0 <= MAXW or target <= 120:
        break
    target = int(target * 0.94)

Image.fromarray(out).save(OUT)
print(json.dumps({"fontsize": SZ, "k": K, "target_w": target,
                  "bbox_x": [bx0, bx1], "bbox_y": [by0, by1],
                  "width": bx1 - bx0, "out": OUT}))
