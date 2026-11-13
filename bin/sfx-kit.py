#!/usr/bin/env python3
"""Synthesize the "energy" SFX kit into sfx/energy/ (48 kHz stereo, peak -1 dBFS). Our own sounds, no licences.

Modelled on the measured sound design of a high-energy walk-and-talk reel (GP Multimedia, DdHguJfhYSU, 2026-11-09):
  pops/ticks  : ~50 ms, centroid 3.5-4 kHz, on every hero word / counter step
  whooshes    : 0.3-0.7 s swell INTO a cut, centroid 4-5 kHz, sub thump on the landing
  sub impacts : sub-heavy (<120 Hz share ~0.4-0.6), ~0.7 s decay, on slams (logo, big number)
Usage: python3 bin/sfx-kit.py            (writes sfx/energy/*.wav + kit.json with measured stats)
"""
import json, os, subprocess, sys
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx', 'energy')
rng = np.random.default_rng(11)


def t_(d): return np.arange(int(d * SR)) / SR


def norm(x, peak_db=-1.0):
    m = np.max(np.abs(x)) + 1e-12
    return x / m * (10 ** (peak_db / 20))


def env_ad(n, a, d, curve=4.0):
    """attack a s (linear), exponential decay d s"""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), np.exp(-(t - a) / max(d, 1e-4) * curve / 4))
    return e


def bandnoise(dur, f_of_t, q_of_t, color='pink', seed=None):
    """noise whose spectrum is a moving gaussian band: centre f_of_t(time) Hz, width centre/q."""
    g = np.random.default_rng(seed) if seed is not None else rng
    n = int(dur * SR); hop = 256; N = 2048
    x = g.standard_normal(n + N)
    win = np.hanning(N); out = np.zeros(n + N); norm_ = np.zeros(n + N)
    fr = np.fft.rfftfreq(N, 1 / SR)
    tilt = 1 / np.sqrt(np.maximum(fr, 20)) if color == 'pink' else np.ones_like(fr)
    for i in range(0, n, hop):
        tt = i / SR; fc = f_of_t(tt); bw = fc / q_of_t(tt)
        S = np.fft.rfft(x[i:i + N] * win)
        S *= tilt * np.exp(-0.5 * ((fr - fc) / bw) ** 2)
        out[i:i + N] += np.fft.irfft(S) * win; norm_[i:i + N] += win ** 2
    return (out / np.maximum(norm_, 1e-6))[:n]


def stereo(x, pan_of_t=None, width=0.0):
    n = len(x); t = np.arange(n) / SR
    p = pan_of_t(t) if pan_of_t else np.zeros(n)          # -1 (L) .. 1 (R)
    l = x * np.sqrt((1 - p) / 2) * np.sqrt(2); r = x * np.sqrt((1 + p) / 2) * np.sqrt(2)
    if width:                                             # tiny Haas decorrelation
        d = int(0.0007 * SR * width); r = np.r_[np.zeros(d), r[:-d]] if d else r
    return np.stack([l, r], 1)


def sine_sweep(dur, f0, f1, curve='exp'):
    t = t_(dur)
    f = f0 * (f1 / f0) ** (t / dur) if curve == 'exp' else f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def soft_clip(x, drive=1.5): return np.tanh(x * drive) / np.tanh(drive)


# ---------------------------------------------------------------- the kit
def pop(pitch=1.0):
    d = 0.09; t = t_(d)
    body = sine_sweep(d, 2300 * pitch, 4600 * pitch) * env_ad(len(t), 0.0015, 0.03)
    click = bandnoise(d, lambda _: 5200, lambda _: 1.6, seed=3) * env_ad(len(t), 0.0004, 0.008)
    return stereo(norm(0.8 * body + 0.6 * norm(click)), width=1)


def click_ui():
    d = 0.06; t = t_(d)
    ping = np.sin(2 * np.pi * 3100 * t) * env_ad(len(t), 0.001, 0.018)
    n = bandnoise(d, lambda _: 5200, lambda _: 1.6, seed=5) * env_ad(len(t), 0.0003, 0.004)
    return stereo(norm(0.7 * ping + norm(n)), width=1)


def tick(var=0):
    d = 0.035; t = t_(d)
    f = [3600, 4100, 3300][var % 3]
    x = np.sin(2 * np.pi * f * t) * env_ad(len(t), 0.0004, 0.006) + 0.5 * bandnoise(d, lambda _: 6000, lambda _: 2.5, seed=7 + var) * env_ad(len(t), 0.0002, 0.003)
    return stereo(norm(x, -3), width=1)


def whoosh(d=0.45, f0=1200, f1=9000, seed=21):
    """swell that PEAKS at the end (place it so the end lands on the cut)"""
    fc = lambda tt: f0 * (f1 / f0) ** min(1.0, tt / d)
    x = bandnoise(d + 0.05, fc, lambda tt: 1.1, color='pink', seed=seed)[:int(d * SR)]
    t = t_(d); e = (t / d) ** 2.2 * (1 - np.exp(-(d - t) / 0.012))          # crescendo, tiny release
    return stereo(norm(soft_clip(norm(x) * e, 1.3)), pan_of_t=lambda tt: np.clip(-0.7 + 1.4 * tt / d, -1, 1), width=2)


def whip():
    d = 0.24
    x = whoosh(d, 1500, 10000, seed=33)[:, 0]
    t = t_(d); crack = bandnoise(d, lambda _: 3000, lambda _: 1.2, seed=34) * np.exp(-np.maximum(0, t - (d - 0.02)) / 0.01) * (t > d - 0.02)
    return stereo(norm(x + 0.6 * norm(crack)), pan_of_t=lambda tt: np.clip(-0.9 + 1.8 * tt / d, -1, 1), width=2)


def impact_sub():
    d = 0.95; t = t_(d)
    boom = sine_sweep(d, 92, 42) * env_ad(len(t), 0.004, 0.32)
    knock = bandnoise(d, lambda _: 900, lambda _: 1.0, seed=41) * env_ad(len(t), 0.0005, 0.02)
    air = bandnoise(d, lambda tt: 2500 * np.exp(-tt * 3), lambda _: 1.2, seed=42) * env_ad(len(t), 0.002, 0.12)
    return stereo(norm(soft_clip(0.8 * boom + 0.9 * norm(knock) + 0.55 * norm(air), 1.8)), width=1)


def impact_punch():
    d = 0.32; t = t_(d)
    thump = sine_sweep(d, 140, 60) * env_ad(len(t), 0.002, 0.09)
    snap = bandnoise(d, lambda _: 2600, lambda _: 1.3, seed=51) * env_ad(len(t), 0.0004, 0.012)
    return stereo(norm(soft_clip(thump + 0.55 * norm(snap), 1.6)), width=1)


def riser(d=1.4):
    fc = lambda tt: 300 * (6000 / 300) ** (tt / d)
    n = bandnoise(d, fc, lambda _: 2.0, seed=61)
    tone = sine_sweep(d, 180, 1400) * 0.25
    t = t_(d); e = (t / d) ** 2.6
    return stereo(norm(soft_clip((norm(n) + tone) * e, 1.4)), pan_of_t=lambda tt: 0.4 * np.sin(2 * np.pi * tt * 1.5), width=2)


def heart_pop():
    a = pop(1.45)[:, 0]; t = t_(0.18)
    sparkle = sum(np.sin(2 * np.pi * f * t) * env_ad(len(t), 0.001, 0.05) * (t >= o) for f, o in ((2637, 0.03), (3136, 0.06), (3951, 0.09)))
    x = np.zeros(len(t)); x[:len(a)] += a; x += 0.35 * sparkle
    return stereo(norm(x), width=1)


def ding():
    d = 0.9; t = t_(d)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, a, dd in ((1318.5, 1, 0.35), (1975.5, .55, .22), (2637, .25, .12)))
    return stereo(norm(x * env_ad(len(t), 0.002, 10)), width=1)


def swipe_up():
    d = 0.3
    return whoosh(d, 2000, 11000, seed=71)


KIT = {
    'pop': pop, 'pop_hi': lambda: pop(1.3), 'pop_lo': lambda: pop(0.8), 'click_ui': click_ui,
    'tick1': lambda: tick(0), 'tick2': lambda: tick(1), 'tick3': lambda: tick(2),
    'whoosh_short': lambda: whoosh(0.32, 1500, 9500, 22), 'whoosh': lambda: whoosh(0.5), 'whoosh_long': lambda: whoosh(0.8, 900, 8000, 23),
    'whip': whip, 'swipe_up': swipe_up, 'impact_sub': impact_sub, 'impact_punch': impact_punch, 'riser': riser,
    'heart_pop': heart_pop, 'ding': ding,
}


def write(name, x):
    import wave
    x = np.clip(x, -1, 1); pcm = (x * 32767).astype('<i2')
    p = os.path.join(OUT, name + '.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return p


def stats(x):
    m = x.mean(1); N = 2048; F = np.abs(np.fft.rfft(m[:N * (len(m) // N or 1)].reshape(-1, N) * np.hanning(N), axis=1)).sum(0) if len(m) >= N else np.abs(np.fft.rfft(m, N))
    fr = np.fft.rfftfreq(N, 1 / SR); tot = F.sum() + 1e-9
    e = np.abs(m); ip = int(np.argmax(e))
    return dict(dur=round(len(m) / SR, 3), peak_at=round(ip / SR, 3), centroid=int((F * fr).sum() / tot), sub_share=round(float(F[fr < 120].sum() / tot), 2))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); meta = {}
    for k, fn in KIT.items():
        x = fn(); write(k, x); meta[k] = stats(x); print(k, meta[k])
    json.dump(meta, open(os.path.join(OUT, 'kit.json'), 'w'), indent=1)
