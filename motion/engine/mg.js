/* mg.js — a small motion-graphics engine for HyperFrames canvas films.
 *
 * Every frame is a pure function of time: film.draw(ctx, t). Nothing is stored between
 * frames, so any frame can be rendered alone (seek-safe) and the renderer can sample
 * sub-frames for motion blur.
 *
 * What is in here, and why (see formats/motion-design.md):
 *   - springs that never overshoot (critically damped), exponential ease in/out for wipes
 *   - tracks: a value that springs to each new keyframe at its time, superposed
 *   - a beat clock (moves start a little before the beat so they land on it)
 *   - three inks that draw the SAME geometry: pencil on paper, clean line on blueprint,
 *     light on black (line density, never glow)
 *   - pencil strokes (resampled, sine wobble re-phased 8x a second, doubled, paper tooth)
 *   - hatching / scan-line fills, hatched type, regular-polygon morphs with constant
 *     arc length, a constant-length line that curls into a circle, a wire cube with
 *     hidden edges dashed and switchable perspective, gears, flood and scan-line wipes.
 */
(function (root) {
  const MG = {};
  const TAU = Math.PI * 2;

  // ---------- time ----------
  MG.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  MG.lerp = (a, b, t) => a + (b - a) * t;
  MG.prog = (t, a, b) => MG.clamp((t - a) / (b - a));
  /** critically damped spring: 0 -> 1, never passes 1. dt in seconds since the move began. */
  MG.spring = (dt, w = 22) => (dt <= 0 ? 0 : 1 - (1 + w * dt) * Math.exp(-w * dt));
  MG.expoOut = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
  MG.expoIn = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : Math.pow(2, 10 * x - 10));
  MG.expoInOut = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2);
  MG.accel = (x) => x * x * x; // for things that leave, accelerating

  /** A value that springs to each keyframe from its time on. keys: [[t, value, w?], ...]
   *  value may be a number or an array of numbers. The first key is the starting value. */
  MG.track = (keys, lead = 0.05) => (t) => {
    let v = keys[0][1];
    const isArr = Array.isArray(v);
    v = isArr ? v.slice() : v;
    for (let i = 1; i < keys.length; i++) {
      const [ti, vi, w] = keys[i];
      const k = MG.spring(t - (ti - lead), w || 22);
      if (k <= 0) continue;
      const prev = keys[i - 1][1];
      if (isArr) for (let j = 0; j < v.length; j++) v[j] += (vi[j] - prev[j]) * k;
      else v += (vi - prev) * k;
    }
    return v;
  };

  /** beat clock: bpm, lead (s). b(n) = time the n-th beat lands; on(t,n) = seconds since a move that lands on beat n began */
  MG.beats = (bpm, lead = 0.05) => {
    const B = 60 / bpm;
    return { B, at: (n) => n * B, start: (n) => n * B - lead, since: (t, n) => t - (n * B - lead), index: (t) => Math.floor(t / B + 1e-6) };
  };

  // ---------- randomness ----------
  MG.rng = (seed) => {
    let a = seed >>> 0;
    return () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  // ---------- colour ----------
  MG.hex = (h) => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  MG.rgba = (h, a = 1) => { const [r, g, b] = MG.hex(h); return `rgba(${r},${g},${b},${a})`; };
  MG.mixHex = (a, b, t) => { const A = MG.hex(a), B = MG.hex(b); return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * t)).join(',')})`; };

  // ---------- geometry ----------
  MG.poly = (n, r, cx = 0, cy = 0, rot = -Math.PI / 2) => Array.from({ length: n }, (_, i) => [cx + r * Math.cos(rot + (i * TAU) / n), cy + r * Math.sin(rot + (i * TAU) / n)]);
  MG.pathLen = (pts, closed) => { let L = 0; const n = pts.length; for (let i = 0; i < (closed ? n : n - 1); i++) { const a = pts[i], b = pts[(i + 1) % n]; L += Math.hypot(b[0] - a[0], b[1] - a[1]); } return L; };
  /** resample a polyline to exactly N points evenly spaced along its length */
  MG.resample = (pts, N, closed = true) => {
    const segs = []; const n = pts.length; let L = 0;
    for (let i = 0; i < (closed ? n : n - 1); i++) { const a = pts[i], b = pts[(i + 1) % n]; const l = Math.hypot(b[0] - a[0], b[1] - a[1]); segs.push([a, b, L, l]); L += l; }
    const out = []; let si = 0;
    for (let k = 0; k < N; k++) {
      const d = closed ? (L * k) / N : (L * k) / (N - 1);
      while (si < segs.length - 1 && segs[si][2] + segs[si][3] < d) si++;
      const [a, b, s0, l] = segs[si]; const u = l ? (d - s0) / l : 0;
      out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]);
    }
    return out;
  };
  MG.lerpPts = (A, B, t) => A.map((p, i) => [p[0] + (B[i][0] - p[0]) * t, p[1] + (B[i][1] - p[1]) * t]);
  MG.rotPts = (pts, a, cx = 0, cy = 0) => { const c = Math.cos(a), s = Math.sin(a); return pts.map(([x, y]) => [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c]); };
  MG.movePts = (pts, dx, dy, sc = 1) => pts.map(([x, y]) => [x * sc + dx, y * sc + dy]);

  /** a line of fixed length L whose curvature k grows until it closes into a circle (k = 2π/L). */
  MG.curl = (L, k, cx, cy, N = 240) => {
    const pts = [];
    for (let i = 0; i < N; i++) {
      const s = -L / 2 + (L * i) / (N - 1);
      if (Math.abs(k) < 1e-6) pts.push([cx + s, cy]);
      else pts.push([cx + Math.sin(k * s) / k, cy - (1 - Math.cos(k * s)) / k + (1 - Math.cos((k * L) / 2)) / k / 2]);
    }
    return pts;
  };

  /** gear outline: teeth n, pitch radius R, tooth depth d */
  MG.gear = (n, R, d, cx, cy, rot = 0) => {
    const pts = []; const per = TAU / n;
    for (let i = 0; i < n; i++) {
      const a = rot + i * per;
      const q = [[-0.5, R - d / 2], [-0.32, R + d / 2], [0.12, R + d / 2], [0.3, R - d / 2]];
      for (const [f, r] of q) pts.push([cx + r * Math.cos(a + f * per), cy + r * Math.sin(a + f * per)]);
    }
    return pts;
  };

  /** cube: rotate (ry about Y, rx about X), persp 0..1 blends ortho -> perspective. Returns {verts2d, edges:[[i,j,hidden]]} */
  MG.cube = (size, cx, cy, ry, rx, persp = 0, depth = 1) => {
    const V = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map(([x, y, z]) => [x, y, z * depth]);
    const cyR = Math.cos(ry), syR = Math.sin(ry), cx_ = Math.cos(rx), sx_ = Math.sin(rx);
    const R = V.map(([x, y, z]) => { let X = x * cyR + z * syR, Z = -x * syR + z * cyR; let Y = y * cx_ - Z * sx_; Z = y * sx_ + Z * cx_; return [X, Y, Z]; });
    const P = R.map(([x, y, z]) => { const f = 1 / (1 + persp * z * 0.2); return [cx + x * size * f, cy + y * size * f]; });
    const faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [3, 2, 6, 7], [0, 3, 7, 4], [1, 2, 6, 5]];
    const vis = faces.map((f) => { const [a, b, c] = f.map((i) => P[i]); return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]); });
    // orientation of a front face depends on winding; front faces are those whose sign matches face 0 when it faces us
    const front = vis.map((s, i) => { const f = faces[i]; const z = f.reduce((acc, j) => acc + R[j][2], 0) / 4; return z < 0 || (Math.abs(z) < 1e-9 && s !== 0); });
    const E = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
    const edges = E.map(([i, j]) => { const adj = faces.map((f, k) => (f.includes(i) && f.includes(j) ? k : -1)).filter((k) => k >= 0); return [i, j, !adj.some((k) => front[k])]; });
    return { P, edges, faces, front };
  };

  // ---------- inks ----------
  MG.INKS = {
    paper: { kind: 'pencil', bg: '#EDE6D5', grid: '#1B3ED2', gridA: 0.13, gridA5: 0.26, line: '#16161A', accent: '#1B3ED2', text: '#16161A' },
    blueprint: { kind: 'clean', bg: '#1B3ED2', grid: '#FFFFFF', gridA: 0.13, gridA5: 0.24, line: '#FFFFFF', accent: '#45F0DD', text: '#FFFFFF' },
    holo: { kind: 'holo', bg: '#07080A', grid: '#45F0DD', gridA: 0.1, gridA5: 0.2, line: '#45F0DD', accent: '#FFFFFF', text: '#45F0DD' },
  };

  MG.grid = (ctx, W, H, ink, step = 60, ox = 0, oy = 0) => {
    ctx.save(); ctx.fillStyle = ink.bg; ctx.fillRect(0, 0, W, H);
    for (let pass = 0; pass < 2; pass++) {
      ctx.strokeStyle = MG.rgba(ink.grid, pass ? ink.gridA5 : ink.gridA); ctx.lineWidth = pass ? 1.4 : 1; ctx.beginPath();
      for (let i = -1, x = ((ox % step) + step) % step - step; x < W + step; x += step, i++) { const idx = Math.round((x - ox) / step); if ((idx % 5 === 0) !== !!pass) continue; ctx.moveTo(x, 0); ctx.lineTo(x, H); }
      for (let y = ((oy % step) + step) % step - step; y < H + step; y += step) { const idx = Math.round((y - oy) / step); if ((idx % 5 === 0) !== !!pass) continue; ctx.moveTo(0, y); ctx.lineTo(W, y); }
      ctx.stroke();
    }
    ctx.restore();
  };

  /** paper grain, drawn once and reused */
  let grainCanvas = null;
  MG.grain = (ctx, W, H, alpha = 0.06) => {
    if (!grainCanvas) {
      grainCanvas = document.createElement('canvas'); grainCanvas.width = 512; grainCanvas.height = 512;
      const g = grainCanvas.getContext('2d'); const img = g.createImageData(512, 512); const r = MG.rng(7);
      for (let i = 0; i < img.data.length; i += 4) { const v = 120 + r() * 135; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
      g.putImageData(img, 0, 0);
    }
    ctx.save(); ctx.globalAlpha = alpha; ctx.globalCompositeOperation = 'multiply';
    for (let y = 0; y < H; y += 512) for (let x = 0; x < W; x += 512) ctx.drawImage(grainCanvas, x, y);
    ctx.restore();
  };

  const wobble = (pts, t, seed, amp, closed) => {
    const ph = Math.floor(t * 8) / 8; // re-phase 8x a second: the hand never holds still
    const P = MG.resample(pts, Math.max(8, Math.round(MG.pathLen(pts, closed) / 6)), closed);
    const n = P.length; const out = []; let s = 0;
    for (let i = 0; i < n; i++) {
      const a = P[(i - 1 + n) % n], b = P[(i + 1) % n];
      const dx = closed || (i > 0 && i < n - 1) ? b[0] - a[0] : (i === 0 ? P[1][0] - P[0][0] : P[n - 1][0] - P[n - 2][0]);
      const dy = closed || (i > 0 && i < n - 1) ? b[1] - a[1] : (i === 0 ? P[1][1] - P[0][1] : P[n - 1][1] - P[n - 2][1]);
      const l = Math.hypot(dx, dy) || 1; s += 6;
      const o = amp * (Math.sin(s * 0.011 + ph * 9.1 + seed) + 0.55 * Math.sin(s * 0.047 + ph * 23.7 + seed * 1.7));
      out.push([P[i][0] - (dy / l) * o, P[i][1] + (dx / l) * o]);
    }
    return out;
  };
  const tracePath = (ctx, P, closed) => { ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]); for (let i = 1; i < P.length; i++) ctx.lineTo(P[i][0], P[i][1]); if (closed) ctx.closePath(); };

  /** stroke a polyline in the current ink. opts: {t, w, color, closed, seed, dash, hidden, draw (0..1 partial)} */
  MG.stroke = (ctx, ink, pts, o = {}) => {
    const closed = !!o.closed; let P = pts;
    if (o.draw != null && o.draw < 1) { if (o.draw <= 0) return; const R = MG.resample(pts, 200, closed); P = R.slice(0, Math.max(2, Math.round(R.length * o.draw))); }
    const closedNow = closed && (o.draw == null || o.draw >= 1);
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    const w = o.w || 4; const col = o.color || ink.line;
    if (ink.kind === 'pencil') {
      const seed = o.seed || 1;
      ctx.strokeStyle = MG.rgba(col, 0.9); ctx.lineWidth = w; if (o.hidden) ctx.setLineDash([10, 10]);
      tracePath(ctx, wobble(P, o.t || 0, seed, (o.amp || 1.1), closedNow), closedNow); ctx.stroke();
      ctx.strokeStyle = MG.rgba(col, 0.4); ctx.lineWidth = w * 0.5;
      tracePath(ctx, wobble(P, o.t || 0, seed + 3.3, (o.amp || 1.1) * 2.2, closedNow), closedNow); ctx.stroke();
    } else if (ink.kind === 'clean') {
      ctx.strokeStyle = col; ctx.lineWidth = o.hidden ? w * 0.55 : w; if (o.hidden) ctx.setLineDash([12, 9]);
      tracePath(ctx, P, closedNow); ctx.stroke();
    } else {
      ctx.strokeStyle = col; ctx.lineWidth = o.hidden ? w * 0.6 : w; if (o.hidden) ctx.setLineDash([12, 9]);
      tracePath(ctx, P, closedNow); ctx.stroke();
      if (!o.hidden) { ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = w * 0.3; tracePath(ctx, P, closedNow); ctx.stroke(); }
    }
    ctx.restore();
  };

  /** fill a closed polygon with the ink's texture. amount 0..1 reveals the lines in order (sweep). */
  MG.fill = (ctx, ink, pts, o = {}) => {
    const amount = o.amount == null ? 1 : o.amount; if (amount <= 0) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity; for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    ctx.save(); tracePath(ctx, pts, true); ctx.clip();
    if (o.solid) { ctx.globalAlpha = o.solid; ctx.fillStyle = o.color || ink.accent; ctx.fillRect(x0, y0, x1 - x0, y1 - y0); ctx.globalAlpha = 1; }
    const col = o.color || (ink.kind === 'pencil' ? ink.accent : ink.line);
    if (ink.kind === 'holo') {
      const pitch = 8; const lit = o.lit == null ? 0.7 : o.lit; ctx.fillStyle = col;
      for (let y = Math.floor(y0 / pitch) * pitch, i = 0; y < y1; y += pitch, i++) { if ((y - y0) / (y1 - y0) > amount) break; const l = typeof lit === 'function' ? lit(y) : lit; ctx.fillRect(x0, y, x1 - x0, Math.max(0.6, l * 3.6)); }
    } else {
      const gap = o.gap || (ink.kind === 'pencil' ? 11 : 9); const ang = o.angle == null ? -Math.PI / 4 : o.angle; const d = Math.hypot(x1 - x0, y1 - y0);
      const cxm = (x0 + x1) / 2, cym = (y0 + y1) / 2; const c = Math.cos(ang), s = Math.sin(ang); const N = Math.ceil(d / gap); const shown = Math.floor(N * amount);
      ctx.strokeStyle = ink.kind === 'pencil' ? MG.rgba(col, 0.62) : MG.rgba(col, 0.75); ctx.lineWidth = ink.kind === 'pencil' ? 1.8 : 1.4;
      ctx.beginPath();
      for (let i = 0; i < shown; i++) {
        const off = -d / 2 + i * gap; const jx = ink.kind === 'pencil' ? Math.sin(i * 12.9898) * 1.4 : 0;
        ctx.moveTo(cxm + off * -s - c * d / 2 + jx, cym + off * c - s * d / 2); ctx.lineTo(cxm + off * -s + c * d / 2 - jx, cym + off * c + s * d / 2);
      }
      ctx.stroke();
      if (o.cross && o.cross > 0) {
        ctx.beginPath(); const sh = Math.floor(N * o.cross);
        for (let i = 0; i < sh; i++) { const off = -d / 2 + i * gap; ctx.moveTo(cxm + off * s - c * d / 2, cym + off * c + s * d / 2); ctx.lineTo(cxm + off * s + c * d / 2, cym + off * c - s * d / 2); }
        ctx.stroke();
      }
    }
    ctx.restore();
  };

  /** big type cut from the ink's fill texture, with a doubled outline. Returns the text width. */
  const textCanvas = {};
  MG.word = (ctx, ink, str, x, y, o = {}) => {
    const size = o.size || 200; const font = `${o.weight || 900} ${size}px ${o.family || 'Geist, Inter, Helvetica, Arial, sans-serif'}`;
    ctx.save(); ctx.font = font; if (o.tracking) ctx.letterSpacing = `${o.tracking}px`;
    let w = ctx.measureText(str).width; const sx = o.fitW ? o.fitW / w : 1; const sy = o.squash != null ? o.squash : 1;
    ctx.translate(x, y); ctx.scale(sx, sx * sy); ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    const key = `${font}|${str}|${o.tracking || 0}`; let tc = textCanvas[key];
    const pad = 20, tw = Math.ceil(w) + pad * 2, th = Math.ceil(size * 1.05) + pad * 2;
    if (!tc) { tc = document.createElement('canvas'); tc.width = tw; tc.height = th; textCanvas[key] = tc; }
    const g = tc.getContext('2d'); g.clearRect(0, 0, tw, th); g.font = font; if (o.tracking) g.letterSpacing = `${o.tracking}px`; g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    g.fillStyle = '#000'; g.fillText(str, tw / 2, th - pad - size * 0.02);
    g.globalCompositeOperation = 'source-in';
    const col = o.color || (ink.kind === 'pencil' ? ink.text : ink.line);
    if (o.solid) { g.fillStyle = o.solidColor || col; g.fillRect(0, 0, tw, th); }
    else if (ink.kind === 'holo') { g.fillStyle = col; for (let yy = 0; yy < th; yy += 8) g.fillRect(0, yy, tw, 5.2); }
    else { g.strokeStyle = MG.rgba(col, ink.kind === 'pencil' ? 0.85 : 0.9); g.lineWidth = ink.kind === 'pencil' ? 2.2 : 1.8; g.beginPath(); for (let k = -th; k < tw; k += ink.kind === 'pencil' ? 7 : 6) { g.moveTo(k, th); g.lineTo(k + th, 0); } g.stroke(); }
    g.globalCompositeOperation = 'source-over';
    ctx.drawImage(tc, -tw / 2, -(th - pad - size * 0.02));
    if (!o.noOutline) {
      ctx.strokeStyle = MG.rgba(col, ink.kind === 'pencil' ? 0.9 : 1); ctx.lineWidth = ink.kind === 'pencil' ? 2.2 : 2.4;
      ctx.strokeText(str, 0, -size * 0.02);
      if (ink.kind === 'pencil') { ctx.strokeStyle = MG.rgba(col, 0.35); ctx.lineWidth = 1.2; const j = (Math.floor((o.t || 0) * 8) % 3) - 1; ctx.strokeText(str, 1.6 + j * 0.6, -size * 0.02 - 1.4); }
      if (ink.kind === 'holo') { ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 0.9; ctx.strokeText(str, 0, -size * 0.02); }
    }
    ctx.restore();
    return w * sx;
  };

  /** small tracked label */
  MG.label = (ctx, ink, str, x, y, o = {}) => {
    ctx.save(); ctx.font = `${o.weight || 700} ${o.size || 26}px Geist, Inter, Helvetica, Arial, sans-serif`; ctx.letterSpacing = `${(o.track == null ? 0.2 : o.track) * (o.size || 26)}px`;
    ctx.fillStyle = o.color || ink.text; ctx.globalAlpha = o.alpha == null ? 1 : o.alpha; ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'alphabetic'; ctx.fillText(str, x, y); ctx.restore();
  };

  // ---------- transitions ----------
  /** draw two worlds split by a clip shape. inside(ctx) draws the new world. */
  MG.within = (ctx, pts, drawInside) => { ctx.save(); tracePath(ctx, pts, true); ctx.clip(); drawInside(); ctx.restore(); };
  MG.belowLine = (ctx, W, y, drawBelow) => { ctx.save(); ctx.beginPath(); ctx.rect(0, y, W, 99999); ctx.clip(); drawBelow(); ctx.restore(); };

  MG.tracePath = tracePath;
  MG.TAU = TAU;
  root.MG = MG;
})(typeof window !== 'undefined' ? window : globalThis);
