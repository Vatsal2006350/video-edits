#!/usr/bin/env python3
"""cinema-flex-reel.py -- the "luxury night out" footage montage.

Built 2026-11-23 for the Ramayana IMAX THEATRE-pod reel. Reusable for any
premium-experience flex (cinema pods, fine dining, suites, first class): a
whispered serif hook that sets up a joke, a gold Cinzel title on the payoff
shot, a beat-cut glamour montage, and a comment-to-DM CTA end card.

  python3 bin/cinema-flex-reel.py spec.json            # full render
  python3 bin/cinema-flex-reel.py spec.json --frames 1.2,5.0,13.4   # stills only

Spec (JSON):
{
  "name": "ramayana-pod",            # output folder name
  "out_root": "~/Downloads/reel-batch/cinema-flex",   # optional
  "grade": "imax-gold",               # imax-gold | velvet-noir | none
  "grain": 6,                         # luma noise strength, 0 = off
  "bloom": 0.32,                      # highlight halation opacity, 0 = off
  "letterbox": 0,                     # px bars top+bottom (0 keeps full 9:16)
  "bpm": 0,                           # if >0, a shot's "beats" sets its length
  "shots": [ {"src": "clip.mov", "in": 3.2, "dur": 1.8, "beats": 4,
              "push": 1.05, "focus": 0.5, "speed": 1.0} ],
  "text":  [ {"at": 0.2, "dur": 2.4, "style": "whisper",
              "lines": ["line one", "line two"], "cy": 900} ],
  "audio": {"src": "song.mp3", "ss": 61.2, "gain": 1.0}   # optional, preview mix only
}

Text styles:
  whisper  Cormorant Garamond Medium Italic, warm ivory, blur-in + rise.
  title    Cinzel SemiBold, engraved gold gradient + bloom, tracking breathes open.
  kicker   Tenor Sans caps, wide tracking, champagne; sits under a title.
  rule     a hairline gold rule that draws out from the centre (lines ignored).
  cta      Cinzel gold word + Cormorant italic under it (lines[0] gold, rest italic).

Every text block is fitted into the centred IG-safe width (724px) and its
vertical position is clamped into y 278..1536. Layer alpha bboxes are written
to layer_bbox.json so placement can be asserted, not eyeballed.

Audio: Instagram reach favours audio attached in the composer, so the upload
copy is SILENT unless audio.burn is true. With audio.src set, a separate
*_preview.mp4 gets the track so the cut can be judged against the music.
"""
import json, math, os, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOT, SAFE_L, SAFE_R = 278, 1536, 59, 918
MAX_W = 2 * (SAFE_R - W // 2)           # 756; keep a margin -> 724
MAX_W = 724
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')

def fpath(name):
    p = os.path.join(FONTS, name)
    if not os.path.exists(p):
        sys.exit(f"missing font {name}: run bash bin/fetch-epic-fonts.sh")
    return p

STYLES = {
    'whisper': dict(font='CormorantGaramond-MediumItalic.ttf', size=80, fill=(246, 238, 224),
                    track=0.0, pitch=1.12, shadow=0.55, glow=0, gold=False, enter=0.75),
    'title':   dict(font='Cinzel-SemiBold.ttf', size=104, fill=None, track=0.16, track_to=0.24,
                    pitch=1.18, shadow=0.45, glow=0.55, gold=True, enter=1.0),
    'kicker':  dict(font='TenorSans-Regular.ttf', size=34, fill=(240, 222, 178), track=0.36,
                    pitch=1.6, shadow=0.5, glow=0, gold=False, enter=0.9),
    'cta_big': dict(font='Cinzel-SemiBold.ttf', size=96, fill=None, track=0.2, track_to=0.24,
                    pitch=1.2, shadow=0.45, glow=0.5, gold=True, enter=0.8),
    'cta_sub': dict(font='CormorantGaramond-MediumItalic.ttf', size=56, fill=(246, 238, 224),
                    track=0.0, pitch=1.15, shadow=0.55, glow=0, gold=False, enter=0.8),
}
GOLD_STOPS = [(0.0, (252, 240, 200)), (0.45, (226, 190, 110)), (0.62, (176, 132, 58)),
              (1.0, (236, 204, 132))]

GRADES = {
    # warm gold highlights, cool lifted shadows, gentle filmic shoulder
    'imax-gold': ("eq=contrast=1.07:saturation=0.9:gamma=0.97,"
                  "colorbalance=rs=-0.05:bs=0.06:rm=0.03:bm=-0.02:rh=0.07:gh=0.035:bh=-0.06,"
                  "curves=master='0/0.025 0.22/0.19 0.5/0.5 0.8/0.83 1/0.965',"
                  "vignette=angle=PI/4.6"),
    # deeper, redder, for velvet interiors
    'velvet-noir': ("eq=contrast=1.12:saturation=0.85:gamma=0.94,"
                    "colorbalance=rs=0.05:bs=-0.02:rm=0.05:bm=-0.03:rh=0.05:bh=-0.05,"
                    "curves=master='0/0.02 0.3/0.24 0.7/0.74 1/0.95',vignette=angle=PI/4"),
    'none': "null",
}

def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3

def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        sys.exit(f"command failed: {' '.join(cmd[:6])} ...")
    return r.stdout

def probe(src, entries):
    return sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
               f'stream={entries}', '-of', 'default=nw=1:nk=1', src]).split()

# ----------------------------------------------------------------- type -----
_font_cache = {}
def font(name, size):
    k = (name, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(fpath(name), size)
    return _font_cache[k]

def line_width(f, text, track_px):
    if abs(track_px) < 0.5:
        return f.getlength(text)
    return sum(f.getlength(c) for c in text) + track_px * max(len(text) - 1, 0)

def draw_line(draw, f, text, x, y, track_px, fill):
    if abs(track_px) < 0.5:
        draw.text((x, y), text, font=f, fill=fill)
        return
    for c in text:
        draw.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track_px

def gold_fill(mask):
    w, h = mask.size
    grad = Image.new('RGB', (1, 256))
    for i in range(256):
        t = i / 255
        for (a, ca), (b, cb) in zip(GOLD_STOPS, GOLD_STOPS[1:]):
            if a <= t <= b:
                u = (t - a) / (b - a)
                grad.putpixel((0, i), tuple(int(ca[j] + (cb[j] - ca[j]) * u) for j in range(3)))
                break
    grad = grad.resize((w, h))
    out = grad.convert('RGBA')
    out.putalpha(mask)
    return out

def render_block(lines, st, size, track_em, progress_lines):
    """Render a centred block into its own canvas. Returns (RGBA, width, height)."""
    f = font(st['font'], size)
    track_px = track_em * size
    asc, desc = f.getmetrics()
    lh = int(size * st['pitch'])
    widths = [line_width(f, ln, track_px) for ln in lines]
    bw = int(max(widths) + 120)
    bh = int(lh * (len(lines) - 1) + asc + desc + 120)
    layer = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    for i, ln in enumerate(lines):
        a = progress_lines[i]
        if a <= 0:
            continue
        rise = (1 - ease_out(a)) * 26
        blur = (1 - ease_out(a)) * 9
        m = Image.new('L', (bw, bh), 0)
        d = ImageDraw.Draw(m)
        x = (bw - widths[i]) / 2
        y = 60 + i * lh + rise
        draw_line(d, f, ln, x, y, track_px, 255)
        if blur > 0.3:
            m = m.filter(ImageFilter.GaussianBlur(blur))
        m = m.point(lambda v, k=ease_out(a): int(v * k))
        # shadow
        if st['shadow']:
            s = m.filter(ImageFilter.GaussianBlur(size * 0.09))
            s = s.point(lambda v, k=st['shadow']: int(v * k))
            sh_img = Image.new('RGBA', (bw, bh), (8, 5, 2, 0))
            sh_img.putalpha(ImageChops.offset(s, 0, int(size * 0.04)))
            layer = Image.alpha_composite(layer, sh_img)
        if st['gold']:
            if st['glow']:
                g = m.filter(ImageFilter.GaussianBlur(size * 0.22))
                g = g.point(lambda v, k=st['glow']: int(min(255, v * k * 1.6)))
                gi = Image.new('RGBA', (bw, bh), (232, 178, 86, 0))
                gi.putalpha(g)
                layer = Image.alpha_composite(layer, gi)
            layer = Image.alpha_composite(layer, gold_fill(m))
        else:
            fi = Image.new('RGBA', (bw, bh), st['fill'] + (0,))
            fi.putalpha(m)
            layer = Image.alpha_composite(layer, fi)
    return layer, max(widths), bh

def fit_size(lines, st, track_em):
    size = st['size']
    while size > 18:
        f = font(st['font'], size)
        if max(line_width(f, ln, track_em * size) for ln in lines) <= MAX_W:
            return size
        size -= 2
    return size

def rule_layer(t_rel, width=300):
    p = ease_io(t_rel / 0.9)
    w = int(width * p)
    img = Image.new('RGBA', (width + 40, 40), (0, 0, 0, 0))
    if w < 2:
        return img
    d = ImageDraw.Draw(img)
    cx = (width + 40) // 2
    d.line([(cx - w // 2, 20), (cx + w // 2, 20)], fill=(226, 192, 120, 235), width=2)
    # diamond centre
    r = 5 * p
    d.polygon([(cx, 20 - r), (cx + r, 20), (cx, 20 + r), (cx - r, 20)], fill=(246, 222, 160, 255))
    return img

def text_frame(items, t):
    frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    text_boxes = []
    for it in items:
        rel = t - it['at']
        if rel < 0 or rel > it['dur']:
            continue
        out_len = it.get('fade_out', 0.45)
        fade = 1.0
        if rel > it['dur'] - out_len:
            fade = max(0.0, (it['dur'] - rel) / out_len)
        style = it['style']
        if style == 'rule':
            img = rule_layer(rel, it.get('width', 300))
            cy = it['cy']
        else:
            sub = []
            if style == 'cta':
                sub = [('cta_big', it['lines'][:1]), ('cta_sub', it['lines'][1:])]
            else:
                sub = [(style, it['lines'])]
            parts = []
            delay = 0.0
            for sname, lines in sub:
                if not lines:
                    continue
                st = STYLES[sname]
                tr0 = st['track']
                tr1 = st.get('track_to', tr0)
                track = tr0 + (tr1 - tr0) * ease_io(rel / max(it['dur'], 0.01))
                size = it.get('size') or fit_size(lines, st, max(tr0, tr1))
                prog = [max(0.0, (rel - delay - i * it.get('stagger', 0.2)) / st['enter'])
                        for i in range(len(lines))]
                delay += it.get('stagger', 0.2) * len(lines) + 0.15
                blk, bw, bh = render_block(lines, st, size, track, prog)
                parts.append(blk)
            gap = it.get('gap', 8)
            tw = max(p.width for p in parts)
            th = sum(p.height for p in parts) + gap * (len(parts) - 1) - 100 * (len(parts) - 1)
            img = Image.new('RGBA', (tw, max(th, 1)), (0, 0, 0, 0))
            y = 0
            for p in parts:
                img.alpha_composite(p, ((tw - p.width) // 2, y))
                y += p.height + gap - 100
            cy = it['cy']
        if fade < 1:
            a = img.getchannel('A').point(lambda v, k=fade: int(v * k))
            img.putalpha(a)
        x = W // 2 - img.width // 2
        y = int(min(max(cy - img.height // 2, SAFE_TOP - 60), SAFE_BOT - img.height + 60))
        scrim = it.get('scrim', 0.0 if style == 'rule' else 0.34)
        if scrim:
            # soft dark pool under the words so they hold on bright, busy shots
            bb = img.getchannel('A').getbbox()
            if bb:
                ent = ease_out(rel / 0.6) * fade
                pad_x, pad_y = 90, 70
                sw, shh = bb[2] - bb[0] + 2 * pad_x, bb[3] - bb[1] + 2 * pad_y
                m = Image.new('L', (sw + 160, shh + 160), 0)
                ImageDraw.Draw(m).ellipse([80, 80, 80 + sw, 80 + shh], fill=int(255 * scrim * ent))
                m = m.filter(ImageFilter.GaussianBlur(48))
                pool = Image.new('RGBA', m.size, (4, 3, 2, 0))
                pool.putalpha(m)
                frame.alpha_composite(pool, (max(0, x + bb[0] - pad_x - 80), max(0, y + bb[1] - pad_y - 80)))
        frame.alpha_composite(img, (x, y))
        tb = img.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        if tb:
            text_boxes.append((tb[0] + x, tb[1] + y, tb[2] + x, tb[3] + y))
    if text_boxes:
        frame.info['text_bbox'] = (min(b[0] for b in text_boxes), min(b[1] for b in text_boxes),
                                   max(b[2] for b in text_boxes), max(b[3] for b in text_boxes))
    return frame

# --------------------------------------------------------------- shots ------
def shot_filter(s, grade, letterbox, dur):
    src = s['src']
    trc = (probe(src, 'color_transfer') or ['unknown'])[0].strip(',')
    vf = []
    if trc in ('arib-std-b67', 'smpte2084'):
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                  "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    sp = s.get('speed', 1.0)
    if sp != 1.0:
        vf.append(f"setpts=PTS/{sp}")
    vf.append(f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos")
    push = s.get('push', 1.04)
    fx = s.get('focus', 0.5)
    # slow push-in, eased, evaluated per frame
    z = f"(1+({push}-1)*(t/{dur}))"
    vf.append(f"scale=w='ceil({W}*{z}/2)*2':h='ceil({H}*{z}/2)*2':eval=frame:flags=bicubic")
    vf.append(f"crop={W}:{H}:x='(iw-{W})*{fx}':y='(ih-{H})/2'")
    vf.append("fps=30,setsar=1")
    vf.append(GRADES[grade])
    if letterbox:
        vf.append(f"drawbox=y=0:w=iw:h={letterbox}:color=black:t=fill,"
                  f"drawbox=y=ih-{letterbox}:w=iw:h={letterbox}:color=black:t=fill")
    if s.get('fade_in'):
        vf.append(f"fade=t=in:st=0:d={s['fade_in']}")
    if s.get('fade_out'):
        vf.append(f"fade=t=out:st={dur - s['fade_out']:.3f}:d={s['fade_out']}")
    vf.append("format=yuv420p")
    return ",".join(vf)

def main():
    spec_path = sys.argv[1]
    frames_only = None
    if '--frames' in sys.argv:
        frames_only = [float(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(',')]
    spec = json.load(open(spec_path))
    base = os.path.dirname(os.path.abspath(spec_path))
    root = os.path.abspath(os.path.join(base, os.path.expanduser(spec.get('out_root', 'out'))))
    out = os.path.join(root, spec['name'])
    work = os.path.join(out, '.work')
    os.makedirs(work, exist_ok=True)
    grade = spec.get('grade', 'imax-gold')
    bpm = spec.get('bpm', 0)
    shots = spec['shots']
    for s in shots:
        s['src'] = os.path.join(base, os.path.expanduser(s['src']))
        if bpm and s.get('beats'):
            s['dur'] = round(s['beats'] * 60.0 / bpm, 4)
    total = sum(s['dur'] for s in shots)
    items = spec.get('text', [])
    print(f"[cinema-flex] {len(shots)} shots, {total:.2f}s, grade {grade}")

    # 1. shots -> one encoded file each, identical settings
    seg_list = os.path.join(work, 'concat.txt')
    with open(seg_list, 'w') as cl:
        for i, s in enumerate(shots):
            seg = os.path.join(work, f'shot_{i:02d}.mp4')
            tmp = seg[:-4] + '.part.mp4'
            key = json.dumps([s, grade, spec.get('letterbox', 0)], sort_keys=True)
            keyf = seg + '.key'
            if not (os.path.exists(seg) and os.path.exists(keyf) and open(keyf).read() == key):
                need = s['dur'] * s.get('speed', 1.0) + 0.1
                sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(s.get('in', 0)), '-t',
                    f'{need:.3f}', '-i', s['src'], '-an', '-vf',
                    shot_filter(s, grade, spec.get('letterbox', 0), s['dur']),
                    '-t', f"{s['dur']:.4f}", '-c:v', 'libx264', '-crf', '14', '-preset', 'veryfast',
                    '-pix_fmt', 'yuv420p', '-r', '30', tmp])
                os.replace(tmp, seg)
                open(keyf, 'w').write(key)
            cl.write(f"file '{seg}'\n")
            print(f"  shot {i:02d} {os.path.basename(s['src'])} @{s.get('in', 0)} {s['dur']:.2f}s")
    plate = os.path.join(work, 'plate.mp4')
    sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', seg_list,
        '-c', 'copy', plate])

    # 2. text layer, frame by frame
    tdir = os.path.join(work, 'text')
    shutil.rmtree(tdir, ignore_errors=True)
    os.makedirs(tdir)
    n = int(round(total * FPS))
    times = [i / FPS for i in range(n)] if frames_only is None else frames_only
    blank = None
    bbox_log = []
    for i, t in enumerate(times):
        fr = text_frame(items, t)
        bb = fr.getchannel('A').getbbox()
        p = os.path.join(tdir, f't_{i:05d}.png')
        if bb is None and frames_only is None:
            if blank is None:
                blank = os.path.join(tdir, 'blank.png')
                fr.save(blank)
            os.link(blank, p)
        else:
            fr.save(p)
        bb = fr.info.get('text_bbox')   # the type itself (alpha > 40), not the scrim
        if bb:
            bbox_log.append({'t': round(t, 3), 'bbox': bb})
            if bb[0] < SAFE_L or bb[2] > SAFE_R or bb[1] < SAFE_TOP - 4 or bb[3] > SAFE_BOT + 4:
                print(f"  WARN text outside IG safe box at t={t:.2f}: {bb}")
    json.dump(bbox_log, open(os.path.join(out, 'layer_bbox.json'), 'w'))

    post = []
    if spec.get('bloom', 0.32):
        # blend MUST run in RGB: a screen blend on YUV chroma planes turns everything magenta
        post.append(f"format=gbrp,split[a][b];[b]curves=all='0/0 0.72/0 1/1',gblur=sigma=22[g];"
                    f"[a][g]blend=all_mode=screen:all_opacity={spec.get('bloom', 0.32)},format=yuv420p")
    post_v = ",".join(post) if post else "null"
    grain = spec.get('grain', 6)

    if frames_only is not None:
        # stills: composite the plate frame + text, no video encode
        for i, t in enumerate(times):
            pf = os.path.join(work, f'plate_{i}.png')
            sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', f'{t:.3f}', '-i', plate,
                '-frames:v', '1', '-vf', post_v.replace('[a][b]', '[a][b]'), pf]
               if not post else
               ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', f'{t:.3f}', '-i', plate,
                '-frames:v', '1', '-filter_complex', f"[0:v]{post_v}", pf])
            im = Image.open(pf).convert('RGBA')
            im.alpha_composite(Image.open(os.path.join(tdir, f't_{i:05d}.png')))
            dst = os.path.join(out, f'frame_{t:05.2f}.png')
            im.convert('RGB').save(dst)
            print("  wrote", dst)
        return

    # 3. composite: plate -> bloom -> text -> grain, one encode
    master = os.path.join(out, f"{spec['name']}_master.mp4")
    tmp = master[:-4] + '.part.mp4'
    fc = (f"[0:v]{post_v}[p];[p][1:v]overlay=0:0:format=auto[o];"
          f"[o]noise=c0s={grain}:c0f=t+u,format=yuv420p[v]" if grain else
          f"[0:v]{post_v}[p];[p][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    cmd = ['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', plate, '-framerate', '30',
           '-i', os.path.join(tdir, 't_%05d.png')]
    aud = spec.get('audio')
    burn = aud and aud.get('burn')
    if burn:
        cmd += ['-ss', str(aud.get('ss', 0)), '-i', os.path.join(base, os.path.expanduser(aud['src']))]
    cmd += ['-filter_complex', fc, '-map', '[v]']
    if burn:
        cmd += ['-map', '2:a', '-af', f"volume={aud.get('gain', 1.0)},afade=t=out:st={total - 0.8:.2f}:d=0.8",
                '-c:a', 'aac', '-b:a', '256k', '-shortest']
    cmd += ['-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-r', '30', '-t', f'{total:.3f}',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-movflags', '+faststart', tmp]
    sh(cmd)
    os.replace(tmp, master)
    print("  master", master)

    # 4. preview with the track (never the upload copy unless burn)
    if aud and not burn and aud.get('src'):
        prev = os.path.join(out, f"{spec['name']}_preview.mp4")
        sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', master, '-ss', str(aud.get('ss', 0)),
            '-i', os.path.join(base, os.path.expanduser(aud['src'])), '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-af', f"volume={aud.get('gain', 1.0)},afade=t=out:st={total - 0.8:.2f}:d=0.8",
            '-c:a', 'aac', '-b:a', '192k', '-shortest', prev])
        print("  preview (with music)", prev)
    phone = os.path.join(out, 'phone', f"{spec['name']}_phone.mp4")
    os.makedirs(os.path.dirname(phone), exist_ok=True)
    src_phone = os.path.join(out, f"{spec['name']}_preview.mp4") if (aud and not burn and aud.get('src')) else master
    sh(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', src_phone, '-vf', 'scale=608:1080',
        '-c:v', 'libx264', '-crf', '26', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', phone])
    print("  phone", phone)

if __name__ == '__main__':
    main()
