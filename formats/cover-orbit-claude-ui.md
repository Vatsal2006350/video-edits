# Cover orbit + Claude UI + iCloud gallery takeover (measured)

The look built for `videos/codex-reel-automation` v08: a talking head stays
visible throughout while his own reel covers appear in a full-screen gallery
takeover, a Claude-style composer types a prompt, and the composer opens into
an edit timeline on the music rise.

Pipeline: one HyperFrames composition rendered **twice** (variable `layer` =
`behind` / `front`), composited frame-exact with `bin/composite-layers.py`
(not an ffmpeg overlay chain — see "The compositor bug" below).

## References measured (not copied)

| Reel | Duration | What was measured |
|---|---|---|
| `instagram.com/reel/DfF2qQKFdpt` (Justyn Berkovits) | 41.37s | cover cards with label chips arcing above the head; solid caption pill; serif display headline that runs behind the head |
| `instagram.com/reel/DfUb4MVslfp` (Prachi Gautam) | 55.01s | two-tier caption: spaced sans lead-in (cap height 23px) over one italic serif keyword — "amazing" = 325px wide, i.e. Instrument Serif Italic ~96px |
| `instagram.com/reel/De7JFJdo4KX` (Vibha Ramprakash) | — | slash-command UI then the effect; checklist card with green ticks |
| `instagram.com/reel/DfNyeKtx45f` (Ritesh Kumar Verma) | — | same slash-command format (`/text-behind`, `/tier-list`, `/captions`, `/freeze-frame`, `/film`, `/spotlight`) — confirms this is a recognised Claude-editing-demo genre, not one person's trick |
| `github.com/Vibha-Ramprakash/claude-video-effects` (MIT) | — | 51 Python effects; vendored whole, see "What we took from the other repo" below |

## What we took from the other repo

Vendored at `effects/claude-video-effects` (commit pinned in
`VENDORED-COMMIT.txt`), wrapped by `bin/fx51.sh` (denylist guard,
no-overwrite, venv auto-setup). All 51 effects are available for any future
reel — run `bin/fx51.sh list`.

We **ran their renderer** (not just read the code) on this footage before
deciding anything, because a framing assumption only shows up in output:

| Effect | Result on a TIGHT talking-head (head ≈ half frame width) |
|---|---|
| `orbit` | cards clip at the frame edges — assumes a wide/small-head shot |
| `fan-build` | cards fly off the top of frame |
| `noise` | **reads correctly** — reels pile up behind the head, nothing rings past the face |

Lesson for next time: **before adopting any "ring/arc/orbit around the head"
effect, render it on the actual footage first.** The geometry that works is a
function of how much of the frame the head fills, not a property of the
effect. We built three versions chasing this (orbit → arc → burst) before
accepting that *none* of them suit this framing and switching to a full-screen
takeover instead — rendering their effect on our footage at step one would
have skipped two of those three iterations.

## Why the cover material ended up as a full-screen takeover, not an overlay

Built three versions in order, each one proving the last couldn't work on
this footage:
1. **Ring around the head** — crosses the face at every angle on a close-up.
2. **Arc anchored to the tracked head** (cards at `cx + d*150*spread`) — fits,
   but five cards each independently tracking a jittery matte read as shaky.
3. **Burst from behind the head** — fixed the shake (behind-layer-only, no
   per-frame layer decision) but was visually thin: "is this the best you can
   do?" was a fair question.

**What shipped:** a full-screen `iCloud Photo Library` scan — grid of his real
covers, a scan beam, tiles flash-select as the beam passes. A full-bleed
surface has nothing to jitter against, so the whole shakiness problem
disappears by construction instead of being tuned away.

```
GAL_IN (lands on the spoken word) → clip-path band opens from centre, tiles
  cascade in from centre-out, per-column parallax while scanning →
GAL_EXIT (same frame as the whoosh) → grid accelerates toward the timeline
  card while the band closes → GAL_OUT, face back, 0.3-0.5s before the next beat
```

Grid: 5 cols × 3 rows inside the safe box (5·162 + 4·12 = 858 ≤ 859 wide),
placed at y 420 so the caption band below it sits on clean dark surface, not
on bright photo tiles (a caption drawn over a bright thumbnail fails the QC
CONTRAST check — see below).

## The compositor bug — the one that actually mattered

**A chain of ffmpeg `overlay` filters over several `-itsoffset` alpha inputs
can silently drop a single frame.** `overlay` pairs inputs by timestamp; with
five streams (two `image2` PNG sequences, three offset alpha WebMs) in one
filter graph, it dropped exactly one frame of the front layer at a fixed
point. The rendered layer PNGs were measured perfectly smooth on both sides
of that instant — the fault was introduced by the compositor, not the
animation. Two full rounds of "fix the animation" were spent on this before
isolating it (base + one layer alone: no hole; add the mattes: hole).

**Fix:** `bin/composite-layers.py` — indexes every stream by frame **number**,
not timestamp. Layer PNG *i* always lands on base frame *i*; a matte stream is
read sequentially once its start frame is reached. A dropped/misaligned frame
is structurally impossible, not just unlikely. ~70s slower per render than
the overlay chain; worth it every time a matte is in the mix.

**Use it, not a filter_complex overlay chain, whenever compositing ≥2 PNG
sequences and/or alpha mattes together** — this is the general case, not a
one-off for this reel. `render_v08.sh` is the reference call.

## The two gate checks that actually caught things

`bin/reel-qc.py` ran against this reel four times before passing clean; it
found seven distinct real faults, not style nitpicks:

1. Cards/proof-labels drawn in BOTH layers (should be behind-only or
   front-only) — caught by the per-element SAFE-BOX check.
2. Caption crossfading under a full-bleed takeover → unreadable for the
   length of both fades — caught by CONTRAST, fixed by handing the caption
   off to the takeover instead of layering under it.
3. Overlapping GSAP tweens on one element at a seek boundary — the SAME root
   cause as the compositor bug and the earlier caption-stacking bug: **two
   tweens owning one property near a boundary is ambiguous under `tl.seek()`.
   Always use one keyframed tween (in → hold → out), never two chained
   `fromTo`s, for anything with hysteresis at a cut point.**
4. **FLASH** (added this session): a layer's alpha coverage jumping away and
   back within 1-2 frames. A sampled contact sheet (even at a tight `--step`)
   **cannot see a one-frame hole** — this is why the compositor bug survived
   two "looks clean" reviews. FLASH runs on every frame, not a sample.
   Self-tested against a synthetic one-frame dropout before trusting it.

Known blind spot (not yet fixed): text drawn ON a full-bleed opaque surface
shares one connected-component with the backdrop, so SAFE-BOX skips checking
it. Place type on a takeover card by hand against the 278–1536 band.

## Head tracking

`bin/face-track.py <matte.webm|mov> <out.json> [--offset S]` reads a matte's
alpha and reports head top / centre-x / width per frame — no model, no new
dependency, since the matte already exists in the render chain. On this
footage: head top 424–492, **centre x 404–478** (he sits left of frame
centre, not at x=540), width 444–548. **Anchor any behind-head art to this,
never to frame centre** — assuming centre was wrong here and would be wrong
on most selfie footage.

## Matte format

Matte as **VP9/alpha WebM** (~15MB per 6s window) instead of ProRes 4444
(~370MB) — this alone saved >1GB across the session's mattes. ffmpeg needs
`-c:v libvpx-vp9` **before** `-i` or it silently drops the alpha and
`alphaextract` fails with "Requested planes not available". Matte only the
windows that need it; a full-film pass fills a tight disk fast.

## GSAP / HyperFrames rules this session re-learned twice

- Initial transforms belong in `gsap.set`, never CSS, or `hyperframes check`
  fails `gsap_css_transform_conflict`.
- **Never two tweens (even `fromTo` + a hard `set`) owning the same property
  near a cut point.** One keyframed tween. This was the caption bug, the
  wipe-dropout symptom at the JS layer, and the lint `overlapping_gsap_tweens`
  warning — three appearances of one rule.
- A full-bleed takeover gets `immediateRender: false` on every tween touching
  it, or a re-seek re-triggers the wrong starting state.

## Reel covers

Pulled live, read-only, from the Instagram Graph API (`/me/media` thumbnails,
token in the login keychain) for whichever account the stored token belongs
to — confirm which account before assuming it matches a screenshot asset
already in the project (this reel's dashboard screenshot was a *different*
account than the live token).

## Sound

SFX from the repo's `sfx/` (`whoosh`, `click`, `slap`), mixed from a cue sheet
the builder emits. Sync rule: **an SFX cue and the motion it accompanies must
share a timestamp exactly** — a whoosh that fires after the clip-path has
already started moving reads as picture-then-sound, which is as noticeable as
a dropped frame. Under the voice bed at weight 0.5 with `alimiter=0.89`.
