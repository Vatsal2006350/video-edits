#!/usr/bin/env python3
"""Render one item label for list-reel.sh.

No scrim box. An earlier version drew a blurred rounded rectangle behind the words and it
read on screen as a grey smudge -- Vatsal called it "the weird shadow". Legibility over
arbitrary photos comes from stacked offset copies of the glyphs instead, which reads as a
soft edge on the letters rather than a panel behind them.

  list-label.py <text> <out.png> <size> <cy> <fontdir> [logo.png]
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

txt, out, size, cy, fdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
logo = sys.argv[6] if len(sys.argv) > 6 else ""
logo_y = int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] else 0   # 0 = sit just above the text

W, H = 1080, 1920
SAFE_R, X0 = 902, 88                      # IG's like/comment rail starts at 918
# The text is CENTRED on W/2, but the safe box is not symmetric about it -- so the limit is
# twice the distance from centre to the rail, not the box width. Using the box width let
# "became a YC founder" run under the like button.
MAXW = min(SAFE_R - X0, 2 * (SAFE_R - W // 2))
font = ImageFont.truetype(f"{fdir}/Montserrat-Bold.ttf", size)

words, lines, cur = txt.split(), [], ""
for w in words:
    t = (cur + " " + w).strip()
    if font.getbbox(t)[2] - font.getbbox(t)[0] > MAXW and cur:
        lines.append(cur); cur = w
    else:
        cur = t
if cur:
    lines.append(cur)

lh = int(size * 1.22)
total = lh * len(lines)
y0 = cy - total // 2

im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
for i, ln in enumerate(lines):
    bb = font.getbbox(ln)
    x = (W - (bb[2] - bb[0])) // 2
    y = y0 + i * lh
    for dx, dy, a in ((0, 3, 150), (0, 5, 95), (2, 2, 110), (-2, 2, 110)):
        d.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, a))
    d.text((x, y), ln, font=font, fill=(255, 255, 255, 255))

if logo and os.path.exists(logo):
    lg = Image.open(logo).convert('RGBA')
    lw = 310
    lg = lg.resize((lw, max(1, int(lg.height * lw / lg.width))))
    ly = logo_y if logo_y else max(320, y0 - lg.height - 28)
    im.alpha_composite(lg, ((W - lw) // 2, ly))

im.save(out)
