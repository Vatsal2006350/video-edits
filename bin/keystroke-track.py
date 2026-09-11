#!/usr/bin/env python3
"""Build a keystroke audio track from typewriter.py's keystrokes.json.

The IG reference (Dcq29SSRGLV) has NO typewriter sound -- this is an addition Vatsal asked
for, so it is a separate step, not baked into the renderer. Cycles three synthesised keys
(sfx/key1-3.wav, 45ms mechanical clicks) with slight random gain so a run does not sound
like one sample looped. Output is a mono 48k wav the same length as the reel; mix it under
the dialogue with ffmpeg amix.

  keystroke-track.py <keystrokes.json> <dur_seconds> <out.wav> [gain=0.35]
"""
import sys, json, wave, numpy as np, os
ev = json.load(open(sys.argv[1])); dur = float(sys.argv[2]); out = sys.argv[3]
gain = float(sys.argv[4]) if len(sys.argv) > 4 else 0.35
sr = 48000
keys = []
for i in (1, 2, 3):
    with wave.open(os.path.expanduser(f'~/Code/video-edits/sfx/key{i}.wav'), 'rb') as w:
        keys.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767)
track = np.zeros(int(sr * dur) + sr, dtype=np.float32)
rng = np.random.default_rng(7)
for n, (t, _) in enumerate(ev):
    k = keys[n % 3]; g = gain * rng.uniform(0.75, 1.0)
    i0 = int(t * sr); track[i0:i0 + len(k)] += k[:len(track) - i0] * g
track = np.clip(track[:int(sr * dur)], -1, 1)
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((track * 32767).astype(np.int16).tobytes())
print(f'{len(ev)} keystrokes -> {out}')
