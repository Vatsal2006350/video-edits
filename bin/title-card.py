#!/usr/bin/env python3
"""Opening card: elegant serif italic lead-in, then a big bold line + the school mark."""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
c=json.loads(sys.argv[1]); F=c['fonts']; OUT=c['outdir']; DUR=c['dur']; FPS=30
os.makedirs(OUT,exist_ok=True)
MAIZE=(255,203,5); W,H=1080,1920
serif=ImageFont.truetype(f"{F}/Playfair-Italic-Med.ttf",100)
bold =ImageFont.truetype(f"{F}/Poppins-Bold.ttf",112)
logo=Image.open(c['logo']).convert('RGBA'); lw=230
logo=logo.resize((lw,round(lw*logo.height/logo.width)),Image.LANCZOS)
L1,L2="how i got into a","TOP 10 CS SCHOOL"
while bold.getbbox(L2)[2]-bold.getbbox(L2)[0] > 960:
    bold=ImageFont.truetype(f"{F}/Poppins-Bold.ttf", bold.size-2)
n=int(DUR*FPS)
for i in range(n):
    t=i/FPS
    im=Image.new('RGBA',(W,H),(0,0,0,0)); sh=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im); ds=ImageDraw.Draw(sh)
    def ease(a): 
        p=max(0.0,min(1.0,a)); return 1-(1-p)**3
    a1=ease((t-0.10)/0.34); a2=ease((t-0.70)/0.34); a3=ease((t-1.05)/0.40)
    if a1>0:
        y=430-int((1-a1)*22)
        ds.text((W//2+3,y+6),L1,font=serif,fill=(0,0,0,int(180*a1)),anchor='mm')
        d.text((W//2,y),L1,font=serif,fill=(255,255,255,int(255*a1)),anchor='mm')
    if a2>0:
        y=560-int((1-a2)*22)
        ds.text((W//2+3,y+7),L2,font=bold,fill=(0,0,0,int(190*a2)),anchor='mm')
        d.text((W//2,y),L2,font=bold,fill=MAIZE+(int(255*a2),),anchor='mm')
    if a3>0:
        lg=logo.copy(); al=lg.split()[3].point(lambda v:int(v*a3)); lg.putalpha(al)
        im.alpha_composite(lg,(W//2-lw//2, 170-int((1-a3)*18)))
    im=Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(15)),im)
    im.save(f"{OUT}/h_{i:04d}.png")
print(json.dumps({"frames":n}))
