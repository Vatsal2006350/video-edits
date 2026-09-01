#!/usr/bin/env python3
"""beats.py <audio> [max_seconds] — detect beat times via spectral-flux onsets.
Prints beat timestamps (seconds), one per line. Used to cut video on the beat."""
import sys, subprocess, wave, numpy as np

def load(path, sr=22050, limit=None):
    cmd=['ffmpeg','-nostdin','-v','error','-i',path,'-ac','1','-ar',str(sr)]
    if limit: cmd+=['-t',str(limit)]
    cmd+=['-f','wav','-']
    raw=subprocess.run(cmd,capture_output=True).stdout
    i=raw.find(b'data'); x=np.frombuffer(raw[i+8:],dtype=np.int16).astype(np.float32)/32768
    return x, sr

def beats(x, sr, hop=512, win=1024):
    n=(len(x)-win)//hop
    spec=np.abs(np.fft.rfft(np.stack([x[i*hop:i*hop+win]*np.hanning(win) for i in range(n)]),axis=1))
    flux=np.maximum(0, np.diff(spec,axis=0)).sum(axis=1)
    flux=(flux-flux.mean())/(flux.std()+1e-9)
    # adaptive threshold peak-pick
    w=int(0.25*sr/hop)
    out=[]
    for i in range(w, len(flux)-w):
        loc=flux[i-w:i+w]
        if flux[i]==loc.max() and flux[i]>loc.mean()+0.7:
            t=i*hop/sr
            if not out or t-out[-1] > 0.22: out.append(t)
    return out

if __name__=='__main__':
    lim=float(sys.argv[2]) if len(sys.argv)>2 else None
    x,sr=load(sys.argv[1], limit=lim)
    for t in beats(x,sr): print(f'{t:.3f}')
