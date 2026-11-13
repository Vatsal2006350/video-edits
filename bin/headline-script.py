#!/usr/bin/env python3
"""Render the reference-style opening headline as a transparent PNG.

The look pairs a condensed Anton headline with a red SignPainter script
overprint. Lines are separated with ``|``. Text is centered inside the reel's
724px headline width and positioned within the Instagram safe box.

Example:
  python3 bin/headline-script.py \
    --headline 'DAY 1 OF|SHARING STARTUP ADVICE' --script 'YC' \
    --out /tmp/opening.png
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
SAFE_X0, SAFE_X1 = 178, 902  # 724px centered headline width per AGENTS.md
SAFE_Y0, SAFE_Y1 = 278, 1536
ANTON = ROOT / "fonts" / "Anton-Regular.ttf"
SCRIPT = Path("/System/Library/Fonts/Supplemental/SignPainter.ttc")


def load_script(size: int) -> ImageFont.FreeTypeFont:
    if not SCRIPT.exists():
        raise SystemExit("SignPainter.ttc is missing; install/use the macOS SignPainter face.")
    return ImageFont.truetype(str(SCRIPT), size, index=0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--headline", required=True, help="Bold title; use | to split lines")
    ap.add_argument("--script", required=True, help="Short cursive word/phrase over the headline")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--y", type=int, default=850, help="Vertical center of the headline block")
    ap.add_argument("--size", type=int, default=152, help="Anton font size, auto-fitted to safe width")
    ap.add_argument("--script-size", type=int, default=118)
    ap.add_argument("--angle", type=float, default=-8, help="Script rotation in degrees")
    ap.add_argument("--fill", default="#F7F5EF", help="Bold headline color")
    ap.add_argument("--script-fill", default="#F22F46", help="Cursive accent color")
    ap.add_argument("--outline", type=int, default=3, help="Subtle dark keyline for bright outdoor footage")
    ap.add_argument("--max-width", type=int, default=724)
    args = ap.parse_args()

    if not ANTON.exists():
        raise SystemExit(f"Missing display font: {ANTON}")
    if not SAFE_Y0 <= args.y <= SAFE_Y1:
        raise SystemExit(f"--y must be inside the Instagram safe area ({SAFE_Y0}..{SAFE_Y1})")

    lines = [line.strip().upper() for line in args.headline.split("|") if line.strip()]
    if not lines:
        raise SystemExit("--headline must contain at least one line")
    max_width = min(args.max_width, SAFE_X1 - SAFE_X0)
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = args.size
    while size > 28:
        font = ImageFont.truetype(str(ANTON), size)
        if max(scratch.textbbox((0, 0), line, font=font)[2] for line in lines) <= max_width:
            break
        size -= 2
    else:
        raise SystemExit("Headline cannot fit the safe width")

    # Draw the headline to a tight transparent layer; add generous vertical gap
    # for the brush stroke while keeping the entire title in the safe box.
    gap = max(8, round(size * 0.05))
    boxes = [scratch.textbbox((0, 0), line, font=font, stroke_width=args.outline) for line in lines]
    heights = [b[3] - b[1] for b in boxes]
    block_h = sum(heights) + gap * (len(lines) - 1)
    top = args.y - block_h // 2
    if top < SAFE_Y0 or top + block_h > SAFE_Y1:
        raise SystemExit(f"Headline block would leave Instagram safe area ({top}..{top + block_h})")

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    y = top
    for line, box, line_h in zip(lines, boxes, heights):
        x = W // 2 - (box[2] - box[0]) // 2
        draw.text((x - box[0], y - box[1]), line, font=font, fill=args.fill,
                  stroke_width=args.outline, stroke_fill=(18, 20, 25, 205))
        y += line_h + gap

    # Rotate a separately rendered script layer so its brush stroke crosses
    # the visual midpoint of the headline, matching the reference treatment.
    sf = load_script(args.script_size)
    sb = scratch.textbbox((0, 0), args.script, font=sf, stroke_width=2)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    script_layer = Image.new("RGBA", (sw + 64, sh + 64), (0, 0, 0, 0))
    sd = ImageDraw.Draw(script_layer)
    sd.text((32 - sb[0], 32 - sb[1]), args.script, font=sf,
            fill=args.script_fill, stroke_width=2, stroke_fill=(25, 18, 21, 220))
    rotated = script_layer.rotate(args.angle, resample=Image.Resampling.BICUBIC, expand=True)
    if rotated.width > max_width:
        ratio = max_width / rotated.width
        rotated = rotated.resize((max_width, round(rotated.height * ratio)), Image.Resampling.LANCZOS)
    px = W // 2 - rotated.width // 2
    py = args.y - rotated.height // 2
    if px < SAFE_X0 or px + rotated.width > SAFE_X1 or py < SAFE_Y0 or py + rotated.height > SAFE_Y1:
        raise SystemExit("Cursive overprint would leave Instagram safe area; reduce --script-size or adjust --y")
    layer.alpha_composite(rotated, (px, py))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    layer.save(args.out)
    alpha = layer.getchannel("A")
    bbox = alpha.getbbox()
    if bbox and not (SAFE_X0 <= bbox[0] and bbox[2] <= SAFE_X1 and SAFE_Y0 <= bbox[1] and bbox[3] <= SAFE_Y1):
        raise SystemExit(f"Rendered alpha bbox {bbox} exceeds safe bounds")
    print(f"{args.out} | alpha_bbox={bbox} | Anton={size}px | SignPainter={args.script_size}px")


if __name__ == "__main__":
    main()
