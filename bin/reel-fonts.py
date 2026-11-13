#!/usr/bin/env python3
"""Reusable, brand-aware font presets for the reel builders.

Commands:
  python3 bin/reel-fonts.py list
  python3 bin/reel-fonts.py fields creator-signature
  python3 bin/reel-fonts.py specimen [output.png]

REEL_FONT_PRESET is consumed by build-story-reel.sh. Licensed reference fonts
are kept in fonts/ with their licenses; unavailable commercial faces use named,
clearly disclosed local substitutes rather than unlicensed downloads.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"


def p(filename: str) -> str:
    return str(FONTS / filename)


SIGNATURE = {
    "hero": "Anton-Regular.ttf",
    "caption": "Instrument Serif",
    "caption_size": 78,
    "caption_bold": 0,
    "outline": 2,
    "highlight": "&H0005CBFF&",
    "hook_size": 112,
    "opening_display": "Anton-Regular.ttf",
    "opening_script": "/System/Library/Fonts/Supplemental/SignPainter.ttc",
    "opening_script_face_index": 0,
    "opening_script_color": "#F22F46",
    "opening_style": "headline-script.py",
}

PRESETS = {
    "creator-signature": {
        **SIGNATURE,
        "label": "Creator signature",
        "sample": "Anton headline + SignPainter script overprint + Instrument Serif captions",
        "note": "Reference-matched bold/cursive opening; warm white display, red script, Instrument Serif captions.",
    },
    "druk-inspired": {
        **SIGNATURE,
        "label": "Druk-inspired",
        "hero": "Anton-Regular.ttf",
        "sample": "Vertically elongated, horizontally compressed Anton display",
        "note": "Rendered through bin/druk-inspired-title.py using bundled OFL Anton; it evokes the tall condensed look but is not the Druk font.",
    },
    "inter-black": {
        **SIGNATURE,
        "label": "Inter Black",
        "hero": "Inter-Black.ttf",
        "sample": "Inter Black display + Instrument Serif captions",
        "note": "Inter Black is instanced locally from the OFL variable font.",
    },
    "lilita-one": {
        **SIGNATURE,
        "hero": "LilitaOne-Regular.ttf",
        "label": "Lilita One",
        "sample": "Rounded, chunky vlog-title display + Instrument Serif captions",
        "note": "Downloaded from Google Fonts; SIL Open Font License is bundled beside it.",
    },
    "akira-inspired": {
        **SIGNATURE,
        "label": "Akira-inspired",
        "hero": "Bungee-Regular.ttf",
        "sample": "Bungee display + Instrument Serif captions",
        "note": "Bungee is the installed blocky fallback; exact Akira Expanded needs its own license.",
    },
    "apple-garamond-inspired": {
        **SIGNATURE,
        "label": "Apple Garamond-inspired",
        "hero": "PlayfairDisplay-BlackItalic.ttf",
        "sample": "Playfair Display Black Italic + Instrument Serif captions",
        "note": "Apple Garamond is not bundled; this is the closest installed editorial serif pairing.",
    },
    "dela-gothic-one": {
        **SIGNATURE,
        "label": "Dela Gothic One",
        "hero": "DelaGothicOne-Regular.ttf",
        "sample": "Dela Gothic One display + Instrument Serif captions",
        "note": "Downloaded from Google Fonts; SIL Open Font License is bundled beside it.",
    },
    "perfectly-nineties-inspired": {
        **SIGNATURE,
        "label": "Perfectly Nineties-inspired",
        "hero": "InstrumentSerif-Regular.ttf",
        "sample": "Instrument Serif display + italic captions",
        "note": "Perfectly Nineties is not bundled; this uses the installed Instrument Serif alternative.",
    },
    "bebas-neue": {
        **SIGNATURE,
        "label": "Bebas Neue",
        "hero": "BebasNeue-Regular.ttf",
        "sample": "Bebas Neue display + Instrument Serif captions",
        "note": "Already available locally; its OFL license is included beside the font.",
    },
}

ALIASES = {
    "signature": "creator-signature",
    "default": "creator-signature",
    "druk": "druk-inspired",
    "akira": "akira-inspired",
    "apple-garamond": "apple-garamond-inspired",
    "perfectly-nineties": "perfectly-nineties-inspired",
}


def get_preset(name: str) -> dict:
    name = ALIASES.get(name, name)
    if name not in PRESETS:
        raise SystemExit(f"Unknown font preset '{name}'. Run: python3 bin/reel-fonts.py list")
    result = dict(PRESETS[name])
    result["name"] = name
    result["hero_path"] = p(result["hero"])
    return result


def emit_fields(name: str) -> None:
    s = get_preset(name)
    vals = [s["caption"], s["caption_size"], s["caption_bold"], s["outline"],
            s["highlight"], s["hero_path"], s["hook_size"], s["hero_path"]]
    print("|".join(map(str, vals)))


def list_presets() -> None:
    print("Reel font presets (use REEL_FONT_PRESET=<name>)")
    print("Opening headline default: Anton bold uppercase + red SignPainter brush-script overprint")
    for name, s in PRESETS.items():
        print(f"\n{name}\n  {s['label']} — {s['sample']}\n  {s['note']}")


def draw_specimen(destination: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width, card_w, card_h = 1560, 750, 252
    margin, gap, header = 30, 20, 122
    rows = (len(PRESETS) + 1) // 2
    height = header + margin + rows * card_h + (rows - 1) * gap + margin
    bg = (13, 24, 40)
    panel = (23, 38, 58)
    gold = (255, 210, 74)
    white = (247, 245, 239)
    muted = (163, 177, 194)
    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)
    f_bold = ImageFont.truetype(p("Inter-Bold.ttf"), 34)
    f_small = ImageFont.truetype(p("Inter-SemiBold.ttf"), 17)
    f_cap = ImageFont.truetype(p("InstrumentSerif-Regular.ttf"), 29)
    f_note = ImageFont.truetype(p("AvenirNext-Regular.ttf"), 14)
    d.text((margin, 24), "REEL TYPE", font=f_bold, fill=white)
    d.rounded_rectangle((margin, 73, margin + 90, 81), radius=4, fill=gold)
    d.text((margin + 106, 63), "Brand anchor: Anton display · Instrument Serif captions · maize accent",
           font=f_small, fill=muted)
    for i, (name, s) in enumerate(PRESETS.items()):
        col, row = i % 2, i // 2
        x = margin + col * (card_w + gap)
        y = header + margin + row * (card_h + gap)
        d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=15, fill=panel)
        d.text((x + 20, y + 13), s["label"].upper(), font=f_small, fill=gold)
        note = s["note"]
        words, lines, line = note.split(), [], ""
        for word in words:
            trial = f"{line} {word}".strip()
            if line and f_note.getlength(trial) > card_w - 42:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        for ni, note_line in enumerate(lines[:2]):
            d.text((x + 20, y + 39 + 17 * ni), note_line, font=f_note, fill=muted)
        hero = ImageFont.truetype(p(s["hero"]), 49)
        line = "DAY 1 OF SHARING"
        while hero.size > 35 and hero.getlength(line) > card_w - 42:
            hero = ImageFont.truetype(p(s["hero"]), hero.size - 2)
        d.text((x + 20, y + 78), line, font=hero, fill=white)
        d.text((x + 20, y + 132), "STARTUP ADVICE", font=hero, fill=white)
        if name == "creator-signature":
            script_path = Path("/System/Library/Fonts/Supplemental/SignPainter.ttc")
            if script_path.exists():
                script = ImageFont.truetype(str(script_path), 51, index=0)
                d.text((x + card_w // 2, y + 157), "YC", font=script,
                       fill=(242, 47, 70), anchor="mm")
        d.text((x + 22, y + 203), "Something I wish I knew earlier.", font=f_cap, fill=gold)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    im.save(destination, quality=94)
    print(destination)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help", "help"}:
        print("Usage: reel-fonts.py list | fields <preset> | json <preset> | specimen [output.png]")
        return
    command = args[0]
    if command == "list":
        list_presets()
    elif command == "fields" and len(args) == 2:
        emit_fields(args[1])
    elif command == "json" and len(args) == 2:
        print(json.dumps(get_preset(args[1]), indent=2))
    elif command == "specimen":
        destination = args[1] if len(args) > 1 else str(FONTS / "font-options.png")
        draw_specimen(destination)
    else:
        raise SystemExit("Usage: reel-fonts.py list | fields <preset> | json <preset> | specimen [output.png]")


if __name__ == "__main__":
    main()
