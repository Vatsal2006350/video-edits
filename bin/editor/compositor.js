/* compositor.js — canvas renderer that mirrors timeline-reel.py exactly.
   ffmpeg pipeline reproduced per segment kind:
     all      : scale cover 1080x1920 + centre crop
     photo    : zoompan z = min(1.06, 1+0.0008*frame)
     freeze   : hue s=0, eq contrast=1.24 brightness=-0.05, zoompan z=min(1.05,1+0.0014*frame), skull after skull_at
     video    : eq contrast=1.05 saturation=1.08
   Overlays (caption PNG, skull PNG) are drawn full-frame like ffmpeg's overlay=0:0. */
export const W=1080, H=1920, FPS=30;

export class MediaPool{
  constructor(med){ this.med=med; this.vid=new Map(); this.img=new Map(); }
  isVid(p){ return /\.(mov|mp4|m4v)$/i.test(p); }
  video(src){
    if(!this.vid.has(src)){
      const v=document.createElement('video');
      v.muted=true; v.playsInline=true; v.preload='auto'; v.crossOrigin='anonymous';
      v.addEventListener('loadeddata',()=>{ if(this.onready) this.onready(src); },{once:true});
      v.addEventListener('seeked',()=>{ if(this.onready) this.onready(src); });
      v.src=this.med(src);
      this.vid.set(src,v);
    }
    return this.vid.get(src);
  }
  image(src){
    if(!this.img.has(src)){
      const i=new Image(); i.crossOrigin='anonymous';
      i.addEventListener('load',()=>{ if(this.onready) this.onready(src); },{once:true});
      i.src=this.med(src);
      this.img.set(src,i);
    }
    return this.img.get(src);
  }
  /** preload everything a spec touches; resolves when all are ready enough to draw */
  async warm(segs, extra=[]){
    const jobs=[];
    const uniq=new Set();
    segs.forEach(s=>{ uniq.add(s.src); if(s.caption) uniq.add(s.caption); });
    extra.forEach(e=>e&&uniq.add(e));
    uniq.forEach(src=>{
      if(this.isVid(src)){
        const v=this.video(src);
        if(v.readyState<2) jobs.push(new Promise(r=>{
          const done=()=>{v.removeEventListener('loadeddata',done);r()};
          v.addEventListener('loadeddata',done); setTimeout(r,6000);
        }));
      } else {
        const i=this.image(src);
        if(!i.complete) jobs.push(new Promise(r=>{
          i.addEventListener('load',r,{once:true}); i.addEventListener('error',r,{once:true}); setTimeout(r,6000);
        }));
      }
    });
    await Promise.all(jobs);
  }
}

/** cover-fit source into WxH with centre crop, then apply zoom about the centre */
function coverRect(sw,sh,zoom){
  const scale=Math.max(W/sw,H/sh)*zoom;
  const dw=sw*scale, dh=sh*scale;
  return {dx:(W-dw)/2, dy:(H-dh)/2, dw, dh};
}

export class Compositor{
  constructor(canvas, pool, opts={}){
    this.c=canvas; this.ctx=canvas.getContext('2d',{alpha:false});
    this.pool=pool; this.skullSrc=opts.skull||null;
    canvas.width=W; canvas.height=H;
  }
  segAt(segs,t){ for(let i=0;i<segs.length;i++) if(t>=segs[i].start && t<segs[i].end) return i; return -1; }

  /** draw the exact frame at time t. playing=true lets video elements run freely. */
  draw(segs,t,playing){
    const x=this.ctx;
    const i=this.segAt(segs,t);
    if(i<0){ x.filter='none'; x.fillStyle='#000'; x.fillRect(0,0,W,H); return -1; }
    const s=segs[i], local=Math.max(0,t-s.start), frame=local*FPS;

    let srcEl=null, sw=0, sh=0, zoom=1, filter='none';
    if(s.kind==='video' && this.pool.isVid(s.src)){
      const v=this.pool.video(s.src);
      srcEl=v; sw=v.videoWidth; sh=v.videoHeight;
      filter='contrast(1.05) saturate(1.08)';
      const want=(s.ss||0)+local;
      if(playing){
        if(v.paused) v.play().catch(()=>{});
        if(Math.abs(v.currentTime-want)>0.25){ try{v.currentTime=want}catch(e){} }
      } else {
        if(!v.paused) v.pause();
        if(Math.abs(v.currentTime-want)>0.05){ try{v.currentTime=want}catch(e){} }
      }
    } else if(s.kind==='freeze'){
      // freeze uses a still: the video's frame at ss, or the photo itself
      if(this.pool.isVid(s.src)){
        const v=this.pool.video(s.src);
        srcEl=v; sw=v.videoWidth; sh=v.videoHeight;
        if(!v.paused) v.pause();
        const want=s.ss||0;
        if(Math.abs(v.currentTime-want)>0.05){ try{v.currentTime=want}catch(e){} }
      } else {
        const im=this.pool.image(s.src); srcEl=im; sw=im.naturalWidth; sh=im.naturalHeight;
      }
      filter='grayscale(1) contrast(1.24) brightness(0.95)';
      zoom=Math.min(1.05, 1+0.0014*frame);
    } else {
      const im=this.pool.image(s.src); srcEl=im; sw=im.naturalWidth; sh=im.naturalHeight;
      zoom=Math.min(1.06, 1+0.0008*frame);
    }
    // asset not decoded yet -> keep the previous frame rather than flashing black
    if(!srcEl||!sw||!sh) return i;
    x.filter='none'; x.fillStyle='#000'; x.fillRect(0,0,W,H);

    const r=coverRect(sw,sh,zoom);
    x.filter=filter;
    try{ x.drawImage(srcEl, r.dx, r.dy, r.dw, r.dh); }catch(e){}
    x.filter='none';

    // skull overlay (freeze only, after skull_at)
    if(s.kind==='freeze' && this.skullSrc && local >= (s.skull_at ?? 0.05)){
      const sk=this.pool.image(this.skullSrc);
      if(sk.complete) x.drawImage(sk,0,0,W,H);
    }
    // caption overlay
    if(s.caption){
      const cp=this.pool.image(s.caption);
      if(cp.complete) x.drawImage(cp,0,0,W,H);
    }
    return i;
  }
}
