#!/usr/bin/env python3
"""Render the YC interview checklist overlay plates for this reusable format.

Usage: yc-interview-list.py <asset-dir>
Creates a hook plate and ten progressive checklist plates at 1080x1920 RGBA.
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1920
ORANGE = (255, 102, 0, 255)
WHITE = (255, 250, 244, 255)
MUTED = (203, 198, 191, 210)
BLACK = (11, 12, 15, 238)
FONT = ROOT / "fonts/Switzer-Bold.otf"
SERIF = ROOT / "fonts/InstrumentSerif-Regular.ttf"
LOGO = ROOT / "logos/yc.png"
ITEMS = [
    ["What are you building?", "What’s the vision?"],
    ["Who is the customer?", "Define your ICP."],
    ["How does the product", "actually work?"],
    ["What problem does it", "solve for them?"],
    ["What do customers use", "instead today?"],
    ["How many paying users?", "What’s usage like?"],
    ["Why is this the right", "founding team?"],
    ["Can this scale, or is it", "custom work each time?"],
    ["Who does what on the", "team?"],
    ["Demo Day goal? What", "have you built so far?"],
]

def f(path, size):
    return ImageFont.truetype(str(path), size)

def centered(draw, xy, text, font, fill):
    b = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (b[2]-b[0])/2 - b[0], xy[1] - (b[3]-b[1])/2 - b[1]),
              text, font=font, fill=fill)

def make_hook():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Quiet dark wash only behind type; leaves the face and shirt visible.
    d.rounded_rectangle((180, 280, 900, 630), 38, fill=(10, 12, 15, 208),
                        outline=(255, 102, 0, 210), width=3)
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((78, 78), Image.Resampling.LANCZOS)
    # Put the transparent YC mark on a clean white tile.
    tile = Image.new("RGBA", (84, 84), (255, 255, 255, 255))
    tile.alpha_composite(logo, ((84-logo.width)//2, (84-logo.height)//2))
    im.alpha_composite(tile, (200, 325))
    d = ImageDraw.Draw(im)
    d.text((310, 337), "3× YC INTERVIEWS", font=f(FONT, 31), fill=ORANGE)
    d.text((200, 436), "THE QUESTIONS", font=f(FONT, 70), fill=WHITE,
           stroke_width=2, stroke_fill=(0, 0, 0, 145))
    d.text((200, 522), "I’d prepare for", font=f(SERIF, 54), fill=WHITE)
    return im

def make_state(done, active):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Left-side gradient scrim, preserving the face at center-right.
    for x in range(59, 651):
        a = round(176 * (1 - min(1, (x-59)/592)))
        d.line((x, 278, x, 1536), fill=(7, 9, 12, a))
    d.rounded_rectangle((59, 300, 465, 1520), 30, fill=(10, 12, 15, 216),
                        outline=(255, 255, 255, 36), width=2)
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((52, 52), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (58, 58), (255, 255, 255, 255))
    tile.alpha_composite(logo, ((58-logo.width)//2, (58-logo.height)//2))
    im.alpha_composite(tile, (70, 325))
    d = ImageDraw.Draw(im)
    d.text((141, 330), "YC INTERVIEW", font=f(FONT, 23), fill=ORANGE)
    d.text((141, 359), "10 QUESTIONS", font=f(FONT, 19), fill=WHITE)
    d.line((70, 398, 442, 398), fill=(255, 255, 255, 85), width=2)
    row_top = 418
    row_h = 101
    for i, lines in enumerate(ITEMS):
        y = row_top + i*row_h
        if i < done:
            text_col = WHITE
            num_col = (255, 102, 0, 255)
            alpha = 255
        elif i == active:
            d.rounded_rectangle((67, y+3, 453, y+row_h-7), 16,
                                fill=(42, 25, 14, 246), outline=(255, 102, 0, 240), width=2)
            text_col = WHITE
            num_col = ORANGE
            alpha = 255
        else:
            text_col = (205, 202, 197, 128)
            num_col = (180, 175, 168, 145)
            alpha = 145
        d.text((74, y+10), f"{i+1:02d}", font=f(FONT, 22), fill=num_col)
        for j, line in enumerate(lines):
            d.text((121, y+7+j*34), line, font=f(FONT, 24), fill=text_col)
        if i < len(ITEMS)-1:
            d.line((121, y+row_h-6, 442, y+row_h-6), fill=(255, 255, 255, 38), width=1)
    return im

make_hook().save(OUT / "hook.png")
make_state(0, -1).save(OUT / "intro-list.png")
for n in range(10):
    make_state(n, n).save(OUT / f"q{n+1:02d}.png")
# Final resolved list, no active highlight.
make_state(10, -1).save(OUT / "done.png")
cta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(cta)
cd.rounded_rectangle((560, 1380, 918, 1515), 30, fill=(10, 12, 15, 232),
                     outline=ORANGE, width=3)
cd.text((596, 1397), "THE YC INTERVIEW", font=f(FONT, 19), fill=ORANGE)
cd.text((596, 1430), "COMMENT YC", font=f(FONT, 42), fill=WHITE)
cta.save(OUT / "cta.png")
print(f"Rendered {14} transparent 1080x1920 checklist plates in {OUT}")
