#!/usr/bin/env python3
"""Fix a coarse person matte at the hair/edge: re-solve alpha from colour and decontaminate the edge.

    <cv2 venv python> bin/refine-hair-matte.py --picture graded.mp4 --matte fg.webm --head head.json \
        --out fg_refined.mov [--frames N] [--preview 1.0,9.1,30 --preview-out sheet.png]

Why: segmentation mattes (hyperframes remove-background) come back as a soft blob around hair, so
wall pixels between strands are kept opaque. Composited over a darker plate that reads as a bright
halo. Here, per frame:
  1. trimap from the coarse alpha: sure-foreground = alpha eroded (wide around the head, narrow on the
     body), sure-background = alpha dilated a little, unknown = the band between.
  2. B = local background colour, filled into the person region by mask-normalised blur of the wall.
     F = local foreground colour, spread outward from the sure-foreground the same way.
  3. in the band, alpha = projection of the pixel colour C onto the line B->F (a colour-difference key
     that resolves single strands of dark hair against a light wall). Where F and B are too close in
     colour to separate (skin on a cream wall), it falls back to the coarse alpha.
  4. edge colour = (C - (1-alpha) B) / alpha, so no wall colour survives in semi-transparent pixels.
  5. light temporal smoothing of alpha in the band only (0.25 of the previous frame) against shimmer.
Writes ProRes 4444 with alpha (composite-layers.py `matte:` reads it). Uses OpenCV from the
claude-video-effects venv.
"""
import argparse, json, subprocess, sys
import numpy as np, cv2

W, H = 1080, 1920
HEAD_BAND = 80

def reader(path, fmt, vp9=False):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error'] + (['-c:v', 'libvpx-vp9'] if vp9 else []) + \
          ['-i', path, '-f', 'rawvideo', '-pix_fmt', fmt, '-']
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 4 * 2)

def nblur(img, mask, sigma):
    """mask-normalised gaussian: fills masked-out pixels from nearby valid ones."""
    k = int(sigma * 3) | 1
    m = cv2.GaussianBlur(mask, (k, k), sigma)
    v = cv2.GaussianBlur(img * mask[..., None], (k, k), sigma)
    return v / np.maximum(m[..., None], 1e-4), m

def ell(r): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def refine(C, a0, head, prev=None):
    """C float32 HxWx3 0..255, a0 float32 HxW 0..1 -> (alpha, rgb)."""
    top, cx, hw = head
    hard = (a0 > 0.5).astype(np.uint8)
    # wide unknown band around the head + hair, narrow on shoulders/arms
    split = int(min(H, top + 1.05 * hw))
    # the coarse blob overshoots hair by up to ~80px: the band must reach that deep around the head
    fg_head = cv2.erode(hard, ell(HEAD_BAND)); fg_body = cv2.erode(hard, ell(6))
    fg_sure = fg_body.copy(); fg_sure[:split] = fg_head[:split]
    # ...but the face itself is never up for grabs: lock an ellipse from brows to chin as solid
    face = np.zeros((H, W), np.uint8)
    cv2.ellipse(face, (int(cx), int(top + 0.80 * hw)), (int(0.40 * hw), int(0.62 * hw)), 0, 0, 360, 1, -1)
    fg_sure = np.maximum(fg_sure, face * hard)
    bg_sure = 1 - cv2.dilate((a0 > 0.03).astype(np.uint8), ell(5))
    unknown = (1 - fg_sure) * (1 - bg_sure)

    # background colour behind the person: wall, from a downsampled normalised blur (fast, smooth)
    s = 4; Cs = cv2.resize(C, (W // s, H // s), interpolation=cv2.INTER_AREA)
    bgm = cv2.resize(bg_sure.astype(np.float32), (W // s, H // s), interpolation=cv2.INTER_AREA)
    bgm = (bgm > 0.99).astype(np.float32)
    B = Cs * 0
    for sig in (6, 14, 30):                       # coarse-to-fine fill so deep holes still get a value
        b, m = nblur(Cs, bgm, sig)
        B = np.where((m[..., None] > 0.02) & (B.sum(-1, keepdims=True) == 0), b, B)
    B = np.where(B.sum(-1, keepdims=True) == 0, Cs.mean((0, 1)), B)
    B = cv2.resize(B, (W, H), interpolation=cv2.INTER_LINEAR)

    # foreground colour, spread outward from sure-foreground (hair colour reaches the strand tips)
    F, mf = nblur(C, fg_sure.astype(np.float32), 9)
    F2, _ = nblur(C, fg_sure.astype(np.float32), 25)
    F = np.where(mf[..., None] > 0.05, F, F2)

    d = F - B; dd = (d * d).sum(-1)
    proj = ((C - B) * d).sum(-1) / np.maximum(dd, 1.0)
    proj = np.clip(proj, 0, 1)
    sep = np.sqrt(dd)
    conf = np.clip((sep - 25) / 35, 0, 1)       # colour separation in 0-255 units
    a_band = conf * proj + (1 - conf) * a0
    alpha = np.where(unknown > 0, a_band, fg_sure.astype(np.float32))
    alpha = np.where(bg_sure > 0, 0, alpha)
    # tame noise: crush the faintest values, keep strands crisp
    alpha = np.clip((alpha - 0.04) / 0.92, 0, 1)
    if prev is not None:
        alpha = np.where(unknown > 0, 0.75 * alpha + 0.25 * prev, alpha)

    # decontaminate: recover the true edge colour; low-alpha pixels take the local foreground colour
    a3 = alpha[..., None]
    Fc = (C - (1 - a3) * B) / np.maximum(a3, 1e-3)
    rgb = np.where(a3 > 0.12, Fc, F)
    rgb = np.where(fg_sure[..., None] > 0, C, rgb)
    return alpha.astype(np.float32), np.clip(rgb, 0, 255).astype(np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--picture', required=True); ap.add_argument('--matte', required=True)
    ap.add_argument('--head', required=True); ap.add_argument('--out')
    ap.add_argument('--frames', type=int); ap.add_argument('--preview'); ap.add_argument('--preview-out')
    ap.add_argument('--plate')
    a = ap.parse_args()
    heads = json.load(open(a.head))['frames']
    def head_at(i):
        lo, hi = max(0, i - 6), min(len(heads), i + 7)
        return tuple(float(np.median([f[k] for f in heads[lo:hi]])) for k in ('top', 'cx', 'width'))

    if a.preview:
        want = [int(round(float(t) * 30)) for t in a.preview.split(',')]
    pr = reader(a.picture, 'rgb24'); mr = reader(a.matte, 'rgba', vp9=a.matte.endswith('.webm'))
    plr = reader(a.plate, 'rgb24') if a.plate else None
    enc = None
    if a.out:
        enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
                                '-framerate', '30', '-i', '-', '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le',
                                '-alpha_bits', '16', '-vendor', 'apl0', a.out], stdin=subprocess.PIPE)
    prev = None; tiles = []; i = 0
    n = a.frames or 10 ** 9
    while i < n:
        cb = pr.stdout.read(W * H * 3); mb = mr.stdout.read(W * H * 4)
        pb = plr.stdout.read(W * H * 3) if plr else None
        if len(cb) < W * H * 3 or len(mb) < W * H * 4: break
        if a.preview and i > max(want): break
        if a.preview and i not in want and not (i + 1 in want):
            i += 1; continue
        C = np.frombuffer(cb, np.uint8).reshape(H, W, 3).astype(np.float32)
        a0 = np.frombuffer(mb, np.uint8).reshape(H, W, 4)[..., 3].astype(np.float32) / 255
        alpha, rgb = refine(C, a0, head_at(i), prev if not a.preview else None)
        prev = alpha
        if enc:
            out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
            enc.stdin.write(out.tobytes())
            if i % 300 == 0: print(f'{i}', flush=True)
        if a.preview and i in want:
            P = np.frombuffer(pb, np.uint8).reshape(H, W, 3).astype(np.float32) if pb else np.full((H, W, 3), 25, np.float32)
            old_rgb = np.frombuffer(mb, np.uint8).reshape(H, W, 4)[..., :3].astype(np.float32)
            old = P * (1 - a0[..., None]) + old_rgb * a0[..., None]
            new = P * (1 - alpha[..., None]) + rgb * alpha[..., None]
            top, cx, hw = head_at(i)
            y0 = int(max(0, top - 80)); x0 = int(max(0, min(W - 640, cx - 320)))
            crop = lambda im: cv2.resize(im[y0:y0 + 420, x0:x0 + 640].astype(np.uint8), (960, 630), interpolation=cv2.INTER_NEAREST)
            tiles.append(np.hstack([crop(old), crop(new)]))
        i += 1
    if enc: enc.stdin.close(); enc.wait(); print('frames', i)
    if a.preview:
        sheet = np.vstack(tiles)
        cv2.imwrite(a.preview_out, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR)); print('preview', a.preview_out)

if __name__ == '__main__': main()
