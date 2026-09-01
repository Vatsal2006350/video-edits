#!/usr/bin/env python3
"""Reel editor server.  python3 server.py [port]  -> http://localhost:8765
Endpoints: /api/assets  /api/audio  /api/beats  /api/thumb  /api/render  /media/*  /out/*"""
import json, os, subprocess, sys, tempfile, urllib.parse, hashlib, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME=os.path.expanduser('~')
WS=os.path.join(HOME,'Code','video-edits')
OUT=os.path.join(HOME,'Downloads','reel-exports'); os.makedirs(OUT,exist_ok=True)
CACHE=os.path.join(tempfile.gettempdir(),'reel_editor'); os.makedirs(CACHE,exist_ok=True)

CLIP_DIRS=[os.path.join(HOME,'Downloads'),
           os.path.join(HOME,'Downloads','content'),
           os.path.join(HOME,'Downloads','photos-broll','kerala-scenic'),
           os.path.join(HOME,'Downloads','photos-broll','maldives-sunset'),
           os.path.join(HOME,'Downloads','photos-broll','broll'),
           '/tmp/before_jpg',
           os.path.join(WS,'receipts')]
AUDIO_DIRS=[os.path.join(HOME,'Downloads'), os.path.join(HOME,'Downloads','music-rf'), '/tmp']
VID={'.mov','.mp4','.m4v'}; IMG={'.jpg','.jpeg','.png'}; AUD={'.mp3','.m4a','.wav','.aac'}

def scan(dirs, exts, limit=400):
    out=[]
    for d in dirs:
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            p=os.path.join(d,f)
            if os.path.isfile(p) and os.path.splitext(f)[1].lower() in exts:
                try: sz=os.path.getsize(p)
                except OSError: continue
                if sz<2000: continue
                out.append({'path':p,'name':f,'dir':os.path.basename(d) or d})
            if len(out)>=limit: break
    return out

def probe_dur(p):
    try:
        r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],
                         capture_output=True,text=True,timeout=25)
        return round(float(r.stdout.strip()),3)
    except Exception: return 0.0

def beats_for(audio):
    key=hashlib.md5(audio.encode()).hexdigest()
    cf=os.path.join(CACHE,key+'.json')
    if os.path.exists(cf):
        return json.load(open(cf))
    bt=subprocess.run([sys.executable,os.path.join(WS,'bin','beats.py'),audio],
                      capture_output=True,text=True).stdout.split()
    beats=[round(float(b),3) for b in bt]
    # rms envelope for the waveform
    sr=22050
    raw=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',audio,'-ac','1','-ar',str(sr),'-f','wav','-'],
                       capture_output=True).stdout
    i=raw.find(b'data')
    import array
    a=array.array('h'); a.frombytes(raw[i+8: i+8+((len(raw)-i-8)//2)*2])
    hop=int(sr*0.02); peaks=[]
    for j in range(0,len(a)-hop,hop):
        seg=a[j:j+hop]; peaks.append(round(max(abs(min(seg)),abs(max(seg)))/32768,3))
    d={'beats':beats,'peaks':peaks,'hop':0.02,'duration':probe_dur(audio)}
    json.dump(d,open(cf,'w'))
    return d

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _send(self,code,ctype,body,extra=None):
        self.send_response(code); self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Access-Control-Allow-Origin','*')
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(body)
    def _json(self,obj,code=200): self._send(code,'application/json',json.dumps(obj).encode())

    def do_GET(self):
        u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
        if u.path=='/compositor.js':
            body=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'compositor.js'),'rb').read()
            return self._send(200,'text/javascript; charset=utf-8',body)
        if u.path=='/' or u.path=='/index.html':
            body=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'editor.html'),'rb').read()
            return self._send(200,'text/html; charset=utf-8',body)
        if u.path=='/api/assets':
            return self._json({'clips':scan(CLIP_DIRS,VID|IMG),'audio':scan(AUDIO_DIRS,AUD)})
        if u.path=='/api/projects':
            pd=os.path.join(WS,'projects'); out=[]
            if os.path.isdir(pd):
                for f in sorted(os.listdir(pd)):
                    if f.endswith('.json'): out.append(f[:-5])
            return self._json({'projects':out})
        if u.path=='/api/project':
            n=q.get('name',[''])[0]
            fp=os.path.join(WS,'projects',n+'.json')
            if not os.path.isfile(fp): return self._json({'error':'no project'},404)
            return self._json(json.load(open(fp)))
        if u.path=='/api/beats':
            a=q.get('audio',[''])[0]
            if not os.path.isfile(a): return self._json({'error':'no audio'},400)
            return self._json(beats_for(a))
        if u.path=='/api/dur':
            return self._json({'duration':probe_dur(q.get('src',[''])[0])})
        if u.path=='/api/thumb':
            src=q.get('src',[''])[0]; t=float(q.get('t',['0'])[0]); grey=q.get('grey',['0'])[0]=='1'
            key=hashlib.md5(f'{src}|{t}|{grey}'.encode()).hexdigest()+'.jpg'
            fp=os.path.join(CACHE,key)
            if not os.path.exists(fp):
                vf="scale=270:480:force_original_aspect_ratio=increase,crop=270:480"
                if grey: vf+=",hue=s=0,eq=contrast=1.24:brightness=-0.05"
                pre=['-ss',str(t)] if (t>0 and os.path.splitext(src)[1].lower() in VID) else []
                subprocess.run(['ffmpeg','-nostdin','-y','-v','error']+pre+['-i',src,'-vframes','1','-vf',vf,fp],
                               capture_output=True)
            if not os.path.exists(fp): return self._json({'error':'thumb failed'},500)
            return self._send(200,'image/jpeg',open(fp,'rb').read(),{'Cache-Control':'max-age=600'})
        if u.path.startswith('/media/') or u.path.startswith('/out/'):
            p=urllib.parse.unquote(u.path[7:] if u.path.startswith('/media/') else u.path[5:])
            if u.path.startswith('/out/'): p=os.path.join(OUT,p)
            if not os.path.isfile(p): return self._json({'error':'404'},404)
            ext=os.path.splitext(p)[1].lower()
            ct={'.mp4':'video/mp4','.mov':'video/quicktime','.mp3':'audio/mpeg','.m4a':'audio/mp4',
                '.wav':'audio/wav','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png'}.get(ext,'application/octet-stream')
            sz=os.path.getsize(p)
            rng=self.headers.get('Range')
            if rng and rng.startswith('bytes='):
                a,_,b=rng[6:].partition('-')
                start=int(a) if a else 0
                end=int(b) if b else sz-1
                end=min(end,sz-1); start=min(start,end)
                with open(p,'rb') as fh:
                    fh.seek(start); data=fh.read(end-start+1)
                self.send_response(206)
                self.send_header('Content-Type',ct)
                self.send_header('Content-Range',f'bytes {start}-{end}/{sz}')
                self.send_header('Accept-Ranges','bytes')
                self.send_header('Content-Length',str(len(data)))
                self.send_header('Access-Control-Allow-Origin','*')
                self.end_headers(); self.wfile.write(data); return
            data=open(p,'rb').read()
            return self._send(200,ct,data,{'Accept-Ranges':'bytes'})
        return self._json({'error':'not found'},404)

    def do_POST(self):
        u=urllib.parse.urlparse(self.path)
        n=int(self.headers.get('Content-Length',0)); body=json.loads(self.rfile.read(n) or b'{}')
        if u.path=='/api/render':
            name=body.get('name','edit')+'.mp4'
            spec={'audio':body['audio'],'audio_ss':body.get('audio_ss',0),'out':os.path.join(OUT,name),
                  'skull':os.path.join(WS,'receipts','skull.png'),
                  'segments':body['segments']}
            sp=os.path.join(CACHE,'spec.json'); json.dump(spec,open(sp,'w'))
            r=subprocess.run([sys.executable,os.path.join(WS,'bin','timeline-reel.py'),sp],
                             capture_output=True,text=True)
            ok=os.path.exists(spec['out'])
            return self._json({'ok':ok,'log':(r.stdout+r.stderr)[-2500:],'url':'/out/'+name if ok else None})
        if u.path=='/api/saveproject':
            n=body.get('name','untitled')
            pd=os.path.join(WS,'projects'); os.makedirs(pd,exist_ok=True)
            bd=os.path.join(pd,'_backups'); os.makedirs(bd,exist_ok=True)
            fp=os.path.join(pd,n+'.json')
            if os.path.exists(fp):                       # timestamped backup of the previous save
                import shutil, datetime
                ts=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                shutil.copy2(fp, os.path.join(bd, f'{n}.{ts}.json'))
            spec=body.get('spec',{})
            json.dump(spec, open(fp,'w'), indent=1)
            return self._json({'ok':True,'path':fp,'segments':len(spec.get('segments',[])),
                               'audio':os.path.basename(spec.get('audio',''))})
        if u.path=='/api/savespec':
            p=os.path.join(WS,'receipts',body.get('name','spec')+'.json')
            json.dump(body.get('spec',{}),open(p,'w'),indent=1)
            return self._json({'ok':True,'path':p})
        return self._json({'error':'not found'},404)

if __name__=='__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8765
    print(f'Reel editor -> http://localhost:{port}')
    ThreadingHTTPServer(('127.0.0.1',port),H).serve_forever()
