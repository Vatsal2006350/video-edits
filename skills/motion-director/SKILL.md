---
name: motion-director
description: Make a pure motion-design film (no footage, or footage inside a designed world) with taste: an intro, a showreel, a product or tool film, a loop, a kinetic quote, an animated explainer. Use when the user asks for motion graphics, a motion design video, an animated intro or logo reveal, "make it smooth like the Opus/Claude motion videos", a showreel, or names a taste pack (drafting-inks, one-shape-ui, loud-poster, editorial-cream, kinetic-architecture). Writes the long director's prompt for the user (bin/motion-brief.py), builds the film on motion/engine/mg.js, renders through HyperFrames, scores it, and gates it against a reference before delivery.
---

# motion-director: taste first, then frames

The user should never have to write a 7,000-character prompt. Their few words become the full brief,
and the brief has the shape the strongest public motion prompts share:
`<inputs> <direction> <structure> <build> <gotchas> <start>`.
Run from the repo root. Read `formats/motion-design.md` once.

## 1. Intake (ask only what you cannot find)
Ask **which kind of video** if the brief doesn't say (`START-HERE.md`). For motion design, collect:
- the subject and the **exact words** for the screen (hero word first)
- numbers: only keys from `channel-facts.json`, or a cited source. Never invent one.
- optional: a track (its BPM and drop get measured), brand files (colours are pulled from them), a footage folder
Look before you ask: `channel-facts.json`, `FOOTAGE.md`, `logos/`, `~/Downloads/music-good/README`.

## 2. Write the brief (the internal prompt)
```bash
python3 bin/motion-brief.py --list                      # taste packs and what each fits
python3 bin/motion-brief.py --subject "..." --words "HERO|LINE 2|LINE 3" --style auto \
  --seconds 24 --bpm 120 --facts effects_count [--track x.mp3] [--brand tokens.css] [--footage dir]
# or: python3 harness/hx.py motion brief -- <same args>
```
It picks a taste pack from `motion/styles.json`, lays the pack's arc over the bars, places the words
with a typographic role each, and writes `motion/<slug>/BRIEF.md` + `beats.json`. Read the brief
back to yourself: if a bar does nothing on its beats, fix the brief before writing code.

## 3. Build on the engine
Copy the shape of `motion/one-line/` (`index.html` + `film.js` + `score.json`). `film.js` exports
`FILM = {W, H, DUR, BPM, draw, frame}`; `frame(ctx, t)` draws one frame from `t` alone.
`motion/engine/mg.js` gives: springs that never overshoot (`MG.spring`, `MG.track`), a beat clock,
three inks (`MG.INKS.paper|blueprint|holo`), pencil/clean/light strokes, hatching and scan-line fills,
hatched type (`MG.word`, `MG.label`), polygon morphs (`MG.resample`, `MG.lerpPts`), a curl that keeps
length, gears, a wire cube with hidden edges and perspective, flood and scan-line wipes.

## 4. Stills, then render
```bash
cd motion && python3 -m http.server 8797 --bind 127.0.0.1   # then open:
# http://127.0.0.1:8797/tools/sheet.html?film=<slug>&t=0.2,2.7,4.7,7.6,9.8,11.9,15.8,19.4,22.9&w=200&cols=9
bin/motion-reel.sh motion/<slug> out.mp4                      # vendors the engine, lints, renders (4 motion-blur sub-frames)
python3 bin/motion-score.py motion/<slug>/score.json score.wav --mux out.mp4 out_sound.mp4
```
Show the user the beat map and the stills sheet before the long render when the brief is new.

## 5. Gate it
```bash
python3 harness/hx.py motion check motion/<slug> --render out.mp4 --ref ~/Downloads/original.mp4
python3 bin/ig-safe.py view out_IG.mp4 sheet.jpg 0.2 2.7 7.6 11.9 15.8 19.4
```
`motion check` fails on: `tl.call()` (not seek-safe), margin tweens (pixel snapping), `../` asset paths,
a hold over 0.6 s, more than 0.5 hard jumps/s. `bin/motion-stats.py` reads the film against a reference
(hard jumps per second, still-frame share, longest hold, mean motion). The reference used so far:
`~/Downloads/original.mp4` (the drafting-inks showreel). Then `bin/export-ig.sh` and the phone mirror,
per CLAUDE.md "Deliverables". True peak must read <= -1.9 dBFS: the score's mux step limits it.

## Taste rules that made the difference
- One carrier. Every shot is made out of the previous one; nothing is replaced, nothing crossfades.
- Something happens on every beat; moves start 0.05 s early so they land on it.
- Springs never overshoot. Exponential in/out only for wipes, presses and exits.
- Light is line density (scan lines), never glow. Two or three inks, never a fourth colour.
- Centred work stays within 724 px; the right edge belongs to Instagram's buttons.
- The last frame is the first frame, picture and sound.

## Adding a taste pack
When a new reference earns it: add a pack to `motion/styles.json` (fits, concept, type, palette, camera,
transitions, arc, banned, from), measure the reference with `bin/motion-stats.py`, and note it here.
Take the rules, never the creator's film.
