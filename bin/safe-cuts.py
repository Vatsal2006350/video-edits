#!/usr/bin/env python3
"""safe-cuts.py <words.json> [beats.txt] — where you can cut without clipping speech.
Alone: lists silence gaps. With beats: keeps only beats that land inside a gap,
so a cut is both on-beat AND between words."""
import json, sys, os

def load_gaps(p):
    d=json.load(open(p)); return d, d.get('gaps',[])

def safe(t, gaps, pad=0.06):
    for g in gaps:
        if g['start']+pad <= t <= g['end']-pad: return True
    return False

def nearest_safe(t, gaps, pad=0.06):
    """nudge a cut to the closest point that doesn't clip a word"""
    if safe(t,gaps,pad): return round(t,3)
    best=None
    for g in gaps:
        for c in (g['start']+pad, g['end']-pad, (g['start']+g['end'])/2):
            if g['start']<=c<=g['end']:
                if best is None or abs(c-t)<abs(best-t): best=c
    return round(best,3) if best is not None else round(t,3)

if __name__=='__main__':
    d,gaps=load_gaps(sys.argv[1])
    print(f"{os.path.basename(d['file'])}  speech {d['duration']:.2f}s  {len(d['words'])} words  {len(gaps)} gaps")
    if len(sys.argv)>2 and os.path.exists(sys.argv[2]):
        beats=[float(x) for x in open(sys.argv[2]).read().split()]
        ok=[b for b in beats if safe(b,gaps)]
        print(f"beats: {len(beats)} total -> {len(ok)} land in a silence gap")
        for b in ok[:12]: print(f"   safe beat @ {b:6.2f}s")
        risky=[b for b in beats if not safe(b,gaps)][:6]
        for b in risky:
            print(f"   beat @ {b:6.2f}s would clip a word -> nudge to {nearest_safe(b,gaps):6.2f}s")
    else:
        for g in gaps[:18]:
            print(f"   gap {g['start']:6.2f}-{g['end']:6.2f}s  ({g['dur']:.2f}s)")
