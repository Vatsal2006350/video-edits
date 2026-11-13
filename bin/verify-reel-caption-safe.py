#!/usr/bin/env python3
"""Render transparent caption proof layers and verify project safe-area geometry."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'videos/international-student-travel-batch'
FONT=ImageFont.truetype(str(ROOT/'fonts/Montserrat-ExtraBold.ttf'),58)
COPY={
11:[(0,6,'I LEFT FOR SCHOOL.'),(6,6,'THE WORLD KEPT OPENING UP.')],
12:[(0,2,'SOME CITIES FEEL LIKE A LAYOVER.'),(2,3.458,'SOME VIEWS STAY WITH YOU.')],
13:[(0,2,"I DON'T TRAVEL TO RUN AWAY."),(2,7.009,'I TRAVEL TO NOTICE MORE.')],
14:[(0,7.409,"THE BEST PARTS OF STUDYING ABROAD\nAREN'T ON THE SYLLABUS.")],
15:[(0,12.223,'A FAMILIAR MEAL CAN SHRINK\nTHE DISTANCE FOR A MINUTE.')],
}
SAFE=(59,278,918,1536)
def wrap(text):
    out=[]
    for para in text.split('\n'):
        line=''
        for word in para.split():
            cand=(line+' '+word).strip()
            if line and FONT.getlength(cand)>710:
                out.append(line); line=word
            else: line=cand
        if line: out.append(line)
    return out

for n,states in COPY.items():
    folder=BASE/f'reel-{n}'/'renders'; proofs=[]
    for state,(start,dur,text) in enumerate(states,1):
        lines=wrap(text); img=Image.new('RGBA',(1080,1920),(0,0,0,0)); draw=ImageDraw.Draw(img)
        first_y=1160-(len(lines)-1)*36
        for idx,line in enumerate(lines):
            width=FONT.getlength(line)
            x=(1080-width)/2
            y=first_y+idx*72
            draw.text((x,y),line,font=FONT,fill=(255,255,255,255),stroke_width=3,stroke_fill=(0,0,0,200))
            bbox=draw.textbbox((x,y),line,font=FONT,stroke_width=3)
            assert bbox[0]>=SAFE[0] and bbox[2]<=SAFE[2] and bbox[1]>=SAFE[1] and bbox[3]<=SAFE[3], (n,state,line,bbox)
            assert width<=724,(n,state,line,width)
        path=folder/f'caption-safe-layer-{state}.png'; img.save(path)
        alpha=img.getchannel('A').getbbox()
        proofs.append({'state':state,'time_sec':start,'duration_sec':dur,'text':text,'alpha_bbox':alpha,'max_line_width_px':round(max(FONT.getlength(l) for l in lines),1),'file':path.name})
    (folder/'caption-safe-proof.json').write_text(json.dumps({'safe_box':{'x':[SAFE[0],SAFE[2]],'y':[SAFE[1],SAFE[3]],'max_centered_width_px':724},'states':proofs},indent=2)+'\n')
    print(f'reel-{n}: {len(proofs)} caption layer(s) pass; widths={ [p["max_line_width_px"] for p in proofs] }')
