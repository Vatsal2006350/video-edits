#!/usr/bin/env python3
"""Bold caption with a coloured outer glow (the IG "yellow glow" look).

The glow is a blurred copy of the glyphs behind the fill, stacked a few times so it
blooms rather than looking like a soft outline. Renders a transparent PNG sequence or
a single still, sized to the video frame.
"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def render(text, cfg, canvas=None):
    W, H = cfg.get('w', 1080), cfg.get('h', 1920)
    sz = cfg.get('size', 108)
    # The bloom extends well past the glyph box, so fit against max_w minus the spread,
    # not against the text width -- otherwise the glow is what clips at the frame edge.
    maxw = cfg.get('max_w')
    if maxw:
        pad = (cfg.get('spread', 6) + cfg.get('radius', 18)) * 2
        while sz > 24:
            f = ImageFont.truetype(cfg['font'], sz)
            bb = f.getbbox(text)
            if bb[2] - bb[0] + pad <= maxw:
                break
            sz -= 2
    font = ImageFont.truetype(cfg['font'], sz)
    y    = cfg.get('y', 1500)
    x    = cfg.get('x', W // 2)          # centred by default; set it to move a stamp off a face
    anch = cfg.get('anchor', 'mm')       # 'lm' left-anchors, so a long stamp grows rightwards
                                         # instead of off the left edge of the safe box
    glow = tuple(cfg.get('glow', [255, 214, 10]))      # gold
    fill = tuple(cfg.get('fill', [255, 255, 255]))
    passes = cfg.get('passes', 3)
    radius = cfg.get('radius', 18)
    spread = cfg.get('spread', 6)                      # stroke width of the glow copy
    stroke = cfg.get('stroke', 0)                      # dark keyline on the fill

    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # --- glow: blurred, dilated copies stacked ---
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((x, y), text, font=font, anchor=anch,
                           fill=glow+(255,), stroke_width=spread, stroke_fill=glow+(255,))
    for i in range(passes):
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(radius*(i+1)/passes)))
    # --- fill on top ---
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(top).text((x, y), text, font=font, anchor=anch, fill=fill+(255,),
                             stroke_width=stroke, stroke_fill=(0, 0, 0, 235) if stroke else None)
    return Image.alpha_composite(im, top)

if __name__ == '__main__':
    cfg = json.loads(sys.argv[1])
    out = cfg['out']
    if cfg.get('text') is not None:
        render(cfg['text'], cfg).save(out)
        print(json.dumps({"out": out}))
