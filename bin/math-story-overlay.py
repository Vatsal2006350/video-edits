#!/usr/bin/env python3
"""Render Instagram-safe animated calculation graphics as a transparent MOV.

The JSON spec is a short timeline of cards. Each cue may interpolate named
integer values from its ``counts`` map; the same value can then appear in its
equation and result strings. Alpha is preserved with QuickTime Animation.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS = 1080, 1920, 30
SAFE = (59, 278, 918, 1536)
CARD = (210, 322, 870, 748)  # 660 px including shadow, inside the centred 724 px limit
SEQUENCE_CARD = (210, 390, 870, 645)
MAIZE = (255, 202, 73)
CREAM = (250, 247, 239)
MUTED = (199, 197, 190)
INK = (11, 15, 20)
FONT_BOLD = ROOT / "fonts" / "Inter-Bold.ttf"
FONT_SERIF = ROOT / "fonts" / "InstrumentSerif-Regular.ttf"
FONT_DISPLAY = ROOT / "fonts" / "DMSerifDisplay-Regular.ttf"


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def ease(x: float) -> float:
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def count_value(spec: dict, local_t: float) -> int | str:
    start = float(spec.get("from", 0))
    end = float(spec["to"])
    delay = float(spec.get("delay", 0))
    duration = max(0.001, float(spec.get("duration", 0.6)))
    if local_t < delay:
        return str(spec.get("placeholder", "?"))
    f = ease((local_t - delay) / duration)
    return round(start + (end - start) * f)


def wrapped_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_w:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fitted_font(draw: ImageDraw.ImageDraw, text: str, path: Path, size: int, max_w: int) -> ImageFont.FreeTypeFont:
    size = int(size)
    while size > 18:
        font = ImageFont.truetype(str(path), size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_w:
            return font
        size -= 1
    return ImageFont.truetype(str(path), size)


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont,
             fill: tuple[int, int, int, int], max_w: int = 620) -> None:
    font = fitted_font(draw, text, FONT_BOLD if font.getname()[0] == "Inter" else FONT_SERIF,
                       font.size, max_w)
    box = draw.textbbox((0, 0), text, font=font)
    x = W // 2 - (box[2] - box[0]) // 2
    draw.text((x - box[0], y - box[1]), text, font=font, fill=fill)


def render_card(cue: dict, local_t: float, alpha: float, y_shift: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = CARD
    y0 += round(y_shift)
    y1 += round(y_shift)
    a = round(255 * alpha)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x0, y0 + 12, x1, y1 + 12), radius=30, fill=(0, 0, 0, round(a * 0.48)))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))

    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x1, y1), radius=28,
                        fill=(INK[0], INK[1], INK[2], round(a * 0.91)),
                        outline=(255, 202, 73, round(a * 0.82)), width=2)
    d.rounded_rectangle((x0 + 27, y0 + 24, x0 + 214, y0 + 59), radius=17,
                        fill=(255, 202, 73, round(a * 0.18)))
    tagfont = ImageFont.truetype(str(FONT_BOLD), 20)
    d.text((x0 + 42, y0 + 31), "QUICK MATH", font=tagfont, fill=(*MAIZE, a))

    step = int(cue.get("step", 1))
    for i in range(4):
        cx, cy = x1 - 112 + i * 20, y0 + 42
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4),
                  fill=(*MAIZE, a) if i < step else (150, 151, 152, round(a * 0.45)))

    values = {key: count_value(value, local_t) for key, value in cue.get("counts", {}).items()}
    title = cue["title"].format(**values)
    equation = cue["equation"].format(**values)
    result = cue["result"].format(**values)
    note = cue["note"].format(**values)

    titlefont = fitted_font(d, title.upper(), FONT_BOLD, 30, 620)
    titlebox = d.textbbox((0, 0), title.upper(), font=titlefont)
    d.text((W // 2 - (titlebox[2] - titlebox[0]) // 2, y0 + 92), title.upper(),
           font=titlefont, fill=(*CREAM, a))
    d.line((x0 + 36, y0 + 145, x1 - 36, y0 + 145), fill=(255, 255, 255, round(a * 0.16)), width=2)

    eqfont = fitted_font(d, equation, FONT_BOLD, 43, 620)
    eqbox = d.textbbox((0, 0), equation, font=eqfont)
    d.text((W // 2 - (eqbox[2] - eqbox[0]) // 2, y0 + 169), equation,
           font=eqfont, fill=(*CREAM, a))

    resfont = fitted_font(d, result, FONT_SERIF, 57, 620)
    resbox = d.textbbox((0, 0), result, font=resfont)
    d.text((W // 2 - (resbox[2] - resbox[0]) // 2, y0 + 240), result,
           font=resfont, fill=(*MAIZE, a))

    note_font = fitted_font(d, note, FONT_BOLD, 25, 620)
    lines = wrapped_lines(d, note, note_font, 620)
    for i, line in enumerate(lines[:2]):
        note_box = d.textbbox((0, 0), line, font=note_font)
        d.text((W // 2 - (note_box[2] - note_box[0]) // 2, y0 + 330 + 30 * i), line,
               font=note_font, fill=(*MUTED, a))
    return layer


def render_frame(spec: dict, t: float) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if "sequence" in spec:
        return render_sequence_frame(spec, t)
    for cue in spec["cards"]:
        start, end = float(cue["start"]), float(cue["end"])
        fade = min(0.20, (end - start) * 0.24)
        if not start - fade <= t <= end + fade:
            continue
        local = max(0.0, t - start)
        opacity = min(ease((t - start) / fade), ease((end - t) / fade))
        shift = 24 * (1.0 - ease((t - start) / fade))
        if opacity > 0:
            canvas.alpha_composite(render_card(cue, local, opacity, shift))
    return canvas


def render_sequence_frame(spec: dict, t: float) -> Image.Image:
    """Keep one compact card on screen while its equation changes in place."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = SEQUENCE_CARD
    entrance = ease(t / 0.28)
    shift = round(12 * (1.0 - entrance))
    a = round(255 * entrance)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x0, y0 + shift + 12, x1, y1 + shift + 12), radius=30,
                         fill=(0, 0, 0, round(a * 0.48)))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0 + shift, x1, y1 + shift), radius=28,
                        fill=(INK[0], INK[1], INK[2], round(a * 0.92)),
                        outline=(255, 202, 73, round(a * 0.82)), width=2)

    states = spec["sequence"]
    active = states[0]
    for state in states:
        if float(state["start"]) <= t:
            active = state
        else:
            break
    state_age = max(0.0, t - float(active["start"]))
    text_in = ease(state_age / 0.22)
    text_a = round(a * text_in)
    text_shift = round(9 * (1.0 - text_in))
    values = {key: count_value(value, state_age) for key, value in active.get("counts", {}).items()}
    equation = active["equation"].format(**values)
    result = active["result"].format(**values)

    eqfont = fitted_font(d, equation, FONT_BOLD, 45, 620)
    eqbox = d.textbbox((0, 0), equation, font=eqfont)
    d.text((W // 2 - (eqbox[2] - eqbox[0]) // 2, y0 + shift + 68 + text_shift), equation,
           font=eqfont, fill=(*CREAM, text_a))
    resfont = fitted_font(d, result, FONT_DISPLAY, 66, 620)
    resbox = d.textbbox((0, 0), result, font=resfont)
    d.text((W // 2 - (resbox[2] - resbox[0]) // 2, y0 + shift + 152 + text_shift), result,
           font=resfont, fill=(*MAIZE, text_a))
    return layer


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="transparent .mov")
    ap.add_argument("--proof-dir", type=Path, help="save representative transparent PNG frames")
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text())
    cards = spec.get("cards", [])
    sequence = spec.get("sequence", [])
    if not cards and not sequence:
        raise SystemExit("spec must contain cards or a sequence")
    duration = (float(spec["duration"]) if sequence else max(float(c["end"]) for c in cards))
    # All pixels, including the safe-area bounds, are verified in the PNG layer.
    for bounds in (CARD, SEQUENCE_CARD):
        if bounds[0] < SAFE[0] or bounds[2] > SAFE[2] or bounds[1] < SAFE[1] or bounds[3] > SAFE[3]:
            raise SystemExit(f"card bounds {bounds} exceed Instagram safe box {SAFE}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="math-overlay-") as td:
        work = Path(td)
        frames = math.ceil(duration * FPS)
        for i in range(frames):
            frame = render_frame(spec, i / FPS)
            bbox = frame.getchannel("A").getbbox()
            if bbox and not (SAFE[0] <= bbox[0] and bbox[2] <= SAFE[2] and SAFE[1] <= bbox[1] and bbox[3] <= SAFE[3]):
                raise SystemExit(f"rendered alpha bbox {bbox} exceeds Instagram safe area {SAFE}")
            frame.save(work / f"f{i:05d}.png")
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-y", "-v", "error",
            "-framerate", str(FPS), "-i", str(work / "f%05d.png"),
            "-c:v", "qtrle", "-pix_fmt", "argb", "-r", str(FPS),
            "-movflags", "+faststart", str(args.out),
        ], check=True)
    if args.proof_dir:
        args.proof_dir.mkdir(parents=True, exist_ok=True)
        if sequence:
            marks = [float(state["start"]) for state in sequence]
            marks += [(float(state["start"]) + float(state["end"])) / 2 for state in sequence]
            marks += [duration - 0.10]
            for n, t in enumerate(sorted(set(marks)), start=1):
                render_frame(spec, t).save(args.proof_dir / f"state{n:02d}-{t:.2f}.png")
        else:
            for n, cue in enumerate(cards, start=1):
                for label, t in (("in", float(cue["start"]) + 0.35),
                                 ("hold", (float(cue["start"]) + float(cue["end"])) / 2),
                                 ("out", float(cue["end"]) - 0.10)):
                    render_frame(spec, t).save(args.proof_dir / f"cue{n:02d}-{label}.png")
    print(f"wrote {args.out} | {frames} frames at {FPS}fps | safe card bounds {SEQUENCE_CARD if sequence else CARD}")


if __name__ == "__main__":
    main()
