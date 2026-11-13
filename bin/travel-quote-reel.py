#!/usr/bin/env python3
"""Single-shot travel quote sticker, measured against Da3a4RuyiL6."""
import hashlib,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];project=Path(sys.argv[1]).resolve();s=json.loads((project/'spec.json').read_text())
src=Path(s['source']);out=Path(s['output']);out.mkdir(parents=True,exist_ok=True);(out/'phone').mkdir(exist_ok=True)
shots=s.get('shots',[{'source':str(src),'source_in':s['source_in'],'duration':s['duration']}])
denied=(ROOT/'FOOTAGE-DENYLIST.md').read_text();sources=[]
for shot in shots:
 path=Path(shot['source']);digest=hashlib.file_digest(path.open('rb'),'sha256').hexdigest();assert digest not in denied
 sources.append({**shot,'sha256':digest})
def run(*a):subprocess.run([str(x) for x in a],check=True)
im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im);style=s.get('caption_style','card')
if style=='plain-serif':
 size=54;font=ImageFont.truetype(str(ROOT/'fonts/InstrumentSerif-Regular.ttf'),size)
 max_width=max(d.textlength(line,font=font) for line in s['lines'])
 assert max_width<=724, f'caption exceeds centered IG rail-safe width: {max_width:.1f}px'
 top=s.get('caption_top',365);pitch=size+12
 for i,line in enumerate(s['lines'][:-1]):
  width=d.textlength(line,font=font);x=540-width/2
  d.text((x,top+i*pitch),line,font=font,anchor='lt',fill='white',stroke_width=2,stroke_fill='#141414')
 lastw=d.textlength(s['lines'][-1],font=font); emoji_size=34; gap=9
 emoji_w=emoji_size*2+4; group_w=lastw+gap+emoji_w
 group_x=540-group_w/2;last_y=top+(len(s['lines'])-1)*pitch
 # Centre the final line and reference-style emoji pair as one lockup.
 d.text((group_x,last_y),s['lines'][-1],font=font,anchor='lt',fill='white',stroke_width=2,stroke_fill='#141414')
 face=Image.open(ROOT/'.work/da3a4ruyil6/emoji/pleading.png').convert('RGBA').resize((emoji_size,emoji_size),Image.Resampling.LANCZOS)
 heart=Image.open(ROOT/'.work/da3a4ruyil6/emoji/heart.png').convert('RGBA').resize((emoji_size,emoji_size),Image.Resampling.LANCZOS)
 im.alpha_composite(face,(int(group_x+lastw+gap),last_y+4));im.alpha_composite(heart,(int(group_x+lastw+gap+emoji_size+4),last_y+4))
elif style=='gold-italic':
 size=s.get('font_size',44);font=ImageFont.truetype(str(ROOT/'fonts/Montserrat-ExtraBold.ttf'),size)
 top=s.get('caption_top',1356);pitch=s.get('line_pitch',52);shear=0.16
 # Match the reference's warm-yellow, bold italic treatment with a clean black
 # keyline. Each line is rendered and slanted independently, then centered.
 for i,line in enumerate(s['lines']):
  width=int(d.textlength(line,font=font))+24;height=size+24
  line_im=Image.new('RGBA',(width,height));line_d=ImageDraw.Draw(line_im)
  line_d.text((12,5),line,font=font,anchor='lt',fill='#F7D002',stroke_width=3,stroke_fill='#080808')
  line_im=line_im.transform((width+int(height*shear),height),Image.Transform.AFFINE,(1,-shear,0,0,1,0),resample=Image.Resampling.BICUBIC)
  box=line_im.getchannel('A').getbbox();assert box
  line_im=line_im.crop(box)
  assert line_im.width<=724, f'caption exceeds centered IG rail-safe width: {line_im.width}px'
  im.alpha_composite(line_im,(540-line_im.width//2,top+i*pitch))
else:
 size=46
 while True:
  font=ImageFont.truetype(str(ROOT/'fonts/Oswald-VF.ttf'),size)
  if max(d.textlength(line,font=font) for line in s['lines'])<=660 and d.textlength(s['lines'][-1],font=font)<=610:break
  size-=1
 top=370;pitch=size+14;bottom=top+34+pitch*len(s['lines'])
 d.rounded_rectangle((178,top,901,bottom),radius=20,fill='white')
 inline=s.get('heart_inline',False)
 if not inline:d.rounded_rectangle((488,bottom-18,592,bottom+72),radius=20,fill='white')
 for i,line in enumerate(s['lines']):
  width=d.textlength(line,font=font);x=540-width/2
  d.text((x,top+22+i*pitch),line,font=font,anchor='lt',fill='#141414')
 lastw=d.textlength(s['lines'][-1],font=font)
 heart=Image.open(ROOT/'.work/da3a4ruyil6/emoji/heart.png').convert('RGBA').resize((42 if inline else 54,42 if inline else 54),Image.Resampling.LANCZOS)
 im.alpha_composite(heart,(int(540+lastw/2+12),top+22+(len(s['lines'])-1)*pitch) if inline else (513,bottom+6))
 if not inline:
  face=Image.open(ROOT/'.work/da3a4ruyil6/emoji/pleading.png').convert('RGBA').resize((42,42),Image.Resampling.LANCZOS)
  im.alpha_composite(face,(int(540+lastw/2+7),top+22+(len(s['lines'])-1)*pitch-1))
bbox=im.getchannel('A').getbbox();assert bbox[0]>=59 and bbox[2]<=918 and bbox[1]>=278 and bbox[3]<=1536 and bbox[2]-bbox[0]<=724
im.save(project/'caption.png');(project/'type-measurement.json').write_text(json.dumps({'font':'Instrument Serif' if style=='plain-serif' else ('Montserrat ExtraBold with 0.16 shear' if style=='gold-italic' else 'Oswald regular'),'font_size':size,'caption_alpha_bbox':bbox,'adaptation':'plain-serif' if style=='plain-serif' else ('reference-matched gold italic with black keyline' if style=='gold-italic' else '724px rail-safe white quote panel')},indent=2))
inputs=[];filters=[]
for i,shot in enumerate(shots):
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',shot['source']]));v=next(x for x in probe['streams'] if x['codec_type']=='video')
 assert shot['source_in']+shot['duration']<=float(probe['format']['duration'])
 inputs+=['-ss',shot['source_in'],'-t',shot['duration'],'-i',shot['source']]
 vf='setpts=PTS-STARTPTS,fps=30,'
 if v.get('color_transfer') in ('arib-std-b67','smpte2084'):vf+='zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,'
 vf+='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p'
 filters.append(f'[{i}:v:0]{vf}[s{i}]')
filters.append(''.join(f'[s{i}]' for i in range(len(shots)))+f'concat=n={len(shots)}:v=1:a=0[v]')
dur=s['duration'];master=out/(s['name']+'.mp4')
filters.append(f'[v][{len(shots)}:v]overlay=0:0:format=auto,format=yuv420p[p]');filters.append(f'[{len(shots)+1}:a:0]atrim=0:{dur},asetpts=PTS-STARTPTS,afade=t=out:st={dur-.1}:d=0.1,loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.79:level=false[a]')
run('ffmpeg','-nostdin','-y','-v','error',*inputs,'-loop','1','-i',project/'caption.png','-i',s['music'],'-filter_complex',';'.join(filters),'-map','[p]','-map','[a]','-t',dur,'-r','30','-c:v','libx264','-crf','15','-preset','slow','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','256k','-ac','2','-ar','44100','-movflags','+faststart',master)
run('bash',ROOT/'bin/export-ig.sh',master,out/(s['name']+'_IG.mp4'))
run('ffmpeg','-nostdin','-y','-v','error','-i',master,'-vf','scale=608:1080','-r','30','-c:v','libx264','-crf','26','-preset','fast','-profile:v','baseline','-level','3.1','-pix_fmt','yuv420p','-c:a','aac','-ac','2','-ar','44100','-b:a','128k','-movflags','+faststart',out/'phone'/master.name)
run('python3',ROOT/'bin/ig-safe.py','view',master,out/'safe-view.jpg','0','7.5','15')
(project/(s['name']+'-receipt.json')).write_text(json.dumps({'sources':sources,'music_source':s['reference'],'music_range':[0,dur],'master':str(master),'published':False},indent=2))
