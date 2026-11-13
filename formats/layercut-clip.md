# Layercut clip (interview / podcast re-edit with words behind the head)

An interview clip re-edited so the idea is on screen: the speaker fills a 9:16 frame, one huge word per
sentence sits **behind** their head, small caps captions sit at chest height with the emphasised word in
serif italic, and **concept cards** draw what is being explained (a slider, a comparison, a curve, a loop).
Tool: `bin/clip-edit.sh <spec.json>`. Skill: `clip-editor`. Reference look: lapoz.app "Layercut"
(Sam Altman, same passage as our clip 02), measured below.

## Why it is cheap to run
| step | cost | cached in `specs/work/<name>/` |
|---|---|---|
| cuts | reused from the clip's `qc.json` (already snapped so nobody is cut mid-word); new clips use `clips` | — |
| words | reused from `words.json`; a new clip runs mlx-whisper once | `words.json` |
| base cut (1920x1080, 30 fps, voice) | ffmpeg, seconds | `layercut_base_<hash>.mp4` |
| matte + person track | RobustVideoMatting on MPS: ~50 s for a 40 s clip | `..._alpha.mkv`, `..._track.json` |
| composite + mix | ~90 s for a 40 s clip | — |
The agent writes only the `edit` block (about 25 lines). Nothing is generated per clip, so a re-edit after
a note costs one JSON change and ~90 s of render, not a new program.

## Measured look
| thing | value |
|---|---|
| frame | 1080x1920; speaker crop scaled to 1700 px tall (1080p source) or 1380 px (720p), bottom-aligned |
| room | darkened to 58%, 30% desaturated; top 12% of the plate fades into #0B0B0C |
| crop | follows the person's head from the matte (no face detector); holds per shot, jumps on a cut or a move over 300 px |
| behind word | Anton, fitted to ≤1010 px, 92-100% white falling to 55% toward the head; every third word outline only; springs in from 1.12x; the head overlaps its lower half |
| ring | r 410 behind the head, dashed, 24% white, turning 18°/s |
| captions | Inter Bold 46 caps at y 1230 (1040 when a card is up); spoken words white, upcoming grey |
| emphasis | the spec's `emph` + `edit.italic` words drop to a second line in Instrument Serif Italic 112, accent colour |
| cards | 920x330 rounded panel (14,14,16 at 84%) at y 1170, spring in, 0.25 s out |
| accent | #FFD43B (maize) unless `edit.accent` |
| sound | voice + spec music: loudnorm -20, volume 0.18-0.22, side-chain ducked (ratio 6) |

## Concept cards (what to draw for which idea)
| idea in the sentence | card | params |
|---|---|---|
| how much something is rated, where it sits on a spectrum | `slider` | a, b, value 0-1, title |
| two options, a myth vs the truth, before/after | `compare` | a, b, winner (the other is struck through), title |
| steps, a ranking, a hierarchy | `list` | items, title |
| a number that matters, a running count | `stat` | value, from, label |
| growth, decay, compounding, diminishing returns, Dunning-Kruger | `curve` | shape: exponential, s, j, decline, u, dunning, linear; x, y; falloff |
| loss aversion, prospect theory | `prospect` | gain, loss |
| habits, feedback, vicious/virtuous circles | `loop` | nodes |
| overlap of two things | `venn` | a, b, mid |
| a list of qualities, tags | `chips` | words |
| the line itself | `quote` | text |
Anchor every card to the word that says it: `"on": "compounding", "nth": 2`.


## v2 rules (2026-11-13, after Vatsal's notes: "gaps, overlaps, cards look AI-generated")
- **No panels.** Cards are type drawn straight on the frame over a dark backing that starts *above*
  the type (y 940 with a card, 1110 without): serif italic, thin rules, `01 02 03` Anton numbers,
  a small tracked accent label with a short rule. Never a rounded box with a grey title.
- **Emphasis is inline.** The emphasised word sits in the caption line in serif italic (accent), padded
  16 px each side so italic overhang never touches the next word. No second line under the caption.
- **No blinking.** A caption stays up through pauses under 0.8 s, until the next phrase starts.
- **One card at a time.** An earlier card leaves 0.3 s before the next lands.
- **Anchors fail loudly.** An `on:` word not in the transcript is skipped with a warning (it used to land
  at 0 s). `on:word#2` = the second time it is said. Numbers with commas: anchor on the digits
  (`"on": "20"` for 20,000) and give `value: "20,000"`; the counter keeps the comma and a `pre` (£, $).
- **Translated clips** (Hindi/Punjabi) use the spec's English `lines`: they are mapped into edit time in
  story order, duplicates dropped, lines the cut truncates dropped, and each line is one caption group.
- **Wide/vertical sources** (stage keynotes): the base keeps the source shape, HLG is tonemapped to
  Rec.709, and a window (`window_h`, default 880 px) follows the head; a speaker at the frame edge is
  padded with a feathered black edge so they stay centred. The tracker prefers a figure whose feet reach
  low in the frame, so people on a projector screen are not picked.


## Stabilisation (2026-11-13, after "the AGI in the back is flickering, the numbers shake")
Root causes found frame by frame on Jason keynote 04: the word was placed from the head position *each frame*
(jitter), the crop followed with a dead zone in whole pixels (stepping and lag), the tracker flipped to a woman on
the projector screen whenever Jason was small, and a camera change between two similar shots was not detected.
- The camera is a path computed for the whole clip: per shot, head x/top are median-despiked and smoothed
  with a zero-lag Gaussian (sigma 14 frames x, 21 frames y). Crops are sub-pixel (`resize(box=...)`).
- A shot change is an edit boundary, a head jump over 250 px in one frame, or a frame-difference cut **with**
  head motion (a projector slide changing trips the frame difference while the speaker stands still).
- The tracker stays with the person it follows: other figures are discounted by distance (score / (1 + d/120)).
- Each behind-word gets one fixed height for its whole life (median of the smoothed head over its time).
- A behind-word appears when its word is spoken and leaves `behind_hold` (2.4 s) after, or at the next word.
  `hook_word: true` restores a word on frame 1.
- Tall/wide sources are matted at downsample 0.5 (cache `_alpha_r50.mkv`).
- Check: `specs/work/<name>/layercut_camera.json` logs the crop and word y per frame; fast moves (>15 px/frame)
  must line up with real cuts, and the word y must never change while a word is on screen.

## Rules
- Behind words: one per sentence, a noun or the stake ("COMPOUNDING", "FALL OFF"), never a pronoun or filler.
  Write them in `edit.behind` for anything that will be posted; `auto` is a fallback.
- Cards say only what the speaker says. No invented numbers; a count must be countable in the clip.
- Third-party clips: credit the show and guest in the IG caption; keep edits transformative.
- Check: `bin/clip-edit.sh <spec> --stills 1.5,6,9.5,13` before the full render; then `bin/export-ig.sh`.

## Done so far (2026-11-13)
02 Altman (compounding), 07 Elon (pencils, with a running mention counter), 16 Kahneman (mental accounts,
prospect theory), 17 Munger (invert). Outputs: `~/Downloads/reel-batch/faceless-podcast/*_layercut*.mp4`.
