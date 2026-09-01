#!/usr/bin/env python3
"""audio-map.py <audio> — report structure: RMS envelope, the drop, and beats after it."""
import sys, subprocess, numpy as np
sr=22050
raw=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',sys.argv[1],'-ac','1','-ar',str(sr),'-f','wav','-'],
                   capture_output=True).stdout
i=raw.find(b'data'); x=np.frombuffer(raw[i+8:],dtype=np.int16).astype(np.float32)/32768
hop=int(sr*0.05)
rms=np.array([np.sqrt((x[j:j+hop]**2).mean()) for j in range(0,len(x)-hop,hop)])
t=np.arange(len(rms))*0.05
# drop = largest sustained jump in energy
win=int(0.6/0.05)
best=(0,0.0)
for k in range(win,len(rms)-win):
    before=rms[k-win:k].mean(); after=rms[k:k+win].mean()
    if before>1e-6:
        r=after/before
        if r>best[1]: best=(k,r)
print(f"duration      {len(x)/sr:.2f}s")
print(f"DROP at       {best[0]*0.05:.2f}s  (energy x{best[1]:.1f})")
print("envelope (0.5s steps):")
for k in range(0,len(rms),10):
    bar='#'*int(rms[k]/max(rms.max(),1e-9)*40)
    print(f"  {t[k]:5.1f}s {bar}")
