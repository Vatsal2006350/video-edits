#!/usr/bin/env python3
"""News-page ("pager") reel: one story = photo + highlighted headline + dek (+ chart / bars), 1080x1920.

    python3 bin/pager-reel.py <spec.json>        # one reel
    python3 bin/pager-reel.py specs/*.json        # several

Look: measured off The Sarcastic Page card (instagram.com/p/Dfm6D1Aoust): full-bleed photo on top that
fades into the panel, a bold centred headline with the key phrase on a solid highlight box, a one-line grey
dek. Ours is the dark version (IG draws its own white text over the bottom, which vanishes on white) and
uses our own kicker pill instead of their logo. Brand-coloured highlight per company (Nvidia green etc).

Spec:
{"name", "photo", "focus": [fx, fy] (0-1 crop centre), "kicker": "BREAKING", "accent": "#76B900",
 "accent_text": "#000000", "headline": "Jensen Huang [[Resigns as Nvidia CEO]] After 33 Years",
 "dek": "...", "logos": ["logos/nvidia_w.png"], "visual": {"type": "chart"|"bars"|"stat", ...},
 "music": {"file", "seek"}, "duration": 9, "out"}
Every number on screen must come from a source listed in the spec's "sources" (checked by hand).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS = 1080, 1920, 30
BG = (12, 12, 13)
PHOTO_H = 1130
TEXT_W = 724                      # centred text bound for the IG safe box (x 59-918)
HEAD_FONT = os.path.join(FONTS, "Montserrat-ExtraBold.ttf")
DEK_FONT = os.path.join(FONTS, "Inter-SemiBold.ttf")
KICK_FONT = os.path.join(FONTS, "Inter-Black.ttf")


def hexc(h, a=255):
    h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ease(u):
    u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3


# ---------------------------------------------------------------- headline layout
def parse_rich(text):
    """'a [[b c]] d' -> word tokens with a highlight flag. Markers may sit inside a token (quotes, colons)."""
    toks, hl = [], False
    for seg_i, seg in enumerate(text.replace("]]", "[[").split("[[")):
        hl = seg_i % 2 == 1
        for w in seg.split():
            toks.append([w, hl])
    # glue punctuation-only tokens (": ") onto the previous word, unhighlighted part stays with it
    out = []
    for w, h in toks:
        if out and all(c in ":,.!?”’\"'" for c in w): out[-1][0] += w
        else: out.append([w, h])
    return [tuple(x) for x in out]


def layout_headline(text, size):
    f = ImageFont.truetype(HEAD_FONT, size)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    toks = parse_rich(text)
    lines, cur = [], []
    for w, hl in toks:
        cand = " ".join(x[0] for x in cur + [(w, hl)])
        if cur and d.textlength(cand, font=f) > TEXT_W:
            lines.append(cur); cur = [(w, hl)]
        else:
            cur.append((w, hl))
    if cur: lines.append(cur)
    return f, lines


def fit_headline(text, max_lines=4):
    """Largest size that fits in <= max_lines with no one-word last line (orphans like "Years" / "17");
    falls back to the largest size that merely fits."""
    first = None
    for size in range(76, 54, -2):
        f, lines = layout_headline(text, size)
        if len(lines) > max_lines: continue
        if first is None: first = (f, lines, size)
        if len(lines[-1]) >= 2: return f, lines, size
    return first if first else (f, lines, size)


def draw_headline(img, f, lines, size, y0, accent, accent_text, wipe):
    """Centred lines; highlighted runs get a solid box that wipes in left->right (wipe 0..1)."""
    d = ImageDraw.Draw(img)
    lh = int(size * 1.22)
    sp = d.textlength(" ", font=f)
    for li, line in enumerate(lines):
        y = y0 + li * lh
        widths = [d.textlength(w, font=f) for w, _ in line]
        total = sum(widths) + sp * (len(line) - 1)
        x = (W - total) / 2
        # group highlighted runs for one continuous box per line
        runs, i = [], 0
        while i < len(line):
            if line[i][1]:
                j = i
                while j < len(line) and line[j][1]: j += 1
                runs.append((i, j)); i = j
            else: i += 1
        xs = [x + sum(widths[:k]) + sp * k for k in range(len(line))]
        for a, b in runs:
            bx0 = xs[a] - 12; bx1 = xs[b - 1] + widths[b - 1] + 12
            cut = bx0 + (bx1 - bx0) * wipe
            if cut > bx0 + 2:
                d.rounded_rectangle([bx0, y - 4, cut, y + int(size * 1.12)], radius=8, fill=accent)
        for k, (w, hl) in enumerate(line):
            col = accent_text if (hl and wipe > 0.6) else (255, 255, 255, 255)
            d.text((xs[k], y), w, font=f, fill=col)
    return y0 + len(lines) * lh


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


# ---------------------------------------------------------------- visuals
def draw_chart(img, v, prog, accent):
    """Line chart of real closes in a dark card over the photo's lower half; draws in with `prog`."""
    data = json.load(open(os.path.join(ROOT, v["data"])))["daily"][-v.get("days", 60):]
    vals = [p[1] for p in data]
    extra = v.get("extra_point")                      # e.g. today's open, drawn red at the end
    if extra: vals = vals + [extra["value"]]
    x0, x1, y0, y1 = 130, 860, 650, 960       # right end stays left of the IG rail (x 918)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([x0 - 40, y0 - 70, x1 + 40, y1 + 50], radius=28, fill=(10, 10, 12, 205))
    img.alpha_composite(card)
    d = ImageDraw.Draw(img)
    lo, hi = min(vals), max(vals); pad = (hi - lo) * 0.12
    lo -= pad; hi += pad
    pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * (vv - lo) / (hi - lo)) for i, vv in enumerate(vals)]
    n = max(2, int(len(pts) * ease(prog)))
    main = pts[:min(n, len(pts) - (1 if extra else 0))]
    if len(main) > 1: d.line(main, fill=(255, 255, 255, 235), width=6, joint="curve")
    lf = ImageFont.truetype(DEK_FONT, 30); bf = ImageFont.truetype(KICK_FONT, 44)
    d.text((x0 - 10, y0 - 54), v.get("title", ""), font=lf, fill=(200, 200, 200, 255))
    if extra and n >= len(pts):
        a, b = pts[-2], pts[-1]
        d.line([a, b], fill=hexc("#FF3B30"), width=7)
        d.ellipse([b[0] - 13, b[1] - 13, b[0] + 13, b[1] + 13], fill=hexc("#FF3B30"))
        lab = extra["label"]; tw = d.textlength(lab, font=bf)
        d.text((min(b[0] - tw / 2, 900 - tw), b[1] + 22), lab, font=bf, fill=hexc("#FF3B30"))
        pa = pts[-2]
        prev = v.get("prev_label")
        if prev:
            tw = d.textlength(prev, font=lf)
            d.text((pa[0] - tw / 2, min(pts[k][1] for k in range(len(pts) - 8, len(pts) - 1)) - 52), prev, font=lf, fill=(255, 255, 255, 230))


def draw_bars(img, v, prog, accent):
    """Two-bar comparison (e.g. $677M -> $1.6B) in a dark card; bars grow with `prog`."""
    x0, x1, y0, y1 = 160, 860, 640, 980        # card edge (x1+40) stays left of the IG rail
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([x0 - 40, y0 - 60, x1 + 40, y1 + 40], radius=28, fill=(10, 10, 12, 205))
    img.alpha_composite(card)
    d = ImageDraw.Draw(img)
    mx = max(b["value"] for b in v["bars"])
    lf = ImageFont.truetype(DEK_FONT, 32); nf = ImageFont.truetype(KICK_FONT, 54)
    bw = 230; gap = (x1 - x0 - bw * len(v["bars"])) / (len(v["bars"]) + 1)
    for i, b in enumerate(v["bars"]):
        u = ease((prog - i * 0.25) / 0.75)
        bh = (y1 - y0 - 120) * b["value"] / mx * u
        bx = x0 + gap * (i + 1) + bw * i
        col = accent if i == len(v["bars"]) - 1 else (110, 110, 115, 255)
        d.rounded_rectangle([bx, y1 - 50 - bh, bx + bw, y1 - 50], radius=14, fill=col)
        tw = d.textlength(b["label"], font=lf); d.text((bx + (bw - tw) / 2, y1 - 40), b["label"], font=lf, fill=(210, 210, 210, 255))
        if u > 0.2:
            tw = d.textlength(b["text"], font=nf)
            d.text((bx + (bw - tw) / 2, y1 - 50 - bh - 66), b["text"], font=nf, fill=(255, 255, 255, int(255 * min(1, u * 1.5))))


def draw_stat(img, v, prog, accent):
    bf = ImageFont.truetype(KICK_FONT, 150); lf = ImageFont.truetype(DEK_FONT, 34)
    d = ImageDraw.Draw(img); u = ease(prog)
    txt = v["text"]; tw = d.textlength(txt, font=bf)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    ld.text(((W - tw) / 2, 760 + 40 * (1 - u)), txt, font=bf, fill=accent[:3] + (int(255 * u),), stroke_width=4, stroke_fill=(0, 0, 0, int(200 * u)))
    lab = v.get("label", ""); lw = ld.textlength(lab, font=lf)
    ld.text(((W - lw) / 2, 930 + 40 * (1 - u)), lab, font=lf, fill=(235, 235, 235, int(255 * u)))
    img.alpha_composite(layer)



# ---------------------------------------------------------------- QC (added after "make sure u quality check all of this")
SAFE = dict(x0=59, x1=918, y0=278, y1=1536)

def _norm_nums(text):
    """Numbers as they'd be checked against sources: '$1.6 Billion' -> ['1.6'], '13%' -> ['13'], '81,911' -> ['81911']."""
    import re
    return [x.replace(",", "") for x in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]

def qc_check(spec, overlays, out, dur):
    flags = []
    # 1. layout: every overlay pixel (text, pills, logos, chart cards) inside the IG safe box, at the final state
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); overlays(lay, dur)
    a = np.asarray(lay)[..., 3]
    ys, xs = np.where(a > 24)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        if x0 < SAFE["x0"] or x1 > SAFE["x1"] or y0 < SAFE["y0"] or y1 > SAFE["y1"]:
            flags.append(f"OUTSIDE SAFE BOX: overlays span x {x0}-{x1}, y {y0}-{y1}")
    # 2. facts: every number in headline/dek/visual labels appears in the sources
    src = " ".join(spec.get("sources", [])).replace(",", "")
    if not spec.get("sources"): flags.append("NO SOURCES")
    shown = spec["headline"] + " " + spec.get("dek", "") + " " + json.dumps(spec.get("visual", {}), ensure_ascii=False)
    shown = shown.replace('"data": "videos/pager-reels/data/nvda.json"', "")
    for n in set(_norm_nums(shown)):
        if n not in src and n not in spec.get("derived_numbers", []):
            flags.append(f"NUMBER NOT IN SOURCES: {n}")
    # 3. photo credit recorded
    cr = os.path.join(ROOT, "videos/pager-reels/img/credits.json")
    if os.path.exists(cr):
        files = [os.path.basename(c["file"]) for c in json.load(open(cr))]
        if os.path.basename(spec["photo"]) not in files and not spec.get("photo_credit"):
            flags.append("PHOTO CREDIT MISSING")
    # 4. audio: audible from the first half second, and the right length
    r = subprocess.run(["ffmpeg", "-nostdin", "-t", "0.5", "-i", out, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    lvl = float(r.split("mean_volume:")[1].split(" dB")[0]) if "mean_volume:" in r else -99
    if lvl < -26: flags.append(f"OPENING TOO QUIET ({lvl} dB)")
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]))
    if abs(d - dur) > 0.15: flags.append(f"DURATION {d:.2f}s != {dur}")
    if "[[" not in spec["headline"]: flags.append("NO HIGHLIGHT")
    return flags

# ---------------------------------------------------------------- render
def cover(im, w, h, fx, fy):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    x = int(min(max(fx * im.width - w / 2, 0), im.width - w)); y = int(min(max(fy * im.height - h / 2, 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def render(spec_path):
    spec = json.load(open(spec_path))
    dur = spec.get("duration", 9.0); n = int(dur * FPS)
    accent = hexc(spec.get("accent", "#76B900")); atext = hexc(spec.get("accent_text", "#000000"))
    fx, fy = spec.get("focus", [0.5, 0.4])
    Z = 1.08
    photo = Image.open(os.path.join(ROOT, spec["photo"])).convert("RGB")
    big = cover(photo, int(W * Z), int(PHOTO_H * Z), fx, fy)
    if spec.get("grade", True):
        arr = np.asarray(big).astype(np.float32)
        arr = (arr - 128) * 1.06 + 128; arr *= 0.92
        big = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # gradient: photo -> panel, plus a top shade so the kicker reads
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grad)
    for y in range(PHOTO_H - 470, PHOTO_H):
        a = int(255 * ease((y - (PHOTO_H - 470)) / 470) ** 1.2)
        gd.line([(0, y), (W, y)], fill=BG + (a,))
    for y in range(0, 420):
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(110 * (1 - y / 420))))
    hf, hlines, hsize = fit_headline(spec["headline"])
    lh = int(hsize * 1.22)
    dek_f = ImageFont.truetype(DEK_FONT, 37)
    dd = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    dek_lines = wrap(dd, spec.get("dek", ""), dek_f, TEXT_W)
    block = len(hlines) * lh + 26 + len(dek_lines) * 50
    head_y = min(1100, 1520 - block)                  # keep the dek above the IG bottom band (y 1536)
    logos = [Image.open(os.path.join(ROOT, p)).convert("RGBA") for p in spec.get("logos", [])]
    logos = [l.resize((int(l.width * 64 / l.height), 64), Image.LANCZOS) if l.height else l for l in logos]
    kf = ImageFont.truetype(KICK_FONT, 34)
    v = spec.get("visual")
    def overlays(img, t):
        if v and v["type"] == "chart": draw_chart(img, v, (t - 0.5) / 2.2, accent)
        if v and v["type"] == "bars": draw_bars(img, v, (t - 0.5) / 1.8, accent)
        if v and v["type"] == "stat": draw_stat(img, v, (t - 0.4) / 0.6, accent)
        d = ImageDraw.Draw(img)
        # kicker pill (frame 1 readable), pulses once at 0.2 s
        k = spec.get("kicker", "BREAKING"); kw = d.textlength(k, font=kf)
        d.rounded_rectangle([64, 300, 64 + kw + 36, 300 + 56], radius=28, fill=accent)
        d.text((82, 306), k, font=kf, fill=atext)
        if spec.get("live_dot"):
            on = int(t * 2) % 2 == 0
            d.ellipse([64 + kw + 52, 316, 64 + kw + 76, 340], fill=(255, 59, 48, 255 if on else 90))
        # logos centred just above the headline
        if logos:
            tot = sum(l.width for l in logos) + 40 * (len(logos) - 1); lx = (W - tot) // 2
            for l in logos:
                img.alpha_composite(l, (lx, head_y - 96)); lx += l.width + 40
        bottom = draw_headline(img, hf, hlines, hsize, head_y, accent, atext, ease((t - 0.15) / 0.45))
        da = int(255 * ease((t - 0.35) / 0.4))
        for j, ln in enumerate(dek_lines):
            tw = d.textlength(ln, font=dek_f)
            d.text(((W - tw) / 2, bottom + 26 + j * 50), ln, font=dek_f, fill=(190, 190, 195, max(da, 0)))

    out = spec["out"]; os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out.replace(".mp4", ".noaudio.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt",
                           "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", tmp],
                          stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        z = 1 + (Z - 1) * (t / dur)                  # slow push-in over the whole reel
        cw, ch = int(W * Z / z), int(PHOTO_H * Z / z)
        cx, cy = (big.width - cw) // 2, (big.height - ch) // 2
        ph = big.crop((cx, cy, cx + cw, cy + ch)).resize((W, PHOTO_H), Image.BILINEAR)
        img = Image.new("RGBA", (W, H), BG + (255,)); img.paste(ph, (0, 0))
        img.alpha_composite(grad)
        overlays(img, t)
        ff.stdin.write(img.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    # music: start where the track is already loud, fade out at the end
    m = spec["music"]
    run = lambda c: subprocess.run(c, check=True, capture_output=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ss", f"{m.get('seek', 0):.2f}", "-i", m["file"], "-map", "0:v",
         "-map", "1:a", "-af", f"aresample=44100,loudnorm=I=-15:TP=-2,afade=t=in:d=0.03,afade=t=out:st={dur - 0.9:.2f}:d=0.9",
         "-t", f"{dur:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
    os.remove(tmp)
    qc = qc_check(spec, overlays, out, dur)
    print(f"wrote {out}  headline {len(hlines)} lines @ {hsize}px; QC: " + ("ok" if not qc else " | ".join(qc)))
    return qc


if __name__ == "__main__":
    bad = {}
    for p in sys.argv[1:]:
        f = render(p)
        if f: bad[os.path.basename(p)] = f
    print(f"\nQC summary: {len(sys.argv) - 1 - len(bad)} ok, {len(bad)} flagged")
    for k, f in bad.items(): print(f"  {k}: {'; '.join(f)}")
    sys.exit(1 if bad else 0)
