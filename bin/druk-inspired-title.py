#!/usr/bin/env python3
"""Render tall, heavy, condensed display type from the bundled OFL Anton font.

This is an original typographic treatment, not the proprietary Druk font.
It enlarges the rendered glyphs vertically and compresses them horizontally.

Example:
  python3 bin/druk-inspired-title.py --line 'I AUTOMATED' --line 'MY INSTAGRAM' \
    --color '#FFFCF6' --color '#FF7127' --top 1245 --gap 120 --out /tmp/hook.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
SAFE = (59, 278, 918, 1536)


def render(lines: list[str], colors: list[str], out: Path, *, top: int = 1245,
           gap: int = 120, size: int = 105, width_scale: float = .86,
           height_scale: float = 1.20, stroke: int = 3,
           font_path: Path | None = None) -> tuple[int, int, int, int]:
    font_path = font_path or ROOT / "fonts" / "Anton-Regular.ttf"
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, text in enumerate(lines):
        font = ImageFont.truetype(str(font_path), size)
        bbox = font.getbbox(text, stroke_width=stroke)
        pad = stroke + 12
        raw = Image.new("RGBA", (bbox[2]-bbox[0]+pad*2, bbox[3]-bbox[1]+pad*2), (0,0,0,0))
        draw = ImageDraw.Draw(raw)
        color = colors[min(i, len(colors)-1)]
        rgb = tuple(bytes.fromhex(color.lstrip('#'))[:3])
        draw.text((pad-bbox[0], pad-bbox[1]), text, font=font,
                  fill=(*rgb, 255), stroke_width=stroke, stroke_fill=(8,11,16,245))
        layer = raw.resize((round(raw.width*width_scale), round(raw.height*height_scale)),
                           Image.Resampling.LANCZOS)
        x = (W-layer.width)//2
        im.alpha_composite(layer, (x, top+i*gap))
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit("No visible title pixels were rendered")
    l,t,r,b = bbox
    sl,st,sr,sb = SAFE
    if l < sl or r > sr or t < st or b > sb:
        raise SystemExit(f"Title exceeds Instagram safe bounds: {bbox}; safe box is {SAFE}")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(f"wrote {out}; alpha bbox={bbox}; safe box={SAFE}")
    return bbox


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--line", action="append", required=True, help="Headline line, repeat as needed")
    p.add_argument("--color", action="append", default=[], help="Hex line color, repeat to pair with lines")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--top", type=int, default=1245)
    p.add_argument("--gap", type=int, default=120)
    p.add_argument("--size", type=int, default=105)
    p.add_argument("--width-scale", type=float, default=.86)
    p.add_argument("--height-scale", type=float, default=1.20)
    p.add_argument("--stroke", type=int, default=3)
    p.add_argument("--font", type=Path, default=None)
    a = p.parse_args()
    render(a.line, a.color or ["#FFFCF6"], a.out, top=a.top, gap=a.gap,
           size=a.size, width_scale=a.width_scale, height_scale=a.height_scale,
           stroke=a.stroke, font_path=a.font)


if __name__ == "__main__":
    main()
