#!/usr/bin/env python3
"""Composite a photo/screenshot into a floating rounded card on a transparent 1080x1920 canvas."""
import sys, json
from PIL import Image, ImageDraw, ImageFilter

c = json.loads(sys.argv[1])
W, H = c.get('w', 1080), c.get('h', 1920)
CW    = c.get('card_w', 1000)          # card width
TOP   = c.get('top', 560)              # card top edge
RAD   = c.get('radius', 26)
SHAD  = c.get('shadow', 34)

src = Image.open(c['src']).convert('RGB')
ch  = round(CW * src.height / src.width)
src = src.resize((CW, ch), Image.LANCZOS)

mask = Image.new('L', (CW, ch), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, CW - 1, ch - 1], RAD, fill=255)

canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
x = (W - CW) // 2
# drop shadow first
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([x, TOP + 12, x + CW, TOP + ch + 12], RAD, fill=(0, 0, 0, 150))
canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(SHAD)))

card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
card.paste(src, (x, TOP), mask)
canvas = Image.alpha_composite(canvas, card)
canvas.save(c['out'])
print(json.dumps({"card": [x, TOP, x + CW, TOP + ch], "out": c['out']}))
