# Stand-in plates (NOT footage): dark warm bokeh "theatre" stills, panned by ffmpeg.
import os; os.makedirs("../../.work/standin", exist_ok=True)
import random, subprocess
from PIL import Image, ImageDraw, ImageFilter
random.seed(7)
looks = [((10,6,4),(255,190,110)), ((6,6,10),(140,170,255)), ((14,5,6),(255,120,90)), ((8,7,5),(255,215,150))]
for k,(bg,lc) in enumerate(looks):
    W,H=1400,2400
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    for y in range(H):
        v=int(18*(1-abs(y-H*0.62)/H))
        d.line([(0,y),(W,y)],fill=tuple(min(255,c+v) for c in bg))
    over=Image.new('RGB',(W,H)); od=ImageDraw.Draw(over)
    for _ in range(70):
        x,y=random.randint(0,W),random.randint(int(H*0.15),int(H*0.85)); r=random.randint(18,90)
        a=random.uniform(0.25,1.0); c=tuple(int(ch*a) for ch in lc)
        od.ellipse([x-r,y-r,x+r,y+r],fill=c)
    over=over.filter(ImageFilter.GaussianBlur(14))
    from PIL import ImageChops
    im=ImageChops.add(im,over)
    im.save(f'../../.work/standin/plate{k}.png')
    subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-framerate','30','-i',f'../../.work/standin/plate{k}.png','-t','6',
      '-vf',"crop=1200:2133:x='100*t/6':y='130-60*t/6',scale=1080:1920,format=yuv420p",
      '-c:v','libx264','-crf','16','-preset','veryfast',f'../../.work/standin/plate{k}.mp4'],check=True)
print('ok')
