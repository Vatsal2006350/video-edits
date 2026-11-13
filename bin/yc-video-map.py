#!/usr/bin/env python3
"""Render the YC-orange founder-video guide overlay as reusable motion frames.

Usage: yc-video-map.py OUTDIR SEGMENT_DIR ASSEMBLED_VIDEO --music-seek SECONDS
The segment directory is produced by build-story-reel.sh. Chapter timing is
measured from those exact files, so a recut keeps every graphic on its line.
"""
import argparse
import bisect
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
YC_LOGO = ROOT / "logos/yc.png"
SWITZER = ROOT / "fonts/Switzer-Bold.otf"
SERIF = ROOT / "fonts/InstrumentSerif-Regular.ttf"
W, H, FPS = 1080, 1920, 30
S = 2  # cards are drawn at 2x, then reduced once for clean type
ORANGE = (255, 102, 0, 255)
WHITE = (255, 251, 246, 255)
BLACK = (16, 16, 16, 236)
GRAY = (198, 198, 198, 255)
CARD_X, CARD_Y, CARD_W = 183, 1095, 714


def probe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], text=True)
    return float(out.strip())


def smooth(v):
    v = max(0.0, min(1.0, v))
    return v * v * (3 - 2 * v)


def ease_out(v):
    v = max(0.0, min(1.0, v))
    return 1 - (1 - v) ** 3


def font(path, size):
    return ImageFont.truetype(str(path), round(size * S))


def text_at(draw, xy, value, face, size, fill, max_w=None):
    f = font(face, size)
    if max_w is not None:
        while draw.textbbox((0, 0), value, font=f)[2] > max_w * S and size > 20:
            size -= 1
            f = font(face, size)
    box = draw.textbbox((0, 0), value, font=f)
    draw.text((round(xy[0] * S) - box[0], round(xy[1] * S) - box[1]),
              value, font=f, fill=fill)


def card_base(height):
    im = Image.new("RGBA", (CARD_W*S, height*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2*S, 2*S, (CARD_W-2)*S, (height-2)*S),
                        radius=23*S, fill=BLACK, outline=ORANGE, width=2*S)
    d.rounded_rectangle((18*S, 21*S, 25*S, (height-21)*S),
                        radius=4*S, fill=ORANGE)
    return im, d


def logo_icon(size):
    # The repository icon has a transparent Y cutout. Flatten it over white so
    # the standard white Y remains white when the card is composited on black.
    source = Image.open(YC_LOGO).convert("RGBA")
    white = Image.new("RGBA", source.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, source).resize((size*S, size*S), Image.Resampling.LANCZOS)


def make_opening():
    """YC's published video prompt paired with a five-part framework."""
    height = 286
    im, d = card_base(height)
    im.alpha_composite(logo_icon(74), (38*S, 35*S))
    text_at(d, (132, 44), "YC FOUNDER VIDEO", SWITZER, 28, ORANGE, 535)
    text_at(d, (42, 117), "5 THINGS TO GET RIGHT", SWITZER, 47, WHITE, 620)
    text_at(d, (42, 179), "What are you doing, and why?", SERIF, 41, WHITE, 628)
    d.line((42*S, 230*S, 668*S, 230*S), fill=(255, 102, 0, 190), width=2*S)
    text_at(d, (42, 245), "1 MINUTE   ·   FOUNDERS TALKING   ·   BULLET POINTS", SWITZER, 20, WHITE, 626)
    return im.resize((CARD_W, height), Image.Resampling.LANCZOS)


def make_stage(number, title, question, bullets):
    height = 254
    im, d = card_base(height)
    text_at(d, (42, 21), f"{number:02d}  /  {title}", SWITZER, 25, ORANGE, 575)
    text_at(d, (42, 57), question, SERIF, 42, WHITE, 628)
    d.line((42*S, 113*S, 668*S, 113*S), fill=(255, 255, 255, 80), width=1*S)
    for i, bullet in enumerate(bullets):
        y = 133 + i*46
        d.ellipse((45*S, (y+11)*S, 56*S, (y+22)*S), fill=ORANGE)
        text_at(d, (72, y), bullet, SWITZER, 27, WHITE, 574)
    return im.resize((CARD_W, height), Image.Resampling.LANCZOS)


def make_payoff():
    im = Image.new("RGBA", (CARD_W*S, 202*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2*S, 2*S, (CARD_W-2)*S, 200*S),
                        radius=23*S, fill=ORANGE)
    text_at(d, (42, 43), "MAKE IT CRYSTAL CLEAR", SWITZER, 49, (14, 14, 14, 255), 620)
    text_at(d, (44, 124), "One line. One product. Why it’s unique.", SERIF, 34,
            (21, 21, 21, 255), 620)
    return im.resize((CARD_W, 202), Image.Resampling.LANCZOS)


def make_cta():
    im, d = card_base(202)
    logo = logo_icon(94)
    im.alpha_composite(logo, (44*S, 52*S))
    text_at(d, (165, 48), "COMMENT YC", SWITZER, 63, WHITE, 510)
    text_at(d, (166, 124), "For the expanded guide", SERIF, 36, ORANGE, 500)
    return im.resize((CARD_W, 202), Image.Resampling.LANCZOS)


def fade_card(layer, card, t, start, duration, y, slide=True, out_fade=0.28):
    local = t - start
    if local < 0 or local > duration:
        return
    opacity = smooth(local / 0.24) * smooth((duration-local) / out_fade)
    if opacity <= 0.005:
        return
    x = CARD_X - round(42 * (1 - ease_out(local / 0.33))) if slide else CARD_X
    if opacity < 0.999:
        faded = card.copy()
        faded.putalpha(card.getchannel("A").point(lambda a: round(a * opacity)))
    else:
        faded = card
    layer.alpha_composite(faded, (x, y))


def draw_top(layer, t, starts, ends):
    idx = bisect.bisect_right(starts, t) - 1
    if idx < 0:
        return
    idx = min(idx, 4)
    x0, x1 = 230, 850
    nodes = [x0 + i * 155 for i in range(5)]
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((183, 287, 897, 392), radius=24,
                        fill=(12, 12, 12, 224), outline=(255, 102, 0, 176), width=2)
    d.rounded_rectangle((x0, 320, x1, 327), radius=3, fill=(255, 255, 255, 86))
    end = ends[idx]
    fraction = max(0.0, min(1.0, (t-starts[idx]) / max(0.001, end-starts[idx])))
    fill_x = nodes[idx] if idx == 4 else nodes[idx] + (nodes[idx+1]-nodes[idx])*fraction
    d.rounded_rectangle((x0, 320, round(fill_x), 327), radius=3, fill=ORANGE)
    labels = ["PRODUCT", "FOUNDERS", "FIT", "TRACTION", "VISION"]
    for i, (x, label) in enumerate(zip(nodes, labels)):
        radius = 11 if i == idx else 8
        fill = ORANGE if i <= idx else (167, 167, 167, 255)
        d.ellipse((x-radius, 323-radius, x+radius, 323+radius), fill=fill,
                  outline=(255, 255, 255, 235), width=2)
        f = ImageFont.truetype(str(SWITZER), 18 if len(label) > 7 else 20)
        b = d.textbbox((0, 0), label, font=f)
        d.text((x-(b[2]-b[0])/2-b[0], 354-b[1]), label, font=f,
               fill=WHITE if i == idx else (218, 218, 218, 220))


def render(args):
    out = args.outdir
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("f_*.png"):
        old.unlink()
    files = sorted(args.segments.glob("p[0-9][0-9].mp4"))
    if len(files) != 12:
        raise SystemExit(f"Expected 12 speech segments, found {len(files)} in {args.segments}")
    durations = [probe_duration(p) for p in files]
    ends = []
    acc = 0.0
    for value in durations:
        acc += value
        ends.append(acc)
    total = probe_duration(args.video)
    intro_end = ends[1]
    starts = [intro_end, ends[3], ends[6], ends[7], ends[8]]
    stage_ends = [ends[3], ends[6], ends[7], ends[8], total]
    cta_start = ends[10]
    drop = 32.16 - args.music_seek

    opening = make_opening()
    stage_cards = [
        make_stage(1, "PRODUCT", "What is your company making?",
                   ["Describe it in one line", "Explain why it’s unique"]),
        make_stage(2, "FOUNDERS", "What has each founder built or achieved?",
                   ["Lead with your best proof", "Add a real number or honor"]),
        make_stage(3, "FOUNDER FIT", "Why are you the right team?",
                   ["Show founder-market fit", "Connect your experience"]),
        make_stage(4, "TRACTION", "What progress can you show?",
                   ["Name the market", "Share revenue and traction"]),
        make_stage(5, "VISION", "What could this become?",
                   ["End with one ambitious line", "Say where it can go"]),
    ]
    payoff = make_payoff()
    cta = make_cta()
    frame_count = math.ceil(total * FPS)
    checks = {}
    for frame in range(frame_count):
        t = frame / FPS
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_top(layer, t, starts, stage_ends)
        fade_card(layer, opening, t, 0, intro_end+0.08, 1035, out_fade=0.28)
        for i, start in enumerate(starts):
            if i == 0:
                stage_duration = drop-start+0.10
            elif i == 4:
                stage_duration = max(0.0, cta_start-start)
            else:
                stage_duration = stage_ends[i]-start
            fade_card(layer, stage_cards[i], t, start, stage_duration,
                      1070, out_fade=0.27)
        # The product clarity line gets its own visual hit on the measured track drop.
        fade_card(layer, payoff, t, drop, starts[1]-drop+0.04,
                  1095, out_fade=0.22)
        fade_card(layer, cta, t, cta_start, total-cta_start, 1116,
                  out_fade=0.28)
        if frame % FPS == 0:
            box = layer.getchannel("A").getbbox()
            if box and not (box[0] >= 59 and box[1] >= 278 and box[2] <= 918 and box[3] <= 1536):
                raise SystemExit(f"Graphic outside IG safe area at {t:.2f}s: {box}")
            checks[f"{t:.2f}"] = box
        # The frame sequence is temporary, so spend CPU here to keep it small
        # enough for machines with limited free space.
        layer.save(out / f"f_{frame:05d}.png", compress_level=9)

    manifest = {
        "source_segments": [str(p) for p in files],
        "segment_durations": durations,
        "duration": total,
        "hook_end": ends[0],
        "intro_end": intro_end,
        "chapter_starts": starts,
        "chapter_ends": stage_ends,
        "cta_start": cta_start,
        "music_seek": args.music_seek,
        "music_drop_on_video": drop,
        "safe_alpha_boxes_each_second": checks,
        "frame_count": frame_count,
    }
    (out / "timing.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k: manifest[k] for k in ("duration", "intro_end", "chapter_starts",
                                                "music_drop_on_video", "frame_count")}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("outdir", type=Path)
    p.add_argument("segments", type=Path)
    p.add_argument("video", type=Path)
    p.add_argument("--music-seek", type=float, required=True)
    render(p.parse_args())
