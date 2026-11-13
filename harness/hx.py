#!/usr/bin/env python3
"""hx — the reel harness. One entry point for the stages that repeat on every reel.

    python3 harness/hx.py status
    python3 harness/hx.py scout ingest  <run.json>            # normalise + dedupe search results into research/scout-runs/
    python3 harness/hx.py scout fetch   <run.json>            # public metadata per reel (yt-dlp, cached in .work/scout-cache)
    python3 harness/hx.py scout rank    <run.json> [--md]     # ranked table: engagement, repeats across queries
    python3 harness/hx.py caption check <caption.txt> [--source transcript.json] [--facts channel-facts.json]
    python3 harness/hx.py effects brief "<brief>"             # shortlist of templates/effects/refs (reel-picker)
    python3 harness/hx.py effects check <pick.json>           # every effect's needs vs. the facts we can prove
    python3 harness/hx.py motion brief  -- --subject "..." --words "A|B" [motion-brief.py args]   # write BRIEF.md
    python3 harness/hx.py motion check  motion/<film> [--render out.mp4 --ref reference.mp4]  # film + render gates
    python3 harness/hx.py cleanup scan                        # what could be deleted, and why not (dry run)
    python3 harness/hx.py cleanup apply <plan.json> --yes     # delete exactly the reviewed plan, nothing else

Stages and their contracts are in harness/HARNESS.md. Nothing here publishes anything.
"""
import argparse, datetime as dt, glob, json, math, os, re, shutil, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUNS = os.path.join(ROOT, 'research', 'scout-runs')
CACHE = os.path.join(ROOT, '.work', 'scout-cache')
QUEUE = os.path.join(ROOT, 'publishing', 'queue')
REEL_BATCH = os.path.expanduser('~/Downloads/reel-batch')
FACTS = os.path.join(ROOT, 'channel-facts.json')
REEL_RE = re.compile(r'instagram\.com/(?:reels?|p)/([A-Za-z0-9_-]+)')

# ---------------------------------------------------------------- scout
def _norm_url(u):
    m = REEL_RE.search(u or '')
    return f'https://www.instagram.com/reel/{m.group(1)}/' if m else None

def cmd_scout_ingest(a):
    """Input: [{"query": "...", "results": [{"url": "...", "title": "...", "snippet": "..."}]}, ...]
    Output: research/scout-runs/<name>.json with one row per reel: url, id, queries it appeared for, first title/snippet."""
    raw = json.load(open(a.run))
    rows = {}
    for q in raw:
        for r in q.get('results', []):
            url = _norm_url(r.get('url'))
            if not url: continue
            rid = url.split('/reel/')[1].strip('/')
            row = rows.setdefault(rid, dict(id=rid, url=url, queries=[], title='', snippet=''))
            if q['query'] not in row['queries']: row['queries'].append(q['query'])
            row['title'] = row['title'] or (r.get('title') or '')[:200]
            row['snippet'] = row['snippet'] or (r.get('snippet') or '')[:400]
    name = os.path.splitext(os.path.basename(a.run))[0]
    out = os.path.join(RUNS, f'{name}.json')
    os.makedirs(RUNS, exist_ok=True)
    doc = dict(run=name, ingested=dt.date.today().isoformat(), queries=[q['query'] for q in raw],
               reels=sorted(rows.values(), key=lambda r: -len(r['queries'])), metrics={})
    json.dump(doc, open(out, 'w'), indent=1, ensure_ascii=False)
    print(f'ingested {len(rows)} unique reels from {len(raw)} queries -> {os.path.relpath(out, ROOT)}')

def _run_path(a):
    p = a.run if os.path.exists(a.run) else os.path.join(RUNS, a.run if a.run.endswith('.json') else a.run + '.json')
    return p

def cmd_scout_fetch(a):
    p = _run_path(a); doc = json.load(open(p)); os.makedirs(CACHE, exist_ok=True)
    ok = fail = 0
    for r in doc['reels']:
        cf = os.path.join(CACHE, r['id'] + '.json')
        if not os.path.exists(cf) or a.refresh:
            res = None
            for attempt in range(3):                      # Instagram rate-limits bursts: back off, then retry
                time.sleep(a.gap)
                res = subprocess.run(['yt-dlp', '--skip-download', '--dump-json', '--no-warnings', r['url']],
                                     capture_output=True, text=True, timeout=120)
                if res.returncode == 0 and res.stdout.strip(): break
                if 'rate-limit' not in res.stderr: break
                time.sleep(60 * (attempt + 1))
            if res.returncode != 0 or not res.stdout.strip():
                fail += 1; r['fetch_error'] = (res.stderr.strip().splitlines() or ['no output'])[-1][:160]; continue
            j = json.loads(res.stdout.splitlines()[0])
            json.dump({k: j.get(k) for k in ('like_count', 'comment_count', 'duration', 'uploader', 'channel',
                                             'timestamp', 'description', 'view_count')}, open(cf, 'w'), ensure_ascii=False)
        m = json.load(open(cf))
        doc['metrics'][r['id']] = m; ok += 1
    json.dump(doc, open(p, 'w'), indent=1, ensure_ascii=False)
    print(f'fetched {ok} ok, {fail} failed (cached in .work/scout-cache)')

def _score(m):
    likes, comments = (m.get('like_count') or 0), (m.get('comment_count') or 0)
    return math.log10(1 + likes) + 1.5 * math.log10(1 + comments)

def cmd_scout_rank(a):
    doc = json.load(open(_run_path(a)))
    rows = []
    for r in doc['reels']:
        m = doc['metrics'].get(r['id'], {})
        rows.append(dict(id=r['id'], who=m.get('uploader') or m.get('channel') or '?', likes=m.get('like_count'),
                         comments=m.get('comment_count'), repeats=len(r['queries']), score=round(_score(m) + 0.5 * len(r['queries']), 2),
                         title=(r['title'] or r['snippet'])[:90], url=r['url'], days=_age_days(m.get('timestamp'))))
    rows.sort(key=lambda x: -x['score'])
    if not doc['metrics']:
        print('NOTE: no metrics yet (fetch failed or not run). Ranking is by query repeats only. Run: hx.py scout fetch <run> later.')
    lines = ['| score | likes | comments | queries | who | age (d) | id | what it is |', '|---|---|---|---|---|---|---|---|']
    for x in rows:
        lines.append(f"| {x['score']} | {x['likes'] if x['likes'] is not None else '—'} | {x['comments'] if x['comments'] is not None else '—'} | {x['repeats']} | {x['who']} | {x['days'] if x['days'] is not None else '—'} | {x['id']} | {x['title']} |")
    table = '\n'.join(lines)
    print(table)
    if a.md:
        out = os.path.join(ROOT, 'research', f"{doc['run']}-ranking.md")
        open(out, 'w').write(f"# Scout ranking: {doc['run']}\n\nQueries: {', '.join(doc['queries'])}\n\nScore = log10(1+likes) + 1.5*log10(1+comments) + 0.5 per query repeat. Views are not in public metadata for most reels, so they are not scored.\n\n{table}\n")
        print('wrote', os.path.relpath(out, ROOT))

def _age_days(ts):
    if not ts: return None
    return round((time.time() - float(ts)) / 86400, 1)

# ---------------------------------------------------------------- caption
BANNED = {'8M': 'user said "8M in 30 days"; the API says 411,939. Ask before any on-screen use.',
          '23K': 'user said 23K; the API says 25,304. Use 25K+ only if rounding down.'}

def _numbers(text):
    # 751,857 and 751857 are the same number; 25.3K is checked as 25.3
    return set(t.replace(',', '').rstrip('.') for t in re.findall(r'\d[\d,.]*\d|\d', text))

def cmd_caption_check(a):
    text = open(a.caption).read()
    facts = json.load(open(a.facts))
    allowed = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'value' and isinstance(v, str): allowed.update(_numbers(v))
                walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, (int, float)): allowed.add(str(o))
        elif isinstance(o, str): allowed.update(_numbers(o))
    walk(facts)
    if a.source:
        src = json.load(open(a.source))
        allowed.update(_numbers(' '.join(w.get('w', '') for w in src.get('words', [])) if 'words' in src else json.dumps(src)))
    problems = []
    for tok in sorted(_numbers(text)):
        if tok not in allowed:
            problems.append(f'number "{tok}" is in neither channel-facts.json nor the footage transcript')
    for k, why in BANNED.items():
        if re.search(rf'\b{k}\b', text): problems.append(f'"{k}": {why}')
    if re.search(r'\b(age|aged|years old|\d+ ?ft|\d+ ?cm|height)\b', text, re.I):
        problems.append('age/height wording: never write these unless he said it on camera')
    if len(text) > 2200: problems.append('caption over 2200 characters')
    if problems:
        print('CAPTION FAILS'); [print(' -', p) for p in problems]; sys.exit(1)
    print('caption ok: every number is verified or said on camera')

# ---------------------------------------------------------------- effects
def cmd_effects_brief(a):
    subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'reel-picker', 'suggest.py'), a.brief])

def cmd_effects_check(a):
    pick = json.load(open(a.pick))
    facts = json.load(open(FACTS))
    cat = json.load(open(os.path.join(ROOT, 'catalog', 'reel-catalog.json')))
    byid = {i['id']: i for i in cat['items'] if i['kind'] == 'effect'}
    problems = []; warnings = []
    for e in pick.get('fx_plan', {}).get('effects', []):
        item = byid.get(e['fx'])
        if not item: problems.append(f"{e['fx']}: not in the catalog"); continue
        if item.get('needs') and item['needs'] not in ('', 'nothing'):
            warnings.append(f"{e['fx']} needs \"{item['needs']}\": use real values from channel-facts.json or footage, or drop it")
        if float(e['end']) <= float(e['start']): problems.append(f"{e['fx']}: end must be after start")
    if any(w_ for w_ in warnings if 'view' in w_) and facts.get('views_last_30d', {}).get('use_on_screen') is False:
        warnings.append('view-count effects: channel-facts marks 8M as NOT usable on screen; only API numbers (411,939 / 751,857) qualify')
    for p in problems: print('FAIL', p)
    for w in warnings: print('WARN', w)
    if not problems and not warnings: print('effects ok')
    sys.exit(1 if problems else 0)

# ---------------------------------------------------------------- motion
def cmd_motion_brief(a):
    subprocess.run([sys.executable, os.path.join(ROOT, 'bin', 'motion-brief.py'), *a.rest], check=False)

def cmd_motion_check(a):
    """Gates for a motion film. Each one is a failure this repo already had."""
    film = os.path.abspath(a.film); problems = []; warnings = []
    idx = os.path.join(film, 'index.html'); js = os.path.join(film, 'film.js')
    if not os.path.exists(idx): problems.append('no index.html')
    src = (open(idx).read() if os.path.exists(idx) else '') + (open(js).read() if os.path.exists(js) else '')
    code = re.sub(r'//[^\n]*|/\*.*?\*/', '', src, flags=re.S)
    # 2026-11-13: tl.call() text swaps were not seek-safe (frames went wrong when seeking back)
    if re.search(r'\.call\(', code): problems.append('tl.call() is not seek-safe: draw every frame from t alone')
    # 2026-11-13: margin tweens snapped to whole pixels and stuttered under frame-by-frame capture
    if re.search(r'margin(Left|Top)\s*:', code): problems.append('margin tweens snap to whole pixels: animate transforms or canvas geometry')
    # 2026-11-13: HyperFrames refused ../engine/ (asset paths above the project root)
    if re.search(r'(src|href)="\.\./', src): problems.append('asset path climbs above the project (../): bin/motion-reel.sh vendors engine/mg.js')
    # 2026-11-13: frame 0 showed the END label because sub-frames wrapped round the loop
    if 'FILM' in src and 'LABEL_T' not in src and 'sub' in src: warnings.append('labels may read sub-frame time; pin them to the frame time')
    brief = os.path.join(film, 'BRIEF.md')
    if not os.path.exists(brief): warnings.append('no BRIEF.md: write one with bin/motion-brief.py so the film can be rebuilt and judged')
    elif 'Still to ask: nothing' not in open(brief).read(): warnings.append('BRIEF.md still has open questions in <inputs>')
    if a.render:
        # 2026-11-13: a 0.97 s dead hold and 40% still frames read as dead air next to the reference
        sys.path.insert(0, os.path.join(ROOT, 'bin'))
        import importlib.util
        spec = importlib.util.spec_from_file_location('ms', os.path.join(ROOT, 'bin', 'motion-stats.py')); ms = importlib.util.module_from_spec(spec); spec.loader.exec_module(ms)
        s = ms.stats(a.render); print(ms.row(s))
        if s['longest_hold_s'] > 0.6: problems.append(f"a hold of {s['longest_hold_s']}s: something should happen on every beat")
        if s['hard_jumps_per_s'] > 0.5: problems.append(f"{s['hard_jumps_per_s']} hard jumps/s: cuts or pops in a no-cut film")
        if a.ref:
            r = ms.stats(a.ref); print(ms.row(r))
            if s['mean_motion'] < r['mean_motion'] * 0.5: warnings.append('much calmer than the reference')
    for w in warnings: print('warn:', w)
    if problems:
        print('MOTION CHECK FAILS'); [print(' -', p) for p in problems]; sys.exit(1)
    print('motion check ok')

# ---------------------------------------------------------------- cleanup
SUPERSEDED_RE = re.compile(r'_v\d+')

def _in_queue(name):
    hits = glob.glob(os.path.join(QUEUE, '*', 'publish.json'))
    for p in hits:
        if name in open(p, errors='ignore').read(): return True
    return False

def _age_min(p):
    return (time.time() - os.path.getmtime(p)) / 60

def _size(p):
    if os.path.isfile(p): return os.path.getsize(p)
    total = 0
    for d, _, fs in os.walk(p):
        for f in fs:
            try: total += os.path.getsize(os.path.join(d, f))
            except OSError: pass
    return total

def cmd_cleanup_scan(a):
    """Builds a plan. Deletes nothing. Every candidate has a reason; every protected item has a reason too."""
    plan = dict(created=dt.datetime.now().isoformat(timespec='seconds'), delete=[], keep=[])
    # Class 1: job intermediates under videos/*/work and transcode caches of finished jobs.
    for w in glob.glob(os.path.join(ROOT, 'videos', '*', 'work')) + glob.glob(os.path.join(ROOT, 'videos', '*', '.transcode-cache')):
        job = os.path.basename(os.path.dirname(w))
        age = _age_min(w)
        if age < 60:
            plan['keep'].append(dict(path=w, why=f'modified {age:.0f} min ago (rule: keep anything under 60 min)')); continue
        if _in_queue(job):
            plan['keep'].append(dict(path=w, why='a publishing/queue item references this job')); continue
        plan['delete'].append(dict(path=w, size=_size(w), why=f'job "{job}" intermediates, idle {age/60:.1f} h, not queued'))
    # Class 2: superseded reel versions in ~/Downloads/reel-batch.
    # Only MASTER files are versions (name.mp4 in a folder root). _IG and phone/ files are copies of a master:
    # they are never ranked against it, and they go with the master when it is superseded.
    masters = {}
    for p in glob.glob(os.path.join(REEL_BATCH, '*', '*.mp4')):
        base = os.path.basename(p)
        if base.endswith(('_IG.mp4', '_phone.mp4')): continue
        stem = SUPERSEDED_RE.sub('', re.sub(r'\.mp4$', '', base))
        masters.setdefault((os.path.dirname(p), stem), []).append(p)
    for (folder, stem), files in masters.items():
        if len(files) < 2: continue
        files.sort(key=os.path.getmtime)
        newest = files[-1]
        for p in files[:-1]:
            name = os.path.basename(p)
            copies = [os.path.join(folder, name[:-4] + '_IG.mp4'), os.path.join(folder, name[:-4] + '_phone.mp4'),
                      os.path.join(folder, 'phone', name), os.path.join(folder, 'phone', name[:-4] + '_phone.mp4')]
            targets = [q for q in [p] + copies if os.path.exists(q)]
            if any(_age_min(q) < 60 for q in targets):
                plan['keep'].append(dict(path=p, why='superseded but a file in this version is under 60 min old')); continue
            if any(_in_queue(os.path.basename(q)) for q in targets):
                plan['keep'].append(dict(path=p, why='queued for publishing')); continue
            for q in targets:
                plan['delete'].append(dict(path=q, size=os.path.getsize(q), why=f'superseded by {os.path.basename(newest)}'))
    total = sum(x['size'] for x in plan['delete'])
    plan['total_bytes'] = total
    out = os.path.join(ROOT, '.work', 'cleanup-plan.json')
    os.makedirs(os.path.dirname(out), exist_ok=True); json.dump(plan, open(out, 'w'), indent=1)
    print(f"DRY RUN. {len(plan['delete'])} candidates, {total/2**30:.2f} GB. {len(plan['keep'])} protected.")
    for x in plan['delete'][:40]: print(f"  DEL {x['size']/2**20:8.1f} MB  {os.path.relpath(x['path'], ROOT) if x['path'].startswith(ROOT) else x['path']}  — {x['why']}")
    print(f'plan saved: {os.path.relpath(out, ROOT)}. Review it, then: hx.py cleanup apply {os.path.relpath(out, ROOT)} --yes')

def cmd_cleanup_apply(a):
    plan = json.load(open(a.plan))
    if not a.yes: sys.exit('refusing without --yes. Review the plan first.')
    freed = 0
    for x in plan['delete']:
        p = x['path']
        # guard: only delete inside the two allowed areas, and never the plan's protected list
        if not (p.startswith(os.path.join(ROOT, 'videos')) or p.startswith(REEL_BATCH)): print('SKIP outside allowed area', p); continue
        if not os.path.exists(p): continue
        if _age_min(p) < 60: print('SKIP modified within 60 min', p); continue
        freed += _size(p)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        print('deleted', p)
    print(f'freed {freed/2**30:.2f} GB')

# ---------------------------------------------------------------- status
def cmd_status(a):
    du = lambda p: _size(p) / 2**30 if os.path.exists(p) else 0
    print(f'videos/      {du(os.path.join(ROOT, "videos")):6.1f} GB')
    print(f'.work/       {du(os.path.join(ROOT, ".work")):6.1f} GB')
    print(f'reel-batch/  {du(REEL_BATCH):6.1f} GB')
    queued = [d for d in os.listdir(QUEUE) if os.path.isfile(os.path.join(QUEUE, d, 'publish.json'))] if os.path.isdir(QUEUE) else []
    print(f'queue items  {len(queued)}')
    runs = sorted(glob.glob(os.path.join(RUNS, '*.json')))
    print(f'scout runs   {len(runs)}' + (f'  (latest: {os.path.basename(runs[-1])})' if runs else ''))
    cat = os.path.join(ROOT, 'catalog', 'reel-catalog.json')
    print('catalog      ' + ('present' if os.path.exists(cat) else 'MISSING: run bin/reel-pick rebuild'))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status').set_defaults(f=cmd_status)
    s = sub.add_parser('scout').add_subparsers(dest='op', required=True)
    x = s.add_parser('ingest'); x.add_argument('run'); x.set_defaults(f=cmd_scout_ingest)
    x = s.add_parser("fetch"); x.add_argument("run"); x.add_argument("--refresh", action="store_true"); x.add_argument("--gap", type=float, default=6, help="seconds between requests"); x.set_defaults(f=cmd_scout_fetch)
    x = s.add_parser('rank'); x.add_argument('run'); x.add_argument('--md', action='store_true'); x.set_defaults(f=cmd_scout_rank)
    c = sub.add_parser('caption').add_subparsers(dest='op', required=True)
    x = c.add_parser('check'); x.add_argument('caption'); x.add_argument('--source'); x.add_argument('--facts', default=FACTS)
    x.set_defaults(f=cmd_caption_check)
    e = sub.add_parser('effects').add_subparsers(dest='op', required=True)
    x = e.add_parser('brief'); x.add_argument('brief'); x.set_defaults(f=cmd_effects_brief)
    x = e.add_parser('check'); x.add_argument('pick'); x.set_defaults(f=cmd_effects_check)
    m = sub.add_parser('motion').add_subparsers(dest='op', required=True)
    x = m.add_parser('brief'); x.add_argument('rest', nargs=argparse.REMAINDER); x.set_defaults(f=cmd_motion_brief)
    x = m.add_parser('check'); x.add_argument('film'); x.add_argument('--render'); x.add_argument('--ref'); x.set_defaults(f=cmd_motion_check)
    k = sub.add_parser('cleanup').add_subparsers(dest='op', required=True)
    k.add_parser('scan').set_defaults(f=cmd_cleanup_scan)
    x = k.add_parser('apply'); x.add_argument('plan'); x.add_argument('--yes', action='store_true'); x.set_defaults(f=cmd_cleanup_apply)
    a = ap.parse_args(); a.f(a)

if __name__ == '__main__':
    main()
