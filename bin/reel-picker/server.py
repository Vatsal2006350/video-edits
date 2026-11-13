#!/usr/bin/env python3
"""Reel picker: browse every template / effect / trend ref with moving previews, get suggestions
for a brief, and save the selection to videos/<slug>/pick.json for the agent to build from.

  bin/reel-pick [port]   -> http://localhost:8771
Endpoints: /  /catalog.json  /previews/*  /api/suggest?q=  /api/picks  POST /api/save
"""
import json, os, re, sys, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(__file__))
from suggest import suggest, CATALOG

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, '..', '..'))
PREV = os.path.join(WS, 'catalog', 'previews')
TYPES = {'.jpg': 'image/jpeg', '.png': 'image/png', '.mp4': 'video/mp4', '.json': 'application/json',
         '.html': 'text/html; charset=utf-8'}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)): body = json.dumps(body).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control', 'no-cache')
        self.end_headers(); self.wfile.write(body)

    def file(self, path):
        if not os.path.isfile(path): return self.send(404, {'error': 'not found'})
        size = os.path.getsize(path); ctype = TYPES.get(os.path.splitext(path)[1].lower(), 'application/octet-stream')
        rng = self.headers.get('Range')
        with open(path, 'rb') as fh:
            if rng and ctype == 'video/mp4':           # Safari needs byte ranges for <video>
                a, _, b = rng.replace('bytes=', '').partition('-')
                a = int(a or 0); b = int(b) if b else size - 1
                fh.seek(a); data = fh.read(b - a + 1)
                self.send_response(206); self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
            else:
                data = fh.read(); self.send_response(200)
        self.send_header('Content-Type', ctype); self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path in ('/', '/index.html'): return self.file(os.path.join(HERE, 'picker.html'))
        if u.path == '/catalog.json': return self.file(CATALOG)
        if u.path.startswith('/previews/'):
            p = os.path.realpath(os.path.join(PREV, urllib.parse.unquote(u.path[len('/previews/'):])))
            if not p.startswith(os.path.realpath(PREV) + os.sep): return self.send(403, {'error': 'outside previews'})
            return self.file(p)
        if u.path == '/api/suggest': return self.send(200, suggest(q.get('q', [''])[0]))
        if u.path == '/api/picks':
            rows = []
            for d in sorted(os.listdir(os.path.join(WS, 'videos'))):
                p = os.path.join(WS, 'videos', d, 'pick.json')
                if os.path.isfile(p):
                    j = json.load(open(p)); rows.append(dict(slug=d, saved=j.get('saved'), brief=j.get('brief', '')))
            return self.send(200, sorted(rows, key=lambda r: r['saved'] or '', reverse=True))
        self.send(404, {'error': 'not found'})

    def do_POST(self):
        if self.path != '/api/save': return self.send(404, {'error': 'not found'})
        try: j = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        except ValueError: return self.send(400, {'error': 'bad json'})
        slug = re.sub(r'[^a-z0-9-]+', '-', (j.get('slug') or '').lower()).strip('-')
        if not slug: return self.send(400, {'error': 'give the reel a short name'})
        if not j.get('template') and not j.get('effects'): return self.send(400, {'error': 'pick a template or at least one effect'})
        d = os.path.join(WS, 'videos', slug); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, 'pick.json')
        if os.path.exists(p):                         # keep history instead of overwriting a previous choice
            os.rename(p, os.path.join(d, f'pick.{time.strftime("%Y%m%d-%H%M%S")}.json'))
        fx = [dict(fx=e['id'], start=float(e.get('start') or 0), end=float(e.get('end') or 0),
                   **({'text': e['text']} if e.get('text') else {})) for e in j.get('effects', [])]
        pick = dict(slug=slug, saved=time.strftime('%Y-%m-%dT%H:%M:%S'), brief=j.get('brief', ''),
                    footage=j.get('footage', ''), template=j.get('template'), trend_refs=j.get('trends', []),
                    notes=j.get('notes', ''), fx_plan={'effects': fx},
                    next='Agent: read this, follow the template format file, then bin/fx-extra.sh --plan '
                         'with fx_plan on the graded base (--check stills first).')
        json.dump(pick, open(p, 'w'), indent=1)
        self.send(200, dict(ok=True, path=os.path.relpath(p, WS)))

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8771
    print(f'reel picker on http://localhost:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
