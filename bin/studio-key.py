#!/usr/bin/env python3
"""Clean key of a matted talking head over a generated backdrop, without the white fringe.

The u2net matte (hyperframes remove-background) leaves two artefacts on a bright wall: a flickering edge
where the subject moves, and edge pixels whose colour is half wall (white halo around hair, shoulders,
hands). This does, per frame:
  1. alpha = min(3-frame temporal average, current)   -- never reveals wall behind a moving edge
  2. MinFilter choke + GaussianBlur feather + levels     -- pulls the halo in, keeps a soft edge
  3. edge-darken: a band of `extend` px inside the boundary is multiplied toward the backdrop (factor `edge_k` at the
     very edge -> 1 inside), so wall-coloured edge pixels read as shadow, not as a white rim (extending interior colour
     instead smeared skin tone into the hair -- tested, worse)
  4. optional y-ramp darkening so hands/desk sink into the backdrop, or `floor` {y0,y1,dir}: below the ramp the output IS
     the graded original frame (no key) -- the matte flickers on arms/hands against the desk, the original does not
  4b. `insert` [clip_frame, n]: a b-roll insert of n frames lives at that clip frame; layer lookups and output names shift by n
  5. behind-layer text (k_*.png) goes between backdrop and subject

Usage (JSON argv[1]):
  {"fg":"fg/","colour":"gfg/","backdrop":"studio_bg.png","out":"pro/","n":458,
   "choke":7,"feather":2.0,"levels":[0.10,0.90],"extend":10,
   "ramp":[1250,1450,0.55],"behind":"kin/k_%04d.png","front":["caps/c_%04d.png","kin/f_%04d.png"],
   "skip":[[96,122]]}
Frame files are f_%04d.png 1-based in fg/colour; k_/f_ layers are 0-based.
"""
import sys, json, os, numpy as np
from PIL import Image, ImageFilter
c=json.loads(sys.argv[1]); W,H=c.get('w',1080),c.get('h',1920)
FG,COL,OUT=c['fg'],c['colour'],c['out']; N=c['n']; os.makedirs(OUT,exist_ok=True)
CH=c.get('choke',7); FE=c.get('feather',2.0); LO,HI=c.get('levels',[0.10,0.90]); EX=c.get('extend',10); EDGE_K=c.get('edge_k',0.25); DESPILL=c.get('despill',0.9); DS_L=c.get('despill_luma',60); DS_S=c.get('despill_sat',0.40)
ramp=c.get('ramp'); skip=set(i for a,b in c.get('skip',[]) for i in range(a,b+1))
FLOOR=c.get('floor'); INS=c.get('insert',[10**9,0])
bg=np.asarray(Image.open(c['backdrop']).convert('RGB').resize((W,H))).astype(np.float32)
yy=np.mgrid[0:H,0:W][0]
rampm=np.clip((yy-ramp[0])/(ramp[1]-ramp[0]),0,1)[...,None]*ramp[2] if ramp else None
floorm=np.clip((yy-FLOOR['y0'])/(FLOOR['y1']-FLOOR['y0']),0,1)[...,None] if FLOOR else None
def rgba(p): return Image.open(p).convert('RGBA').resize((W,H),Image.LANCZOS)
def alpha(i): return np.asarray(rgba(f'{FG}/f_{i:04d}.png'))[:,:,3].astype(np.float32)
def layer(base, p):
    if p and os.path.exists(p): return Image.alpha_composite(base, rgba(p))
    return base
prev=None; cur=alpha(1); nxt=alpha(2)
for i in range(1,N+1):
    if (i-1) in skip:
        prev,cur=cur,nxt; nxt=alpha(min(i+2,N)); continue
    a=np.minimum((cur*2+(prev if prev is not None else cur)+nxt)/4, cur)
    A=Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.MinFilter(CH)).filter(ImageFilter.GaussianBlur(FE))
    a=np.clip((np.asarray(A).astype(np.float32)/255-LO)/(HI-LO),0,1)
    col=np.asarray(rgba(f'{COL}/f_{i:04d}.png'))[:,:,:3].astype(np.float32)
    if EX>0:                                   # edge-darken: boundary band multiplied toward the backdrop (wall-coloured edge pixels go dark)
        inner=np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MinFilter(2*EX+1)).filter(ImageFilter.GaussianBlur(EX*0.6))).astype(np.float32)/255
        col=col*(EDGE_K+(1-EDGE_K)*inner)[...,None]
        if DESPILL>0:                          # wall-coloured pixels in the band -> dark (bright + unsaturated = wall, not skin/hair)
            mx=col.max(2); mn=col.min(2); sat=(mx-mn)/np.maximum(mx,1); luma=col.mean(2)
            wall=np.clip((luma-DS_L)/40,0,1)*np.clip((DS_S-sat)/0.25,0,1)*(1-inner)   # hair ~50 luma stays, skin sat>0.4 stays
            col=col*(1-DESPILL*wall)[...,None]
    if rampm is not None: col=col*(1-rampm)
    o=(i-1)+(INS[1] if (i-1)>=INS[0] else 0)                 # timeline index of this clip frame
    base=Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
    base=layer(base, c.get('behind','').replace('%04d',f'{o:04d}') if c.get('behind') else None)
    B=np.asarray(base).astype(np.float32)[:,:,:3]
    out=B*(1-a[...,None])+col*a[...,None]
    if floorm is not None:                        # hands/desk zone: graded original, no matte involved
        fl=np.asarray(Image.open(f"{FLOOR['dir']}/f_{i:04d}.png").convert('RGB').resize((W,H))).astype(np.float32)
        out=out*(1-floorm)+fl*floorm
    im=Image.fromarray(np.clip(out,0,255).astype(np.uint8)).convert('RGBA')
    for f in c.get('front',[]): im=layer(im, f.replace('%04d',f'{o:04d}'))
    im.convert('RGB').save(f'{OUT}/f_{o+1:04d}.png')
    prev,cur=cur,nxt; nxt=alpha(min(i+2,N))
print(json.dumps({'frames':N,'skipped':len(skip)}))
