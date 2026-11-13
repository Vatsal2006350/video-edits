#!/usr/bin/env python3
"""High-quality person matte with RobustVideoMatting (resnet50, cached in ~/.cache/torch/hub).

    .agents/skills/video-effects/.venv/bin/python bin/rvm-matte.py <picture.mp4> <out.mov> [--ratio 0.4]
        [--start S --count N]   (a short window, e.g. to test)

Why not hyperframes remove-background for hero shots: it returns a soft blob around hair, so wall
between strands stays opaque and glows over a darker plate. RVM is a recurrent video matting model:
strand-level hair alpha, temporally stable, and it predicts the true foreground colour, so the edge
carries no wall colour. Output: ProRes 4444 with alpha (bin/composite-layers.py `matte:` reads it);
rgb = original pixel where the subject is solid, RVM's foreground colour on the soft edge.
Runs on Apple Silicon (mps). GPL-3.0 model, used locally, not bundled.
"""
import argparse, subprocess, sys
import numpy as np, torch

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--ratio', type=float, default=0.4, help='downsample_ratio: larger = finer hair, slower')
ap.add_argument('--start', type=float, default=0); ap.add_argument('--count', type=int)
a = ap.parse_args()

dev = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
m = torch.hub.load('PeterL1n/RobustVideoMatting', 'resnet50', trust_repo=True).eval().to(dev)
probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                        '-of', 'csv=p=0', a.src], capture_output=True, text=True).stdout.strip().split(',')
W, H = int(probe[0]), int(probe[1])
rd = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(a.start), '-i', a.src] +
                      (['-frames:v', str(a.count)] if a.count else []) + ['-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                      stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
wr = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
                       '-framerate', '30', '-i', '-', '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le',
                       '-alpha_bits', '16', '-vendor', 'apl0', a.out], stdin=subprocess.PIPE)
rec = [None] * 4; n = 0
with torch.no_grad():
    while True:
        b = rd.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        src = torch.from_numpy(np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()).to(dev).permute(2, 0, 1)[None].float() / 255
        fgr, pha, *rec = m(src, *rec, downsample_ratio=a.ratio)
        p = pha[0, 0].clamp(0, 1); f = fgr[0].clamp(0, 1)
        solid = (p > 0.985).float()
        rgb = src[0] * solid + f * (1 - solid)
        out = torch.cat([rgb, p[None]], 0).permute(1, 2, 0).mul(255).round().byte().cpu().numpy()
        wr.stdin.write(out.tobytes()); n += 1
        if n % 300 == 0: print(n, flush=True)
wr.stdin.close(); wr.wait(); print('frames', n)
