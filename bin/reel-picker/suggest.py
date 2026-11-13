#!/usr/bin/env python3
"""Rank templates / effects / trend refs for a plain-English reel brief.

  python3 bin/reel-picker/suggest.py "travel reel about missing my parents, airport clips"
  python3 bin/reel-picker/suggest.py --json "..."

Keyword + synonym scoring over catalog/reel-catalog.json tags. It is a shortlist for the creator to
pick from in the picker UI (bin/reel-pick), not a decision.
"""
import json, math, os, re, sys

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CATALOG = os.path.join(WS, 'catalog', 'reel-catalog.json')

# brief word -> extra tag words it implies
SYN = {
    'claude': 'ai edited automation workflow', 'codex': 'ai claude automation', 'ai': 'claude automation',
    'edit': 'edited claude', 'edited': 'claude ai', 'views': 'numbers proof view count instagram',
    'followers': 'numbers instagram profile', 'growth': 'numbers graph views', 'stats': 'numbers stat data',
    'trip': 'travel', 'flight': 'travel airport', 'abroad': 'travel international', 'home': 'parents family travel',
    'mom': 'parents family', 'dad': 'parents family', 'cook': 'food recipe', 'recipe': 'food', 'eat': 'food',
    'tips': 'list steps advice', 'steps': 'list steps', 'how': 'explainer steps', 'advice': 'list tips',
    'startup': 'founder yc', 'founder': 'yc startup', 'hackathon': 'event jachacks promo',
    'talk': 'talking head', 'keynote': 'talk conference', 'podcast': 'conversation',
    'funny': 'meme reaction', 'meme': 'reaction', 'sad': 'emotional', 'miss': 'emotional parents',
    'hook': 'opener title', 'title': 'opener hook', 'list': 'steps tips',
}
AI_WORDS = set('claude ai edit edited editing codex automation automate prompt'.split())
STOP = set('a an the and or of to in on for with my me i is it this that about reel video make new some'.split())

def words(s): return [w for w in re.findall(r'[a-z0-9]+', s.lower()) if w not in STOP]

def score(item, q):
    tags = set(words(item.get('tags', '') + ' ' + item.get('name', '') + ' ' + item.get('look', '')))
    s = sum(2 if w in tags else 0 for w in q['direct']) + sum(1 for w in q['implied'] if w in tags)
    if s and item.get('poster'): s += 0.3     # something to look at beats nothing
    if s and item['kind'] == 'trend':         # proven engagement breaks ties
        s += math.log10(1 + item.get('likes', 0) + item.get('comments', 0)) / 2
    return s

def suggest(brief, n_tpl=4, n_fx=8, n_trend=3, catalog=None):
    cat = catalog or json.load(open(CATALOG))
    direct = words(brief); implied = []
    for w in direct: implied += words(SYN.get(w, ''))
    q = dict(direct=direct, implied=implied)
    out = {}
    for kind, n in (('template', n_tpl), ('effect', n_fx), ('trend', n_trend)):
        if kind == 'trend' and not set(direct) & AI_WORDS:   # every scouted ref is a "Claude edited this" reel
            out[kind] = []; continue
        rows = [(score(i, q), i) for i in cat['items'] if i['kind'] == kind]
        rows = [r for r in rows if r[0] >= 1]      # no match -> say so instead of padding with noise
        rows.sort(key=lambda r: -r[0])
        out[kind] = [dict(id=i['id'], name=i['name'], score=round(s, 1), why=i.get('look', '')[:110],
                          needs=i.get('needs', ''), warn=i.get('warn', '')) for s, i in rows[:n]]
    return out

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--json']
    if not args: print(__doc__); sys.exit(1)
    res = suggest(' '.join(args))
    if '--json' in sys.argv: print(json.dumps(res, indent=1)); sys.exit()
    for kind, rows in res.items():
        print(f'\n{kind.upper()}S')
        if not rows: print('  (no clear match: browse them in the picker)')
        for r in rows:
            extra = (f"  [needs: {r['needs']}]" if r['needs'] else '') + (f"  ! {r['warn']}" if r['warn'] else '')
            print(f"  {r['score']:>4}  {r['id']:<26} {r['why']}{extra}")
    print('\nPick visually: bin/reel-pick  ->  http://localhost:8771')
