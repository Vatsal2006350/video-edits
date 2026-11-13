#!/usr/bin/env python3
"""Render a transparent, character-by-character title sequence."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

c = json.loads(sys.argv[1])
w, h, fps = c.get("w", 1080), c.get("h", 1920), c.get("fps", 30)
duration, text, out = c["duration"], c["text"], c["outdir"]
font = ImageFont.truetype(c["font"], c.get("size", 78))
x, y = c.get("x", 84), c.get("y", 270)
start, cps = c.get("start", .18), c.get("cps", 15)
os.makedirs(out, exist_ok=True)

for frame in range(round(duration * fps)):
    t = frame / fps
    count = max(0, int((t - start) * cps) + 1)
    shown = text[:count]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    # Soft black shadow keeps the elegant serif readable without a box or heavy grade.
    draw.multiline_text((x + 3, y + 5), shown, font=font, fill=(0, 0, 0, 190), spacing=2)
    draw.multiline_text((x, y), shown, font=font, fill=(255, 255, 255, 255), spacing=2)
    logo_path = c.get("logo")
    if logo_path and t >= c.get("logo_at", 1.35):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((c.get("logo_w", 310), c.get("logo_h", 125)))
        fade = min(1.0, (t - c.get("logo_at", 1.35)) / .28)
        logo.putalpha(logo.getchannel("A").point(lambda a: int(a * fade)))
        im.alpha_composite(logo, (c.get("logo_x", x), c.get("logo_y", y + 190)))
    im.save(f"{out}/t_{frame:04d}.png")
