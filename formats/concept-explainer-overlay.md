# Concept-explainer overlay: animated data cards on talking-head conference footage

Built for `videos/isg-ai-summit` reel 07 ("the last programming language your agents
need" — Jason Mars explaining Jac at the ISG AI Summit). The published v1 had a frame-zero
hook and running captions but nothing explaining the actual technical claim while he made
it: 600,000 lines of TypeScript/Next.js became 30,000 lines in Jac, and Jac supersets
Python/TypeScript/JavaScript rather than competing with them. Audience feedback: captions
were hard to read against the venue's own busy screen, and there was nothing to look at
"especially when he explains the concept."

## Getting the timing right without a saved aligned.json

The original build's per-word caption timing wasn't saved anywhere editable, so a font
or overlay revision has to re-derive it. **`uvx --from mlx-whisper mlx_whisper --word-timestamps True`
is enough on its own** — it returned clean, correct timestamps on this clip (including
"Jac", which base whisper usually mishears as "Jack"), so the heavier `force-align.py`
(whisperx, needs its own venv that didn't exist on this machine) wasn't necessary. Feed it
exactly the concatenated source ranges from `selects.json`'s `segments` array (the picture
cut's own boundaries) so the audio duration matches the reel to the frame — do not
re-transcribe the whole source and try to re-locate the excerpt by eye.

Read the word timestamps straight off the output JSON (`segments[].words[].{word,start,end}`)
— that schema already matches what `bin/make-captions.py` expects as `aligned.json`, so no
reformatting step is needed beyond fixing the one or two words whisper mishears.

## Caption legibility: cinematic serif + a text-sized soft scrim, not a lower-third bar

A thin-stroke serif over a moving conference-stage background (hexagon wall, bright
screen) is illegible at phone speed no matter the stroke width. First fix was a full-width
opaque box behind heavier type (ASS `BorderStyle: 3`) — legible, but it read as "a big black
bar," not the "grand, cinematic" look the house wants (the reference was the
`codex-reel-automation` reel's two-tier Instrument Serif treatment). Final version:

- **Font**: `make-captions.py` gained `letter_spacing` (ASS `\fsp`) and `blur` (ASS `\blur`)
  options. Instrument Serif, tracked caps, `\blur` for a soft glow edge instead of a hard
  outline — this is the "grand" look, not the Archivo-Black-in-a-box look. **Measure the
  rendered width before committing to a size**: the serif's wide glyphs blew past the house
  724px centred-text bound at the size that looked right in isolation (118px → 873px on the
  worst group); dropped to 92px + 2px tracking to land under 724px, checked against every
  caption group's text, not just a couple of samples.
- **Backing**: a small blurred rounded pill sized to *that caption's own text*
  (`bin/make-captions.py` now also writes `caps-groups.json`, one row per caption group with
  its exact text/start/end, so a companion overlay never has to re-derive the grouping), not
  a full-width bar. Reads as a soft glow, not a plate.
- **The scrim still has to fully occlude the OLD (v1) burned-in captions**, which is a
  harder constraint than it sounds: the old caption pipeline's word grouping almost
  certainly used different `max_words`/`max_chars` than the new one, so at any given instant
  the old and new text are not the same width, even for the same words — a pill sized tightly
  to the *new* text left the *old* text's wider instances exposed at the edges (shipped once;
  ghosting was visible above/around the new line). **Measure the old caption's actual pixel
  footprint** (a yellow-pixel mask scan across several timestamps, not a guess from one
  crop) and size the scrim's floor/ceiling (`MIN_SCRIM_W`/`MAX_SCRIM_W`) to comfortably
  exceed it in both axes, independent of what the new text measures. Also extend the
  vertical span past both the old position and the new one if they don't land on the same
  baseline (they didn't here — old captions sat ~80px higher than the new Instrument Serif
  line's `MarginV`).
- `MAX_SCRIM_W` still has to respect the safe-box's 724px centred bound even though the
  scrim isn't text — a backing wider than that crosses into IG's own UI rail.

## The data-card system

One evolving card (`videos/isg-ai-summit/jac_graphics.py`), not a HyperFrames comp — this
reel has no "behind the head" requirement (wide static conference shot, speaker occupies
the lower-left third), so a plain PIL-rendered PNG sequence composited with **one** ffmpeg
`overlay` is the right tool per the root CLAUDE.md workflow note (single simple layer).
Card region: `x 460-918, y 470-1030`, chosen to sit in the open hexagon-wall space to the
speaker's upper right, clear of his body and clear of the caption bar — checked against
frames at the actual beat timestamps, not assumed.

- **Beat 1 (code-size shrink):** a vertical bar grows in sync with a counting number as he
  says "600,000 lines" (word timestamps anchor the count-up), holds, then both bar and
  number morph (grey→yellow, 600K→30K) exactly on "to Jac", ending with a stamped
  "20X LESS CODE" badge timed to the end of "lines of code."
- **Beat 2 (open/supersets/replaces):** "OPEN SOURCE" and "FREE" chips pop on those exact
  words; three language chips (Python/TypeScript/JavaScript — the ecosystem Jac's own
  docs list, not a guess) fly in and merge into a single "JAC" chip on "supersets... up
  there", with "REPLACES THEM" landing on that word.

**Lesson re-learned from the first draft:** derive every row's y-position from a fixed
card-top anchor, never from another row's dynamic height (the bar's height, in this case).
The first draft computed the number/subtitle/chip positions as offsets from the *bar's*
top edge, so they visibly jumped and overlapped every time the bar animated. Fixed anchors
for every row, independent of what the bar is doing, eliminated the bug outright instead of
tuning offsets.

**VFX pass (second revision):** the first cut of the cards was functionally correct but
flat — rounded rects, flat fills, linear eases — and read as "a chart," not motion graphics.
Cheap, no-dependency PIL techniques that actually changed the read:
- A vertical gradient fill + a one-pixel top highlight line on the card (`rounded_card`)
  reads as glass/depth instead of a flat panel, for near-zero cost.
- `glow_blob()` (an ellipse blurred with `ImageFilter.GaussianBlur`) behind the bar fill,
  behind badges, and as a soft halo behind the whole card — cached once per card instance,
  reused every frame, basically free.
- `sparkle_burst()` — a handful of small diamonds radiating outward on a fixed seed (so it's
  reproducible, not actually random) at the exact frame a badge or merge lands. The payoff
  moments ("20X LESS CODE", the JAC chip-merge) read as *earned* instead of just appearing.
- `ease_out_back()` (a small overshoot) on every pop-in instead of `ease_out_cubic` — chips
  and badges land with a slight bounce rather than settling flatly. Reserve plain cubic
  easing for continuous motion (the bar's grow/shrink), back-ease for discrete pops.
- A diagonal "sheen" polygon clipped to the bar's own rounded-rect mask, so a flat colour
  fill reads as material rather than a solid block.
- Language chips got a small colour-coded monogram dot (blue "PY", blue "TS", yellow "JS")
  instead of plain text pills — real icon assets aren't available for third-party languages
  under this repo's `logos/`-only rule, so a simple circular monogram is the honest
  substitute, not a fabricated logo.

## What was checked, not assumed

- `bin/reel-qc.py master` on the rebuilt export: the first IG export failed true-peak
  (-1.6 dBFS, need ≤ -1.9) even with the house `export-ig.sh` defaults — AAC inter-sample
  peaking overshot the nominal alimiter ceiling by about 0.7 dB on this particular
  music+voice mix. Fixed by tightening `IG_LIMIT=0.68` (not by touching the shared
  `export-ig.sh` defaults, which are correct for the general case).
- `bin/ig-safe.py view` at every beat timestamp of the new cards, not just the usual
  evenly-spaced sample — confirmed the card sits inside the safe box at its widest
  (badge/chip) states, not just its resting state.
