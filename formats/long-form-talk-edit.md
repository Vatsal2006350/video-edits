# Long-form talk edit (YouTube, 16:9)

Built for Jason Mars's All Things Open talk and ISG AI Summit keynote (v5, 2026-11-12). Project and tools:
`videos/jason-talks/v5/`. Research: `research/2026-11-12-long-form-talk-editing.md`.

## Pipeline
1. **Find obstructions.** `scan_frames.py` pulls 2 fps thumbnails; `obstruction.py`, `corners.py` and `skim.py`
   make contact sheets of frames that differ from a rolling-median background, plus an every-8-seconds skim.
   LOOK at the sheets: the detectors flag exposure changes too.
2. **Plan the cut.** `plan_<name>.json` lists editorial cuts as phrase anchors (`from` / `to` / `at` in source
   seconds). `cut_v5.py <name>` applies them, then drops um/uh, collapses one-word stutters and shortens pauses
   over 0.9 s to 0.45 s. An optional `cold_open` repeats the strongest line at the start. Read the joins with
   `joins.py <name>` before rendering; never cut inside a thought.
3. **Plan the graphics.** `events_<name>.json`: each card is anchored to the words that trigger it
   (`phrase` + `at`), list items and comparison rows to their own words. `near.py <name> <src_t>` shows the
   kept words around a time. Types: `title chapter words stat list compare pipeline timeline walker lower qcard`;
   `cover: true` makes a full-frame card on a blurred plate.
4. **Cover what can't be cut.** `cover_check.py <name> '[[src_a,src_b],...]'` lists each obstruction window that
   survives the cut and the full-frame card covering it. Every window must say "cut out" or name a card.
5. **Stills first.** `render_v5.py <name> stills t,t,...` then `sheet.py <name>`. Then `run_all.sh`
   (6 chunks per talk in parallel, then the audio pass), then concat + mux.

## Measured numbers
- Frame 1920x1080 @30, iPhone HLG tonemapped (zscale + hable) before compositing.
- Wide-shot framing alternates 1.0x / 1.18x per cut (hides jump cuts), plus a +0.035x push over 25 s inside a take.
- Portrait source: crop y 173 to 1574 of 1920 (drops lens-edge objects top and bottom), panel 832x1080,
  blurred and darkened (0.38) fill. Panel slides from centre to x=140 while a side card shows.
- Side cards: right column x 1150 (wide shot) or x 1000 (portrait), dark card INK #0C0E16 at 84% alpha.
  Accent amber #FFB020. Anton for numbers and chapters, Inter Black / Bold for text.
- Caps per card: words 7.5 s, stat 6 s, list 9 s (or last item + 3.5 s), compare 9.5 s, chapter 2.2 to 3.4 s.
  Roughly one card every 25 to 35 s.
- Captions: Inter Bold 44, rounded box at y 952, active word in amber, line break on pauses over 0.45 s or
  46 characters. Caption fixes for proper nouns live in `FIX` inside `render_v5.py`.
- Progress bar: 6 px amber at the bottom edge with chapter ticks.
- Audio: pieces joined with 12 to 15 ms fades, highpass 70 Hz, gentle 2.5:1 compression,
  `loudnorm I=-14 TP=-1.5`. No music, no SFX.
