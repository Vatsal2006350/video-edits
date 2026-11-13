#!/usr/bin/env python3
"""Faceless podcast-clip builder: long 16:9 interview -> 1080x1920 reel.

    bin/podcast-clip.sh <spec.json>          # wrapper: runs this under uvx with opencv

What it does, in order:
  1. cuts the spec's source ranges (`hook` flash-forward first, then `clips`) into one edit;
  2. finds camera cuts inside each range and, per shot, detects faces (Haar frontal+profile);
     one dominant face -> 9:16 crop that follows the speaker ("crop"); two faces, a wide, or no
     face -> the 16:9 shot framed over a blurred, darkened copy of itself ("frame");
     `layout` in the spec forces one or the other for the whole reel;
  3. grades per style, punch-zooms the `punch` ranges (a hard 1.14x cut-in, no zoompan);
  4. writes word-by-word ASS captions: English from local whisper word timings (per range,
     cached), or hand-written `lines` (translated Hindi/Punjabi) in source time;
  5. headline PNG from frame one (no fade-in, fades out), optional giant `bg_word` in the
     framed layout's background, a small source credit;
  6. music bed under the voice with side-chain ducking, audible from frame one, faded out;
  7. master (crf 15 slow) -> caller runs bin/export-ig.sh + ig-safe view.

Styles (`style`): emotional (Instrument Serif, cream, low-sat warm grade, vignette, word
reveal), funny (Anton caps, yellow active word, punchy), bold (Anton caps white/maize,
contrasty), hindi-emotional (emotional look with phrase subtitles). See
formats/faceless-podcast-clip.md for the measured numbers and the reasons.
"""
import json, os, subprocess, sys, hashlib, math, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS = 1080, 1920, 30
SAFE = dict(x0=59, x1=918, y0=278, y1=1536)
CENTER_MAX_W = 2 * (SAFE["x1"] - W // 2)          # 756 -> keep 724 to be safe
TEXT_W = 724

STYLES = {
    "emotional": dict(cap_font="Instrument Serif", cap_file="InstrumentSerif-Regular.ttf", cap_size=92,
                      caps=False, fill="F4EDE1", active="FFFFFF", dim_alpha="70", outline=2, shadow=3,
                      head_file="InstrumentSerif-Italic.ttf", head_size=96, head_fill=(244, 237, 225),
                      head_case="as-is", max_chars=24, max_words=5,
                      grade="eq=saturation=0.78:contrast=1.04:brightness=0.0:gamma=0.98"
                            ",colorbalance=rs=0.04:gs=0.01:bs=-0.03:rm=0.03:bm=-0.02",
                      bg_word_file="InstrumentSerif-Italic.ttf", music_vol=0.30, duck_ratio=5),
    "funny": dict(cap_font="Anton", cap_file="Anton-Regular.ttf", cap_size=104,
                  caps=True, fill="FFFFFF", active="2BD9FF", dim_alpha=None, outline=7, shadow=0,
                  head_file="Anton-Regular.ttf", head_size=104, head_fill=(255, 217, 43),
                  head_case="upper", max_chars=16, max_words=3,
                  grade="eq=saturation=1.12:contrast=1.06", bg_word_file="Anton-Regular.ttf",
                  music_vol=0.22, duck_ratio=8),
    "bold": dict(cap_font="Anton", cap_file="Anton-Regular.ttf", cap_size=100,
                 caps=True, fill="FFFFFF", active="05CBFF", dim_alpha=None, outline=6, shadow=0,
                 head_file="Anton-Regular.ttf", head_size=100, head_fill=(255, 255, 255),
                 head_case="upper", max_chars=16, max_words=3,
                 grade="eq=saturation=0.92:contrast=1.10:brightness=-0.01",
                 bg_word_file="Anton-Regular.ttf", music_vol=0.26, duck_ratio=6),
}
STYLES["hindi-emotional"] = dict(STYLES["emotional"], cap_size=72, max_chars=34, box=True, outline=10, shadow=0)  # dark box: thin serif vanished on a white shirt (13)
STYLES["hindi-funny"] = dict(STYLES["funny"], cap_size=74, outline=6)   # phrase subtitles in Anton caps

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))[:400]}\n{r.stderr[-2500:]}")
    return r.stdout

def q(t):          # quantize to the frame grid
    return round(t * FPS) / FPS

# ---------------------------------------------------------------- shots + faces
def analyse(src, t0, t1, cache_dir):
    """Return list of shots [(a,b,layout,cx)] in source time for range t0..t1."""
    key = hashlib.md5(f"{src}{t0}{t1}v11".encode()).hexdigest()[:12]
    cp = os.path.join(cache_dir, f"shots_{key}.json")
    if os.path.exists(cp):
        return json.load(open(cp))
    import cv2
    fr = cv2.data.haarcascades
    front = cv2.CascadeClassifier(fr + "haarcascade_frontalface_default.xml")
    prof = cv2.CascadeClassifier(fr + "haarcascade_profileface.xml")
    sw, sh = 960, 540
    step = 1 / 6
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", src,
                          "-vf", f"fps=6,scale={sw}:{sh}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True).stdout
    n = len(raw) // (sw * sh * 3)
    frames = np.frombuffer(raw[: n * sw * sh * 3], np.uint8).reshape(n, sh, sw, 3)
    samples, prev = [], None
    for i, f in enumerate(frames):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([cv2.cvtColor(f, cv2.COLOR_BGR2HSV)], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        gf = g.astype(np.float32)
        # dark studio cuts only reach ~0.29 Bhattacharyya (Raj Shamani set), so 0.24 or a pixel jump
        cut = prev is not None and (cv2.compareHist(prev, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.24 or
                                    float(np.mean(np.abs(gf - prevg))) > 8.0)
        prev = hist; prevg = gf
        faces = []
        for det, flip in ((front, False), (prof, False), (prof, True)):
            img = cv2.flip(g, 1) if flip else g
            for (x, y, w, h) in det.detectMultiScale(img, 1.1, 5, minSize=(34, 34)):
                if flip: x = sw - x - w
                faces.append((x + w / 2, w * h))
        # merge duplicates from the three detectors
        merged = []
        for cx, a in sorted(faces, key=lambda z: -z[1]):
            if all(abs(cx - m[0]) > 90 for m in merged):
                merged.append((cx, a))
        lit = g > 45                                    # lit subject on a dark set (profile = no Haar face)
        cols = lit.sum(axis=0).astype(np.float64)
        samples.append(dict(t=t0 + i * step, cut=cut, faces=merged, lit=float(lit.mean()),
                            litx=float((cols * np.arange(sw)).sum() / cols.sum()) if cols.sum() else sw / 2))
    # group into shots
    shots, cur = [], []
    for s in samples:
        if s["cut"] and cur:
            shots.append(cur); cur = []
        cur.append(s)
    if cur: shots.append(cur)
    out = []
    for k, sh_ in enumerate(shots):
        a = t0 if k == 0 else sh_[0]["t"] - step / 2
        b = t1 if k == len(shots) - 1 else shots[k + 1][0]["t"] - step / 2
        counts = [len(s["faces"]) for s in sh_]
        singles = [s["faces"][0][0] for s in sh_ if len(s["faces"]) == 1 or
                   (len(s["faces"]) > 1 and s["faces"][0][1] > 2.6 * s["faces"][1][1])]
        multi = sum(1 for c in counts if c >= 2 and True)
        # two people who both fit in the 1080 window (over-the-shoulder / two-shot): keep both in,
        # otherwise the frontal host's face wins and the guest talking at the edge gets cropped out.
        pairs = [(s["faces"][0][0] + s["faces"][1][0]) / 2 for s in sh_ if len(s["faces"]) >= 2 and
                 abs(s["faces"][0][0] - s["faces"][1][0]) / sw * 1920 < 820]
        fw_ = [math.sqrt(f[1]) for s in sh_ for f in s["faces"][:1]]
        wide = bool(fw_) and float(np.median(fw_)) < 0.075 * sw     # faces this small = a wide shot
        n_ = len(sh_)
        nofaces = sum(1 for s in sh_ if not s["faces"]) >= 0.6 * n_
        big = [s["faces"][0][0] for s in sh_ if s["faces"] and math.sqrt(s["faces"][0][1]) >= 0.075 * sw]
        if wide and sum(1 for s in sh_ if s["faces"]) >= 0.5 * n_:
            allx = [f[0] for s in sh_ for f in s["faces"]]
            out.append([a, b, "frame", (min(allx) + max(allx)) / 2 / sw * 1920])
        elif len(pairs) >= 0.3 * n_:
            out.append([a, b, "crop", float(np.median(pairs)) / sw * 1920])
        elif len(big) >= 0.3 * n_ or (big and nofaces):     # face seen part of the time = still a close-up
            out.append([a, b, "crop", float(np.median(big)) / sw * 1920])
        elif nofaces:                                        # dark profile close-up: crop on the lit mass
            out.append([a, b, "crop", float(np.median([s["litx"] for s in sh_])) / sw * 1920])
        else:   # wide / two-shot: remember where the people are so the framed zoom keeps them in
            allx = [f[0] for s in sh_ for f in s["faces"]]
            cx = (min(allx) + max(allx)) / 2 / sw * 1920 if allx else 960.0
            out.append([a, b, "frame", cx])
    # merge micro shots (<0.5s) into neighbours: detector flicker, not real cuts
    merged = []
    for s in out:
        if merged and (s[1] - s[0] < 0.5 or (merged[-1][2] == s[2] and abs(merged[-1][3] - s[3]) < 90)):
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    json.dump(merged, open(cp, "w"))
    return merged

# ---------------------------------------------------------------- render pieces
def bg_word_png(word, style, path):
    st = STYLES[style]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    size = 420
    f = ImageFont.truetype(os.path.join(FONTS, st["bg_word_file"]), size)
    while d.textlength(word, font=f) > W * 1.02 and size > 120:
        size -= 10; f = ImageFont.truetype(os.path.join(FONTS, st["bg_word_file"]), size)
    tw = d.textlength(word, font=f)
    bb = d.textbbox((0, 0), word, font=f)
    y = BOX_Y - bb[3] + int((bb[3] - bb[1]) * 0.30)   # sits on the box, tucked behind its top edge
    d.text(((W - tw) / 2, y), word, font=f, fill=(255, 255, 255, 40))
    img.save(path)

BOX_Y = 600     # top of the 1080x1080 picture box; headline band is y 290..590 above it

def render_piece(src, a, b, layout, cx, style, punch, out, bgword_png, frames, frame_mode="box"):
    st = STYLES[style]
    z = 1.14 if punch else 1.0
    grade = st["grade"]
    if frame_mode == "box":
        # Square box: single speaker -> 1:1 source crop at native 1080 (no upscale), following the face;
        # two-shot / wide -> whole 16:9 frame at 1080x608 inside the box. Canvas = blurred, dimmed copy.
        if layout == "crop":
            s = int(1080 / z) // 2 * 2
            x = int(min(max(cx - s / 2, 0), 1920 - s)); y = int((1080 - s) * 0.3)
            fg = f"[0:v]crop={s}:{s}:{x}:{y},scale=1080:1080:flags=lanczos[fg]"
            if frames >= 75 and not punch:      # slow 4% push-in so held shots never sit dead still
                fg = (f"[0:v]crop={s}:{s}:{x}:{y},scale=w='2*trunc(540*(1+0.04*n/{frames}))':h=-2:"
                      f"flags=bicubic:eval=frame,crop=1080:1080[fg]")
            fy = BOX_Y
        else:
            wz = 1.3 * z            # a 1.3x framed zoom reads as a shot, not a letterbox
            fw = int(W * wz) // 2 * 2; fh = int(fw * 9 / 16) // 2 * 2
            x = int(min(max(cx / 1920 * fw - W / 2, 0), fw - W))
            fg = f"[0:v]scale={fw}:{fh}:flags=lanczos,crop={W}:{fh}:{x}:0[fg]"
            fy = BOX_Y + (1080 - fh) // 2
        # Canvas: flat black, measured off the 225K-like Aujla clip-page reel (DNyGGvo2HFN). A blurred
        # copy of the shot dragged the source's own sponsor pop-ups into the background.
        fg2 = fg.replace("[fg]", f",{grade}[fgg]")
        bg = f"color=c=black:s={W}x{H}:r={FPS}[bgb]"
        bg += ";[bgb][1:v]overlay=0:0[bg]" if bgword_png else ";[bgb]null[bg]"
        fc = f"{fg2};{bg};[bg][fgg]overlay=0:{fy}:shortest=1,fps={FPS},format=yuv420p"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", src]
        if bgword_png: cmd += ["-loop", "1", "-i", bgword_png]
        cmd += ["-filter_complex", fc, "-frames:v", str(frames), "-an", "-c:v", "libx264", "-crf", "12",
                "-preset", "fast", out]
        run(cmd); return
    if layout == "crop":
        cw = int(608 / z) // 2 * 2; ch = int(1080 / z) // 2 * 2
        x = int(min(max(cx - cw / 2, 0), 1920 - cw)); y = (1080 - ch) // 2
        if punch: y = max(0, int((1080 - ch) * 0.35))    # zoom toward the eyes, not the chest
        vf = (f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6,{grade},"
              f"fps={FPS},format=yuv420p")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", src,
               "-vf", vf]
    else:
        fw = int(W * z) // 2 * 2; fh = int(fw * 9 / 16) // 2 * 2
        fg = f"[0:v]scale={fw}:{fh}:flags=lanczos,crop={W}:{min(fh, H)},unsharp=5:5:0.5[fg]"
        bg = (f"[0:v]scale=-2:{H},crop={W}:{H},boxblur=28:3,eq=brightness=-0.20:saturation=0.75[bgb]")
        if bgword_png:
            bg += f";[bgb][1:v]overlay=0:0[bg]"
        else:
            bg += ";[bgb]null[bg]"
        fc = f"{fg};{bg};[bg][fg]overlay=(W-w)/2:(H-h)/2,{grade},fps={FPS},format=yuv420p"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", src]
        if bgword_png: cmd += ["-loop", "1", "-i", bgword_png]
        cmd += ["-filter_complex", fc]
    cmd += ["-frames:v", str(frames), "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", out]
    run(cmd)

# ---------------------------------------------------------------- words
def whisper_words(src, a, b, cache_dir, lang="en", prompt=None):
    key = hashlib.md5(f"{src}{a:.2f}{b:.2f}{lang}".encode()).hexdigest()[:12]
    jp = os.path.join(cache_dir, f"w_{key}.json")
    if not os.path.exists(jp):
        wav = os.path.join(cache_dir, f"w_{key}.wav")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src, "-ac", "1",
             "-ar", "16000", wav])
        cmd = ["uvx", "--from", "mlx-whisper", "mlx_whisper", "--model", "mlx-community/whisper-large-v3-turbo",
               "--language", lang, "--word-timestamps", "True", "--condition-on-previous-text", "False",
               "--output-format", "json", "--output-dir", cache_dir, "--output-name", f"w_{key}", wav]
        if prompt: cmd += ["--initial-prompt", prompt]
        run(cmd)
        os.remove(wav)
    words = []
    for s in json.load(open(jp))["segments"]:
        for w in s.get("words", []):
            if w["start"] > b - a + 0.05: continue     # whisper hallucinates past the end
            words.append(dict(w=w["word"].strip(), s=a + w["start"], e=a + max(w["end"], w["start"] + 0.08)))
    return words

def to_edit_time(t, pieces):
    """Map a source time to edit time; None if the moment was cut."""
    for p in pieces:
        if p["a"] - 0.02 <= t <= p["b"] + 0.02:
            return p["off"] + min(max(t - p["a"], 0), p["b"] - p["a"])
    return None

# ---------------------------------------------------------------- captions (ASS)
EMPH = set()

def ass_color(hexrgb, alpha="00"):
    r, g, b = hexrgb[0:2], hexrgb[2:4], hexrgb[4:6]
    return f"&H{alpha}{b}{g}{r}&"

def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def build_ass(groups, style, margin_v, path, phrase_mode=False):
    st = STYLES[style]
    fill, act = ass_color(st["fill"]), ass_color(st["active"])
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['cap_font']},{st['cap_size']},{fill},{fill},{'&H66000000&' if st.get('box') else '&H00101010&'},&H96000000&,0,0,0,0,100,100,{2 if st['caps'] else 0},0,{3 if st.get('box') else 1},{st['outline']},{st['shadow']},2,{1080 - 918 + 20},{59 + 20},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for g in groups:
        g_end = g[-1]["e"]
        if phrase_mode:
            txt = g[0]['w'].upper() if st["caps"] else g[0]['w']
            ev.append(f"Dialogue: 0,{ts(g[0]['s'])},{ts(g_end)},Cap,,0,0,0,,{{\\fad(60,60)}}{txt}")
            continue
        for i, w in enumerate(g):
            a = w["s"]; b = g[i + 1]["s"] if i + 1 < len(g) else g_end
            if b - a < 0.01: continue
            parts = []
            for j, x in enumerate(g):
                emc = ass_color("FFD84D") if x["w"].strip(".,?!…\"'").lower() in EMPH else None
                if st["dim_alpha"]:                       # reveal: spoken words solid, upcoming dim
                    if j < i: parts.append(f"{{\\1c{emc or fill}\\alpha&H00&}}{x['w']}")
                    elif j == i: parts.append(f"{{\\1c{emc or act}\\alpha&H00&}}{x['w']}")
                    else: parts.append(f"{{\\1c{fill}\\alpha&H{st['dim_alpha']}&\\3a&HC0&\\4a&HFF&}}{x['w']}")
                else:                                     # pop: active word coloured and 108%
                    if j == i: parts.append(f"{{\\1c{emc or act}\\fscx108\\fscy108}}{x['w']}{{\\fscx100\\fscy100}}")
                    else: parts.append(f"{{\\1c{emc or fill}}}{x['w']}")
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{' '.join(parts)}")
    open(path, "w").write(hdr + "\n".join(ev) + "\n")

def group_words(words, st, breaks):
    groups, cur = [], []
    for w in words:
        cand = " ".join(x["w"] for x in cur + [w])
        gap = w["s"] - cur[-1]["e"] if cur else 0
        brk = bool(cur) and any(cur[-1]["s"] < x <= w["s"] + 0.01 for x in breaks)
        ends = bool(cur) and cur[-1]["w"][-1:] in ".?!"
        if cur and (len(cand) > st["max_chars"] or len(cur) >= st["max_words"] or gap > 0.45 or brk or ends):
            groups.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur: groups.append(cur)
    for i, g in enumerate(groups):       # hold each group until the next starts (no flicker), max +0.5s
        nxt = groups[i + 1][0]["s"] if i + 1 < len(groups) else g[-1]["e"] + 0.5
        g[-1]["e"] = min(max(g[-1]["e"], nxt - 0.001), g[-1]["e"] + 0.5) if nxt > g[-1]["e"] else g[-1]["e"]
    return groups

# ---------------------------------------------------------------- headline
def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines

EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"

def _is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or o in (0xFE0F, 0x200D)

def draw_rich(img, xy, text, font, size, fill):
    """Text with colour emoji (Apple Color Emoji only renders at 160px, so draw there and scale)."""
    d = ImageDraw.Draw(img); x, y = xy
    ef = ImageFont.truetype(EMOJI_FONT, 160)
    i = 0
    while i < len(text):
        ch = text[i]
        if _is_emoji(ch):
            j = i
            while j < len(text) and _is_emoji(text[j]): j += 1
            for e in [c for c in text[i:j] if ord(c) not in (0xFE0F, 0x200D)]:
                tile = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
                ImageDraw.Draw(tile).text((0, 0), e, font=ef, embedded_color=True)
                bb = tile.getbbox()
                if bb:
                    tile = tile.crop(bb); s = int(size * 1.05) / tile.height
                    tile = tile.resize((max(1, int(tile.width * s)), int(tile.height * s)), Image.LANCZOS)
                    img.alpha_composite(tile, (int(x), int(y + size * 0.08)))
                    x += tile.width + size * 0.12
            i = j
        else:
            j = i
            while j < len(text) and not _is_emoji(text[j]): j += 1
            d.text((x, y), text[i:j], font=font, fill=fill)
            x += d.textlength(text[i:j], font=font)
            i = j

def rich_width(d, text, font, size):
    plain = "".join(c for c in text if not _is_emoji(c))
    n = sum(1 for c in text if _is_emoji(c) and ord(c) not in (0xFE0F, 0x200D))
    return d.textlength(plain, font=font) + n * size * 1.2

def clip_caption_png(line1, line2, path, top=300):
    """Clip-page top text, measured on DNyGGvo2HFN: bold sans white, lowercase, emoji, ~800px wide
    first line at y~300, a smaller 'wait for...' second line. Returns the bottom y."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f1p = os.path.join(FONTS, "Inter-Bold.ttf"); f2p = os.path.join(FONTS, "Inter-SemiBold.ttf")
    size = 58
    while True:
        f1 = ImageFont.truetype(f1p, size)
        lines = []
        cur = ""
        toks = []
        for wd in line1.split():                       # never let an emoji wrap onto its own line
            if toks and all(_is_emoji(c) for c in wd): toks[-1] += " " + wd
            else: toks.append(wd)
        for word in toks:
            t = (cur + " " + word).strip()
            if rich_width(d, t, f1, size) <= TEXT_W: cur = t
            else: lines.append(cur); cur = word
        if cur: lines.append(cur)
        if len(lines) <= 2 or size <= 46: break
        size -= 2
    y = top
    for ln in lines:
        w = rich_width(d, ln, f1, size)
        draw_rich(img, ((W - w) / 2, y), ln, f1, size, (255, 255, 255, 255))
        y += int(size * 1.18)
    if line2:
        s2 = 38; f2 = ImageFont.truetype(f2p, s2)
        w = rich_width(d, line2, f2, s2)
        draw_rich(img, ((W - w) / 2, y + 4), line2, f2, s2, (255, 255, 255, 215))
        y += int(s2 * 1.3) + 4
    img.save(path)
    return y, img.getbbox()

def headline_png(text, style, path, top, credit=None, bottom=BOX_Y - 14):
    """Headline fitted into the band top..bottom (shrinks until it fits), bottom-aligned on the box."""
    st = STYLES[style]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    t = text.upper() if st["head_case"] == "upper" else text
    size = st["head_size"]
    credit_h = 46 if credit else 0
    while True:
        f = ImageFont.truetype(os.path.join(FONTS, st["head_file"]), size)
        lines = []
        for para in t.split("\n"): lines += wrap(d, para, f, TEXT_W)
        lh = int(size * (1.0 if st["head_case"] == "upper" else 1.04))
        if (len(lines) * lh + credit_h <= bottom - top) or size < 50: break
        size -= 3
    top = bottom - credit_h - len(lines) * lh       # bottom-align so the text hugs the picture
    hl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); hd = ImageDraw.Draw(hl_layer)
    y = top
    for ln in lines:
        tw = d.textlength(ln, font=f)
        x = (W - tw) / 2
        if style in ("funny", "bold"):
            hd.text((x, y), ln, font=f, fill=st["head_fill"] + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255))
        else:
            hd.text((x, y), ln, font=f, fill=st["head_fill"] + (255,))
        y += lh
    if style not in ("funny", "bold"):        # soft shadow for the thin serif
        sh = hl_layer.split()[3].filter(ImageFilter.GaussianBlur(10))
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.75)))
        img = Image.alpha_composite(img, shadow)
    img = Image.alpha_composite(img, hl_layer)
    if credit:
        cf = ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.ttf"), 28)
        d2 = ImageDraw.Draw(img)
        tw = d2.textlength(credit, font=cf)
        d2.text(((W - tw) / 2, y + 8), credit, font=cf, fill=(255, 255, 255, 175))
        y += credit_h
    img.save(path)
    bb = img.getbbox()
    return bb, y


# ---------------------------------------------------------------- cut QC (added after "you're cutting his speech")
def pcm(src, t0, t1, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t0, 0):.3f}", "-to", f"{t1:.3f}", "-i", src,
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

def rms_track(x, sr=16000, hop=0.02, win=0.06):
    h, w = int(sr * hop), int(sr * win)
    if len(x) < w: return np.zeros(1)
    return np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, len(x) - w, h)])

def _thr(src, a, b):
    return (np.percentile(rms_track(pcm(src, a, b)), 90) or 1e-3) * 0.10

def snap_range(src, a, b):
    """Move a cut to the nearest real pause so no word is clipped. End: first 80 ms quiet run in
    [b-0.06, b+0.7], else the quietest point there. Start: last quiet run in [a-0.35, a+0.06], else keep a.
    (Whisper can't judge this: it pins first words to 0 and stretches last words to the segment end.)"""
    thr = _thr(src, a, b)
    e = rms_track(pcm(src, b - 0.06, b + 0.7))
    near = e[:18]           # no pause found -> the dip between words within +0.3 s, never into the next word
    nb = b - 0.06 + int(np.argmin(near)) * 0.02 + 0.03 if len(near) else b
    for i in range(len(e) - 3):
        if (e[i:i + 4] < thr).all(): nb = b - 0.06 + i * 0.02 + 0.08; break
    na = a          # starts stay where authored (whisper word start - 0.08): snapping back pulls in the host
    return max(na, 0), nb

def edge_loud(src, a, b):
    """QC: is there speech energy right at either cut? Returns (start_loud, end_loud)."""
    thr = _thr(src, a, b) * 1.6
    s0 = rms_track(pcm(src, a, a + 0.08)); s1 = rms_track(pcm(src, b - 0.08, b))
    return (len(s0) and s0.min() > thr), (len(s1) and s1.min() > thr)

def onset_beats(path, seek, dur):
    x = pcm(path, seek, seek + dur, 22050)
    if len(x) < 22050: return np.array([])
    hop = 512; fr = np.array([np.sum(np.abs(np.fft.rfft(x[i:i + 2048] * np.hanning(2048))))
                              for i in range(0, len(x) - 2048, hop)])
    flux = np.maximum(np.diff(fr), 0); flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    t = np.arange(len(flux)) * hop / 22050
    peaks, last = [], -1
    for i in range(1, len(flux) - 1):
        if flux[i] > 1.0 and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1] and t[i] - last > 0.22:
            peaks.append(t[i]); last = t[i]
    return np.array(peaks)

def beat_offset(music, seek, cuts, total, lead):
    """Shift the music start (0..4 s) so its onsets land on our cuts (+-70 ms). Speech is never moved."""
    beats = onset_beats(music, seek, total + 6)
    if not len(beats) or not cuts: return 0.0, 0
    best = (0, 0.0)
    for d in np.arange(0, 4.0, 0.01):
        bt = beats - d
        hits = sum(1 for c in cuts if np.min(np.abs(bt - c)) < 0.07)
        if hits > best[0]: best = (hits, float(d))
    return best[1], best[0]


# ---------------------------------------------------------------- v3: loud music start, laughs, emoji bursts
def loud_seek(path, seek):
    """Skip a quiet intro: first point at/after `seek` where the 1 s level reaches 60% of the track's
    median level (Nature of Daylight / Cornfield Chase open near silence -> "no music at the start")."""
    x = pcm(path, seek, seek + 90, 8000)
    if len(x) < 16000: return seek
    e = np.array([np.sqrt(np.mean(x[i:i + 8000] ** 2)) for i in range(0, len(x) - 8000, 2000)])
    ok = np.where(e >= 0.6 * np.median(e))[0]
    return seek + (float(ok[0]) * 0.25 if len(ok) else 0.0)

def laugh_times(src, a, b, words):
    """Laughter = loud stretches (>= 0.4 s) with no whisper word on them. Returns source times."""
    x = pcm(src, a, b); e = rms_track(x)
    if len(e) < 10: return []
    thr = np.percentile(e, 90) * 0.22
    t = a + np.arange(len(e)) * 0.02
    talk = np.zeros(len(e), bool)
    for w in words: talk |= (t >= w["s"] - 0.12) & (t <= w["e"] + 0.12)
    free = (e > thr) & ~talk
    out, i = [], 0
    while i < len(free):
        if free[i]:
            j = i
            while j < len(free) and free[j]: j += 1
            if (j - i) * 0.02 >= 0.4: out.append(float(t[i]) + 0.1)
            i = j
        else: i += 1
    return out

def emoji_tile(e, size):
    ef = ImageFont.truetype(EMOJI_FONT, 160)
    tile = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((10, 10), e, font=ef, embedded_color=True)
    tile = tile.crop(tile.getbbox())
    return tile.resize((size, int(tile.height * size / tile.width)), Image.LANCZOS)

def emoji_layer(times, total, path, box_y, emojis="🤑💸💰💵🤑💸"):
    """Transparent 1080x1920 layer: at each time a burst of money emoji pops from the lower middle of the
    picture box, sprays up and out, falls with gravity, fades. One qtrle .mov, overlaid once."""
    import random
    rnd = random.Random(7)
    parts = []
    for t0 in times:
        for k in range(9):
            parts.append(dict(t0=t0 + rnd.uniform(0, 0.18), x=540 + rnd.uniform(-160, 160), y=box_y + 760,
                              vx=rnd.uniform(-520, 520), vy=rnd.uniform(-1500, -900), rot=rnd.uniform(-40, 40),
                              spin=rnd.uniform(-160, 160), size=rnd.choice([110, 130, 150, 170]),
                              e=emojis[k % len(emojis)], life=rnd.uniform(1.1, 1.5)))
    tiles = {}
    n = int(round(total * FPS))
    blank = bytes(W * H * 4)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "qtrle", path], stdin=subprocess.PIPE)
    for f in range(n):
        t = f / FPS
        act = [p for p in parts if p["t0"] <= t < p["t0"] + p["life"]]
        if not act: ff.stdin.write(blank); continue
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for p in act:
            u = t - p["t0"]
            sc = min(1.0, u / 0.12) * (1.15 if u < 0.2 else 1.0)          # pop in, slight overshoot
            al = 1.0 if u < p["life"] - 0.3 else max(0.0, (p["life"] - u) / 0.3)
            key = (p["e"], p["size"])
            if key not in tiles: tiles[key] = emoji_tile(p["e"], p["size"])
            tl = tiles[key]
            tl = tl.resize((max(2, int(tl.width * sc)), max(2, int(tl.height * sc))), Image.BILINEAR)
            tl = tl.rotate(p["rot"] + p["spin"] * u, expand=True, resample=Image.BILINEAR)
            if al < 1: tl.putalpha(tl.split()[3].point(lambda v: int(v * al)))
            x = p["x"] + p["vx"] * u; y = p["y"] + p["vy"] * u + 0.5 * 2600 * u * u
            x = min(max(x, 70 + tl.width / 2), 905 - tl.width / 2)       # stay inside the IG safe box
            if y < box_y - 20 or y > box_y + 1100: continue
            img.alpha_composite(tl, (int(x - tl.width / 2), int(y - tl.height / 2)))
        ff.stdin.write(img.tobytes())
    ff.stdin.close(); ff.wait()

# ---------------------------------------------------------------- main
def main():
    spec_path = sys.argv[1]
    spec = json.load(open(spec_path))
    base_dir = os.path.dirname(os.path.abspath(spec_path))
    work = os.path.join(base_dir, "work", spec["name"]); os.makedirs(work, exist_ok=True)
    cache = os.path.join(base_dir, "work", "_cache"); os.makedirs(cache, exist_ok=True)
    src = spec["src"]; style = spec.get("style", "emotional"); st = STYLES[style]
    EMPH.update(w.lower() for w in spec.get("emph", []))

    ranges = []
    if spec.get("hook"): ranges.append(dict(a=spec["hook"][0], b=spec["hook"][1], hook=True))
    for a, b in spec["clips"]: ranges.append(dict(a=a, b=b, hook=False))
    qc = []
    for r in ranges:                                   # cut at real pauses, then verify with whisper
        if spec.get("snap", True): r["a"], r["b"] = snap_range(src, r["a"], r["b"])
        if edge_loud(src, r["a"], r["b"])[1]:
            qc.append(f"end {r['b']:.2f}: no pause before the next word (check the last word)")
        if edge_loud(src, r["a"], r["b"])[0]:
            qc.append(f"start {r['a']:.2f}: speech right at the cut (check the first word)")
    lead = (spec.get("music") or {}).get("lead", 0.5) if spec.get("music") else 0
    if lead: ranges[0]["a"] -= lead                     # picture + music before the first word
    print("QC cuts:", "ok" if not qc else "; ".join(qc))
    json.dump(dict(ranges=ranges, qc=qc), open(os.path.join(work, "qc.json"), "w"), indent=1)

    # pieces: range -> shots -> punch splits, all frame-quantised in edit time
    pieces, off = [], 0.0
    punches = spec.get("punch", [])
    for r in ranges:
        dur = q(r["b"] - r["a"]); r["b"] = r["a"] + dur
        shots = analyse(src, r["a"], r["b"], cache)
        forced = spec.get("layout", "auto")
        bounds = sorted({r["a"], r["b"]} | {s[0] for s in shots} | {s[1] for s in shots} |
                        {x for p in punches for x in p if r["a"] < x < r["b"]})
        bounds = [r["a"] + q(x - r["a"]) for x in bounds]
        bounds = sorted(set(bounds))
        for a, b in zip(bounds, bounds[1:]):
            if b - a < 1 / FPS: continue
            mid = (a + b) / 2
            shot = next((s for s in shots if s[0] - 0.01 <= mid <= s[1] + 0.01), shots[-1])
            layout = shot[2] if forced == "auto" else forced
            cx = shot[3]
            if forced == "crop" and shot[2] != "crop":
                cx = spec.get("crop_cx", 960)
            punch = any(p[0] <= mid <= p[1] for p in punches)
            pieces.append(dict(a=a, b=b, off=off, layout=layout, cx=cx, punch=punch, hook=r["hook"]))
            off += b - a
    total = off
    print(f"{spec['name']}: {len(pieces)} pieces, {total:.2f}s, layouts "
          f"{[p['layout'][0] + ('*' if p['punch'] else '') for p in pieces]}")

    fmode = spec.get("frame_mode", "box")
    global BOX_Y
    head = os.path.join(work, "headline.png")
    if spec.get("top"):          # clip-page top text decides where the picture box starts
        tb, bb = clip_caption_png(spec["top"][0], spec["top"][1] if len(spec["top"]) > 1 else "", head,
                                  spec.get("head_top", 300))
        BOX_Y = int(min(max(430, tb + 28), 560))
    bgw = None
    if spec.get("bg_word"):
        bgw = os.path.join(work, "bgword.png"); bg_word_png(spec["bg_word"], style, bgw)

    # 1. video pieces (REUSE_PICTURE=1 keeps the rendered picture when only the audio mix changed)
    reuse = bool(os.environ.get("REUSE_PICTURE")) and os.path.exists(os.path.join(work, "picture.mp4"))
    lst = []
    for i, p in enumerate(pieces):
        out = os.path.join(work, f"p{i:03d}.mp4")
        frames = round((p["b"] - p["a"]) * FPS)
        if reuse: break
        render_piece(src, p["a"], p["b"], p["layout"], p["cx"], style, p["punch"], out, bgw, frames, fmode)
        lst.append(f"file '{out}'")
    open(os.path.join(work, "list.txt"), "w").write("\n".join(lst) + "\n")
    base = os.path.join(work, "base.mp4")
    if not reuse: run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "list.txt"),
         "-c", "copy", base])

    # 2. voice: per range, 10ms fades at every join so cuts don't click
    vparts = []
    for i, r in enumerate(ranges):
        o = os.path.join(work, f"v{i:02d}.wav")
        d = r["b"] - r["a"]
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{r['a']:.3f}", "-t", f"{d:.3f}", "-i", src, "-ac", "2",
             "-ar", "48000", "-af", f"afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.3f}:d=0.015", o])
        vparts.append(o)
    voice = os.path.join(work, "voice.wav")
    run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", v] for v in vparts], []) +
        ["-filter_complex", "".join(f"[{i}:a]" for i in range(len(vparts))) + f"concat=n={len(vparts)}:v=0:a=1,"
         "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,loudnorm=I=-16:TP=-2:LRA=9"
         + (f",volume=enable='lt(t,{lead:.3f})':volume=0" if lead else ""),
         "-ar", "48000", voice])

    # 3. captions: below the framed shot, or lower third on the crop (bottom edge of text ~y1460)
    all_frame = all(p["layout"] == "frame" for p in pieces)
    capmv = spec.get("cap_margin_v") or (H - min(BOX_Y + 930, 1500) if fmode == "box" else (H - 1430 if all_frame else H - 1470))
    breaks = [p["off"] for p in pieces[1:]]
    ass = os.path.join(work, "caps.ass")
    if spec.get("lines"):                              # hand-written (translated) phrase subtitles
        groups = []
        for ln in spec["lines"]:     # [t0, t1, text, (true = belongs to the flash-forward hook)]
            t0, t1, txt = ln[:3]
            pool = [p for p in pieces if p["hook"] == (len(ln) > 3 and bool(ln[3]))]
            a = to_edit_time(t0, pool); b = to_edit_time(t1, pool)
            if a is None or b is None or b <= a: continue
            groups.append([dict(w=txt, s=a, e=b)])
        build_ass(groups, style, capmv, ass, phrase_mode=True)
    else:
        words = []
        fixes = spec.get("fix", {})
        for r in ranges:
            for w in whisper_words(src, r["a"], r["b"], cache, spec.get("lang", "en"), spec.get("prompt")):
                t = to_edit_time(w["s"], [p for p in pieces if p["hook"] == r["hook"]])
                e = to_edit_time(w["e"], [p for p in pieces if p["hook"] == r["hook"]])
                if t is None: continue
                txt = w["w"]
                for k, v in fixes.items():
                    if txt.strip(".,?!").lower() == k.lower(): txt = txt.lower().replace(k.lower(), v)
                if not txt: continue
                if words and txt[:1] in ("-", "%", "'") and t - words[-1]["e"] < 0.5:   # "non -obvious", "5 %"
                    words[-1]["w"] += txt.upper() if st["caps"] else txt; words[-1]["e"] = e if e else t + 0.2
                    continue
                words.append(dict(w=txt.upper() if st["caps"] else txt, s=t, e=e if e else t + 0.2))
        words.sort(key=lambda w: w["s"])
        json.dump(words, open(os.path.join(work, "words.json"), "w"), indent=0, ensure_ascii=False)
        build_ass(group_words(words, st, breaks), style, capmv, ass)

    # 4. headline
    head_top = spec.get("head_top", 290)
    if not spec.get("top"):
        bb, head_bottom = headline_png(spec["headline"], style, head, head_top, spec.get("credit"))
    hold = spec.get("headline_hold", 0)                 # 0 = whole reel
    flash = ""
    hook_end = next((p["off"] for p in pieces if not p["hook"]), 0) if spec.get("hook") else 0
    if hook_end:     # 3-frame white dip at the flash-forward -> story seam
        flash = f",drawbox=x=0:y=0:w=iw:h=ih:color=white@0.85:t=fill:enable='between(t,{hook_end - 0.05:.3f},{hook_end + 0.05:.3f})'"
    head_enable = f":enable='lte(t,{hold})'" if hold else ""
    fade = f",fade=t=out:st={hold - 0.35:.2f}:d=0.35:alpha=1" if hold else ""
    shade = ""
    if not all_frame and fmode != "box":   # a soft dark gradient behind the headline so it reads over a bright shirt
        shade = "[0:v]drawbox=x=0:y=0:w=iw:h=%d:color=black@0.28:t=fill[v0];" % min(head_bottom + 60, 760)
    else:
        shade = "[0:v]null[v0];"
    # laugh-triggered emoji bursts: spec "bursts": "auto" (loud stretches with no words) or [source times]
    bspec = spec.get("bursts") or []
    if isinstance(bspec, str): bspec = [bspec]
    burst_src = [x for x in bspec if not isinstance(x, str)]      # explicit source times (e.g. YouTube [laughter] cues)
    if "auto" in bspec:
        for r in ranges:
            ws = whisper_words(src, r["a"], r["b"], cache, spec.get("qc_lang", spec.get("lang", "en")))
            burst_src += laugh_times(src, r["a"], r["b"], ws)
    bt = sorted(x for x in (to_edit_time(t, [p for p in pieces if not p["hook"]]) for t in burst_src) if x is not None)
    bt = [t for i, t in enumerate(bt) if i == 0 or t - bt[i - 1] > 1.2]
    extra_in, bfc, vlast = [], "", "[vb]"
    if bt and not reuse:
        blayer = os.path.join(work, "bursts.mov")
        emoji_layer(bt, total, blayer, BOX_Y, spec.get("burst_emoji", "🤑💸💰💵🤑💸"))
        extra_in = ["-i", blayer]; bfc = "[vs][2:v]overlay=0:0:eof_action=pass[vb];"
        print(f"bursts at {[round(t, 1) for t in bt]}")
    else:
        bfc = "[vs]null[vb];"
    bar_y = BOX_Y + 1080 - 6       # thin progress bar on the bottom edge of the picture
    fc = (f"{shade}[1:v]format=rgba{fade}[hl];[v0][hl]overlay=0:0{head_enable}{flash},"
          f"subtitles='{ass}':fontsdir='{FONTS}'[vs];{bfc}"
          f"color=c=white@0.85:s={W}x6:r={FPS},format=rgba[bar];"
          f"{vlast}[bar]overlay=x='-W+W*t/{total:.3f}':y={bar_y}:shortest=1[v]")
    picture = os.path.join(work, "picture.mp4")
    if not reuse: run(["ffmpeg", "-v", "error", "-y", "-i", base, "-loop", "1", "-t", f"{total:.3f}", "-i", head] + extra_in +
        ["-filter_complex", fc, "-map", "[v]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "12",
         "-preset", "fast", "-pix_fmt", "yuv420p", picture])

    # 5. music bed + mix
    m = spec.get("music")
    mix = os.path.join(work, "mix.wav")
    if m:
        mv = m.get("vol", st["music_vol"] * 1.25)
        fo = max(total - 1.6, 0)
        seek = loud_seek(m["file"], m.get("seek", 0))
        if m.get("beat_align", True):
            cuts = sorted({round(p["off"], 3) for i, p in enumerate(pieces[1:], 1)
                           if p["a"] != pieces[i - 1]["b"] or p["punch"] != pieces[i - 1]["punch"]})
            d, hits = beat_offset(m["file"], seek, cuts, total, lead)
            seek += d
            print(f"music: seek {seek:.2f}s, {hits}/{len(cuts)} cuts on an onset")
        # bed first, then measure its lead-in and lift it to a fixed -18 dB so the opening is never "empty"
        bed = os.path.join(work, "bed.wav")
        ld = max(lead, 0.5)
        for attempt in range(10):      # a faded-in intro can still be near silent: step 2 s in until it is not
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{seek:.3f}", "-t", f"{total + 0.5:.3f}", "-i", m["file"],
                 "-af", f"aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-3,volume={mv}", bed])
            r = subprocess.run(["ffmpeg", "-nostdin", "-t", f"{ld:.2f}", "-i", bed, "-af", "volumedetect", "-f", "null", "-"],
                               capture_output=True, text=True).stderr
            lvl = float(r.split("mean_volume:")[1].split(" dB")[0]) if "mean_volume:" in r else -90
            if lvl > -40: break
            seek += 2.0
        g = min(max(10 ** ((-18 - lvl) / 20), 1.0), 14.0)
        print(f"music lead-in {lvl} dB -> gain x{g:.1f}")
        run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-i", bed, "-filter_complex",
             f"[1:a]atrim=0:{total:.3f},"
             f"volume='if(lt(t,{ld:.2f}),{g:.2f},if(lt(t,{ld + 1.0:.2f}),{g:.2f}-({g:.2f}-1)*(t-{ld:.2f})/1.0,1))':eval=frame,"
             f"afade=t=in:d=0.03,afade=t=out:st={fo:.2f}:d=1.6[m];"
             f"[0:a]asplit=2[vk][vo];"
             f"[m][vk]sidechaincompress=threshold=0.06:ratio={min(st['duck_ratio'], 3)}:attack=30:release=400:makeup=1[md];"
             f"[vo][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]",
             "-map", "[a]", "-ar", "48000", mix])
    else:
        shutil.copy(voice, mix)

    out = spec["out"]; os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out) and not (spec.get("overwrite") or os.environ.get("OVERWRITE")):
        sys.exit(f"refusing to overwrite delivered file {out} (bump the version)")
    run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", mix, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out])
    r = subprocess.run(["ffmpeg", "-nostdin", "-t", "0.5", "-i", out, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    lvl = float(r.split("mean_volume:")[1].split(" dB")[0]) if "mean_volume:" in r else -99
    flags = []
    if m and lvl < -26: flags.append(f"OPENING MUSIC TOO QUIET ({lvl} dB)")
    if total > spec.get("max_len", 50): flags.append(f"TOO LONG ({total:.1f}s > {spec.get('max_len', 50)})")
    print(f"wrote {out} ({total:.2f}s); opening {lvl} dB; headline bbox {bb}; " + ("QC " + "; ".join(flags) if flags else "QC ok"))

if __name__ == "__main__":
    main()
