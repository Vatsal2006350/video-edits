#!/usr/bin/env python3
"""timeline-reel.py <spec.json> — build a reel where every cut sits on an exact timestamp.
spec: {audio, out, segments:[{kind:video|photo|freeze, src, ss, start, end, caption, skull_at}]}
Segment durations come from (end-start), so cuts land exactly on the beats you choose."""
import json, subprocess, sys, os, tempfile, shutil
S=json.load(open(sys.argv[1]))
T=tempfile.mkdtemp()
FILL="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
parts=[]
for i,g in enumerate(S['segments']):
    dur=round(g['end']-g['start'],3)
    out=f"{T}/p{i}.mp4"
    vf=f"{FILL},format=yuv420p,fps=30"
    if g['kind']=='video':
        cmd=['ffmpeg','-nostdin','-y','-v','error','-ss',str(g.get('ss',0)),'-t',str(dur),'-i',g['src'],
             '-vf',f"{FILL},eq=contrast=1.05:saturation=1.08,format=yuv420p,fps=30"]
    elif g['kind']=='photo':
        cmd=['ffmpeg','-nostdin','-y','-v','error','-framerate','30','-loop','1','-t',str(dur),'-i',g['src'],
             '-vf',f"{FILL},zoompan=z='min(1.06,1+0.0008*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p"]
    else:  # freeze: greyscale still, skull fades/scales in after skull_at seconds
        still=f"{T}/f{i}.png"
        # -ss only for video sources; on a still image it seeks past the single frame
        pre=['-ss',str(g['ss'])] if (g.get('ss') and not g['src'].lower().endswith(('.jpg','.jpeg','.png','.heic'))) else []
        subprocess.run(['ffmpeg','-nostdin','-y','-v','error']+pre+['-i',g['src'],'-vframes','1',
                        '-vf',f"{FILL},hue=s=0,eq=contrast=1.24:brightness=-0.05",still],check=True)
        sk=g.get('skull_at',0.35)
        cmd=['ffmpeg','-nostdin','-y','-v','error','-framerate','30','-loop','1','-t',str(dur),'-i',still,
             '-i',S['skull'],'-filter_complex',
             f"[0:v][1:v]overlay=0:0:enable='gte(t,{sk})',"
             f"zoompan=z='min(1.05,1+0.0014*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[v]",
             '-map','[v]']
    cmd+=['-an','-r','30','-fps_mode','cfr','-c:v','libx264','-crf','17','-preset','fast',out]
    subprocess.run(cmd,check=True)
    if g.get('caption'):
        o2=f"{T}/c{i}.mp4"
        subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-i',out,'-i',g['caption'],
                        '-filter_complex','[0:v][1:v]overlay=0:0,format=yuv420p[v]','-map','[v]',
                        '-an','-r','30','-fps_mode','cfr','-c:v','libx264','-crf','17',o2],check=True)
        out=o2
    parts.append(out); print(f"  {g['start']:5.2f}-{g['end']:5.2f}s ({dur:4.2f}s) {g['kind']:6} {os.path.basename(g['src'])[:34]}")
with open(f"{T}/l.txt","w") as fh:
    for p in parts: fh.write(f"file '{p}'\n")
vid=f"{T}/v.mp4"
subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-f','concat','-safe','0','-i',f"{T}/l.txt",
                '-c:v','libx264','-crf','16','-r','30','-fps_mode','cfr','-an',vid],check=True)
d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',vid],
                       capture_output=True,text=True).stdout)
ass=float(S.get('audio_ss',0) or 0)
apre=['-ss',str(ass)] if ass>0 else []
subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-i',vid]+apre+['-i',S['audio'],
                '-map','0:v','-map','1:a','-t',str(d),'-c:v','copy','-c:a','aac','-b:a','192k',
                '-af',f"afade=t=out:st={max(0,d-0.6):.2f}:d=0.6",'-movflags','+faststart',S['out']],check=True)
shutil.rmtree(T)
print(f"[timeline] -> {S['out']}  {d:.2f}s")
