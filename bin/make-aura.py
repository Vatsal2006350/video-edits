#!/usr/bin/env python3
"""make-aura.py — build a 'disappeared' reel: hook -> drop -> achievement cards,
each card flipping colour->greyscale+skull on a beat.  Audio is trimmed so the
drop lands right after the hook."""
import json, os, subprocess, sys, tempfile

H=os.path.expanduser('~'); WS=f'{H}/Code/video-edits'; Y=f'{WS}/receipts'
EXPORT=f'{H}/Downloads/reel-exports'; MU=f'{H}/Downloads/music-rf'
os.makedirs(EXPORT,exist_ok=True)

def dur(p):
    return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
        '-of','csv=p=0',p],capture_output=True,text=True).stdout.strip())

def drop_of(p):
    out=subprocess.run([sys.executable,f'{WS}/bin/audio-map.py',p],capture_output=True,text=True).stdout
    for l in out.splitlines():
        if l.startswith('DROP at'): return float(l.split()[2].rstrip('s'))
    return 2.0

def beats(p, limit=40):
    o=subprocess.run([sys.executable,f'{WS}/bin/beats.py',p,str(limit)],capture_output=True,text=True).stdout
    return [float(x) for x in o.split()]

def build(name, track, hook, hook_ss, cards, caption, hook_lead=3.0, tail=2.4):
    src=f'{MU}/{track}' if not track.startswith('/') else track
    d=drop_of(src)
    ss=max(0, d-hook_lead)                       # trim so the drop lands after the hook
    cut=f'{MU}/aura_{name}.m4a'
    subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-ss',str(ss),'-i',src,
                    '-t','22','-c:a','aac','-b:a','192k',cut],check=True)
    B=[b for b in beats(cut) if b>hook_lead-0.35]
    if not B: B=[hook_lead]
    segs=[{'kind':'video','src':hook,'ss':hook_ss,'start':0.0,'end':round(B[0],3),
           'caption':caption,'skull_at':0.05}]
    t=B[0]; bi=1
    for c in cards:
        nxt=[b for b in B[bi:] if b>t+1.45]
        colour_end = nxt[0] if nxt else t+1.7
        bi=B.index(colour_end)+1 if colour_end in B else bi+1
        nxt2=[b for b in B[bi:] if b>colour_end+0.95]
        grey_end = nxt2[0] if nxt2 else colour_end+1.2
        bi=B.index(grey_end)+1 if grey_end in B else bi+1
        kind='video' if c['src'].lower().endswith(('.mov','.mp4')) else 'photo'
        segs.append({'kind':kind,'src':c['src'],'ss':c.get('ss',0),
                     'start':round(t,3),'end':round(colour_end,3),'skull_at':0.05})
        segs.append({'kind':'freeze','src':c['src'],'ss':c.get('ss',0),
                     'start':round(colour_end,3),'end':round(grey_end,3),'skull_at':0.05})
        t=grey_end
    segs[-1]['end']=round(min(dur(cut), segs[-1]['end']+tail),3)
    spec={'audio':cut,'audio_ss':0,'skull':f'{Y}/skull.png',
          'out':f'{EXPORT}/{name}.mp4','segments':segs}
    sp=f'{tempfile.gettempdir()}/{name}.json'; json.dump(spec,open(sp,'w'))
    r=subprocess.run([sys.executable,f'{WS}/bin/timeline-reel.py',sp],capture_output=True,text=True)
    json.dump(spec,open(f'{WS}/projects/{name}.json','w'),indent=1)
    ok=os.path.exists(spec['out'])
    print(f"{'ok ' if ok else 'FAIL'} {name:22} {track:22} drop@{d:5.1f}s -> {len(segs)} segs, "
          f"{dur(spec['out']) if ok else 0:.2f}s")
    return ok
