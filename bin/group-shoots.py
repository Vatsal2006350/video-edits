#!/usr/bin/env python3
"""group-shoots.py <dir> — cluster clips into shoots by date + what you're wearing.
Samples the torso region of each clip and compares dominant colour, so multiple
takes from the same session can be intercut as one continuous piece."""
import subprocess, os, sys, glob, json, colorsys
from collections import defaultdict

def torso_colour(path):
    """dominant hue/sat/val of the centre-lower frame = the shirt"""
    out='/tmp/_tc.ppm'
    subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-ss','1','-i',path,'-vframes','1',
                    '-vf','crop=iw*0.42:ih*0.26:iw*0.29:ih*0.46,scale=24:24','-f','rawvideo',
                    '-pix_fmt','rgb24','-'],capture_output=True)
    r=subprocess.run(['ffmpeg','-nostdin','-v','error','-ss','1','-i',path,'-vframes','1',
                      '-vf','crop=iw*0.42:ih*0.26:iw*0.29:ih*0.46,scale=16:16','-f','rawvideo',
                      '-pix_fmt','rgb24','-'],capture_output=True).stdout
    if len(r)<768: return None
    px=[(r[i],r[i+1],r[i+2]) for i in range(0,768,3)]
    n=len(px)
    rr=sum(p[0] for p in px)/n; gg=sum(p[1] for p in px)/n; bb=sum(p[2] for p in px)/n
    h,s,v=colorsys.rgb_to_hsv(rr/255,gg/255,bb/255)
    return {'rgb':(round(rr),round(gg),round(bb)),'h':round(h,3),'s':round(s,3),'v':round(v,3)}

def close(a,b):
    if not a or not b: return False
    dh=min(abs(a['h']-b['h']), 1-abs(a['h']-b['h']))
    return dh<0.07 and abs(a['s']-b['s'])<0.20 and abs(a['v']-b['v'])<0.20

if __name__=='__main__':
    d=sys.argv[1] if len(sys.argv)>1 else os.path.expanduser('~/Downloads/photos-broll/talking')
    files=sorted([f for e in ('*.MOV','*.mov','*.mp4') for f in glob.glob(os.path.join(d,e))])
    info=[]
    for f in files:
        b=os.path.basename(f); day=b[:4]
        c=torso_colour(f)
        info.append({'file':b,'day':day,'colour':c})
    # group: same day AND similar clothing
    groups=[]
    for it in info:
        placed=False
        for g in groups:
            if g['day']==it['day'] and close(g['colour'],it['colour']):
                g['files'].append(it['file']); placed=True; break
        if not placed:
            groups.append({'day':it['day'],'colour':it['colour'],'files':[it['file']]})
    groups.sort(key=lambda g:-len(g['files']))
    for g in groups:
        c=g['colour']
        tag=f"rgb{c['rgb']}" if c else "n/a"
        print(f"\nSHOOT {g['day']}  {tag}  ({len(g['files'])} clip{'s' if len(g['files'])>1 else ''})")
        for f in g['files']: print(f"   {f}")
    json.dump(groups,open('/tmp/shoots.json','w'),indent=1,default=str)
