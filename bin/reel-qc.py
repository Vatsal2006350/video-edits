#!/usr/bin/env python3
"""Reel quality gate. Measures what eyeballing misses, then blocks the render.

    bin/reel-qc.py layers  --front DIR --behind DIR [--track t.json] [--json out.json]
    bin/reel-qc.py master  <master.mp4> [--ig <ig.mp4>] [--json out.json]

`layers` runs BEFORE compositing, on the transparent PNG sequences, so faults
are cheap to fix. `master` runs after, on the finished file. Both exit non-zero
if any ERROR check fails, so a build script can gate on them.

Checks (each one exists because it shipped broken at least once):

  SAFE-BOX      solid content (alpha>200) inside x 59..918, y 278..1536.
                Soft shadows are ignored at that threshold on purpose.
  CENTRED-WIDTH centred type within 724px = 2*(918-540).
  LAYER-FLICKER an element that swaps between the behind and front layer more
                than once per second reads as a flicker. This is THE bug that
                made cover 5 strobe: a per-frame behind/front test with no
                hysteresis flips whenever the head width jitters.
  CONTRAST      every text pixel against the picture underneath it, as WCAG
                relative luminance. Light type over a bright wall is the
                failure; "nicer font but sometimes invisible" is this check.
  FLASH         a layer's coverage that jumps away and back within one or two
                frames: a dropout or a strobe. Found a real one-frame hole at
                the exact instant a clip-path tween ended, where a second tween
                took over the same property - invisible in any sampled sheet,
                obvious on playback. Runs on EVERY frame, not the sample step.
  SPECS         master/IG container, fps, profile, channels, rate, loudness,
                true peak, and the edit-list atom that broke reel 36.

Known blind spot: text drawn ON a full-bleed opaque surface shares one alpha
component with it, so the SAFE-BOX check skips that text along with the
backdrop. Place type on a takeover card by hand against the 278..1536 band;
the gate will not catch it for you.

Nothing here is a style opinion; every threshold is a number from AGENTS.md or
a measured failure.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920
SAFE = (59, 278, 918, 1536)
CENTRED_MAX = 724
SOLID = 200           # alpha above this is content, below is shadow/AA
MIN_HOLD_S = 0.25
MIN_CONTRAST = 3.0    # text vs backdrop, WCAG relative-luminance ratio
FPS = 30


def lum(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def components(mask, min_px=200):
    """Connected components of a boolean mask, as bboxes. Two-pass labelling
    with union-find on a downscaled mask - no scipy in this repo's Python."""
    sm = np.array(Image.fromarray((mask * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)) > 100
    h, w = sm.shape
    lab = np.zeros((h, w), np.int32)
    parent = [0]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    nxt = 1
    for y in range(h):
        for x in range(w):
            if not sm[y, x]:
                continue
            up = lab[y - 1, x] if y else 0
            left = lab[y, x - 1] if x else 0
            if up and left:
                lab[y, x] = min(up, left); union(up, left)
            elif up or left:
                lab[y, x] = up or left
            else:
                lab[y, x] = nxt; parent.append(nxt); nxt += 1
    out = {}
    for y in range(h):
        for x in range(w):
            l = lab[y, x]
            if not l:
                continue
            r = find(l)
            b = out.setdefault(r, [x, x, y, y, 0])
            b[0] = min(b[0], x); b[1] = max(b[1], x)
            b[2] = min(b[2], y); b[3] = max(b[3], y); b[4] += 1
    # Refine each coarse box against the full-res mask: the 1/4 search is fast
    # but quantised to 4px, which would report a card's edge 1-3px outside the
    # safe box and cry wolf.
    res = []
    for b in out.values():
        if b[4] * 16 < min_px:
            continue
        x0, x1 = max(0, b[0] * 4 - 4), min(W - 1, b[1] * 4 + 7)
        y0, y1 = max(0, b[2] * 4 - 4), min(H - 1, b[3] * 4 + 7)
        sub = mask[y0:y1 + 1, x0:x1 + 1]
        ys, xs = np.where(sub)
        if not len(xs):
            continue
        res.append((x0 + int(xs.min()), x0 + int(xs.max()),
                    y0 + int(ys.min()), y0 + int(ys.max()), int(sub.sum())))
    return res


def composite_contrast(layer, pic):
    """Mean contrast of this layer's solid marks against the ring around them,
    measured on the composited picture (what a viewer actually sees)."""
    al = layer[..., 3].astype(float) / 255.0
    comp = pic.astype(float) * (1 - al[..., None]) + layer[..., :3].astype(float) * al[..., None]
    core = (layer[..., 3] > 235)
    if core.sum() < 300:
        return None, 0, None
    # Only judge TEXT. A photo card is a solid block: erode it and most of it
    # survives, while letterforms are thin and mostly vanish. Without this the
    # check calls every cover thumbnail an unreadable mark.
    m0 = Image.fromarray((core * 255).astype(np.uint8))
    eroded = np.array(m0.filter(ImageFilter.MinFilter(7))) > 127
    if eroded.sum() > 0.55 * core.sum():
        return None, 0, None
    core = core & ~np.array(m0.filter(ImageFilter.MinFilter(13))) > 0
    if core.sum() < 300:
        return None, 0, None
    m = Image.fromarray((core * 255).astype(np.uint8))
    near = np.array(m.filter(ImageFilter.MaxFilter(5))) > 127
    far = np.array(m.filter(ImageFilter.MaxFilter(15))) > 127
    ring = far & ~near
    if ring.sum() < 200:
        return None, 0, None
    L = lum(comp)
    a_, b_ = L[core].mean(), L[ring].mean()
    hi, lo = max(a_, b_), min(a_, b_)
    ys, xs = np.where(core)
    bbox = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
    return (hi + 0.05) / (lo + 0.05), int(core.sum()), bbox


def frames(d):
    return sorted(Path(d).glob("frame_*.png"))


def load(p):
    return np.array(Image.open(p).convert("RGBA"))


def video_frame(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(path),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    if len(raw) < W * H * 3:
        return None
    return np.frombuffer(raw[: W * H * 3], np.uint8).reshape(H, W, 3)


def check_layers(front, behind, picture, step, findings):
    ff, bf = frames(front), frames(behind)
    n = min(len(ff), len(bf))
    if not n:
        findings.append(("ERROR", "LAYERS", "no frames found", None))
        return
    # --- per-frame geometry + contrast
    pic_cache = {}
    outside, outside_detail = {}, {}
    first_seen, last_seen, seen_counts = {}, {}, {}
    for i in range(0, n, step):
        t = i / FPS
        for tag, seq in (("front", ff), ("behind", bf)):
            a = load(seq[i])
            al = a[..., 3]
            soli = al > SOLID
            if not soli.any():
                continue
            ys, xs = np.where(soli)
            x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
            # Per ELEMENT, not the union of the frame: otherwise one travelling
            # cursor drags the whole frame's bbox out of the box. An element
            # moving through the unsafe zone is fine; one parked there is not.
            for (cx0, cx1, cy0, cy1, _n) in components(soli):
                # A deliberate full-bleed surface (a takeover card, a grade) is
                # allowed to fill the frame; what must stay inside the box is
                # the content ON it, which is checked as its own component.
                if (cx1 - cx0) > 0.95 * W and (cy1 - cy0) > 0.95 * H:
                    continue
                if cx0 < SAFE[0] or cx1 > SAFE[2] or cy0 < SAFE[1] or cy1 > SAFE[3]:
                    key = (tag, cx0 // 60, cy0 // 60)
                    outside.setdefault(key, []).append(round(t, 2))
                    outside_detail[key] = f"{tag} element x{cx0}..{cx1} y{cy0}..{cy1} outside the safe box"
            # Contrast is measured on the COMPOSITE against each mark's own
            # surroundings. Measuring the layer against the picture underneath
            # calls every opaque card unreadable, which is a false alarm: what
            # matters is the mark versus whatever ends up around it.
            if picture:
                if i not in pic_cache:
                    pic_cache[i] = video_frame(picture, t)
                pic = pic_cache[i]
                if pic is not None:
                    ratio, cov, bbox = composite_contrast(a, pic)
                    if ratio is not None and cov > 300 and ratio < MIN_CONTRAST:
                        findings.append(("ERROR", "CONTRAST",
                                         f"{tag} text contrast {ratio:.2f}:1 at x{bbox[0]}..{bbox[1]} "
                                         f"y{bbox[2]}..{bbox[3]} (need {MIN_CONTRAST}:1)", round(t, 2)))
    for key, times in outside.items():
        secs = len(times) * step / FPS
        # A stationary element outside the box is a real placement bug; a few
        # frames of travel is not.
        sev = "ERROR" if secs >= 0.6 else "WARN"
        findings.append((sev, "SAFE-BOX",
                         f"{outside_detail[key]} for {secs:.1f}s", times[0]))

    # --- single-frame dropouts / strobes, every frame of both layers
    for tag, seq in (("front", ff), ("behind", bf)):
        cov = []
        for p in seq:
            im = Image.open(p)
            im.draft("RGBA", (im.width // 8, im.height // 8))
            cov.append((np.array(im.convert("RGBA"))[..., 3] > 200).mean())
        for i in range(1, len(cov) - 1):
            d_prev, d_next = abs(cov[i] - cov[i - 1]), abs(cov[i] - cov[i + 1])
            if d_prev > 0.25 and d_next > 0.25 and abs(cov[i - 1] - cov[i + 1]) < 0.12:
                findings.append(("ERROR", "FLASH",
                                 f"{tag} coverage {cov[i-1]*100:.0f}% -> {cov[i]*100:.0f}% -> "
                                 f"{cov[i+1]*100:.0f}% in one frame", round(i / FPS, 2)))

    # --- layer flicker: does the SAME region swap layers repeatedly?
    gridw, gridh = 12, 20
    occ = []
    for i in range(0, n, step):
        fa = load(ff[i])[..., 3] > SOLID
        ba = load(bf[i])[..., 3] > SOLID
        cell = np.zeros((gridh, gridw), np.int8)
        for gy in range(gridh):
            for gx in range(gridw):
                sl = (slice(gy * H // gridh, (gy + 1) * H // gridh),
                      slice(gx * W // gridw, (gx + 1) * W // gridw))
                f_, b_ = fa[sl].mean() > 0.02, ba[sl].mean() > 0.02
                cell[gy, gx] = 1 if (f_ and not b_) else (-1 if (b_ and not f_) else 0)
        occ.append(cell)
    if len(occ) > 2:
        occ = np.array(occ)
        for gy in range(gridh):
            for gx in range(gridw):
                s = occ[:, gy, gx]
                s = s[s != 0]
                if len(s) < 3:
                    continue
                swaps = int((np.diff(s) != 0).sum())
                secs = len(s) * step / FPS
                if secs > 0.5 and swaps / secs > 1.0:
                    findings.append(("ERROR", "LAYER-FLICKER",
                                     f"cell ({gx},{gy}) swaps behind/front {swaps}x in {secs:.1f}s", None))
    return


def ffprobe(path, entries):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries,
                          "-of", "json", str(path)], capture_output=True, text=True).stdout
    return json.loads(out or "{}")


def check_master(master, ig, findings):
    d = ffprobe(master, "stream=codec_name,width,height,r_frame_rate,pix_fmt")
    v = next((s for s in d.get("streams", []) if s.get("width")), {})
    if (v.get("width"), v.get("height")) != (W, H):
        findings.append(("ERROR", "SPECS", f"master is {v.get('width')}x{v.get('height')}, need {W}x{H}", None))
    if v.get("r_frame_rate") != "30/1":
        findings.append(("ERROR", "SPECS", f"master fps {v.get('r_frame_rate')}, need 30/1", None))
    if not ig:
        return
    d = ffprobe(ig, "stream=codec_name,profile,level,channels,sample_rate,r_frame_rate")
    vs = next((s for s in d.get("streams", []) if s.get("profile") in ("High", "Main", "Baseline")), {})
    a = next((s for s in d.get("streams", []) if s.get("channels")), {})
    if vs.get("profile") != "High" or str(vs.get("level")) != "40":
        findings.append(("ERROR", "SPECS", f"IG profile/level {vs.get('profile')}/{vs.get('level')}, need High/40", None))
    if a.get("channels") != 2 or str(a.get("sample_rate")) != "44100":
        findings.append(("ERROR", "SPECS", f"IG audio {a.get('channels')}ch @{a.get('sample_rate')}, need 2ch @44100", None))
    trace = subprocess.run(["ffprobe", "-v", "trace", str(ig)], capture_output=True, text=True)
    if (trace.stderr + trace.stdout).count("elst"):
        findings.append(("ERROR", "SPECS", "IG copy carries an elst atom (broke reel 36 after IG transcode)", None))
    eb = subprocess.run(["ffmpeg", "-nostdin", "-i", str(ig), "-af", "ebur128=peak=true", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    mi = re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)
    mp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)
    if mi and not (-15.5 <= float(mi[-1]) <= -13.0):
        findings.append(("ERROR", "SPECS", f"IG loudness {mi[-1]} LUFS, need about -14", None))
    if mp and float(mp[-1]) > -1.9:
        findings.append(("ERROR", "SPECS", f"IG true peak {mp[-1]} dBFS, need <= -1.9", None))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("layers"); l.add_argument("--front", required=True); l.add_argument("--behind", required=True)
    l.add_argument("--picture"); l.add_argument("--step", type=int, default=6); l.add_argument("--json")
    m = sub.add_parser("master"); m.add_argument("master"); m.add_argument("--ig"); m.add_argument("--json")
    a = ap.parse_args()

    findings = []
    if a.cmd == "layers":
        check_layers(a.front, a.behind, a.picture, a.step, findings)
    else:
        check_master(a.master, a.ig, findings)

    # collapse repeats so one systemic fault is one line, with its time range
    grouped = {}
    for sev, code, msg, t in findings:
        k = (sev, code, re.sub(r"[\d.]+", "#", msg))
        g = grouped.setdefault(k, dict(sev=sev, code=code, msg=msg, times=[], n=0))
        g["n"] += 1
        if t is not None:
            g["times"].append(t)
    rows = []
    for g in grouped.values():
        ts = g["times"]
        rows.append(dict(severity=g["sev"], check=g["code"], detail=g["msg"], count=g["n"],
                         first=min(ts) if ts else None, last=max(ts) if ts else None))
    rows.sort(key=lambda r: (-r["count"], r["check"]))
    errs = sum(1 for r in rows if r["severity"] == "ERROR")
    if a.json:
        Path(a.json).write_text(json.dumps(dict(ok=errs == 0, errors=errs, findings=rows), indent=1))
    if not rows:
        print("QC PASS — no findings")
        return 0
    for r in rows:
        span = f"  [{r['first']}s..{r['last']}s]" if r["first"] is not None else ""
        print(f"{r['severity']:5} {r['check']:14} x{r['count']:<4} {r['detail']}{span}")
    print(f"\nQC {'FAIL' if errs else 'PASS'} — {errs} error group(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
