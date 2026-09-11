#!/usr/bin/env python3
"""For each clip, find the steadiest window of a given length.
Decodes small greyscale frames, scores frame-to-frame motion, and reports the
lowest-motion window plus rough colour/contrast stats so shaky takes can be avoided."""
import subprocess, sys, json, os, glob, tempfile
import numpy as np

W,H,FPS = 96,171,6
WIN = float(sys.argv[1]) if len(sys.argv)>1 else 1.4
roots = sys.argv[2:] or [os.path.expanduser('~/Downloads/photos-broll')]

def frames(path):
    p=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',path,
                      '-vf',f'fps={FPS},scale={W}:{H}','-pix_fmt','gray','-f','rawvideo','-'],
                     capture_output=True)
    a=np.frombuffer(p.stdout,dtype=np.uint8)
    n=len(a)//(W*H)
    return a[:n*W*H].reshape(n,H,W).astype(np.float32) if n else None

def colour(path,t):
    p=subprocess.run(['ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',path,'-frames:v','1',
                      '-vf',f'scale={W}:{H}','-pix_fmt','rgb24','-f','rawvideo','-'],capture_output=True)
    a=np.frombuffer(p.stdout,dtype=np.uint8)
    if len(a)<W*H*3: return 0.0,0.0
    a=a[:W*H*3].reshape(H,W,3).astype(np.float32)
    sat=float(np.mean(a.max(2)-a.min(2)))
    con=float(np.std(a.mean(2)))
    return sat,con

out=[]
files=[]
for r in roots:
    for ext in ('MOV','mov','mp4','MP4'):
        files+=glob.glob(f'{r}/**/*.{ext}',recursive=True)
files=sorted(set(files))
for f in files:
    g=frames(f)
    if g is None or len(g)<int(WIN*FPS)+2: continue
    d=np.abs(np.diff(g,axis=0)).mean(axis=(1,2))       # per-frame motion
    k=int(WIN*FPS)
    if len(d)<k: continue
    csum=np.concatenate([[0],np.cumsum(d)])
    means=(csum[k:]-csum[:-k])/k                        # rolling mean motion
    i=int(np.argmin(means))
    t=i/FPS
    sat,con=colour(f,t+WIN/2)
    out.append({'file':f,'best_t':round(t,2),'motion':round(float(means[i]),3),
                'motion_med':round(float(np.median(means)),3),
                'sat':round(sat,1),'con':round(con,1),'dur':round(len(g)/FPS,1)})
out.sort(key=lambda x:x['motion'])
work = os.environ.get('VIDEO_EDITS_WORK_ROOT', os.path.join(tempfile.gettempdir(), 'video-edits'))
os.makedirs(work, exist_ok=True)
json.dump(out, open(os.path.join(work, 'stability.json'), 'w'), indent=1)
print(f"scanned {len(out)} clips  (window {WIN}s)")
for o in out[:24]:
    print(f"  motion {o['motion']:6.2f}  sat {o['sat']:5.1f}  con {o['con']:5.1f}  @{o['best_t']:5.1f}s  {os.path.basename(o['file'])[:52]}")
