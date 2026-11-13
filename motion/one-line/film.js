/* "One line becomes a reel" — a 24 s looping vertical film (1080x1920, 120 BPM, 48 beats, 12 bars).
 * Brief: motion/one-line/BRIEF.md (written by bin/motion-brief.py, preset drafting-inks).
 * One pencil line is promoted twice: graphite on paper -> clean line on blueprint -> light on black,
 * and never leaves the screen. Every shot is made out of the one before it. No cuts, no fades.
 * Facts on screen: 88 effects (channel-facts.json effects_count), 76 looks (catalog), 1080x1920, 30 fps, 120 BPM, 0 cuts.
 */
(function () {
  const { clamp, lerp, prog, spring, expoOut, expoIn, expoInOut, accel, track, INKS, TAU } = MG;
  const W = 1080, H = 1920, CX = 540, CY = 900, DUR = 24, BPM = 120;
  const BAR = ['DRAFT', 'TYPE', 'CURVE', 'MORPH', 'TILE', 'SOLID', 'GEAR', 'PANEL', 'DATA', 'LIGHT', 'WAVE', 'END'];
  const beat = MG.beats(BPM, 0.05);
  const sp = (t, t0, w = 22) => spring(t - (t0 - 0.05), w); // a move that LANDS on t0

  // ---------- shared measures ----------
  const WORD = 'REELS', WORD_W = 720, WORD_SIZE = 230; // centred work is bounded by 724 px (IG safe box)
  const BASE = CY + 90; // baseline of the hero word
  const CAP = WORD_SIZE * 0.72 * 1.02;
  const RAIL0 = BASE - CAP - 96; // rail 96 px above the letters
  const LINE_L = 720; // the line, once crushed

  // ---------- small parts ----------
  const hline = (x0, x1, y) => [[x0, y], [x1, y]];
  const rectPts = (x, y, w, h) => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
  const typed = (s, k) => s.slice(0, Math.round(s.length * clamp(k)));
  const hexPts = (r, x, y, N) => { const p = MG.poly(6, r, x, y); return N ? MG.resample(p, N) : p; };
  const ccw = (pts) => [pts[0], ...pts.slice(1).reverse()]; // match the curl's winding

  function letters(ctx, ink, str, cx, base, size, each, o = {}) {
    // draw a word one letter at a time; each(i, n) -> {dx, dy, sy, alpha}
    ctx.save(); ctx.font = `900 ${size}px Geist, Inter, Helvetica, Arial, sans-serif`;
    const widths = [...str].map((c) => ctx.measureText(c).width); const total = widths.reduce((a, b) => a + b, 0);
    ctx.restore();
    const sx = o.fitW ? o.fitW / total : 1; let x = cx - (total * sx) / 2;
    [...str].forEach((c, i) => {
      const m = each(i, str.length) || {}; const cw = widths[i] * sx;
      if ((m.alpha == null ? 1 : m.alpha) > 0.01 && c !== ' ') {
        ctx.save(); ctx.globalAlpha = m.alpha == null ? 1 : m.alpha;
        if (m.sy != null) { ctx.translate(0, base + (m.dy || 0)); ctx.scale(1, Math.max(0.0001, m.sy)); ctx.translate(0, -(base + (m.dy || 0))); }
        MG.word(ctx, ink, c, x + cw / 2 + (m.dx || 0), base + (m.dy || 0), { size, fitW: cw, t: o.t, color: o.color, noOutline: o.noOutline });
        ctx.restore();
      }
      x += cw;
    });
  }

  function labels(ctx, ink, t) {
    const bi = clamp(Math.floor(t / 2), 0, 11); const b = Math.min(48, beat.index(t) + 1);
    MG.label(ctx, ink, `FIG. ${String(bi + 1).padStart(2, '0')} — ${BAR[bi]}`, 96, 318, { size: 24, weight: 700, track: 0.22, alpha: 0.85 });
    MG.label(ctx, ink, `BEAT ${String(b).padStart(2, '0')} / 48`, 900, 1512, { size: 24, weight: 700, track: 0.22, align: 'right', alpha: 0.85 });
  }

  // ---------- rails (bars 1-2) ----------
  const gap = track([[0, 0], [1.0, 140, 20], [1.5, 300, 20], [2.0, 210, 26], [2.5, 210], [3.0, 0, 40], [3.12, 230, 30], [3.5, 260, 22], [4.0, 0, 34]]);
  const railMid = (t) => {
    if (t < 0.36) return RAIL0;
    if (t < 0.5) return lerp(RAIL0, BASE + 26, accel(prog(t, 0.36, 0.5)));
    return lerp(BASE + 26, CY, sp(t, 1.0, 18));
  };
  const railW = (t) => lerp(760, 680, sp(t, 1.0, 18)) + (t > 3.9 ? (LINE_L - 680) * sp(t, 4.0, 30) : 0);

  function hookAndType(ctx, ink, t) {
    const g = t < 0.95 ? 0 : gap(t); const mid = railMid(t); const rw = railW(t);
    const top = mid - g / 2, bot = mid + g / 2;
    // hero word, pressed flat by the falling rail
    if (t < 0.5) {
      const squash = clamp((BASE - (t < 0.36 ? RAIL0 : mid)) / CAP, 0, 1);
      const sy = t < 0.36 ? 1 : clamp((BASE - mid) / (BASE - RAIL0), 0, 1);
      if (sy > 0.01) {
        ctx.save(); ctx.translate(0, BASE); ctx.scale(1, sy); ctx.translate(0, -BASE);
        MG.word(ctx, ink, WORD, CX, BASE, { size: WORD_SIZE, fitW: WORD_W, t });
        ctx.restore();
      }
      const k = 1 - prog(t, 0.0, 0.3); // the small lines un-type
      MG.label(ctx, ink, typed('INTRODUCING', k), CX, RAIL0 - 34, { size: 26, align: 'center', weight: 700, track: 0.3 });
      MG.label(ctx, ink, typed('A MOTION SYSTEM', k), CX, BASE + 70, { size: 26, align: 'center', weight: 700, track: 0.3 });
      void squash;
    }
    // the rails
    MG.stroke(ctx, ink, hline(CX - rw / 2, CX + rw / 2, top), { t, w: 5, seed: 2 });
    if (g > 0.5) MG.stroke(ctx, ink, hline(CX - rw / 2, CX + rw / 2, bot), { t, w: 5, seed: 5 });
    // ruler ticks sweep along the top rail
    if (t > 1.0 && t < 4.0) {
      const k = expoOut(prog(t, 1.0, 1.45)); const n = 41; const shown = Math.floor(n * k);
      const fade = 1 - prog(t, 3.8, 4.0);
      ctx.save(); ctx.globalAlpha = fade;
      for (let i = 0; i < shown; i++) { const x = CX - rw / 2 + (rw * i) / (n - 1); MG.stroke(ctx, ink, [[x, top], [x, top - (i % 5 === 0 ? 22 : 11)]], { t, w: 2.2, seed: i, color: ink.accent, amp: 0.4 }); }
      ctx.restore();
    }
    // a live height dimension
    if (t > 1.45 && t < 3.95) {
      const a = clamp(prog(t, 1.45, 1.7)) * (1 - prog(t, 3.75, 3.95)); const x = CX - rw / 2 - 40; // left of the rails: the right edge belongs to Instagram's buttons
      ctx.save(); ctx.globalAlpha = a;
      MG.stroke(ctx, ink, [[x, top], [x, bot]], { t, w: 2, color: ink.accent, amp: 0.4 });
      MG.stroke(ctx, ink, [[x - 10, top], [x + 10, top]], { t, w: 2, color: ink.accent, amp: 0.3 });
      MG.stroke(ctx, ink, [[x - 10, bot], [x + 10, bot]], { t, w: 2, color: ink.accent, amp: 0.3 });
      MG.label(ctx, ink, String(Math.round(g)), x - 14, mid + 9, { size: 24, weight: 800, color: ink.accent, track: 0.05, align: 'right' });
      ctx.restore();
    }
    // words live in the slot between the rails
    if (t >= 1.95 && t < 4.05 && g > 0.5) {
      ctx.save(); ctx.beginPath(); ctx.rect(CX - rw / 2 - 2, top + 3, rw + 4, g - 6); ctx.clip();
      const size = 150; const base = bot - (g - size * 0.72) / 2;
      if (t < 2.5) { // ONE LINE rises through the baseline, then lifts out of the top
        const out = expoIn(prog(t, 2.33, 2.48)) * (g + 40);
        letters(ctx, ink, 'ONE LINE', CX, base, size, (i) => ({ dy: (1 - spring(t - (2.0 + i * 0.035), 30)) * (size + 10) - out }), { fitW: 620, t });
      } else if (t < 3.0) { // BECOMES whips in from the left
        const dx = -1400 * (1 - expoOut(prog(t, 2.45, 2.65)));
        MG.word(ctx, ink, 'BECOMES', CX + dx, base, { size, fitW: 640, t });
      } else if (t < 3.5) { // the rails clap shut on it and stretch A REEL out of the line
        const sy = clamp(g / 230); const flyK = expoIn(prog(t, 3.32, 3.5));
        if (t < 3.06) MG.word(ctx, ink, 'BECOMES', CX, bot, { size, fitW: 640, t, squash: clamp(g / 210) });
        else letters(ctx, ink, 'A REEL', CX, base, size, (i, n) => ({ sy, dx: (i < n / 2 ? -1 : 1) * flyK * 900 * (0.5 + Math.abs(i - (n - 1) / 2) / n) }), { fitW: 580, t });
      } else { // REELS in blue pencil, letters dropping one every 0.05 s; at 4.0 the rails crush it
        const sy = t > 3.9 ? clamp(g / 260) : 1;
        letters(ctx, ink, WORD, CX, base, size + 20, (i) => ({ dy: -(1 - spring(t - (3.5 + i * 0.05), 30)) * 500, sy }), { fitW: 640, t, color: ink.accent });
      }
      ctx.restore();
    }
  }

  // ---------- bar 3: curves ----------
  function bez(p0, h1, h2, p3, N = 120) { const out = []; for (let i = 0; i < N; i++) { const u = i / (N - 1), v = 1 - u; out.push([v * v * v * p0[0] + 3 * v * v * u * h1[0] + 3 * v * u * u * h2[0] + u * u * u * p3[0], v * v * v * p0[1] + 3 * v * v * u * h1[1] + 3 * v * u * u * h2[1] + u * u * u * p3[1]]); } return out; }
  function curves(ctx, ink, t) {
    const x0 = CX - LINE_L / 2, x1 = CX + LINE_L / 2; const p0 = [x0, CY], p3 = [x1, CY];
    const out = sp(t, 4.1, 20) - sp(t, 5.0, 24); // handles out, then in
    const flip = sp(t, 4.5, 20); const ang = lerp(-58, 58, flip) * Math.PI / 180; const L = 300 * out;
    const h1 = [x0 + L * Math.cos(ang), CY + L * Math.sin(ang)], h2 = [x1 - L * Math.cos(ang), CY - L * Math.sin(ang)];
    const fan = sp(t, 4.5, 18) * (1 - sp(t, 5.5, 22)); const wave = sp(t, 5.0, 16) * (1 - sp(t, 5.5, 20));
    for (let c = 8; c >= 0; c--) {
      if (c > 0 && fan < 0.01) continue;
      const off = (c - 4) * 34 * fan; const N = 160; const base = bez(p0, [h1[0], h1[1] + off], [h2[0], h2[1] - off], p3, N);
      const pts = base.map(([x, y], i) => { const u = i / (N - 1); const env = Math.sin(Math.PI * u); return [x, y + wave * 70 * env * Math.sin(u * TAU * 2.75 - (t - 5) * 7 + c * 0.45)]; });
      MG.stroke(ctx, ink, pts, { t, w: c === 0 ? 5 : 2.4, seed: c + 1, color: c === 0 ? ink.line : ink.accent, amp: c === 0 ? 1.1 : 0.7 });
    }
    if (out > 0.02) { // pen-tool handles
      ctx.save(); ctx.globalAlpha = clamp(out * 1.4);
      for (const [p, h] of [[p0, h1], [p3, h2]]) {
        MG.stroke(ctx, ink, [p, h], { t, w: 2, color: ink.accent, amp: 0.3 });
        MG.stroke(ctx, ink, rectPts(p[0] - 9, p[1] - 9, 18, 18), { t, w: 2.2, closed: true, amp: 0.3 });
        MG.stroke(ctx, ink, MG.poly(16, 9, h[0], h[1]), { t, w: 2.2, closed: true, color: ink.accent, amp: 0.2 });
      }
      MG.label(ctx, ink, 'EASE', h1[0] + 18, h1[1] - 14, { size: 24, weight: 800, color: ink.accent });
      ctx.restore();
    }
  }

  // ---------- bar 4: morph ----------
  const N = 240;
  const shapeAt = (t) => {
    const k = sp(t, 6.1, 14); const curlK = k * TAU / LINE_L;
    let pts = MG.curl(LINE_L, curlK, CX, CY, N);
    if (k > 0.98) { // closed: hand over to resampled shapes, start point on top, same winding
      const R0 = LINE_L / TAU; const grow = sp(t, 6.35, 18); const r = lerp(R0, 235, grow);
      const circle = ccw(MG.resample(MG.poly(N, r, CX, CY), N));
      const tri = ccw(MG.resample(MG.poly(3, 235 * 1.25, CX, CY + 40), N));
      const sq = ccw(MG.resample(MG.poly(4, 235 * 1.18, CX, CY, -Math.PI / 4), N));
      const hex = ccw(MG.resample(MG.poly(6, 270, CX, CY), N));
      const a = sp(t, 6.5, 20), b = sp(t, 7.0, 20), c = sp(t, 7.5, 20);
      pts = MG.lerpPts(MG.lerpPts(MG.lerpPts(circle, tri, a), sq, b), hex, c);
      const turn = a * (1 - b) * (TAU / 3) * 1; // the triangle turns 120° as it forms
      if (turn) pts = MG.rotPts(pts, turn * (1 - a) + 0, CX, CY);
      const spin = (a - b) * TAU / 3; pts = MG.rotPts(pts, spin * 0.0, CX, CY);
    } else {
      // keep the curl centred on the frame while it closes
      let sx = 0, sy = 0; pts.forEach(([x, y]) => { sx += x; sy += y; }); sx /= N; sy /= N; pts = MG.movePts(pts, CX - sx * k - CX * (1 - k), (CY - sy) * k);
    }
    return pts;
  };
  function morph(ctx, ink, t) {
    const pts = shapeAt(t); const closed = sp(t, 6.1, 14) > 0.98;
    if (closed) MG.fill(ctx, ink, pts, { amount: prog(t, 7.15, 7.7), cross: prog(t, 7.6, 7.95) });
    MG.stroke(ctx, ink, pts, { t, w: 5, closed, seed: 3 });
  }

  // ---------- bar 5-6: tiles and cubes ----------
  const R_SMALL = 84, DX = Math.sqrt(3) * R_SMALL, DY = 1.5 * R_SMALL;
  const CELLS = (() => { const out = []; for (let q = -2; q <= 2; q++) for (let r = -2; r <= 2; r++) { const s = -q - r; if (Math.abs(s) > 2) continue; const ring = Math.max(Math.abs(q), Math.abs(r), Math.abs(s)); out.push({ x: DX * (q + r / 2), y: DY * r, ring }); } return out; })();
  function tiles(ctx, ink, t, opt = {}) {
    const shrink = sp(t, 8.0, 20); const r = lerp(270, R_SMALL, shrink);
    const ring1 = sp(t, 8.05, 18), ring2 = sp(t, 8.5, 18);
    const hatch = prog(t, 9.0, 9.45), solid = prog(t, 9.3, 9.6);
    const conv = sp(t, 10.5, 16); // bar 6: outer cubes slide into the centre
    const cubeLines = prog(t, 10.0, 10.35);
    for (const c of CELLS) {
      const k = c.ring === 0 ? 1 : c.ring === 1 ? ring1 : ring2; if (k <= 0.001) continue;
      const x = CX + c.x * k * (1 - conv), y = CY + c.y * k * (1 - conv);
      const rr = lerp(r * (c.ring === 2 ? clamp(ring2 * 1.2) : 1), 270, conv); // every cube grows into the one it slides into
      const hp = hexPts(rr, x, y);
      const fadeOut = c.ring === 0 ? 1 : 1 - conv * conv; if (fadeOut < 0.02) continue;
      ctx.save(); ctx.globalAlpha = fadeOut;
      if (ink.kind === 'pencil') MG.fill(ctx, ink, hp, { amount: hatch, cross: hatch * 0.9, solid: solid * 0.92 });
      if (!(c.ring > 0 && conv > 0.995)) MG.stroke(ctx, ink, hp, { t, w: c.ring === 0 ? 4 : 3, closed: true, seed: c.x + c.y });
      if (opt.cubes && cubeLines > 0) { // three visible edges + three hidden: a cube seen corner-on
        for (let j = 0; j < 6; j++) { const v = hp[j]; const hidden = j % 2 === 0; MG.stroke(ctx, ink, [[x, y], [lerp(x, v[0], cubeLines), lerp(y, v[1], cubeLines)]], { t, w: hidden ? 2 : 3, hidden, seed: j }); }
      }
      ctx.restore();
    }
  }

  // ---------- cube / gear (bars 6-8) ----------
  const CUBE_S = 270 / Math.sqrt(8 / 3);
  function cubeView(t) {
    // iso (45°, 35.26°) -> quarter turn with perspective -> facing front -> flat (gear) -> depth back
    const iso = [Math.PI / 4, Math.atan(1 / Math.sqrt(2))];
    const q = sp(t, 11.0, 14), f = sp(t, 11.5, 16);
    const ry = iso[0] + (Math.PI / 2) * q + (Math.PI / 4) * f; // 45° -> 135° (a quarter turn) -> 180° (facing front)
    const rx = iso[1] * (1 - f);
    const flat = sp(t, 12.0, 20) * (1 - sp(t, 13.6, 18)); const depth = 1 - flat;
    return { ry, rx, persp: q, depth };
  }
  function drawCube(ctx, ink, t, alpha = 1, unfold = 0) {
    const v = cubeView(t); const c = MG.cube(CUBE_S, CX, CY, v.ry, v.rx, v.persp, v.depth);
    ctx.save(); ctx.globalAlpha = alpha;
    for (const [i, j, hidden] of c.edges) MG.stroke(ctx, ink, [c.P[i], c.P[j]], { t, w: hidden ? 2.2 : 3.6, hidden, seed: i * 8 + j });
    ctx.restore();
    return c;
  }
  const gearRot = (t, ratio = 1) => { let a = 0; for (let k = 0; k < 6; k++) a += spring(t - (12.25 + k * 0.25 - 0.05), 30) * (Math.PI / 4); return a * ratio; };
  function gears(ctx, ink, t) {
    const toGear = sp(t, 12.1, 18) * (1 - sp(t, 13.5, 18));
    const side = CUBE_S * 2; const sq = ccw(MG.resample(MG.poly(4, side / Math.SQRT2, CX, CY, -Math.PI / 4), 320));
    const rot = gearRot(t); const g16 = ccw(MG.resample(MG.gear(16, 208, 26, CX, CY, rot - Math.PI / 2), 320));
    const pts = MG.lerpPts(sq, g16, toGear);
    MG.stroke(ctx, ink, pts, { t, w: 3.6, closed: true, seed: 7 });
    if (toGear > 0.6) {
      const a = clamp((toGear - 0.6) / 0.4);
      ctx.save(); ctx.globalAlpha = a; MG.stroke(ctx, ink, MG.poly(64, 208, CX, CY), { t, w: 1.6, hidden: true, closed: true }); MG.stroke(ctx, ink, MG.poly(32, 26, CX, CY), { t, w: 3, closed: true }); MG.label(ctx, ink, '16T', CX, CY + 70, { size: 26, weight: 800, align: 'center' }); ctx.restore();
    }
    const small = [[10, 130, -50, 12.5], [12, 156, -130, 13.0]];
    for (const [n, R, deg, t0] of small) {
      const k = sp(t, t0, 18) * (1 - sp(t, 13.5, 20)); if (k < 0.01) continue;
      const d = (208 + R) * k; const gx = CX + d * Math.cos((deg * Math.PI) / 180), gy = CY + d * Math.sin((deg * Math.PI) / 180);
      const rr = -rot * (16 / n) + Math.PI / n;
      MG.stroke(ctx, ink, MG.gear(n, R * k, 26 * k, gx, gy, rr), { t, w: 3.2, closed: true, seed: n });
      ctx.save(); ctx.globalAlpha = k; MG.stroke(ctx, ink, MG.poly(48, R * k, gx, gy), { t, w: 1.4, hidden: true, closed: true }); MG.stroke(ctx, ink, MG.poly(24, 18 * k, gx, gy), { t, w: 2.6, closed: true }); MG.label(ctx, ink, `${n}T`, gx, gy + 54 * k, { size: 24, weight: 800, align: 'center' }); ctx.restore();
    }
  }

  // ---------- bar 8-9: the panel ----------
  const PANELS = [ // [x, y, w, h] in the safe box
    [96, 372, 808, 82],    // header
    [96, 480, 300, 534],   // the 9:16 reel
    [420, 480, 484, 300],  // chart
    [420, 806, 232, 208],  // tile A
    [672, 806, 232, 208],  // tile B
    [96, 1040, 808, 120],  // timeline
  ];
  const CROSS = (() => { const s = 150; const c = [CX - s / 2, CY - s / 2]; return [[c[0], c[1] - s], [c[0] - s, c[1]], c, [c[0] + s, c[1]], [c[0], c[1] + s], [c[0], c[1] + 2 * s]].map(([x, y]) => [x, y, s, s]); })();
  const HEIGHTS = [42, 30, 36, 44, 50, 46, 52, 62, 50, 56, 62, 72, 60, 66, 58, 76, 56, 62, 68, 74, 70, 78, 86, 94];
  function panelRects(t) {
    const unfold = sp(t, 14.0, 16), slide = sp(t, 14.5, 18);
    const front = [CX - CUBE_S, CY - CUBE_S, CUBE_S * 2, CUBE_S * 2];
    return PANELS.map((p, i) => { const c = CROSS[i]; const a = front.map((v, j) => lerp(v, c[j], unfold)); return a.map((v, j) => lerp(v, p[j], slide)); });
  }
  function panel(ctx, ink, t) {
    const R = panelRects(t); const fill = prog(t, 15.0, 15.4);
    R.forEach(([x, y, w, h], i) => MG.stroke(ctx, ink, rectPts(x, y, w, h), { t, w: 3, closed: true, seed: i + 11 }));
    if (fill <= 0) return;
    const [hx, hy, hw, hh] = R[0]; ctx.save(); ctx.globalAlpha = fill;
    MG.label(ctx, ink, 'VIDEO-EDITS — MOTION REEL', hx + 26, hy + hh / 2 + 9, { size: 24, weight: 800, track: 0.14 });
    const ring = sp(t, 16.5, 18) * (1 - sp(t, 18.2, 18)); const light = sp(t, 17.0, 26);
    MG.label(ctx, ink, 'BARS', hx + hw - 300, hy + hh / 2 + 9, { size: 22, weight: 800, track: 0.14, alpha: 1 - ring * 0.6 });
    MG.label(ctx, ink, 'RING', hx + hw - 220, hy + hh / 2 + 9, { size: 22, weight: 800, track: 0.14, color: ring > 0.5 ? ink.accent : ink.text });
    MG.stroke(ctx, ink, rectPts(hx + hw - 118, hy + hh / 2 - 16, 64, 32), { t, w: 2.4, closed: true });
    MG.fill(ctx, ink, MG.poly(20, 11, hx + hw - 102 + light * 32, hy + hh / 2), { solid: 1, color: light > 0.5 ? ink.accent : ink.line });
    // the 9:16 reel frame: the film drawing itself in miniature (a hexagon, a line)
    const [rx, ry, rw, rh] = R[1];
    MG.fill(ctx, ink, rectPts(rx + 6, ry + 96, rw - 12, rh - 102), { amount: expoOut(prog(t, 15.45, 15.95)) * (1 - prog(t, 17.0, 17.3)), gap: 14 }); // hatching sweeps into the reel frame
    MG.label(ctx, ink, '1080 × 1920', rx + 22, ry + 40, { size: 22, weight: 800, track: 0.14 });
    MG.label(ctx, ink, '30 FPS', rx + 22, ry + 72, { size: 22, weight: 700, track: 0.14, alpha: 0.7 });
    MG.stroke(ctx, ink, MG.poly(6, 70, rx + rw / 2, ry + rh / 2 + 10), { t, w: 2.6, closed: true });
    MG.stroke(ctx, ink, hline(rx + 40, rx + rw - 40, ry + rh - 60), { t, w: 2.6 });
    // chart: one bar per second of this film
    const [cx, cy, cw, ch] = R[2]; const now = clamp(t, 0, DUR); const sec = Math.floor(now);
    const bw = (cw - 40) / HEIGHTS.length; const grow = prog(t, 15.0, 15.5);
    const bars = HEIGHTS.map((v, i) => { const hgt = (ch - 60) * (v / 100) * clamp(grow * 1.5 - i * 0.02); return [cx + 20 + i * bw, cy + ch - 20, bw - 5, hgt]; });
    if (ring < 0.01) bars.forEach(([x, y, w, h2], i) => {
      const pts = rectPts(x, y - h2, w, h2); const live = t > 16.0;
      if (live && i === sec) MG.fill(ctx, ink, pts, { solid: 1, color: ink.accent });
      else if (live && i < sec) MG.fill(ctx, ink, pts, { amount: 1 });
      MG.stroke(ctx, ink, pts, { t, w: 1.6, closed: true, seed: i, amp: 0.5 });
    });
    else { // the baseline bends round into a ring
      const ox = cx + cw / 2, oy = cy + ch / 2 + 6; const r0 = 70;
      bars.forEach(([, , , h2], i) => { const a = -Math.PI / 2 + (i / HEIGHTS.length) * TAU + Math.max(0, t - 16.5) * 0.9; const lx = (bars[i][0] - (cx + cw / 2)), ly = 0;
        const flatP = [[bars[i][0] + bars[i][2] / 2, bars[i][1]], [bars[i][0] + bars[i][2] / 2, bars[i][1] - h2]];
        const ringP = [[ox + r0 * Math.cos(a), oy + r0 * Math.sin(a)], [ox + (r0 + h2 * 0.55) * Math.cos(a), oy + (r0 + h2 * 0.55) * Math.sin(a)]];
        MG.stroke(ctx, ink, MG.lerpPts(flatP, ringP, ring), { t, w: i === sec ? 6 : 3.4, color: i === sec ? ink.accent : ink.line, amp: 0.3 }); void lx; void ly; });
      MG.label(ctx, ink, String(sec), ox, oy + 12, { size: 34, weight: 900, align: 'center', alpha: ring });
    }
    if (t > 16.0) { // a graph line along the bar tops
      const k = expoOut(prog(t, 16.0, 16.45)) * (1 - ring); const top = bars.map(([x, y, w, h2]) => [x + w / 2, y - h2 - 8]);
      MG.stroke(ctx, ink, top, { t, w: 2.6, color: ink.accent, draw: k, amp: 0.4 });
    }
    // tiles: counters roll up (facts about this film and this repo)
    const roll = expoOut(prog(t, 15.5, 16.1));
    const tile = (r, a, aL, b, bL) => { const [x, y, w, h2] = r; MG.label(ctx, ink, String(Math.round(a * roll)), x + 22, y + 74, { size: 56, weight: 900, track: 0.0 }); MG.label(ctx, ink, aL, x + 24, y + 104, { size: 20, weight: 700, track: 0.2, alpha: 0.8 }); MG.label(ctx, ink, String(Math.round(b * roll)), x + 22, y + 170, { size: 56, weight: 900, track: 0.0 }); MG.label(ctx, ink, bL, x + 24, y + 198, { size: 20, weight: 700, track: 0.2, alpha: 0.8 }); void h2; };
    tile(R[3], 88, 'EFFECTS', 76, 'LOOKS');
    tile(R[4], 120, 'BPM', 0, 'CUTS');
    // timeline: the 12 bar names, a keyframe diamond on each, a playhead at the real time
    const [tx, ty, tw, th] = R[5];
    BAR.forEach((n, i) => { const x = tx + 24 + (i * (tw - 48)) / 11; MG.stroke(ctx, ink, [[x, ty + 28], [x + 9, ty + 37], [x, ty + 46], [x - 9, ty + 37]], { t, w: 2, closed: true, amp: 0.2, color: t / 2 >= i + 1 && t > 16 ? ink.accent : ink.line }); ctx.save(); ctx.translate(x + 6, ty + th - 14); ctx.rotate(-Math.PI / 2); MG.label(ctx, ink, n, 0, 0, { size: 13, weight: 800, track: 0.12, alpha: 0.75 }); ctx.restore(); });
    if (t > 16.0) { const k = expoOut(prog(t, 16.0, 16.3)); const x = tx + 24 + ((now / DUR) * (tw - 48)) * k; MG.stroke(ctx, ink, [[x, ty - 8], [x, ty + th + 8]], { t, w: 4, color: ink.accent, amp: 0.2 }); }
    // the cursor arrives, clicks RING, then LIGHT
    if (t > 16.1 && t < 17.6) {
      const p1 = [hx + hw - 200, hy + hh / 2 + 4], p2 = [hx + hw - 86, hy + hh / 2 + 2]; const a = sp(t, 16.45, 20), b = sp(t, 16.95, 20);
      const from = [CX + 260, CY + 420]; const p = [lerp(lerp(from[0], p1[0], a), p2[0], b), lerp(lerp(from[1], p1[1], a), p2[1], b)];
      const press = (spring(t - 16.5, 40) - spring(t - 16.62, 40)) + (spring(t - 17.0, 40) - spring(t - 17.12, 40));
      const s = 1 - press * 0.18; const arrow = [[0, 0], [0, 34], [9, 26], [16, 42], [22, 39], [15, 24], [27, 24]].map(([x, y]) => [p[0] + x * s, p[1] + y * s]);
      MG.fill(ctx, ink, arrow, { solid: 1, color: ink.kind === 'clean' ? '#FFFFFF' : ink.line }); MG.stroke(ctx, ink, arrow, { t, w: 2, closed: true, color: ink.bg, amp: 0 });
    }
    ctx.restore();
  }

  // ---------- bar 10-11: light ----------
  // a height field seen in a fixed oblique view: x across, z into the screen, y up.
  // Bar 10: 24 columns stand up as the chart (one per second). Bar 11: their tops join into a
  // surface that becomes a travelling wave. 21.5: it flattens back into the one line.
  const MX = 24, MZ = 9, ML = 660, MD = 340;
  const proj = (x, y, z, turn) => { const a = turn; return [CX - ML / 2 + x + z * Math.cos(a) * 0.62 - 90, CY + 330 - y - z * Math.sin(a) * 0.62]; };
  function barsToLight(ctx, ink, t) {
    const lift = sp(t, 18.0, 14), toWave = sp(t, 20.0, 12), flat = sp(t, 21.5, 16);
    const turn = track([[0, 0.52], [19.0, -0.42, 10], [19.5, 0.3, 12], [20.0, 0.52, 12]])(t); // the solids turn to show their other side
    const scroll = (i) => { // the data scrolls one column per beat from 18.5 to 20
      let v = HEIGHTS[i];
      for (let k = 1; k <= 3; k++) { const at = 18.0 + k * 0.5; const prev = HEIGHTS[(i + k - 1) % HEIGHTS.length], next = HEIGHTS[(i + k) % HEIGHTS.length]; v += (next - prev) * spring(t - (at - 0.05), 26); }
      return v;
    };
    const sweep = ((t - 18.2) / 0.5) * 6; // a light runs along the columns, six columns a beat
    const height = (i, j) => {
      const bar = (scroll(i) / 100) * 560 * lift * (j < 2 ? 1 : 1 - toWave);
      const wave = (150 + 60 * Math.sin(i * 0.3)) * (0.55 + 0.45 * Math.sin(i * 0.42 + j * 0.7 - (t - 20) * 5.2));
      return lerp(bar, wave, toWave) * (1 - flat);
    };
    const dx = ML / MX; const now = Math.floor(clamp(t, 0, DUR - 0.01));
    if (toWave < 0.98) { // columns: front face lit by scan density, outline in light
      ctx.save(); ctx.globalAlpha = 1 - toWave;
      for (let i = 0; i < MX; i++) {
        const h = height(i, 0); const x = i * dx + 4, w = dx - 10;
        const f = [proj(x, 0, 0, turn), proj(x + w, 0, 0, turn), proj(x + w, h, 0, turn), proj(x, h, 0, turn)];
        const top = [proj(x, h, 0, turn), proj(x + w, h, 0, turn), proj(x + w, h, 40, turn), proj(x, h, 40, turn)];
        const isNow = i === now; const hit = Math.max(0, 1 - Math.abs(((sweep % (MX + 6)) - 3) - i) / 3);
        MG.fill(ctx, ink, f, { lit: isNow ? 0.95 : 0.32 + 0.6 * hit }); MG.fill(ctx, ink, top, { lit: 0.85 });
        MG.stroke(ctx, ink, f, { t, w: isNow ? 3 : 2, closed: true, color: isNow ? '#FFFFFF' : ink.line });
        MG.stroke(ctx, ink, top, { t, w: 1.6, closed: true });
      }
      ctx.restore();
    }
    if (toWave > 0.02) { // the surface: lines along x for each depth row, and along z for each column
      ctx.save(); ctx.globalAlpha = toWave * (1 - flat);
      for (let j = MZ - 1; j >= 0; j--) { const z = (j / (MZ - 1)) * MD; const row = []; for (let i = 0; i < MX; i++) row.push(proj(i * dx + dx / 2, height(i, j), z, turn)); MG.stroke(ctx, ink, row, { t, w: j === 0 ? 3.4 : 1.6, color: j === 0 ? ink.line : ink.line }); }
      for (let i = 0; i < MX; i += 1) { const col = []; for (let j = 0; j < MZ; j++) col.push(proj(i * dx + dx / 2, height(i, j), (j / (MZ - 1)) * MD, turn)); MG.stroke(ctx, ink, col, { t, w: 1.1, hidden: i % 2 === 1 }); }
      ctx.restore();
    }
    // the floor plate, dashed
    MG.stroke(ctx, ink, [proj(-20, 0, 0, turn), proj(ML + 20, 0, 0, turn), proj(ML + 20, 0, MD, turn), proj(-20, 0, MD, turn)], { t, w: 1.4, closed: true, hidden: true });
    if (flat > 0.02) MG.stroke(ctx, ink, hline(lerp(proj(0, 0, 0, turn)[0], CX - LINE_L / 2, flat), lerp(proj(ML, 0, 0, turn)[0], CX + LINE_L / 2, flat), lerp(proj(0, 0, 0, turn)[1], CY, flat)), { t, w: 5 });
  }

  // ---------- bar 12: end (the line becomes the wordmark again, then paper) ----------
  function endScene(ctx, ink, t) {
    const up = sp(t, 22.0, 18); const railY = lerp(CY, RAIL0, up); const rw = lerp(LINE_L, 760, up);
    MG.stroke(ctx, ink, hline(CX - rw / 2, CX + rw / 2, railY), { t, w: 5, seed: 2 });
    const rise = prog(t, 22.2, 22.9);
    ctx.save(); ctx.beginPath(); ctx.rect(0, railY + 4, W, H); ctx.clip();
    letters(ctx, ink, WORD, CX, BASE, WORD_SIZE, (i) => ({ dy: (1 - spring(t - (22.25 + i * 0.06), 26)) * (BASE - railY + 40) }), { fitW: WORD_W, t });
    ctx.restore();
    MG.label(ctx, ink, typed('INTRODUCING', prog(t, 22.9, 23.25)), CX, RAIL0 - 34, { size: 26, align: 'center', weight: 700, track: 0.3 });
    MG.label(ctx, ink, typed('A MOTION SYSTEM', prog(t, 23.0, 23.4)), CX, BASE + 70, { size: 26, align: 'center', weight: 700, track: 0.3 });
    // a pass of light crosses the wordmark on the last beats: scan density, not glow
    const pass = prog(t, 22.85, 23.45); if (pass > 0 && pass < 1 && ink.kind === 'holo') {
      const bx = lerp(CX - WORD_W / 2 - 120, CX + WORD_W / 2 + 120, expoInOut(pass));
      ctx.save(); ctx.beginPath(); ctx.rect(bx - 70, RAIL0, 140, BASE - RAIL0 + 20); ctx.clip();
      MG.word(ctx, ink, WORD, CX, BASE, { size: WORD_SIZE, fitW: WORD_W, t, solid: true, solidColor: '#FFFFFF', noOutline: true }); ctx.restore();
    }
    void rise;
  }

  // ---------- the world, drawn in one ink ----------
  let LABEL_T = null; // labels read the frame's time, not the sub-frame's
  function world(ctx, ink, t) {
    MG.grid(ctx, W, H, ink, 60, CX, CY);
    if (ink.kind === 'pencil') MG.grain(ctx, W, H, 0.07);
    if (t < 4.05) hookAndType(ctx, ink, t);
    else if (t < 6.0) curves(ctx, ink, t);
    else if (t < 8.0) morph(ctx, ink, t);
    else if (t < 11.0) tiles(ctx, ink, t, { cubes: t >= 10.0 });
    else if (t < 14.0) { if (t < 12.05 || t > 13.6) drawCube(ctx, ink, t); if (t > 11.95 && t < 13.7) gears(ctx, ink, t); }
    else if (t < 18.0) { if (t < 14.3) drawCube(ctx, ink, t, 1 - prog(t, 14.0, 14.3)); panel(ctx, ink, t); }
    else if (t < 22.0) barsToLight(ctx, ink, t);
    else endScene(ctx, ink, t);
    labels(ctx, ink, LABEL_T == null ? t : LABEL_T);
  }

  // ---------- ink changes: a flood with a hard edge, then two scan lines ----------
  function frame(ctx, t) {
    t = ((t % DUR) + DUR) % DUR;
    const floodK = expoIn(prog(t, 9.6, 10.0));
    const scan1 = expoInOut(prog(t, 17.3, 17.95)); // blueprint -> light
    const scan2 = expoInOut(prog(t, 23.45, 23.98)); // light -> paper (the loop)
    let a = INKS.paper, b = null, mode = null, k = 0;
    if (t >= 9.6 && t < 10.0) { a = INKS.paper; b = INKS.blueprint; mode = 'flood'; k = floodK; }
    else if (t >= 10.0 && t < 17.3) a = INKS.blueprint;
    else if (t >= 17.3 && t < 17.95) { a = INKS.blueprint; b = INKS.holo; mode = 'scan'; k = scan1; }
    else if (t >= 17.95 && t < 23.45) a = INKS.holo;
    else if (t >= 23.45) { a = INKS.holo; b = INKS.paper; mode = 'scan'; k = scan2; }
    world(ctx, a, t);
    if (mode === 'flood') { const r = lerp(R_SMALL, 2400, k); MG.within(ctx, hexPts(r, CX, CY), () => world(ctx, b, t)); }
    if (mode === 'scan') { const y = lerp(-10, H + 10, k); ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, y); ctx.clip(); world(ctx, b, t); ctx.restore(); ctx.fillStyle = b.kind === 'pencil' ? '#45F0DD' : '#FFFFFF'; ctx.fillRect(0, y - 2, W, 4); }
  }

  /** draw(ctx, t) with optional motion blur: n sub-frames over a 180° shutter at 30 fps */
  let accum = null;
  function draw(ctx, t, sub = 4) {
    LABEL_T = ((t % DUR) + DUR) % DUR;
    if (sub <= 1) { frame(ctx, t); LABEL_T = null; return; }
    if (!accum) { accum = document.createElement('canvas'); accum.width = W; accum.height = H; }
    const a = accum.getContext('2d'); const shutter = 0.5 / 30;
    for (let i = 0; i < sub; i++) {
      const ts = t - shutter * (i / sub);
      if (i === 0) { frame(ctx, ts); continue; }
      frame(a, ts); ctx.save(); ctx.globalAlpha = 1 / (i + 1); ctx.drawImage(accum, 0, 0); ctx.restore();
    }
    LABEL_T = null;
  }

  window.FILM = { W, H, DUR, BPM, draw, frame };
})();
