#!/usr/bin/env python3
"""Synthesize the camera SFX kit into sfx/camera/ (48 kHz stereo, peak -1 dBFS). Our own sounds, no licences.

  shutter   mechanical shutter: two sharp clicks 28 ms apart + a short filtered-noise body
  rip       paper rip: band noise rising in pitch with dense crackle grains, 0.45 s
  crackle   film-burn crackle: sparse impulses + a hot hiss swell, 0.6 s
  rec_beep  record start: two soft sine blips (1.4 kHz, 2.1 kHz)
Usage: python3 bin/sfx-camera.py
"""
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx', 'camera')
rng = np.random.default_rng(7)


def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))


def write(name, x, peak_db=-1.0):
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)
    st = np.stack([x, np.roll(x, 12) * 0.96], 1)                          # tiny stereo offset
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(name, f'{len(x) / SR:.2f}s')


def click(n, decay):
    t = np.arange(n) / SR; return bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t / decay)


def shutter():
    n = int(0.16 * SR); x = np.zeros(n)
    x[:int(0.02 * SR)] += click(int(0.02 * SR), 0.003)
    o = int(0.028 * SR); x[o:o + int(0.03 * SR)] += 0.8 * click(int(0.03 * SR), 0.004)
    t = np.arange(n) / SR; x += 0.25 * bp(rng.standard_normal(n), 400, 3000) * np.exp(-t / 0.035)
    return x


def rip():
    d = 0.45; n = int(d * SR); t = np.arange(n) / SR
    body = np.zeros(n)
    for i in range(0, n, 1024):                                            # band rises 900 -> 4 kHz
        seg = rng.standard_normal(1024); c = 900 + 3100 * (i / n); body[i:i + 1024] = bp(seg, c * 0.6, c * 1.6)[:len(body[i:i + 1024])]
    grains = np.zeros(n); k = rng.integers(0, n - 200, 420)
    for j in k: grains[j:j + 120] += rng.standard_normal(120) * np.exp(-np.arange(120) / 18) * rng.uniform(0.3, 1)
    env = np.minimum(1, t / 0.02) * np.exp(-np.maximum(0, t - 0.3) / 0.06)
    return (0.6 * body + bp(grains, 1200, 9000)) * env


def crackle():
    d = 0.6; n = int(d * SR); t = np.arange(n) / SR
    hiss = bp(rng.standard_normal(n), 2500, 12000) * np.sin(np.pi * t / d) ** 2 * 0.35
    pops = np.zeros(n)
    for j in rng.integers(0, n - 400, 70): pops[j:j + 300] += rng.standard_normal(300) * np.exp(-np.arange(300) / 40) * rng.uniform(0.2, 1)
    rumble = bp(rng.standard_normal(n), 40, 200) * np.sin(np.pi * t / d) * 0.5
    return hiss + bp(pops, 800, 10000) + rumble


def rec_beep():
    out = []
    for f in (1400, 2100):
        t = np.arange(int(0.07 * SR)) / SR; out += [np.sin(2 * np.pi * f * t) * np.sin(np.pi * t / 0.07) ** 2, np.zeros(int(0.03 * SR))]
    return np.concatenate(out) * 0.6


if __name__ == '__main__':
    for name, fn in (('shutter', shutter), ('rip', rip), ('crackle', crackle), ('rec_beep', rec_beep)): write(name, fn())
