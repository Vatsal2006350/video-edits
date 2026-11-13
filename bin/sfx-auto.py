#!/usr/bin/env python3
"""Energy sound-design track from a cue spec -> one stereo WAV + the expanded cue sheet.

  python3 bin/sfx-auto.py spec.json out_sfx.wav [--words aligned.json]

spec.json (all times in REEL seconds; every key optional except duration):
{
  "duration": 48.7,
  "cuts":   [5.10, 6.20],          # transition: whoosh/whip that PEAKS on the cut + a punch thump on the landing
  "whips":  [11.18],               # harder whip-pan transition (pairs with energy-pass.py --whips)
  "pops":   [8.70, 10.40],         # a word/graphic appears: alternating pop / pop_hi / pop_lo
  "hero_words": ["views", "Claude"],# with --words: a pop on the start of each of these spoken words
  "slams":  [4.03],                # big reveal (logo, number, title): sub impact + click
  "ticks":  [[16.2, 17.4, 8]],     # counter ticking: start, end, count
  "hearts": [5.5, 5.9],            # like-heart bursts
  "risers": [22.45],               # riser that ENDS at this time (build into a payoff)
  "dings":  [36.5],                # notification / CTA
  "extra":  [{"name": "swipe_up", "t": 30.0, "gain_db": -12, "align": "end"}],
  "master_db": 0
}
Levels are dB re. the kit's -1 dBFS peaks, tuned to sit under a voice mixed around -16 LUFS (see formats/energy-walk-talk.md).
Kit: sfx/energy/ (make it with bin/sfx-kit.py).
"""
import json, os, sys, wave
import numpy as np

SR = 48000
KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sfx', 'energy')
LEVEL = {'pop': -14, 'pop_hi': -14, 'pop_lo': -12, 'click_ui': -24, 'tick1': -17, 'tick2': -21, 'tick3': -18,   # measured: pops ~8-10 dB under voice
         'whoosh_short': -10, 'whoosh': -14, 'whoosh_long': -15, 'whip': -15, 'swipe_up': -10,         # transitions ~5-7 dB under voice
         'impact_punch': -16, 'impact_sub': -18, 'riser': -21, 'heart_pop': -16, 'ding': -19}          # sub hits ~3 dB under (sub reads quieter)
_cache = {}


def snd(name):
    if name not in _cache:
        with wave.open(os.path.join(KIT, name + '.wav')) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32).reshape(-1, 2) / 32767
        _cache[name] = a
    return _cache[name]


def peak_offset(name):
    a = np.abs(snd(name)).mean(1); return int(np.argmax(a))


def expand(spec, words=None):
    cues = []
    add = lambda n, t, align='start', db=None: cues.append(dict(name=n, t=round(float(t), 3), align=align, gain_db=LEVEL[n] if db is None else db))
    cuts = sorted(spec.get('cuts', []))
    for i, t in enumerate(cuts):
        gap = min([abs(t - c) for c in cuts if c != t] + [9])
        add('whoosh_short' if gap < 1.2 else 'whoosh', t, 'end'); add('impact_punch', t, 'start', LEVEL['impact_punch'] - 3)
    for t in spec.get('whips', []):
        add('whip', t, 'end'); add('impact_punch', t)
    pops = list(spec.get('pops', []))
    if words and spec.get('hero_words'):
        hero = {w.lower().strip('.,!?') for w in spec['hero_words']}
        for w in words:
            if w['word'].lower().strip(' .,!?"\'') in hero: pops.append(w['start'])
    last = -9
    for k, t in enumerate(sorted(pops)):
        if t - last < 0.12: continue                       # never machine-gun pops
        add(['pop', 'pop_hi', 'pop_lo'][k % 3], t); last = t
    for t in spec.get('slams', []): add('impact_sub', t); add('click_ui', t)
    for t0, t1, n in spec.get('ticks', []):
        for j in range(int(n)): add(f'tick{j % 3 + 1}', t0 + (t1 - t0) * j / max(1, n - 1))
    for t in spec.get('hearts', []): add('heart_pop', t)
    for t in spec.get('risers', []): add('riser', t, 'end')
    for t in spec.get('dings', []): add('ding', t)
    for e in spec.get('extra', []): add(e['name'], e['t'], e.get('align', 'start'), e.get('gain_db'))
    return sorted(cues, key=lambda c: c['t'])


def render(cues, duration, master_db=0.0):
    n = int(duration * SR) + SR; out = np.zeros((n, 2), np.float32)
    for c in cues:
        a = snd(c['name']) * (10 ** ((c['gain_db'] + master_db) / 20))
        i0 = int(c['t'] * SR) - (peak_offset(c['name']) if c['align'] == 'end' else 0)
        if i0 < 0: a = a[-i0:]; i0 = 0
        i1 = min(n, i0 + len(a)); out[i0:i1] += a[:i1 - i0]
    out = out[:int(duration * SR)]
    pk = np.abs(out).max()
    if pk > 0.89: out *= 0.89 / pk                         # headroom; the final IG export limits again
    return out


def write(p, x):
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1])); outp = sys.argv[2]
    words = None
    if '--words' in sys.argv:
        d = json.load(open(sys.argv[sys.argv.index('--words') + 1]))
        words = d['words'] if isinstance(d, dict) and 'words' in d else [w for s in d.get('segments', []) for w in s.get('words', [])] if isinstance(d, dict) else d
    cues = expand(spec, words)
    write(outp, render(cues, spec['duration'], spec.get('master_db', 0)))
    json.dump(cues, open(os.path.splitext(outp)[0] + '_cues.json', 'w'), indent=1)
    from collections import Counter
    print(outp, len(cues), 'cues', dict(Counter(c['name'] for c in cues)))
