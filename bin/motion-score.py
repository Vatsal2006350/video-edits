#!/usr/bin/env python3
"""Synthesize an original score for a motion film from its beat map and event list.

    python3 bin/motion-score.py motion/one-line/score.json out.wav
    python3 bin/motion-score.py motion/one-line/score.json out.wav --mux film.mp4 film_with_sound.mp4

score.json:
  {"bpm": 120, "seconds": 24, "loop": true,
   "pad": [[0, "paper"], [10, "blueprint"], [17.6, "holo"], [23.6, "paper"]],
   "events": {"thud": [0.45, ...], "tick": [1.0, ...], "click": [...],
              "pencil": [[4.1, 0.4], ...], "whoosh": [[9.6, 0.4], ...]}}

Everything is made from sines and filtered noise (numpy only), so there is nothing to
license. Sounds sit on the visible actions; the beat is a soft kick and an offbeat hat.
The mux step compresses and limits the score (sharp synthesized ticks overshoot between
samples otherwise); bin/export-ig.sh does the final loudness.
"""
import json
import subprocess
import sys
import wave

import numpy as np

SR = 48000


def env(n, a=0.002, r=0.08):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(r, 1e-4))
    return e


def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


def highpass(x, cut):
    return x - lowpass(x, cut)


rng = np.random.default_rng(7)


def kick():
    n = int(0.32 * SR); t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.11) * 0.55


def hat():
    n = int(0.05 * SR)
    return highpass(rng.standard_normal(n), 7000) * env(n, 0.001, 0.012) * 0.08


def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 3100 * t) * 0.5 + highpass(rng.standard_normal(n), 4000) * 0.5) * env(n, 0.0005, 0.006) * 0.16


def click():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1800 * t) + 0.6 * np.sin(2 * np.pi * 900 * t)) * env(n, 0.0005, 0.012) * 0.22


def thud():
    n = int(0.45 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 20)) * t) * env(n, 0.001, 0.16)
    snap = highpass(rng.standard_normal(n), 1500) * env(n, 0.0005, 0.02) * 0.4
    return (body + snap) * 0.5


def pencil(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = highpass(lowpass(rng.standard_normal(n), 5200), 1800)
    grain = 0.55 + 0.45 * np.sin(2 * np.pi * 23 * t + 3 * np.sin(2 * np.pi * 3.1 * t))
    shape = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.05)
    return noise * grain * shape * 0.09


def whoosh(dur):
    n = int((dur + 0.25) * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); seg = 2048
    for s in range(0, n, seg):  # a band of noise whose centre rises through the wipe
        u = min(1, (s / SR) / dur); cut = 300 + 5200 * u ** 2
        out[s:s + seg] = highpass(lowpass(noise[s:s + seg], cut), cut * 0.35)
    shape = np.where(t < dur, (t / dur) ** 2, np.exp(-(t - dur) / 0.07))
    return out * shape * 0.32


PADS = {  # quiet sustained chords that change colour with the ink
    'paper': [110.0, 164.81, 220.0, 261.63],
    'blueprint': [123.47, 185.0, 246.94, 293.66],
    'holo': [130.81, 196.0, 261.63, 329.63, 392.0],
}


def pad(seconds, plan, loop):
    n = int(seconds * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for k, (t0, name) in enumerate(plan):
        t1 = plan[k + 1][0] if k + 1 < len(plan) else seconds
        fade = 0.35
        w = np.clip((t - (t0 - fade)) / fade, 0, 1) * np.clip(((t1 + fade) - t) / fade, 0, 1)
        if not w.any():
            continue
        tone = sum(np.sin(2 * np.pi * f * t + i) * (0.6 if i == 0 else 0.35) for i, f in enumerate(PADS[name]))
        tone *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t) ** 2
        out += tone * w
    out = lowpass(out, 1400) * 0.05
    if loop:  # match the last samples to the first so the loop is seamless
        x = int(0.02 * SR); out[-x:] = out[-x:] * np.linspace(1, 0, x) + out[:x] * np.linspace(0, 1, x)
    return out


def place(buf, sig, at, pan=0.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j = min(len(buf), i + len(sig)); s = sig[: j - i]
    buf[i:j, 0] += s * (1 - max(0, pan)); buf[i:j, 1] += s * (1 + min(0, pan))


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]
    seconds, bpm = spec['seconds'], spec['bpm']; B = 60 / bpm
    buf = np.zeros((int(seconds * SR), 2))
    for k in range(int(seconds / B)):
        place(buf, kick(), k * B)
        place(buf, hat(), k * B + B / 2, pan=0.25)
    ev = spec.get('events', {})
    for at in ev.get('thud', []): place(buf, thud(), at)
    for i, at in enumerate(ev.get('tick', [])): place(buf, tick(), at, pan=((i % 5) - 2) * 0.12)
    for at in ev.get('click', []): place(buf, click(), at)
    for at, d in ev.get('pencil', []): place(buf, pencil(d), at, pan=-0.1)
    for at, d in ev.get('whoosh', []): place(buf, whoosh(d), at)
    p = pad(seconds, spec.get('pad', [[0, 'paper']]), spec.get('loop', True)); buf[:, 0] += p; buf[:, 1] += p
    peak = np.max(np.abs(buf)) or 1; buf *= 0.6 / peak
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(buf, -1, 1) * 32767).astype('<i2').tobytes())
    print(f'wrote {out} ({seconds}s, {bpm} BPM)')
    if '--mux' in sys.argv:
        i = sys.argv.index('--mux'); film, dst = sys.argv[i + 1], sys.argv[i + 2]
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', film, '-i', out, '-map', '0:v', '-map', '1:a',
                        '-af', 'lowpass=f=9000,acompressor=threshold=0.06:ratio=4:attack=2:release=90:makeup=2,alimiter=limit=0.4:attack=1:release=40:level=false',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', dst], check=True)
        print(f'muxed {dst}')


if __name__ == '__main__':
    main()
