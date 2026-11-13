#!/usr/bin/env python3
"""Frame-level smoothness QC: find stutter (repeated/frozen frames inside moving footage) and report cuts.

    python3 bin/motion-qc.py <video.mp4> [--from S --to S]

Why: the 2026-11-12 camera-modes v2 spin flash-cut between frozen stills and its mode strip jumped
~500 px/frame with no motion blur; it read as lag ("very choppy"). Run this before any preview goes out.
Reports per-second motion, runs of >=2 near-identical frames between moving frames (stutter), and the
largest frame-to-frame jumps (should be your intended cuts, nothing else).
"""
import subprocess, sys
import numpy as np

def main():
    a = sys.argv[1:]; src = a[0]
    t0 = float(a[a.index('--from') + 1]) if '--from' in a else 0; t1 = float(a[a.index('--to') + 1]) if '--to' in a else 1e9
    w, h = 135, 240
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    fps = 30.0
    # measure the PICTURE only (rows 16-62% of the frame): UI chrome that keeps moving can hide a frozen picture
    r0, r1 = int(h * 0.16), int(h * 0.62)
    d = np.abs(np.diff(f[:, r0:r1], axis=0)).mean(axis=(1, 2))      # d[i] = change from frame i to i+1
    idx = [i for i in range(len(d)) if t0 <= i / fps <= t1]
    stutters = []
    for i in idx[2:-2]:
        ctx = np.median(np.r_[d[max(0, i - 6):i], d[i + 1:i + 7]])
        if ctx > 1.2 and d[i] < 0.2 * ctx and d[i] < 0.8: stutters.append(i)   # picture (nearly) held while everything around it moves
    runs, i = [], 0
    while i < len(d):
        if d[i] < 0.05:
            j = i
            while j < len(d) and d[j] < 0.05: j += 1
            if j - i >= 2 and t0 <= i / fps <= t1: runs.append((i / fps, (j - i + 1)))
            i = j
        else: i += 1
    print(f'{src}: {len(f)} frames')
    print('mean motion per second:', ' '.join(f'{s}:{d[int(s*fps):int((s+1)*fps)].mean():.1f}' for s in range(int(len(d) / fps)) if t0 <= s <= t1))
    print('STUTTER (held frame inside motion):', [f'{i/fps:.2f}s' for i in stutters] or 'none')
    print('frozen runs (>=3 identical frames):', [f'{t:.2f}s x{n}' for t, n in runs] or 'none')
    big = sorted(idx, key=lambda i: -d[i])[:12]
    print('largest jumps (should be cuts):', ' '.join(f'{(i+1)/fps:.2f}s({d[i]:.0f})' for i in sorted(big)))
    sys.exit(1 if stutters else 0)

if __name__ == '__main__':
    main()
