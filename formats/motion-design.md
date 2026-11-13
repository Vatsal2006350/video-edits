# Motion design (no footage, no cuts)

The look of the best "Claude made this video" posts: an animation written as code, where every shot
is made out of the one before it. It reads as smooth because nothing is replaced and nothing
crossfades. The eye follows one thing from the first frame to the last.

Example: `motion/one-line/` ("one line becomes a reel", 24 s, 1080x1920, 120 BPM, 48 beats, 12 bars).
Deliverable: `~/Downloads/reel-batch/motion-one-line/01_one-line-becomes-a-reel{,_IG}.mp4`.
Skill: `motion-director` (the whole flow, step by step).

## The flow

| step | tool | what it does |
|---|---|---|
| intake | `START-HERE.md` | ask the kind of video, the exact words, the cleared numbers |
| brief | `bin/motion-brief.py` (`hx.py motion brief`) | picks a taste pack from `motion/styles.json`, measures the track/brand/footage, lays the arc over the bars, writes `BRIEF.md` + `beats.json` |
| build | `motion/engine/mg.js` + `motion/<film>/film.js` | every frame a pure function of t |
| stills | `motion/tools/sheet.html?film=<film>&t=...` | the frames you would judge, before the render |
| render | `bin/motion-reel.sh motion/<film> out.mp4` | vendors the engine, HyperFrames check, render with 4 motion-blur sub-frames |
| sound | `bin/motion-score.py score.json score.wav --mux` | original score from sines and noise: soft kick on beats, a sound on every visible action, limited |
| gate | `hx.py motion check motion/<film> --render out.mp4 --ref ref.mp4` | seek-safety, pixel snapping, ../ paths, holds, hard jumps; `bin/motion-stats.py` against a reference |
| deliver | `bin/export-ig.sh`, `bin/ig-safe.py view`, phone mirror | CLAUDE.md "Deliverables" |

## The rules (from the references that work)

1. **One carrier.** Every shot is made out of the previous one: shapes, type and colour transform into the next scene.
2. **No cuts, no fades.** Ink changes are a flood with a hard edge or one horizontal scan line.
3. **A beat grid.** 120 BPM, something on every beat, moves start 0.05 s early so they land on it. No hold over 0.5 s.
4. **Springs that never overshoot.** `1 - (1 + w t) e^(-w t)`, w 12-40. Exponential in/out only for wipes, presses and exits.
5. **Pure function of time.** No `tl.call()`, no state between frames: HyperFrames seeks frame by frame and motion-blur sub-frames run backwards.
6. **Transforms and geometry, not layout.** Margins and left/top snap to whole pixels and stutter.
7. **Light is line density.** Scan lines whose thickness follows the light. No glow, no flares, no particles.
8. **Few inks.** Two or three, each stage's accent is the next stage's colour, never a fourth colour.
9. **Safe box.** Centred work within 724 px (x 178-902); labels at y 318 and 1512; the right edge belongs to Instagram's buttons.
10. **Facts only.** Numbers on screen come from `channel-facts.json` or the user's words. The film uses 88 effects (effects_count), 76 looks (catalog), 120 BPM, 0 cuts.
11. **Loop.** The last frame is the first frame, picture and sound.

## Measured (bin/motion-stats.py, 30 fps, 160 px greyscale)

| film | hard jumps/s | still share | longest hold | mean motion |
|---|---|---|---|---|
| reference: drafting-inks showreel (`~/Downloads/original.mp4`, 30 s) | 0.23 | 27.0% | 0.4 s | 1.94 |
| `motion/one-line` r7 (24 s) | 0.21 | 34.9% | 0.5 s | 1.42 |

The first renders of `one-line` held still for 0.9-1.0 s three times (the hologram chart, the dashboard
fill, the end card) and read as dead air next to the reference. Each was fixed by giving that bar a move on
every beat: the chart scrolls one column a beat, the solids turn, a hatch sweeps into the reel panel, a
pass of light crosses the wordmark.

## Taste packs (`motion/styles.json`)

| pack | fits | from |
|---|---|---|
| drafting-inks | introduce a person, a tool or a system; how something is built | heyiamnick's showreel prompt |
| one-shape-ui | an app or SaaS product, a feature flow | twoclipping's UI-morph prompt |
| loud-poster | a launch or drop with real clips and photos | twoclipping's castr trailer prompt |
| editorial-cream | a talking-head point: a number grows, a comparison, a step, a chapter | Skillry CreatorMotion's house style |
| kinetic-architecture | a quote, a manifesto, a founder line | gdgtify's BUILD THE FLOOR prompt |

Take the rules from a reference, never the creator's film. Add a pack only when a reference earns it,
and measure it with `bin/motion-stats.py` first.
