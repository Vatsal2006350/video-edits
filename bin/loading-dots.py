#!/usr/bin/env python3
"""Three-dot loading animation on black -> PNG frames (typing-indicator style pulse)."""
import sys, json, os, math
from PIL import Image, ImageDraw

cfg  = json.loads(sys.argv[1])
W, H = cfg.get('w', 1080), cfg.get('h', 1920)
FPS  = cfg.get('fps', 30)
DUR  = cfg.get('dur', 1.0)
CY   = cfg.get('cy', H // 2)
GOLD = tuple(cfg.get('gold', [255, 210, 60]))
R    = cfg.get('r', 20)            # base radius
GAP  = cfg.get('gap', 84)
CYC  = cfg.get('cycle', 0.62)      # one full sweep across the three dots
OUT  = cfg['outdir']
os.makedirs(OUT, exist_ok=True)

n = int(round(DUR * FPS))
for i in range(n):
    t = i / FPS
    im = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(3):
        ph = ((t / CYC) - k * 0.16) % 1.0          # each dot lags the one before it
        pulse = max(0.0, math.sin(ph * math.pi)) ** 2
        r = R * (0.72 + 0.5 * pulse)
        a = 0.34 + 0.66 * pulse
        col = tuple(int(c * a) for c in GOLD)
        cx = W // 2 + (k - 1) * GAP
        d.ellipse([cx - r, CY - r, cx + r, CY + r], fill=col)
    im.save(f"{OUT}/d_{i:04d}.png")
print(json.dumps({"frames": n, "fps": FPS, "outdir": OUT}))
