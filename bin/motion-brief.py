#!/usr/bin/env python3
"""Write the full motion-design prompt (the brief) from a few words, so nobody types 7,000 characters.

    python3 bin/motion-brief.py --subject "my reel factory" --words "REELS|ONE LINE|BECOMES|A REEL" \\
        --style auto --seconds 24 --bpm 120 --out motion/one-line

    # with real material: a track (BPM and drop are measured), brand files, footage, cleared numbers
    python3 bin/motion-brief.py --subject "castr launch" --track ~/Downloads/music-good/x.mp3 \\
        --brand path/to/tokens.css --footage ~/Downloads/clips --facts followers,views_last_30d

What it does
  1. Picks a taste pack from motion/styles.json (or the one you name) by matching the subject,
     words and footage against each pack's `fits`.
  2. Measures what it can: the track's tempo and drop (bin/music-map.py), the footage (durations,
     orientation), the brand files (hex colours found in them), the cleared numbers
     (channel-facts.json). Anything it cannot know becomes a question in <inputs>, never a guess.
  3. Lays the pack's story arc over the bars of the film (one bar = 4 beats) and puts the user's
     exact words on the bars, with a typographic role for each.
  4. Writes BRIEF.md in the grammar the strongest reference prompts share:
     <inputs> <direction> <structure> <build> <gotchas> <start>, plus beats.json (the bar map).

The brief is the internal prompt: the agent builds the film from it with motion/engine/mg.js,
shows the stills (motion/tools/sheet.html) and the beat map before rendering, and checks the
render with bin/motion-stats.py. See formats/motion-design.md and the motion-director skill.
"""
import argparse
import glob
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "motion" / "styles.json"
FACTS = ROOT / "channel-facts.json"

ENGINE_GOTCHAS = [
    "Every frame is a pure function of time (film.frame(ctx, t)). Never keep state between frames and never use tl.call(): HyperFrames seeks frame by frame and the motion-blur sub-frames run backwards in time.",
    "Animate transforms and canvas geometry, never margins or left/top: layout properties snap to whole pixels and stutter (hyperframes check flags gsap_non_transform_motion).",
    "HyperFrames refuses asset paths that climb above the project (../): bin/motion-reel.sh copies motion/engine/mg.js into the project as engine/mg.js.",
    "Wait for document.fonts.ready before the first paint, or frame 0 renders in a fallback face.",
    "A shape morph needs the same point count, the same start point and the same winding on both shapes (MG.resample + reversing to match), or it twists through itself.",
    "A flood that has covered the frame must become a full-frame fill; a shape that keeps growing still leaves corners on a tall frame.",
    "Counters and labels read the frame's time, not the sub-frame's, or the digits smear.",
    "Four sub-frames ghost on fast whips; use 8 for any move faster than a frame width in 0.2 s.",
    "Keep the last frame equal to the first frame, picture and sound, so Instagram's loop is invisible.",
]


def load_styles():
    return json.loads(STYLES.read_text(encoding="utf-8"))


def pick_pack(styles, wanted, text):
    packs = styles["packs"]
    if wanted and wanted != "auto":
        for p in packs:
            if p["id"] == wanted:
                return p, "named"
        raise SystemExit(f"no style pack '{wanted}'. Packs: {', '.join(p['id'] for p in packs)}")
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    def score(p):
        bag = set(re.findall(r"[a-z]{3,}", (p["fits"] + " " + p["concept"] + " " + p["name"]).lower()))
        return len(words & bag)
    ranked = sorted(packs, key=score, reverse=True)
    best = ranked[0] if score(ranked[0]) > 0 else packs[0]
    return best, "matched" if score(ranked[0]) > 0 else "default"


def measure_track(path):
    if not path:
        return None
    info = {"file": os.path.basename(path)}
    try:
        out = subprocess.run(["python3", str(ROOT / "bin" / "music-map.py"), path], capture_output=True, text=True, timeout=300).stdout
        m = re.search(r"drop@\s*([\d.]+)s", out); b = re.search(r"([\d.]+)\s*bpm", out, re.I)
        if m: info["drop_s"] = float(m.group(1))
        if b: info["bpm"] = float(b.group(1))
    except Exception as e:  # measured values are a bonus; the brief still says what is unknown
        info["error"] = str(e)
    return info


def measure_footage(folder):
    if not folder:
        return []
    media = []
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(folder), "*")))[:40]:
        if not re.search(r"\.(mp4|mov|m4v|jpg|jpeg|png|heic|webp)$", f, re.I):
            continue
        row = {"file": os.path.basename(f)}
        try:
            p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", f], capture_output=True, text=True, timeout=30)
            j = json.loads(p.stdout or "{}"); s = (j.get("streams") or [{}])[0]
            row["w"], row["h"] = s.get("width"), s.get("height")
            d = (j.get("format") or {}).get("duration")
            if d and float(d) > 0.2: row["seconds"] = round(float(d), 1)
        except Exception:
            pass
        media.append(row)
    return media


def brand_colours(paths):
    found = []
    for p in paths or []:
        try:
            txt = Path(os.path.expanduser(p)).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for h in re.findall(r"#[0-9a-fA-F]{6}\b", txt):
            if h.upper() not in found: found.append(h.upper())
    return found[:8]


def cleared_facts(keys):
    if not FACTS.exists():
        return {}
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    want = [k.strip() for k in (keys or "").split(",") if k.strip()]
    out = {}
    for k in want:
        v = data.get(k)
        if isinstance(v, dict) and "value" in v:
            out[k] = {"value": v["value"], "as_of": v.get("as_of"), "label": v.get("use_on_screen") or v.get("label") or k}
        elif v is not None:
            out[k] = {"value": v}
    return out


def lay_out_bars(pack, seconds, bpm, words):
    bar_s = 4 * 60 / bpm; n = max(4, int(round(seconds / bar_s)))
    arc = pack["arc"]
    idx = [min(len(arc) - 1, int(i * len(arc) / n)) for i in range(n)]  # stretch or compress the arc evenly
    bars = []
    for i in range(n):
        step = arc[idx[i]]; name = step.split(":")[0].strip().upper()[:10] if ":" in step else f"BAR{i + 1}"
        bars.append({"bar": i + 1, "start": round(i * bar_s, 2), "end": round((i + 1) * bar_s, 2), "name": name, "does": step.split(":", 1)[-1].strip(), "words": []})
    if words:  # the hero word opens and closes the film; the rest sit on the early bars in order
        bars[0]["words"].append({"text": words[0], "role": "hero: fitted to the safe width, the film's first and last frame"})
        for j, w in enumerate(words[1:]):
            b = bars[min(len(bars) - 2, 1 + j // 2)]
            b["words"].append({"text": w, "role": "slot word: lives between the rails, the rails resize to fit it" if pack["id"] == "drafting-inks" else "kinetic line: letters arrive one by one"})
        bars[-1]["words"].append({"text": words[0], "role": "hero returns: the loop closes"})
    return bars, bar_s


def numbers_in(words):
    return sorted({m for w in words for m in re.findall(r"\d[\d,.]*\s*[KkMm%]?", w)})


def write_brief(a):
    styles = load_styles(); shared = styles["shared"]
    words = [w.strip() for w in (a.words or "").split("|") if w.strip()]
    track = measure_track(a.track); bpm = (track or {}).get("bpm") or a.bpm
    footage = measure_footage(a.footage); colours = brand_colours(a.brand); facts = cleared_facts(a.facts)
    pack, how = pick_pack(styles, a.style, " ".join([a.subject] + words + [m["file"] for m in footage]))
    bars, bar_s = lay_out_bars(pack, a.seconds, bpm, words)
    unverified = [n for n in numbers_in(words) if not any(n.replace(" ", "") in str(f["value"]) for f in facts.values())]
    W, H = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}[a.aspect]

    asks = []
    if not words: asks.append("the exact words to put on screen (the hero word first)")
    optional = []
    if not a.track: optional.append(f"a track; without one the film gets an original synthesized score at {bpm:g} BPM (bin/motion-score.py)")
    if not colours and pack["id"] in ("loud-poster", "editorial-cream", "one-shape-ui"): asks.append("brand colours or a tokens file; otherwise the pack palette is used")
    if unverified: asks.append(f"where these numbers come from: {', '.join(unverified)} (they stay off screen until cleared)")
    if pack["id"] == "loud-poster" and not footage: asks.append("real clips or photos to play inside the design")

    L = []
    L.append(f"# Motion brief: {a.subject}\n")
    L.append(f"Written by bin/motion-brief.py from: subject, {len(words)} words, style `{pack['id']}` ({how}), {a.seconds}s at {bpm:g} BPM, {a.aspect}.\n")
    L.append("<inputs>")
    L.append(f"Subject: {a.subject}")
    L.append(f"Exact words, in order: {' / '.join(words) if words else '(none given)'}")
    if facts: L.append("Cleared numbers (channel-facts.json): " + "; ".join(f"{k} = {v['value']} (as of {v.get('as_of')})" for k, v in facts.items()))
    if track: L.append(f"Track: {track['file']}, {track.get('bpm', '?')} BPM measured, drop at {track.get('drop_s', '?')} s. Put the payoff bar on the drop.")
    if footage: L.append(f"Footage ({len(footage)} files): " + ", ".join(f"{m['file']} {m.get('w')}x{m.get('h')}{(' ' + str(m['seconds']) + 's') if m.get('seconds') else ''}" for m in footage[:12]))
    if colours: L.append("Brand colours found: " + ", ".join(colours) + ". They replace the pack's accents; keep its neutrals.")
    L.append("Still to ask: " + ("; ".join(asks) if asks else "nothing required.") + (" Optional: " + "; ".join(optional) + "." if optional else ""))
    L.append("</inputs>\n")

    L.append("<direction>")
    L.append(f"A {a.seconds}-second looping {a.aspect} motion film, {W}x{H} at 30 fps. Taste pack: {pack['name']} (from {pack['from']}).")
    L.append(f"Concept, in one line: {pack['concept']}.")
    L.append("Every shot is made out of the previous one: shapes, type and colour transform into the next scene. No cuts, no fades.")
    t = pack["type"]; L.append(f"Type: {t['family']}. Big words weight {t['big']}; labels {t['labels']}.")
    pal = dict(pack["palette"]);
    if colours: pal.update({f"brand{i + 1}": c for i, c in enumerate(colours[:3])})
    L.append("Palette: " + ", ".join(f"{k} {v}" for k, v in pal.items()) + ".")
    if pack.get("inks"): L.append("Inks (the same geometry drawn in whichever ink is on screen):\n- " + "\n- ".join(pack["inks"]))
    L.append(f"Camera: {pack['camera']}.")
    L.append("Transitions: " + "; ".join(pack["transitions"]) + ".")
    if pack.get("furniture"): L.append("On screen all film: " + "; ".join(pack["furniture"]) + ".")
    L.append(f"Frame: {shared['frame_rules']}.")
    L.append(f"Honesty: {shared['honesty']}. {shared['muted']}.")
    L.append("Banned: " + ", ".join(shared["banned_always"] + pack.get("banned", [])) + ".")
    L.append("</direction>\n")

    L.append("<structure>")
    L.append(f"{bpm:g} BPM, {int(a.seconds / (60 / bpm))} beats, {len(bars)} bars of {bar_s:g} s. {shared['beat']}.")
    L.append(f"Easing: {shared['easing']}.")
    for b in bars:
        line = f"Bar {b['bar']}, {b['name']}, {b['start']:g}-{b['end']:g} s: {b['does']}."
        if b["words"]: line += " Words: " + "; ".join(f"\"{w['text']}\" ({w['role']})" for w in b["words"]) + "."
        L.append(line)
    L.append("The last frame is the first frame, so it loops.")
    L.append("</structure>\n")

    L.append("<build>")
    L.append(f"1. A HyperFrames project in motion/{a.slug}/ (index.html + film.js) on the shared engine {pack['engine']}. Copy the shape of motion/one-line.")
    L.append("2. film.js exports FILM = {W, H, DUR, BPM, draw, frame}; frame(ctx, t) draws one frame from t alone; draw() averages 4 motion-blur sub-frames over a 180° shutter.")
    L.append("3. A beat clock MG.beats(bpm); values are MG.track keyframes that spring in, landing on their beat.")
    L.append(f"4. Sound: {'the track, placed so its drop lands on the payoff bar' if track else 'an original score from motion/' + a.slug + '/score.json via bin/motion-score.py (soft kick on beats, a sound on every visible action)'}; the film must also read muted.")
    L.append(f"5. Stills first: http://127.0.0.1:8797/tools/sheet.html?film={a.slug}&t=... (serve motion/). Then render: bin/motion-reel.sh motion/{a.slug} out.mp4.")
    L.append("6. Check: bin/motion-stats.py out.mp4 --ref <reference.mp4> (hard jumps per second, still-frame share, mean motion) and bin/ig-safe.py view; export with bin/export-ig.sh.")
    L.append("</build>\n")

    L.append("<gotchas>")
    L.extend("- " + g for g in ENGINE_GOTCHAS)
    L.append("</gotchas>\n")

    L.append("<start>")
    L.append("Ask the questions in <inputs> that are still open (only those). Then show the beat map (beats.json) and 6 stills from the sheet before rendering. Render only after the stills read well at phone size.")
    L.append("</start>")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "BRIEF.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "beats.json").write_text(json.dumps({"bpm": bpm, "seconds": a.seconds, "bar_seconds": bar_s, "pack": pack["id"], "bars": bars}, indent=1), encoding="utf-8")
    print(f"wrote {out / 'BRIEF.md'} and beats.json  (pack: {pack['id']}, {how}; {len(bars)} bars; open questions: {len(asks)})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", default="")
    ap.add_argument("--words", default="", help='exact on-screen words, "|"-separated, hero word first')
    ap.add_argument("--style", default="auto", help="pack id from motion/styles.json, or auto")
    ap.add_argument("--seconds", type=float, default=24)
    ap.add_argument("--bpm", type=float, default=120)
    ap.add_argument("--aspect", default="9:16", choices=["9:16", "16:9", "1:1", "4:5"])
    ap.add_argument("--track"); ap.add_argument("--footage"); ap.add_argument("--brand", nargs="*")
    ap.add_argument("--facts", help="comma-separated keys from channel-facts.json allowed on screen")
    ap.add_argument("--out", help="folder for BRIEF.md and beats.json (default motion/<slug>)")
    ap.add_argument("--list", action="store_true", help="list the taste packs and exit")
    a = ap.parse_args()
    if a.list:
        for p in load_styles()["packs"]: print(f"{p['id']:22s} {p['fits']}")
        return
    if not a.subject: ap.error("--subject is required")
    a.slug = re.sub(r"[^a-z0-9]+", "-", a.subject.lower()).strip("-")[:40]
    if a.out: a.slug = Path(a.out).name
    a.out = a.out or str(ROOT / "motion" / a.slug)
    write_brief(a)


if __name__ == "__main__":
    main()
