#!/usr/bin/env python3
"""Build a timestamp-verified daylight-evening reference reel from a JSON spec."""
import hashlib,json,subprocess,sys,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
project=Path(sys.argv[1]).resolve();s=json.loads((project/'spec.json').read_text())
src=Path(s['source']); out=Path(s['output']);out.mkdir(parents=True,exist_ok=True);(out/'phone').mkdir(exist_ok=True)
denied=(ROOT/'FOOTAGE-DENYLIST.md').read_text();digest=hashlib.file_digest(src.open('rb'),'sha256').hexdigest()
assert s['uuid'] not in denied and digest not in denied
def run(*args):subprocess.run([str(a) for a in args],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(src)]))
assert probe['format']['tags']['com.apple.quicktime.creationdate']==s['verified_creationdate']
im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im);size=76
while True:
 f=ImageFont.truetype(str(ROOT/'fonts/InstrumentSerif-Regular.ttf'),size)
 if max(d.textbbox((0,0),line,font=f,stroke_width=3)[2] for line in s['lines'])<=714:break
 size-=1
for i,line in enumerate(s['lines']):
 b=d.textbbox((0,0),line,font=f,stroke_width=3);x=540-(b[0]+b[2])/2;y=500+i*size-b[1]
 d.text((x,y),line,font=f,fill='white',stroke_width=3,stroke_fill='#171717')
bbox=im.getchannel('A').getbbox();assert bbox[0]>=59 and bbox[2]<=918 and bbox[1]>=278 and bbox[3]<=1536 and bbox[2]-bbox[0]<=724
im.save(project/'caption.png');(project/'type-measurement.json').write_text(json.dumps({'font_size':size,'alpha_bbox':bbox,'shadow':False},indent=2))
vf='trim=start=0:end=6,setpts=PTS/0.6,fps=30,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,scale=1080:1920,format=yuv420p'
master=out/(s['name']+'.mp4')
run('ffmpeg','-nostdin','-y','-v','error','-i',src,'-loop','1','-i',project/'caption.png','-i',s['music'],'-filter_complex',f'[0:v:0]{vf}[v];[v][1:v]overlay=0:0:format=auto,format=yuv420p[p];[2:a:0]atrim=0:10,asetpts=PTS-STARTPTS,afade=t=out:st=9.9:d=0.1,loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.79:level=false[a]','-map','[p]','-map','[a]','-t','10','-r','30','-c:v','libx264','-crf','15','-preset','slow','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','256k','-ac','2','-ar','44100','-movflags','+faststart',master)
run('bash',ROOT/'bin/export-ig.sh',master,out/(s['name']+'_IG.mp4'))
run('ffmpeg','-nostdin','-y','-v','error','-i',master,'-vf','scale=608:1080','-r','30','-c:v','libx264','-crf','26','-preset','fast','-profile:v','baseline','-level','3.1','-pix_fmt','yuv420p','-c:a','aac','-ac','2','-ar','44100','-b:a','128k','-movflags','+faststart',out/'phone'/master.name)
run('python3',ROOT/'bin/ig-safe.py','view',master,out/'safe-view.jpg','0','5','9.8')
(project/'receipt.json').write_text(json.dumps({'source_sha256':digest,'uuid':s['uuid'],'source_range':[0,6],'speed':0.6,'duration':10,'music_range':[0,10],'master':str(master),'published':False},indent=2))
