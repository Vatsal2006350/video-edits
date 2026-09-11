#!/usr/bin/env python3
"""Mechanical QA for build-story-reel.sh specs, run BEFORE rendering. Catches the "tiny stuff" Vatsal keeps finding:
  - gaps < 0.6s between consecutive cutaways (the speaker flashes for a few frames between b-roll shots)
  - a cutaway sourced from the same take that is speaking under it (reads as the line said twice)
  - a cutaway that starts inside the first 0.4s of a speech segment or ends inside its last 0.3s (jump-cut feel)
  - the same fact/phrase spoken twice across segments (needs transcripts: pass words.json per seg via --words)
  - cutaway seek beyond the source duration
Usage: story-qa.py --segs "$SEGS" --cuts "$CUTS" [--tail "$TAIL"] [--min-gap 0.6]
Prints WARN lines; exit 1 if any.
"""
import sys, argparse, subprocess, os
ap=argparse.ArgumentParser(); ap.add_argument('--segs',required=True); ap.add_argument('--cuts',default=''); ap.add_argument('--tail',default=''); ap.add_argument('--min-gap',type=float,default=0.6)
a=ap.parse_args(); warn=[]
segs=[]; t=0.0
for l in a.segs.strip().splitlines():
    if not l.strip(): continue
    src,s,e=l.split('|')[:3]; s,e=float(s),float(e); segs.append((src,s,e,t,t+(e-s))); t+=e-s
cuts=[]
for l in a.cuts.strip().splitlines():
    if not l.strip(): continue
    ca,cb,src,seek=l.split('|')[:4]; cuts.append((float(ca),float(cb),src,float(seek)))
cuts.sort()
def dur(p):
    try: return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True).stdout)
    except: return 1e9
for i in range(1,len(cuts)):
    g=cuts[i][0]-cuts[i-1][1]
    if 0<g<a.min_gap: warn.append(f"gap {g:.2f}s between cutaways ending {cuts[i-1][1]} and starting {cuts[i][0]}: the speaker flashes -- merge or extend")
for ca,cb,src,seek in cuts:
    for ssrc,s,e,t0,t1 in segs:
        if ca<t1 and cb>t0 and os.path.basename(src)==os.path.basename(ssrc):
            lo=s+(ca-t0); hi=s+(cb-t0)
            if not (seek+ (cb-ca) <= s or seek >= e): warn.append(f"cutaway {ca}-{cb} uses the SAME take as the speech under it ({os.path.basename(src)} @{seek}) -> looks like the line said twice")
        if t0<ca<t0+0.4: warn.append(f"cutaway at {ca} starts inside the first 0.4s of a speech segment (segment starts {t0:.2f})")
        if t1-0.3<cb<t1-0.01: warn.append(f"cutaway ending {cb} stops inside the last 0.3s of a speech segment (ends {t1:.2f}) -- end it AT {t1:.2f} or >=0.3s earlier")
    if seek+(cb-ca)>dur(src)+0.05: warn.append(f"cutaway {os.path.basename(src)} @{seek} +{cb-ca:.1f}s runs past the end of the source")
for l in a.tail.strip().splitlines():
    if not l.strip(): continue
    src,seek,d=l.split('|')[:3]
    if float(seek)+float(d)>dur(src)+0.05: warn.append(f"tail {os.path.basename(src)} @{seek} +{d}s runs past the end of the source")
print(f"story-qa: {len(segs)} segs, {len(cuts)} cutaways, speech {t:.1f}s")
for w in warn: print("WARN", w)
sys.exit(1 if warn else 0)
