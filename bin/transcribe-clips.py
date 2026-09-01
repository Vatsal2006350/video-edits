#!/usr/bin/env python3
"""transcribe-clips.py <dir|file> [outdir] — word-level transcripts for cut safety.
Writes <name>.words.json: {text, words:[{w,start,end}], gaps:[{start,end,dur}]}
`gaps` are silences between words — the only places you can cut without clipping a word."""
import json, os, subprocess, sys, glob, tempfile

MODEL='mlx-community/whisper-large-v3-turbo'
def transcribe(path, outdir):
    base=os.path.splitext(os.path.basename(path))[0]
    out=os.path.join(outdir, base+'.words.json')
    if os.path.exists(out): return out
    with tempfile.TemporaryDirectory() as T:
        wav=os.path.join(T,'a.wav')
        subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-i',path,'-ac','1','-ar','16000',wav],check=True)
        subprocess.run(['uvx','--from','mlx-whisper','mlx_whisper','--model',MODEL,
                        '--word-timestamps','True','--output-format','json',
                        '--output-name','t','--output-dir',T,wav],
                       check=True,capture_output=True)
        j=json.load(open(os.path.join(T,'t.json')))
    words=[]
    for seg in j.get('segments',[]):
        for w in seg.get('words',[]):
            words.append({'w':w.get('word','').strip(),
                          'start':round(w.get('start',0),3),'end':round(w.get('end',0),3)})
    gaps=[]
    for a,b in zip(words, words[1:]):
        d=round(b['start']-a['end'],3)
        if d>=0.18: gaps.append({'start':a['end'],'end':b['start'],'dur':d})
    data={'file':path,'text':j.get('text','').strip(),'words':words,'gaps':gaps,
          'duration':round(words[-1]['end'],3) if words else 0}
    json.dump(data,open(out,'w'),indent=1)
    return out

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2] if len(sys.argv)>2 else os.path.expanduser('~/Downloads/photos-broll/transcripts')
    os.makedirs(outdir,exist_ok=True)
    files=[src] if os.path.isfile(src) else sorted(
        [f for e in ('*.MOV','*.mov','*.mp4') for f in glob.glob(os.path.join(src,e))])
    for i,f in enumerate(files,1):
        try:
            o=transcribe(f,outdir); d=json.load(open(o))
            head=d['text'][:78].replace('\n',' ')
            print(f"[{i}/{len(files)}] {os.path.basename(f)[:34]:34} {len(d['words']):4}w {len(d['gaps']):3}gaps  {head}")
        except Exception as e:
            print(f"[{i}/{len(files)}] {os.path.basename(f)[:34]:34} FAILED {repr(e)[:60]}")
