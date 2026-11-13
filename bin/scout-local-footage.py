#!/usr/bin/env python3
"""Inspect original footage with HDR-aware samples and a hash denylist check."""
import argparse, hashlib, io, json, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
def run(*args):
    return subprocess.check_output(args, stderr=subprocess.DEVNULL)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('output')
    p.add_argument('sources', nargs='+')
    a = p.parse_args()
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    denied = (ROOT/'FOOTAGE-DENYLIST.md').read_text()
    hashes = set(re.findall(r'\b[a-f0-9]{64}\b', denied))
    tiles, records = [], []
    font = ImageFont.truetype(str(ROOT/'fonts/Montserrat-Bold.ttf'), 17)
    for source in a.sources:
        src = Path(source)
        if src.stem in denied:
            continue
        h = hashlib.sha256()
        with src.open('rb') as f:
            for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
        if h.hexdigest() in hashes: continue
        data = json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)))
        v = next(x for x in data['streams'] if x['codec_type']=='video')
        duration = float(data['format']['duration'])
        transfer = v.get('color_transfer')
        vf = 'scale=280:498:force_original_aspect_ratio=decrease,pad=280:498:(ow-iw)/2:(oh-ih)/2'
        if transfer in ('arib-std-b67','smpte2084'):
            vf = 'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'+vf
        record = {'source':str(src),'sha256':h.hexdigest(),'duration':duration,'transfer':transfer,'samples':[]}
        for fraction in (.22,.62):
            t = min(duration-.1, duration*fraction)
            try:
                raw = run('ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',str(src),'-vf',vf,'-frames:v','1','-f','image2pipe','-vcodec','png','-')
                im = Image.open(io.BytesIO(raw)).convert('RGB')
            except subprocess.CalledProcessError: continue
            tile = Image.new('RGB',(280,546),(15,15,15)); tile.paste(im,(0,0))
            ImageDraw.Draw(tile).text((8,502),f'{src.name}\n{t:.2f}s / {duration:.1f}s',font=font,fill='white')
            n = len(tiles)+1; tiles.append(tile)
            im.save(out/f'frame-{n:03d}.jpg')
            record['samples'].append({'tile':n,'seek':round(t,3)})
        records.append(record)
    for start in range(0,len(tiles),12):
        group = tiles[start:start+12]
        sheet = Image.new('RGB',(280*6,546*((len(group)+5)//6)),(15,15,15))
        for i,im in enumerate(group): sheet.paste(im,((i%6)*280,(i//6)*546))
        sheet.save(out/f'scout-{start//12+1:02d}.jpg',quality=88)
    (out/'inventory.json').write_text(json.dumps(records,indent=2))
    print(f'{len(records)} checked sources; {len(tiles)} inspected samples in {out}')

if __name__=='__main__': main()
