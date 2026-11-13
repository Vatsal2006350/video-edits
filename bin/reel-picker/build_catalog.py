#!/usr/bin/env python3
"""Build catalog/reel-catalog.json + catalog/previews/ (poster JPG + muted 4s loop MP4 per entry).

  python3 bin/reel-picker/build_catalog.py [--fx-plan plan.json --fx-stills DIR --fx-video allfx.mp4]

Effects: --fx-plan is the plan used to render all effects back to back (one window each),
--fx-stills holds `still_<t>.png` frames from `fx-extra.sh --still`, --fx-video the rendered plan.
Existing previews are kept (delete a file to rebuild it). Never touches footage.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from catalog_data import TEMPLATES, FX_META, FX_CATS, TRENDS, TREND_LESSONS, RB

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CAT = os.path.join(WS, 'catalog'); PREV = os.path.join(CAT, 'previews')
SCOUT = os.path.join(WS, '.work', 'claude-edited-scout', 'vid')

def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0

def ff(*a):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *a], check=True)

VF = 'scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2'

def poster(src, t, out):
    if not os.path.exists(out): ff('-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-vf', VF, '-q:v', '4', out)

def loop(src, t, length, out):
    if not os.path.exists(out):
        ff('-ss', f'{t:.2f}', '-i', src, '-t', f'{length:.2f}', '-an', '-vf', VF + ',fps=24',
           '-c:v', 'libx264', '-crf', '30', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out)

def rel(p): return os.path.relpath(p, CAT)

def fx_list():
    py = os.path.join(WS, '.agents/skills/claude-video-effects/.venv/bin/python')
    ex = os.path.join(WS, '.agents/skills/reel-effects/scripts/fx_extra.py')
    out = subprocess.run([py, ex, '--list'], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].rstrip('.').isdigit(): rows.append((parts[1], parts[2].strip()))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fx-plan'); ap.add_argument('--fx-stills'); ap.add_argument('--fx-video')
    a = ap.parse_args()
    for d in ('tpl', 'fx', 'trend'): os.makedirs(os.path.join(PREV, d), exist_ok=True)
    items = []

    for t in TEMPLATES:
        e = dict(kind='template', **t); src = os.path.join(RB, t['example']) if t.get('example') else None
        if src and os.path.exists(src):
            d = dur(src); jp = os.path.join(PREV, 'tpl', t['id'] + '.jpg'); mp = os.path.join(PREV, 'tpl', t['id'] + '.mp4')
            at = t.get('at')                      # seconds where the look is clearest, else 30% in
            poster(src, at if at is not None else d * 0.3, jp)
            loop(src, max(0, at - 1) if at is not None else d * 0.25, min(5, d * 0.5), mp)
            e.update(poster=rel(jp), clip=rel(mp), example_path=src)
        items.append(e)

    plan = {f['fx']: f for f in json.load(open(a.fx_plan))['effects']} if a.fx_plan else {}
    for i, (name, desc) in enumerate(fx_list(), 1):
        cat, needs = FX_META.get(name, ('camera', ''))
        e = dict(kind='effect', id=name, name=name, n=i, look=desc, cat=cat, cat_name=FX_CATS[cat], needs=needs,
                 tool=f'bin/fx-extra.sh {name} in.mp4 NEW_out.mp4 --start S --end E', tags=f'{name} {cat} {needs} {desc}')
        jp = os.path.join(PREV, 'fx', name + '.jpg'); mp = os.path.join(PREV, 'fx', name + '.mp4')
        w = plan.get(name)
        if w and a.fx_stills:
            st = os.path.join(a.fx_stills, f"still_{w['start'] + 1.7:.2f}.png")
            if os.path.exists(st): poster(st, 0, jp)
        if w and a.fx_video and os.path.exists(a.fx_video): loop(a.fx_video, w['start'], w['end'] - w['start'], mp)
        if os.path.exists(jp): e['poster'] = rel(jp)
        if os.path.exists(mp): e['clip'] = rel(mp)
        items.append(e)

    for t in TRENDS:
        e = dict(kind='trend', name='@' + t['who'], url=f"https://www.instagram.com/reel/{t['id']}/", look=t['pattern'],
                 tags=t['pattern'] + ' claude edited ai ' + t['try_with'], **t)
        src = os.path.join(SCOUT, t['id'] + '.mp4')
        if os.path.exists(src):
            d = dur(src); jp = os.path.join(PREV, 'trend', t['id'] + '.jpg'); mp = os.path.join(PREV, 'trend', t['id'] + '.mp4')
            poster(src, min(1.0, d * 0.1), jp); loop(src, 0, min(6, d), mp)
            e.update(poster=rel(jp), clip=rel(mp))
        items.append(e)

    out = dict(items=items, fx_categories=FX_CATS, trend_lessons=TREND_LESSONS, scouted='2026-11-11')
    json.dump(out, open(os.path.join(CAT, 'reel-catalog.json'), 'w'), indent=1)
    n = {k: sum(1 for x in items if x['kind'] == k) for k in ('template', 'effect', 'trend')}
    print('catalog:', n, '| with previews:', sum(1 for x in items if x.get('poster')))

if __name__ == '__main__': main()
