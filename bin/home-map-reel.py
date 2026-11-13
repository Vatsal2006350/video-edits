#!/usr/bin/env python3
"""Reference-matched lecture → home-map reel; prepare, visually review, then render."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TONEMAP = 'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'

def run(args):
    subprocess.run([str(x) for x in args], check=True)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def layer(lines, path, emoji=False):
    im = Image.new('RGBA',(1080,1920))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf',50)
    for i, text in enumerate(lines):
        box = draw.textbbox((0,0),text,font=font,stroke_width=3)
        width = box[2]-box[0]
        assert width <= 724
        extra = 55 if emoji else 0
        x = (1080-width-extra)//2-box[0]
        position = (x,382+i*56-box[1])
        draw.text(position,text,font=font,fill='white',stroke_width=4,stroke_fill='black')
        draw.text(position,text,font=font,fill='white',stroke_width=1,stroke_fill='white')
        if emoji:
            face = Image.new('RGBA',(180,180))
            ef = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc',160)
            ImageDraw.Draw(face).text((0,0),'🥺',font=ef,embedded_color=True)
            face = face.crop(face.getbbox()).resize((43,43),Image.Resampling.LANCZOS)
            im.alpha_composite(face,(int(x+box[2]+12),382))
    bbox = im.getbbox()
    assert 59 <= bbox[0] and bbox[2] <= 918 and 278 <= bbox[1] and bbox[3] <= 1536,bbox
    im.save(path)
    return {'text':'\n'.join(lines)+(' 🥺' if emoji else ''),'font':'Arial Bold Italic','size':50,
            'stroke':3,'alpha_bbox':bbox}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    parser.add_argument('--render-reviewed',action='store_true')
    a = parser.parse_args()
    work = a.project.resolve(); work.mkdir(parents=True,exist_ok=True)
    spec = json.loads((work/'spec.json').read_text())
    denied = set(re.findall(r'\b[a-f0-9]{64}\b',(ROOT/'FOOTAGE-DENYLIST.md').read_text()))
    for key in ('lecture','map'):
        source = Path(spec[key]); h = hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
        assert h not in denied
        spec[key+'_sha256'] = h
    drop = round(spec['drop']*30)/30
    duration = round(spec['duration']*30)/30
    map_duration = duration-drop
    raw = probe(spec['lecture'])
    video = next(s for s in raw['streams'] if s['codec_type']=='video')
    vf = (TONEMAP if video.get('color_transfer') in ('arib-std-b67','smpte2084') else '')
    vf += 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30'
    assert spec['lecture_in']+drop <= float(raw['format']['duration'])
    map_speed = (spec['map_out']-spec['map_in'])/map_duration
    map_vf = f'crop=1266:2250:27:300,setpts=(PTS-STARTPTS)/{map_speed},scale=1080:1920,setsar=1,fps=30'
    texts = [layer(['“The lecture is over.','You may go home now.”'],work/'lecture-text.png'),
             layer(['Home?'],work/'home-text.png',emoji=True)]
    (work/'safe-layers.json').write_text(json.dumps(texts,indent=2))
    if not a.render_reviewed:
        for i, (key, start, span, filters) in enumerate([
                ('lecture',spec['lecture_in'],drop,vf),
                ('map',spec['map_in'],spec['map_out']-spec['map_in'],map_vf.split(',setpts')[0]+',scale=1080:1920')]):
            for label, fraction in [('start',.02),('middle',.5),('end',.98)]:
                run(['ffmpeg','-nostdin','-y','-v','error','-ss',start+span*fraction,'-i',spec[key],
                     '-vf',filters,'-frames:v','1',work/f'{key}-{label}.jpg'])
        (work/'spec.json').write_text(json.dumps(spec,indent=2))
        print('Prepared layers and exact-trim review frames. Review before --render-reviewed.')
        return
    for key, seek, frames, filters, text in [
            ('lecture',spec['lecture_in'],round(drop*30),vf,'lecture-text.png'),
            ('map',spec['map_in'],round(map_duration*30),map_vf,'home-text.png')]:
        run(['ffmpeg','-nostdin','-y','-v','error','-ss',seek,'-i',spec[key],'-loop','1','-i',work/text,
             '-filter_complex',f'[0:v]{filters}[bg];[bg][1:v]overlay=0:0:shortest=1[v]',
             '-map','[v]','-an','-frames:v',frames,'-c:v','libx264','-threads','3','-preset','slow',
             '-crf','15','-profile:v','high','-pix_fmt','yuv420p',
             '-color_trc','bt709','-colorspace','bt709','-color_primaries','bt709',work/f'{key}.mp4'])
    (work/'concat.txt').write_text(f"file '{work/'lecture.mp4'}'\nfile '{work/'map.mp4'}'\n")
    run(['ffmpeg','-nostdin','-y','-v','error','-f','concat','-safe','0','-i',work/'concat.txt','-c','copy',work/'picture.mp4'])
    out = Path(spec['output']); out.parent.mkdir(parents=True,exist_ok=True)
    run(['ffmpeg','-nostdin','-y','-v','error','-i',work/'picture.mp4','-i',spec['audio'],
         '-map','0:v:0','-map','1:a:0','-t',duration,'-c:v','copy',
         '-af','loudnorm=I=-14:TP=-2:LRA=11','-c:a','aac','-b:a','256k','-ar','44100','-ac','2',
         '-movflags','+faststart',out])
    run(['bash',ROOT/'bin/export-ig.sh',out,out.with_name(out.stem+'_IG.mp4')])
    phone = out.parent/'phone'/out.name; phone.parent.mkdir(exist_ok=True)
    run(['ffmpeg','-nostdin','-y','-v','error','-i',out,'-vf','scale=608:1080','-c:v','libx264',
         '-profile:v','baseline','-level:v','3.1','-preset','fast','-crf','26','-c:a','aac','-ar','44100',
         '-ac','2','-b:a','128k','-movflags','+faststart',phone])
    run(['python3',ROOT/'bin/ig-safe.py','view',out,work/'safe-view.jpg','1',drop-.1,drop+.1,duration-.3])
    spec.update(rendered_drop=drop,rendered_duration=duration,map_speed=map_speed,published=False,
                review='source start/middle/end frames inspected before render',
                privacy='cropped phone chrome; stopped at city scale before street-level address')
    (work/'receipt.json').write_text(json.dumps(spec,indent=2))
    print(phone)

if __name__ == '__main__': main()
