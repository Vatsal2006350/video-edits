#!/usr/bin/env python3
"""clip-edit — re-edit a podcast/interview clip into a "layercut" reel from its spec. No code per clip.

    .agents/skills/video-effects/.venv/bin/python bin/clip-edit.py videos/faceless-podcast/specs/02_altman_20yrs.json
    ... --stills 2,9,14,21     # only render these edit-time seconds to PNG (look before you render)
    bin/clip-edit.sh <spec.json> [...]                              # same, picks the right Python

The look (measured from lapoz.app's Layercut before/after and the Opus-motion references):
  - the speaker fills a 9:16 frame (full-height crop that follows the person), background darkened;
  - one huge condensed word per sentence sits BEHIND the head (person cut out with RobustVideoMatting);
  - small caps captions at chest height; the emphasised word drops to its own line in serif italic;
  - concept cards from a fixed library draw the idea being said, timed to the word that says it:
      slider · compare · list · stat · curve · loop · venn · chips · quote
  - music bed from the spec, side-chain ducked under the voice.

Token saving: everything that is the same on every clip is here. Per clip the agent writes only an
"edit" block in the existing spec (or nothing: words behind the head and emphasis are chosen
automatically from the spec's "emph" list and the transcript). Cuts come from the spec's qc.json
(already snapped so nobody is cut mid-word), word timings from the cached words.json, and the base
cut, the matte and the person track are cached in specs/work/<name>/ so a re-edit only re-composites.

"edit" block (all optional):
  {"look": "layercut", "accent": "#FFD43B",
   "behind": "auto" | [["COMPOUNDING", "on:compounding"], ["20 YEARS", 9.2]],
   "italic": ["underestimated"],                      # extra emphasis words (spec "emph" is used too)
   "cards": [
     {"type": "slider", "on": "underestimated", "dur": 2.6, "a": "Overrated", "b": "Underestimated", "value": 0.92},
     {"type": "compare", "on": "joke", "dur": 4, "a": "20 years of experience", "b": "1 year, 20 times", "winner": "a"},
     {"type": "curve", "on": "compounding", "nth": 2, "dur": 3.5, "shape": "exponential", "x": "TIME", "y": "SKILL", "falloff": true},
     {"type": "chips", "on": "uncomfortable", "dur": 3, "words": ["uncomfortable", "non-obvious", "new"]},
     {"type": "list", "on": "...", "items": ["...", "..."]},  {"type": "stat", "on": "...", "value": "13", "label": "SECONDS"},
     {"type": "loop", "nodes": ["try", "fail", "learn"]},     {"type": "venn", "a": "...", "b": "...", "mid": "..."},
     {"type": "quote", "text": "..."}]}
Card "on" = the first spoken word that starts with it ("nth" for a later one); or "at": edit seconds.
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONTS = os.path.join(ROOT, 'fonts')
W, H, FPS = 1080, 1920, 30
PLATE_H = 1700                        # the speaker crop is scaled to this height, bottom-aligned (1080p sources)
SAFE = (59, 278, 918, 1536)           # Instagram safe box
STOP = set("""a an the and or but so to of in on at for with from by as is are was were be been being it its this that these
those i you he she we they me him her us them my your our their do does did doing have has had not no yes just like
really very then than there here what when where who why how which would could should will can about into out up
down over under again also only own same too because if while all any some such more most other each few both
know think mean thing things kind sort get got gonna going yeah okay ok well right lot lots one themselves yourself myself
ourselves everyone everybody something anything nothing actually probably basically successive continued people said says""".split())


def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def run(cmd):
    subprocess.run(cmd, check=True)


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def spring(dt, w=18.0):
    return 0.0 if dt <= 0 else 1 - (1 + w * dt) * math.exp(-w * dt)


def ease_out(x):
    x = min(1, max(0, x)); return 1 - (1 - x) ** 3


# ------------------------------------------------------------------ inputs and caches
def load(spec_path):
    """Reuse what the clip already has: qc.json (cuts snapped off words) and words.json (edit-time words).
    A brand-new clip gets its cuts from spec["clips"] and its words from whisper, both cached."""
    spec = json.load(open(spec_path))
    work = os.path.join(os.path.dirname(os.path.abspath(spec_path)), 'work', spec['name']); os.makedirs(work, exist_ok=True)
    qcp, wp = os.path.join(work, 'qc.json'), os.path.join(work, 'words.json')
    ranges = [(r['a'], r['b']) for r in json.load(open(qcp))['ranges']] if os.path.exists(qcp) else [tuple(c) for c in spec['clips']]
    words = json.load(open(wp)) if os.path.exists(wp) else None
    return spec, work, ranges, words


def transcribe(base, work, spec):
    """Word timings for the edit (edit time), cached as words.json. Same model and settings as podcast-clip.py."""
    wp = os.path.join(work, 'words.json')
    wav = os.path.join(work, '_lc_voice.wav')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', base, '-ac', '1', '-ar', '16000', wav])
    cmd = ['uvx', '--from', 'mlx-whisper', 'mlx_whisper', '--model', 'mlx-community/whisper-large-v3-turbo',
           '--language', spec.get('lang', 'en'), '--word-timestamps', 'True', '--condition-on-previous-text', 'False',
           '--output-format', 'json', '--output-dir', work, '--output-name', '_lc_whisper', wav]
    if spec.get('prompt'): cmd += ['--initial-prompt', spec['prompt']]
    run(cmd); os.remove(wav)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', base], capture_output=True, text=True).stdout)
    words = []
    for s in json.load(open(os.path.join(work, '_lc_whisper.json')))['segments']:
        for w in s.get('words', []):
            if w['start'] > dur + 0.05: continue  # whisper hallucinates past the end
            txt = w['word'].strip()
            for bad, good in (spec.get('fix') or {}).items(): txt = re.sub(bad, good, txt, flags=re.I)
            words.append({'w': txt.upper(), 's': w['start'], 'e': max(w['end'], w['start'] + 0.08)})
    json.dump(words, open(wp, 'w'), indent=0)
    return words


def src_info(src):
    """Display size after rotation, and whether the pixels are HDR (iPhone HLG / PQ)."""
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height,color_transfer:stream_side_data=rotation', '-of', 'json', src],
                                  capture_output=True, text=True).stdout)['streams'][0]
    w, h = j['width'], j['height']
    rot = next((abs(int(sd.get('rotation', 0))) for sd in j.get('side_data_list', []) if 'rotation' in sd), 0)
    if rot in (90, 270): w, h = h, w
    return w, h, j.get('color_transfer') in ('arib-std-b67', 'smpte2084')


def dims(path):
    w, h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                           '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')[:2]
    return int(w), int(h)


TONEMAP = 'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,'


def base_cut(spec, work, ranges):
    """The edit's picture and voice, in edit time, cached by the ranges. Keeps the source's shape
    (16:9 -> 1920x1080, vertical -> 1080x1920) and tonemaps HLG/PQ to Rec.709 first."""
    key = hashlib.md5(json.dumps([spec['src'], ranges]).encode()).hexdigest()[:10]
    out = os.path.join(work, f'layercut_base_{key}.mp4')
    if os.path.exists(out):
        return out
    sw, sh, hdr = src_info(spec['src'])
    size = '1080:1920' if sh > sw else '1920:1080'
    parts = []
    for i, (a, b) in enumerate(ranges):
        p = os.path.join(work, f'_lc_part{i}.mp4')
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-i', spec['src'], '-t', f'{b - a:.3f}',
             '-vf', (TONEMAP if hdr else '') + f'fps=30,scale={size}:flags=lanczos,format=yuv420p', '-af', 'aresample=48000',
             '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-c:a', 'pcm_s16le', p.replace('.mp4', '.mov')])
        parts.append(p.replace('.mp4', '.mov'))
    lst = os.path.join(work, '_lc_parts.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'libx264', '-crf', '12',
         '-preset', 'fast', '-c:a', 'pcm_s16le', out.replace('.mp4', '.mov')])
    os.replace(out.replace('.mp4', '.mov'), out)
    for p in parts:
        os.remove(p)
    os.remove(lst)
    return out


def frames(path, w, h, pix='rgb24'):
    ch = 3 if pix == 'rgb24' else 1
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', pix, '-'],
                         stdout=subprocess.PIPE, bufsize=w * h * ch * 4)
    while True:
        b = p.stdout.read(w * h * ch)
        if len(b) < w * h * ch:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, ch) if ch == 3 else np.frombuffer(b, np.uint8).reshape(h, w)


def matte(base, work):
    """RobustVideoMatting over the whole cut -> an alpha video (cached). Tracking is separate (track())."""
    am = base.replace('.mp4', '_alpha.mkv')
    if os.path.exists(am):
        return am
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    m = torch.hub.load('PeterL1n/RobustVideoMatting', 'resnet50', trust_repo=True).eval().to(dev)
    tmp = am + '.part.mkv'; BW, BH = dims(base)
    wr = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{BW}x{BH}',
                           '-framerate', '30', '-i', '-', '-c:v', 'ffv1', tmp], stdin=subprocess.PIPE)
    rec = [None] * 4; prev_small = None
    with torch.no_grad():
        for f in frames(base, BW, BH):
            small = f[::8, ::8].mean(axis=2)
            if prev_small is not None and np.abs(small - prev_small).mean() > 14: rec = [None] * 4  # a shot change
            prev_small = small
            src = torch.from_numpy(f.copy()).to(dev).permute(2, 0, 1)[None].float() / 255
            _, pha, *rec = m(src, *rec, downsample_ratio=0.25)
            wr.stdin.write((pha[0, 0].clamp(0, 1) * 255).byte().cpu().numpy().tobytes())
    wr.stdin.close(); wr.wait(); os.replace(tmp, am)
    return am


def skin_ratio(rgb):
    """Share of skin-coloured pixels (YCrCb box) in a patch: a face turned to camera scores high, hair or a back low."""
    if rgb.size == 0: return 0.0
    r, g, b = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
    cr = 0.5 * r - 0.4187 * g - 0.0813 * b + 128; cb = -0.1687 * r - 0.3313 * g + 0.5 * b + 128
    return float(((cr > 135) & (cr < 180) & (cb > 85) & (cb < 135)).mean())


def track(base, am):
    """Per frame: which person to frame and where their head is (cached next to the matte).
    Among the people the matte finds, pick the one whose head shows the most face, weighted by size, so an
    over-the-shoulder shot frames the speaker, not the back of the nearer head."""
    tr = am.replace('_alpha.mkv', '_track3.json')
    if os.path.exists(tr): return json.load(open(tr))
    out = []; prev_small = None
    BW, BH = dims(base)
    for f, a in zip(frames(base, BW, BH), frames(am, BW, BH, 'gray')):
        small = f[::8, ::8].mean(axis=2); cut = bool(prev_small is not None and np.abs(small - prev_small).mean() > 14); prev_small = small
        col = (a > 128).sum(axis=0).astype(np.float32)
        if col.sum() < 2000: out.append({'cx': None, 'top': None, 'cut': cut}); continue
        k = np.convolve(col, np.ones(41) / 41, mode='same'); on = k > k.max() * 0.2
        segs = []; s = None
        for x, v in enumerate(on):
            if v and s is None: s = x
            if (not v or x == len(on) - 1) and s is not None: segs.append((s, x)); s = None
        best = None
        for s0, s1 in segs:
            mass = col[s0:s1 + 1].sum()
            if mass < 3000: continue
            rows = np.where((a[:, s0:s1 + 1] > 128).sum(axis=1) > 6)[0]
            if not len(rows): continue
            top = int(rows[0]); band = a[top:top + 240, s0:s1 + 1] > 128
            hc = band.sum(axis=0); xs = np.arange(s0, s1 + 1)
            cx = float((hc * xs).sum() / hc.sum()) if hc.sum() else float((s0 + s1) / 2)
            patch = f[top:top + 240, s0:s1 + 1][band] if band.any() else np.zeros((0, 3), np.uint8)
            bottom = int(rows[-1]) / a.shape[0]  # people on a projector screen end mid-frame; the speaker stands on the floor
            score = mass * (0.25 + skin_ratio(patch)) * (0.3 + 0.7 * bottom)
            if best is None or score > best[0]: best = (score, cx, top)
        out.append({'cx': best[1] if best else None, 'top': best[2] if best else None, 'cut': cut})
    json.dump(out, open(tr, 'w'))
    return out


def smooth_track(track):
    """Per shot: hold a steady frame, follow only when the head drifts out of the middle third."""
    n = len(track); cx = np.zeros(n); top = np.zeros(n)
    last_cx, last_top = 960.0, 300.0
    for i, t in enumerate(track):
        last_cx = t['cx'] if t['cx'] is not None else last_cx
        last_top = t['top'] if t['top'] is not None else last_top
        cx[i] = last_cx; top[i] = last_top
    out_cx = np.zeros(n); out_top = np.zeros(n); cur = cx[0]; curt = top[0]
    for i in range(n):
        if track[i]['cut'] or i == 0:
            j = i; seg = []
            while j < n and (j == i or not track[j]['cut']): seg.append(cx[j]); j += 1
            cur = float(np.median(seg)); curt = top[i]
        if abs(cx[i] - cur) > 300: cur = cx[i]  # a missed cut or a big move: jump, never half a person
        elif abs(cx[i] - cur) > 90: cur += (cx[i] - cur) * 0.22  # a walking speaker: follow quickly enough to stay whole
        curt += (top[i] - curt) * 0.15
        out_cx[i] = cur; out_top[i] = curt
    return out_cx, out_top


# ------------------------------------------------------------------ words, sentences, emphasis
def clean(w):
    return re.sub(r"[^\w'%-]", '', w).lower()


def sentences(words):
    out = []; cur = []
    for i, w in enumerate(words):
        cur.append(i)
        gap = words[i + 1]['s'] - w['e'] if i + 1 < len(words) else 9
        if re.search(r'[.?!]$', w['w']) or gap > 0.55 or len(cur) >= 14:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def words_from_lines(spec, ranges):
    """Hindi/Punjabi clips carry hand-written English lines (source time) instead of whisper words.
    Map each line into edit time and spread its words over it by length, so behind-words, cards ("on")
    and captions all work in English. A line keeps its words together as one caption group."""
    offs = []; acc = 0.0
    for a, b in ranges: offs.append((a, b, acc)); acc += b - a
    mapped = []
    for s, e, text, *rest in spec['lines']:
        hit = next(((a, b, o) for a, b, o in offs if a - 0.3 <= s < b), None)
        if not hit: continue
        a, b, o = hit
        if min(b, e) - max(a, s) < 0.6 * (e - s): continue  # the cut keeps too little of this line to read it
        mapped.append((o + max(0, s - a), o + min(b, e) - a, text))
    mapped.sort()  # story (edit) order, not source order
    clean_lines = []
    for s2, e2, text in mapped:  # the same line written twice: keep the first, and never overlap the previous line
        if clean_lines and text == clean_lines[-1][2]: continue
        if clean_lines and s2 < clean_lines[-1][1]: s2 = clean_lines[-1][1]
        if e2 - s2 > 0.3: clean_lines.append((s2, e2, text))
    words = []; gid = 0
    for s2, e2, text in clean_lines:
        toks = text.replace('"', '').split(); n = sum(len(x) + 1 for x in toks); pos = 0
        chunk = 0
        for k, w_ in enumerate(toks):
            ws = s2 + (e2 - s2) * pos / n; pos += len(w_) + 1; we = s2 + (e2 - s2) * pos / n
            if k and k % 6 == 0: chunk += 1
            words.append({'w': w_, 's': ws, 'e': we, 'g': f'{gid}.{chunk}'})
        gid += 1
    return words


def caption_groups(words):
    if words and 'g' in words[0]:  # lines mode: one group per line chunk
        out = []; last = None
        for i, w in enumerate(words):
            if w['g'] != last: out.append([]); last = w['g']
            out[-1].append(i)
        return out
    out = []; cur = []
    for i, w in enumerate(words):
        cur.append(i)
        gap = words[i + 1]['s'] - w['e'] if i + 1 < len(words) else 9
        dur = words[cur[-1]]['e'] - words[cur[0]]['s']
        if re.search(r'[.?!,]$', w['w']) or gap > 0.35 or len(cur) >= 5 or dur > 1.8:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def find_word(words, prefix, nth=1):
    k = 0
    for i, w in enumerate(words):
        if clean(w['w']).startswith(prefix.lower()):
            k += 1
            if k == nth:
                return i
    return None


def plan_behind(words, spec, edit):
    emph = [e.lower() for e in spec.get('emph', []) + edit.get('italic', [])]
    plan = []
    given = edit.get('behind', 'auto')
    if given != 'auto':
        for txt, when in given:
            if isinstance(when, str) and when.startswith('on:'):
                key, _, nth = when[3:].partition('#'); i = find_word(words, key, int(nth or 1))  # on:word#2 = the 2nd time it is said
                if i is None: print(f"behind '{txt}': '{when[3:]}' is not in the transcript, skipped"); continue
                t = words[i]['s']
            else:
                t = float(when)
            plan.append({'t': t, 'text': txt.upper()})
        plan.sort(key=lambda p: p['t'])
    else:
        for sent in sentences(words):
            cands = [i for i in sent if clean(words[i]['w']) not in STOP and len(clean(words[i]['w'])) >= 4]
            if not cands: continue
            pri = [i for i in cands if any(clean(words[i]['w']).startswith(e) for e in emph)]
            i = pri[0] if pri else max(cands, key=lambda j: (len(clean(words[j]['w'])), words[j]['e'] - words[j]['s']))
            plan.append({'t': words[sent[0]]['s'], 'text': clean(words[i]['w']).upper().replace("'", "’")})
    # each word holds until the next one, min 1.2 s; drop repeats back to back
    out = []
    for p in plan:
        if out and out[-1]['text'] == p['text']: continue
        if out and p['t'] - out[-1]['t'] < 1.2: continue
        out.append(p)
    if out: out[0]['t'] = 0.0  # the hook frame always carries a word
    for k, p in enumerate(out):
        p['end'] = out[k + 1]['t'] if k + 1 < len(out) else words[-1]['e'] + 0.5
    return out


# ------------------------------------------------------------------ drawing
class Ink:
    def __init__(self, accent):
        self.accent = hexrgb(accent); self.white = (245, 243, 238); self.dim = (150, 150, 150)
        self.big = F('Anton-Regular.ttf', 400); self.cap = F('Inter-Bold.ttf', 46); self.ital = F('InstrumentSerif-Italic.ttf', 112)
        self.small = F('Inter-Bold.ttf', 30); self.label = F('Inter-Bold.ttf', 26); self.body = F('Inter-Bold.ttf', 40)
        self.serif = F('InstrumentSerif-Regular.ttf', 58); self.num = F('Anton-Regular.ttf', 210)
        self.serif_i = F('InstrumentSerif-Italic.ttf', 58); self.capital = F('InstrumentSerif-Italic.ttf', 74)
        self.numsm = F('Anton-Regular.ttf', 64); self.quote = F('InstrumentSerif-Regular.ttf', 200); self.label = F('Inter-Bold.ttf', 22)
        self._big_cache = {}


def big_word_img(ink, text, outline):
    key = (text, outline)
    if key in ink._big_cache: return ink._big_cache[key]
    f = ink.big; tw = f.getlength(text); size = 400
    if tw > 1010: size = int(400 * 1010 / tw); f = F('Anton-Regular.ttf', size)  # long words fit the frame; short ones stay huge
    tw = f.getlength(text); asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(tw) + 40, asc + desc + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if outline:
        d.text((20, 10), text, font=f, fill=(0, 0, 0, 0), stroke_width=4, stroke_fill=(245, 243, 238, 235))
    else:
        d.text((20, 10), text, font=f, fill=(245, 243, 238, 255))
        g = np.linspace(1.0, 0.55, im.height)[:, None]  # light from above, falls off toward the head
        a = np.array(im); a[..., 3] = (a[..., 3] * g).astype(np.uint8); im = Image.fromarray(a)
    ink._big_cache[key] = (im, size)
    return im, size


def draw_behind(canvas, ink, plan, t, head_y, frame_i):
    # the hook frame shows its word whole (k = 1 when the word starts at 0)
    cur = [p for p in plan if p['t'] - 0.05 <= t < p['end']]
    if not cur: return
    p = cur[-1]; k = 1.0 if p['t'] <= 0 else spring(t - (p['t'] - 0.05), 16); out = 1 - ease_out((t - (p['end'] - 0.18)) / 0.18) if t > p['end'] - 0.18 else 1
    idx = plan.index(p)
    im, size = big_word_img(ink, p['text'], outline=(idx % 3 == 2))
    sc = 1.12 - 0.12 * k
    w, h = int(im.width * sc), int(im.height * sc)
    im2 = im.resize((w, h), Image.LANCZOS)
    if k < 1:
        a = np.array(im2); a[..., 3] = (a[..., 3] * min(1, k * 1.4) * out).astype(np.uint8); im2 = Image.fromarray(a)
    elif out < 1:
        a = np.array(im2); a[..., 3] = (a[..., 3] * out).astype(np.uint8); im2 = Image.fromarray(a)
    y = int(head_y - h * 0.42)  # the head overlaps the lower half of the word
    canvas.alpha_composite(im2, (W // 2 - w // 2, max(140, y)))
    # a thin ring behind the head, turning slowly (it reads as depth, not decoration)
    d = ImageDraw.Draw(canvas); r = 410; cy = head_y + 120; ang = (frame_i / FPS) * 18
    for j in range(36):
        a0 = ang + j * 10
        if j % 3 == 0: continue
        d.arc([W // 2 - r, cy - r, W // 2 + r, cy + r], a0, a0 + 6, fill=(245, 243, 238, 60), width=3)


def text_w(f, s):
    return f.getlength(s)


def tracked(d, xy, s, f, fill, track=0.14):
    """Small caps label with letter tracking (PIL has none)."""
    x, y = xy; sp = f.size * track
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + sp
    return x


def wrap_lines(f, text, maxw):
    lines = []; cur = ''
    for w_ in text.split():
        if cur and f.getlength(cur + ' ' + w_) > maxw: lines.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    if cur: lines.append(cur)
    return lines


def draw_caption(canvas, ink, words, groups, t, emph, y):
    """One caption line (two if long): plain words in Inter caps, emphasised words inline in serif italic.
    A group stays up through short pauses so the screen never blinks empty between phrases."""
    gi = None
    for k, g in enumerate(groups):
        start = words[g[0]]['s'] - 0.08
        nxt = words[groups[k + 1][0]]['s'] - 0.08 if k + 1 < len(groups) else 1e9
        end = min(max(words[g[-1]]['e'] + 0.25, nxt if nxt - words[g[-1]]['e'] < 0.8 else 0), nxt)
        if start <= t < end: gi = g; break
    if gi is None: return
    d = ImageDraw.Draw(canvas)
    toks = []
    for i in gi:
        raw = re.sub(r'^[^\w’\'"]+|[^\w’\'%?!]+$', '', words[i]['w'])
        is_em = any(clean(words[i]['w']).startswith(e) for e in emph)
        f = ink.capital if is_em else ink.cap
        s = raw.lower() if is_em else raw.upper()
        toks.append((s, f, is_em, words[i]['s'] - 0.04 <= t))
    space = ink.cap.getlength(' '); pad = 16  # italic glyphs overhang: give emphasised words room
    rows = [[]]; wsum = 0
    for tk in toks:
        tw = tk[1].getlength(tk[0]) + (2 * pad if tk[2] else 0)
        if rows[-1] and wsum + space + tw > 840: rows.append([]); wsum = 0
        rows[-1].append(tk); wsum += (space if wsum else 0) + tw
    for r, row in enumerate(rows):
        rw = sum(tk[1].getlength(tk[0]) + (2 * pad if tk[2] else 0) for tk in row) + space * (len(row) - 1)
        x = W / 2 - rw / 2; base = y + r * 70 + 50  # shared baseline
        for s, f, is_em, on in row:
            asc = f.getmetrics()[0]
            col = (ink.accent if is_em else ink.white) if on else (120, 120, 120)
            xx = x + (pad if is_em else 0)
            d.text((xx, base - asc), s, font=f, fill=col, stroke_width=2 if not is_em else 1, stroke_fill=(0, 0, 0))
            x += f.getlength(s) + (2 * pad if is_em else 0) + space


# ---- concept cards: editorial type drawn straight on the frame (no panels), 920x380, at progress p ----
CW, CH = 920, 380


def layer():
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)


def header(d, ink, title):
    if not title: return 0
    d.rectangle([0, 18, 36, 21], fill=ink.accent)
    tracked(d, (52, 6), title.upper(), ink.label, ink.accent)
    return 56


def card_slider(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); k = spring(p - 0.15, 9)
    y = top + 150; x0, x1 = 30, 890
    d.line([x0, y, x1, y], fill=(255, 255, 255, 110), width=3)
    for j in range(11):
        xx = x0 + (x1 - x0) * j / 10; h_ = 14 if j % 5 == 0 else 7
        d.line([xx, y - h_, xx, y + h_], fill=(255, 255, 255, 110), width=2)
    v = 0.5 + (c.get('value', 0.85) - 0.5) * k; xk = x0 + (x1 - x0) * v
    d.line([x0 + (x1 - x0) * 0.5, y, xk, y], fill=ink.accent, width=5)
    d.ellipse([xk - 26, y - 26, xk + 26, y + 26], outline=ink.accent + (110,), width=3)
    d.ellipse([xk - 13, y - 13, xk + 13, y + 13], fill=ink.accent)
    for s, x, right, on in ((c['a'], x0, False, v < 0.5), (c['b'], x1, True, v >= 0.5)):
        f = ink.serif_i; w_ = f.getlength(s)
        d.text((x - w_ if right else x, y + 40), s, font=f, fill=ink.accent if on else (170, 170, 170))
    return im


def card_compare(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', ''))
    f = ink.serif; colw = 400
    d.line([460, top + 20, 460, top + 20 + 250 * spring(p, 12)], fill=(255, 255, 255, 90), width=2)
    vs = 'vs'; d.text((460 - ink.serif_i.getlength(vs) / 2, top + 100), vs, font=ink.serif_i, fill=(150, 150, 150))
    for j, key in enumerate(('a', 'b')):
        k = spring(p - 0.1 - j * 0.35, 14)
        if k <= 0.01: continue
        x = 0 if j == 0 else 500; y = top + 24 + (1 - k) * 30
        win = c.get('winner') == key; lose = c.get('winner') and not win
        col = (255, 255, 255, int(255 * k)) if not lose else (140, 140, 140, int(255 * k))
        lines = wrap_lines(f, c[key], colw)[:4]
        for li, s in enumerate(lines): d.text((x, y + li * 64), s, font=f, fill=col)
        if win and p > 0.8:
            kk = ease_out((p - 0.8) / 0.4); w_ = f.getlength(lines[-1])
            d.line([x, y + len(lines) * 64 + 6, x + w_ * kk, y + len(lines) * 64 + 6], fill=ink.accent, width=4)
        if lose and p > 1.0:
            kk = ease_out((p - 1.0) / 0.3)
            for li, s in enumerate(lines):
                yy = y + li * 64 + 36; d.line([x, yy, x + f.getlength(s) * kk, yy], fill=(232, 92, 80), width=4)
    return im


def card_list(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); items = c['items']
    step = c.get('dur', 3) / max(1, len(items)) * 0.75
    for j, it in enumerate(items[:4]):
        k = spring(p - j * step, 16)
        if k <= 0.01: continue
        y = top + 8 + j * 92; x = (1 - k) * 30
        d.text((x, y), f'{j + 1:02d}', font=ink.numsm, fill=ink.accent + (int(255 * k),))
        d.text((x + 100, y + 14), it, font=ink.body, fill=(255, 255, 255, int(255 * k)))
        d.line([x + 100, y + 78, 900, y + 78], fill=(255, 255, 255, int(45 * k)), width=1)
    return im


def card_stat(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); k = ease_out(p / 0.9); v = c['value']; f0 = float(c.get('from', 0))
    m = re.match(r'([\d.,]+)(.*)', str(v).replace(',', '') if ',' in str(v) else str(v))
    if m:
        num = m.group(1); dec = len(num.split('.')[1]) if '.' in num else 0; val = f0 + (float(num) - f0) * k
        s = c.get('pre', '') + (f'{val:,.{dec}f}' if ',' in str(v) else f'{val:.{dec}f}') + m.group(2)
    else:
        s = str(v)
    d.text((0, top - 20), s, font=ink.num, fill=ink.accent)
    d.text((4, top + 200), c.get('label', ''), font=ink.serif_i, fill=ink.white)  # under the number: never runs off the frame
    return im


CURVES = {
    'exponential': lambda x: (math.exp(3.2 * x) - 1) / (math.exp(3.2) - 1),
    's': lambda x: 1 / (1 + math.exp(-10 * (x - 0.5))),
    'j': lambda x: 0.35 - 0.6 * x if x < 0.25 else 0.2 + ((math.exp(3 * (x - 0.25)) - 1) / (math.exp(2.25) - 1)) * 0.8,
    'decline': lambda x: 1 - x ** 0.6,
    'u': lambda x: 1 - math.sin(math.pi * x) * 0.85,
    'dunning': lambda x: 0.95 * math.exp(-((x - 0.15) / 0.1) ** 2) + 0.12 + 0.8 * max(0, x - 0.35) ** 1.3,
    'linear': lambda x: x,
}


def card_curve(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); fn = CURVES[c.get('shape', 'exponential')]
    x0, y0, x1, y1 = 20, CH - 40, 900, top + 30
    d.line([x0, y0, x1, y0], fill=(255, 255, 255, 90), width=2); d.line([x0, y0, x0, y1], fill=(255, 255, 255, 90), width=2)
    tracked(d, (x1 - 120, y0 + 10), c.get('x', 'TIME'), ink.label, (160, 160, 160))
    tracked(d, (x0 + 16, y1 - 4), c.get('y', ''), ink.label, (160, 160, 160))
    draw = ease_out(p / 1.4); N = 120
    pts = [(x0 + (x1 - x0) * (j / N), y0 - (y0 - y1) * max(0, min(1, fn(j / N)))) for j in range(int(N * draw) + 1)]
    if c.get('falloff') and draw > 0:
        k = ease_out((p - 1.2) / 0.8); bx = 0.32; fx0 = x0 + (x1 - x0) * bx; fy = y0 - (y0 - y1) * fn(bx)
        for xx in range(int(fx0), int(fx0 + (x1 - fx0) * k), 22): d.line([xx, fy, xx + 12, fy], fill=(170, 170, 170), width=4)
        if k > 0.9: d.text((x1 - ink.serif_i.getlength(c.get('flat_label', 'most people')), fy - 64), c.get('flat_label', 'most people'), font=ink.serif_i, fill=(190, 190, 190))
    if len(pts) > 1: d.line(pts, fill=ink.accent, width=6, joint='curve')
    if pts: x, y = pts[-1]; d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=ink.accent)
    return im


def card_loop(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); nodes = c['nodes']; n = len(nodes); cx, cy, r = 460, top + 160, 130
    lit = int(p / 0.55) % n
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 80), width=2)
    for j, s in enumerate(nodes):
        a = -math.pi / 2 + j * 2 * math.pi / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a); on = j == lit
        d.ellipse([x - (12 if on else 7), y - (12 if on else 7), x + (12 if on else 7), y + (12 if on else 7)], fill=ink.accent if on else (200, 200, 200))
        f = ink.serif_i; w_ = f.getlength(s); tx = x + 24 if math.cos(a) >= -0.1 else x - 24 - w_
        d.text((tx, y - 40), s, font=f, fill=ink.accent if on else ink.white)
    return im


def card_venn(ink, c, p):
    im, d = layer(); top = header(d, ink, c.get('title', '')); k = spring(p, 12); r = 140; cy = top + 160
    for j, (sx, key) in enumerate(((-1, 'a'), (1, 'b'))):
        x = 460 + sx * (100 * k + 10); col = ink.accent if j else (255, 255, 255)
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=col + (28,), outline=col + (200,), width=3)
        s = c[key]; w_ = ink.serif_i.getlength(s); d.text((x + sx * 70 - w_ / 2, cy - 40), s, font=ink.serif_i, fill=(255, 255, 255))
    if k > 0.8 and c.get('mid'):
        tracked(d, (460 - ink.label.getlength(c['mid'].upper()) * 0.57, cy + r + 4), c['mid'].upper(), ink.label, ink.accent)
    return im


def card_chips(ink, c, p):
    """Words that land one by one in serif italic, separated by accent dots."""
    im, d = layer(); top = header(d, ink, c.get('title', '')); f = ink.serif_i
    step = c.get('dur', 3) / max(1, len(c['words'])) * 0.6
    rows = [[]]; wsum = 0
    for s in c['words']:
        w_ = f.getlength(s) + 70
        if rows[-1] and wsum + w_ > 900: rows.append([]); wsum = 0
        rows[-1].append(s); wsum += w_
    idx = 0
    for ri, row in enumerate(rows):
        tw = sum(f.getlength(s) + 70 for s in row) - 70; x = 460 - tw / 2
        for j, s in enumerate(row):
            k = spring(p - idx * step, 18); idx += 1
            if k > 0.01:
                y = top + 20 + ri * 96 + (1 - k) * 24
                d.text((x, y), s, font=f, fill=(255, 255, 255, int(255 * k)))
                if j < len(row) - 1: d.ellipse([x + f.getlength(s) + 28, y + 44, x + f.getlength(s) + 40, y + 56], fill=ink.accent + (int(255 * k),))
            x += f.getlength(s) + 70
    return im


def card_quote(ink, c, p):
    im, d = layer(); k = ease_out(p / 0.6); f = ink.serif_i
    d.text((0, -40), '“', font=ink.quote, fill=ink.accent + (int(255 * k),))
    for li, s in enumerate(wrap_lines(f, c['text'], 800)[:4]): d.text((90, 40 + li * 70), s, font=f, fill=(255, 255, 255, int(255 * k)))
    return im


def card_prospect(ink, c, p):
    """Prospect theory's value function: a loss hurts more than the same gain pleases."""
    im, d = layer(); top = header(d, ink, c.get('title', '')); cx, cy, sx, sy = 460, top + 160, 420, 140
    d.line([cx - sx, cy, cx + sx, cy], fill=(255, 255, 255, 90), width=2); d.line([cx, cy - sy, cx, cy + sy], fill=(255, 255, 255, 90), width=2)
    tracked(d, (cx + sx - 110, cy + 10), 'GAINS', ink.label, (160, 160, 160)); tracked(d, (cx - sx, cy + 10), 'LOSSES', ink.label, (160, 160, 160))
    draw = ease_out(p / 1.4)
    gain = [(cx + sx * (j / 60 * draw), cy - sy * 0.55 * ((j / 60 * draw) ** 0.55)) for j in range(61)]
    loss = [(cx - sx * (j / 60 * draw), cy + sy * min(1.0, 1.25 * ((j / 60 * draw) ** 0.55))) for j in range(61)]
    d.line(gain, fill=ink.white, width=5); d.line(loss, fill=ink.accent, width=6)
    if p > 1.3:
        k = ease_out((p - 1.3) / 0.4); x = 0.6; g = cy - sy * 0.55 * x ** 0.55; l = cy + sy * min(1, 1.25 * x ** 0.55)
        d.text((cx + sx * x + 12, g - 60), c.get('gain', 'a gain'), font=ink.serif_i, fill=(255, 255, 255, int(255 * k)))
        d.text((cx - sx * x - ink.serif_i.getlength(c.get('loss', 'a loss')) - 12, l - 20), c.get('loss', 'a loss'), font=ink.serif_i, fill=ink.accent + (int(255 * k),))
    return im


CARDS = {'prospect': card_prospect, 'slider': card_slider, 'compare': card_compare, 'list': card_list, 'stat': card_stat, 'curve': card_curve,
         'loop': card_loop, 'venn': card_venn, 'chips': card_chips, 'quote': card_quote}


def plan_cards(words, edit):
    out = []
    for c in edit.get('cards', []):
        if 'on' in c:
            i = find_word(words, c['on'], c.get('nth', 1))
            if i is None: print(f"card {c['type']}: '{c['on']}' is not in the transcript, skipped"); continue
            t = words[i]['s'] - 0.1
        else:
            t = float(c['at'])
        out.append(dict(c, t=t, end=t + c.get('dur', 3.0)))
    out.sort(key=lambda c: c['t'])
    for a, b in zip(out, out[1:]):  # never two cards at once: the earlier one leaves before the next lands
        if a['end'] > b['t'] - 0.3: a['end'] = max(a['t'] + 0.8, b['t'] - 0.3)
    return out


def draw_cards(canvas, ink, cards, t, y):
    for c in cards:
        if not (c['t'] <= t <= c['end'] + 0.25): continue
        p = t - c['t']; im = CARDS[c['type']](ink, c, p)
        k = spring(p, 16) * (1 - ease_out((t - c['end']) / 0.25) if t > c['end'] else 1)
        if k <= 0.01: continue
        a = np.array(im); a[..., 3] = (a[..., 3] * min(1, k)).astype(np.uint8); im = Image.fromarray(a)
        canvas.alpha_composite(im, (80, int(y + (1 - k) * 30)))
        return True
    return False


# ------------------------------------------------------------------ compose
def compose(spec, work, base, am, track, words, edit, stills=None):
    ink = Ink(edit.get('accent', '#FFD43B'))
    emph = [e.lower() for e in spec.get('emph', []) + edit.get('italic', [])]
    behind = plan_behind(words, spec, edit); cards = plan_cards(words, edit); groups = caption_groups(words)
    cx, top = smooth_track(track)
    # a 720p source cannot take a 1.6x push without going soft: frame it looser, more room for the word
    sw, sh, _ = src_info(spec['src']); BW, BH = dims(base); portrait = BH > BW
    PLATE_H = int(edit.get('plate_h', 1700 if min(sw, sh) >= 1080 else 1380)); PLATE_Y = H - PLATE_H
    cut_b = int(edit.get('src_crop_bottom', 0))  # burned-in subtitles in the source: crop them away
    # a wide shot (speaker small on a stage) is framed through a window that follows the head
    WH = int(edit.get('window_h', 880 if portrait else BH - cut_b)); S = PLATE_H / WH; cw = int(round(W / S))
    wy = max(0.0, float(top[0]) - 0.2 * WH) if len(top) else 0.0
    grade_dark = 0.58
    name = spec['name']; pic = os.path.join(work, 'layercut_picture.mp4')
    wr = None
    if not stills:
        wr = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                               '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
                               '-pix_fmt', 'yuv420p', pic], stdin=subprocess.PIPE)
    want = set(int(round(s * FPS)) for s in (stills or []))
    for i, (f, a) in enumerate(zip(frames(base, BW, BH), frames(am, BW, BH, 'gray'))):
        if stills and i not in want:
            if i > max(want): break
            continue
        t = i / FPS
        if portrait:  # a speaker at the very edge of a wide shot: pad with black so they stay centred
            pw = cw // 2; fe = 140; ramp = np.ones(BW, np.float32); ramp[:fe] = np.linspace(0, 1, fe); ramp[-fe:] = np.linspace(1, 0, fe)
            f = np.pad((f * ramp[None, :, None]).astype(np.uint8), ((0, 0), (pw, pw), (0, 0))); a = np.pad(a, ((0, 0), (pw, pw)))  # feathered edge
            x0 = int(min(BW + 2 * pw - cw, max(0, cx[min(i, len(cx) - 1)] + pw - cw / 2)))
        else:
            x0 = int(min(BW - cw, max(0, cx[min(i, len(cx) - 1)] - cw / 2)))
        ht = top[min(i, len(top) - 1)]
        if WH < BH - cut_b:  # window: keep the head about a fifth of the way down, move gently
            target = min(BH - cut_b - WH, max(0, ht - 0.2 * WH)); wy = target if stills else wy + (target - wy) * 0.1
        else:
            wy = 0
        y0 = int(wy)
        crop = Image.fromarray(f[y0:y0 + WH, x0:x0 + cw]).resize((W, PLATE_H), Image.LANCZOS)
        al = Image.fromarray(a[y0:y0 + WH, x0:x0 + cw]).resize((W, PLATE_H), Image.BILINEAR)
        head_y = PLATE_Y + (ht - y0) * S
        canvas = Image.new('RGBA', (W, H), (11, 11, 12, 255))
        plate = np.asarray(crop).astype(np.float32)
        lum = plate.mean(axis=2, keepdims=True); room = float(lum.mean())
        dark = min(grade_dark, 42.0 / max(room, 1.0))  # bright rooms are pulled down further so white words read
        plate = (plate * 0.7 + lum * 0.3) * dark
        pl = Image.fromarray(plate.clip(0, 255).astype(np.uint8)).convert('RGBA')
        fade = np.clip(np.linspace(0, 1, PLATE_H) / 0.12, 0, 1)[:, None] * np.ones((1, W))  # the plate's top fades into black
        pl.putalpha(Image.fromarray((fade * 255).astype(np.uint8)))
        canvas.alpha_composite(pl, (0, PLATE_Y))
        draw_behind(canvas, ink, behind, t, head_y, i)
        person = crop.convert('RGBA'); person.putalpha(al)
        canvas.alpha_composite(person, (0, PLATE_Y))
        card_up = any(c['t'] <= t <= c['end'] + 0.25 for c in cards)
        # the dark backing starts above the type, so captions and cards read even on a white shirt
        y0 = 940 if card_up else 1110; ys = np.arange(H - y0)
        ramp = np.clip(ys / 170.0, 0, 1) * (225 if card_up else 195)
        sd = np.zeros((H - y0, W, 4), np.uint8); sd[..., 3] = ramp[:, None].astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(sd), (0, y0))
        has_card = draw_cards(canvas, ink, cards, t, 1160)
        draw_caption(canvas, ink, words, groups, t, emph, 1000 if has_card else 1230)
        out = canvas.convert('RGB')
        if stills:
            p = os.path.join(work, f'layercut_still_{t:05.2f}.jpg'); out.save(p, quality=88); print('still', p)
        else:
            wr.stdin.write(out.tobytes())
    if wr:
        wr.stdin.close(); wr.wait()
    return pic


def mix(spec, work, base, pic, out):
    m = spec.get('music') or {}
    if m.get('file'):
        vol = m.get('vol', 0.22)
        flt = (f"[1:a]atrim=start={m.get('seek', 0)},asetpts=PTS-STARTPTS,loudnorm=I=-20,volume={vol},afade=t=in:d=0.25[mu];"
               f"[0:a]asplit[v1][v2];[mu][v2]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=250[duck];"
               f"[v1][duck]amix=inputs=2:normalize=0:duration=first,aresample=44100,loudnorm=I=-15:TP=-3.5:LRA=11[a]")  # true-peak headroom: old interview audio overshoots in AAC
        cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', base, '-i', m['file'], '-i', pic, '-filter_complex', flt,
               '-map', '2:v', '-map', '[a]']
    else:
        cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', base, '-i', pic, '-map', '1:v', '-map', '0:a', '-af', 'aresample=44100,loudnorm=I=-15:TP=-3.5:LRA=11']
    run(cmd + ['-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out])


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__); return
    spec_path = sys.argv[1]; stills = None; out = None
    if '--stills' in sys.argv: stills = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
    if '--out' in sys.argv: out = os.path.expanduser(sys.argv[sys.argv.index('--out') + 1])
    spec, work, ranges, words = load(spec_path)
    edit = spec.get('edit', {})
    base = base_cut(spec, work, ranges)
    if spec.get('lines'): words = words_from_lines(spec, ranges)  # translated clips: English lines, not whisper
    elif words is None: words = transcribe(base, work, spec)
    am = matte(base, work)
    trk = track(base, am)
    pic = compose(spec, work, base, am, trk, words, edit, stills)
    if stills: return
    out = out or os.path.expanduser(spec['out']).replace('.mp4', '_layercut.mp4')
    if os.path.exists(out): raise SystemExit(f'refusing to overwrite {out}')
    mix(spec, work, base, pic, out)
    print('wrote', out)


if __name__ == '__main__':
    main()
