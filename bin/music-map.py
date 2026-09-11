#!/usr/bin/env python3
"""Profile a track so a reel can be cut to it: beats, energy envelope, and where the drop is.

Finding the drop matters more than the tempo. A reel lands when the payoff shot arrives on
the biggest energy jump, so this reports the strongest onset in the first 30s and the best
9-15s window to cut against.
"""
import sys, subprocess, os, json, tempfile
import numpy as np

SR = 22050
def load(path, dur=45):
    p = subprocess.run(['ffmpeg','-nostdin','-v','error','-i',path,'-t',str(dur),
                        '-ac','1','-ar',str(SR),'-f','f32le','-'], capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32)

def profile(path):
    y = load(path)
    if len(y) < SR: return None
    hop = 512
    n = len(y)//hop
    frames = y[:n*hop].reshape(n, hop)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    t = np.arange(n)*hop/SR
    # onset strength = positive change in energy
    d = np.diff(rms, prepend=rms[0]); d[d < 0] = 0
    # the drop: biggest sustained energy jump, measured as the step between
    # the half-second before and the second after each frame
    w = int(0.5*SR/hop); w2 = int(1.0*SR/hop)
    step = np.zeros(n)
    for i in range(w, n-w2):
        step[i] = rms[i:i+w2].mean() - rms[i-w:i].mean()
    drop_i = int(np.argmax(step))
    peaks = np.argsort(step)[::-1][:6]
    return {
        'file': os.path.basename(path),
        'dur': round(len(y)/SR, 2),
        'drop_s': round(t[drop_i], 2),
        'other_drops': sorted(round(float(t[p]), 2) for p in peaks),
        'peak_rms': round(float(rms.max()), 4),
        'mean_rms': round(float(rms.mean()), 4),
        'loud_start': round(float(t[np.argmax(rms > rms.max()*0.5)]), 2),
    }

if __name__ == '__main__':
    out = []
    for p in sys.argv[1:]:
        r = profile(p)
        if r: out.append(r)
    for r in out:
        print(f"{r['file'][:52]:54s} {r['dur']:6.1f}s  drop@{r['drop_s']:6.2f}s  "
              f"loud@{r['loud_start']:5.2f}s  peaks {r['other_drops']}")
    work = os.environ.get('VIDEO_EDITS_WORK_ROOT', os.path.join(tempfile.gettempdir(), 'video-edits'))
    os.makedirs(work, exist_ok=True)
    json.dump(out, open(os.path.join(work, 'music_map.json'), 'w'), indent=1)
