# video-edits toolkit — what each tool does and when an agent should reach for it

Everything is local: ffmpeg, PIL/numpy, mlx-whisper, hyperframes (matte). No API calls.
Frame is 1080x1920. IG safe box is **x 59–918, y 278–1536**; centred text is bounded by
**724px** (twice centre-to-rail), not the box width. Verify placement on the *rendered*
layer PNGs, never by eyeballing a still. Read `FOOTAGE.md` before using any clip.

## Reel builders  (`bin/`, each is `ENV=... bash bin/x.sh`)
| tool | format | notes |
|---|---|---|
| `or-reel.sh` | "X OR Y" gold fisheye hook → loading dots → beat-cut payoffs | cut lands before the drop |
| `list-reel.sh` | "N things I did at N": one still/clip per beat + label, payoff on the drop | `BEATS`, `HOOK`, `ITEMS` `path\|seek\|text\|logo\|cy\|logo_y` |
| `glowup-reel.sh` | childhood stills desaturated, colour returns at the drop | stills cover-cropped, payoff letterboxed |
| `diptych-reel.sh` | then/now top-bottom split, cut together | |
| `card-reel.sh` | one hero line per shot, no talking head | |
| `travel-story-reel.sh` | opening line → beat-cut montage → closing line | `stab=1` per shot |
| `bounce-reel.sh` | typing open → hard-cut bounce (guitar / keyboard), one italic caption held the whole time | `SHOTS=path\|seek\|dur\|zoom`, `L1`/`L2`, burns `AUDIO`; drop shot is `zoom=1`. `formats/daily-routine-bounce.md` |
| `receipt-reel2.sh` | meme hook → receipts, viral-matched (Montserrat Bold 61 + shadow, photos on black bars, per-scene `dur`, `tat` text delay); `AUDIO=`/`AUDIO_SS=` burns the music and exports IG-spec | supersedes `receipt-reel.sh` |
| `build-story-reel.sh` | talking head with forced-aligned captions + typed serif hook; `SEGS` speech cuts, `CUTS` cutaways in speech time, `TAIL` b-roll appended after the speech (music only), `WORDFIX` caption corrections (`heard=meant,to#2=from,junk=`; `#N` targets one occurrence), `MIDTEXT` lower-third hero lines (`start|dur|size|align|top|line1|line2`), `BROLL_VF` grade applied to every cutaway/tail clip, `SFX` cues (`t|file.wav|gain_dB`, mixed with the bed and ducked under voice), `MUSIC`/`MUSIC_SS`/`MUSVOL` (0.17 is the level Vatsal signed off for a ducked song bed; 0.30 was 'too loud'); drops whisper's hallucinated tail words | |
| `promo-reel` (= `promo-caption.py` + `kinetic-hook.py` + `lib-still.sh`) | JacHacks / Kumar promo: kinetic hero words behind the matte + running captions + logo cards | see below |

## Text renderers  (PNG sequences; overlay with ffmpeg)
- `kinetic-hook.py` — hero words on cue. Per item: `face fill shadow track layer(front|behind) from(left|right|up|scale|cut) fade leave_fade life hold hero echo echo_gap echo_alpha cap_h y_bottom squash_to logo`. `cap_h`+`squash_to` = the Kumar fixed-cap / X-compressed look; `from:cut`+`leave_fade:0.02` = hard cuts; `echo:3` = the ×3 stack. Writes `k_*.png` (behind) and `f_*.png` (front).
- `promo-caption.py` — running captions from `aligned.json`: `font size cy anchor(baseline|top) line_pitch max_words fill hl stroke highlight mute skip_before cards card_top`. `card_top` pins the logo rows at an absolute y (use it to keep cards off the face). Anton+stroke = Mumbai style; Montserrat, red, `anchor:top` = Kumar style. Cards: transparent logos in fitted boxes, 2 per row, photos up to 660px.
- `typewriter.py` — phrase-by-phrase typewriter hook (Instrument Serif, 24 chars/s, hold-until-next, 0.13s fade, last phrase caps). `phrases:[{t,at,caps?,until?}]` from aligned words. Dark ink on bright backgrounds; set `fill` white on graded footage. Also writes `keystrokes.json` (one time per non-space character).
- `keystroke-track.py <keystrokes.json> <dur> <out.wav> [gain=0.35]` — keystroke SFX track from that file (cycles `sfx/key1-3.wav`, jittered gain). Mix under the dialogue with `amix=normalize=0`. The reference reel has NO clicks; add only when asked.
- `hero-type.py`, `dynamic-hook.py`, `typed-hook.py`, `fisheye-text.py`, `glow-text.py`, `list-label.py` — older single-purpose renderers, all rail-aware.
- `lib-still.sh` — `still_vf` (letterbox over blurred self), `still_black_vf` (black bars), `still_cover_vf` (crop to fill). **Never** `scale:-1,zoompan s=` — it stretches.

## Mattes / behind-body
- `embed-behind.sh <in> <out> <t0> <t1> <png>` — matte the speaker in a window, put a PNG behind them.
- For per-frame text behind the body: `hyperframes remove-background` once → keep `bg/` + `fg/` PNGs → composite bg + `k_` + fg + `f_` (see the reel-34 chain in memory). Grade bg and fg *separately* before compositing; a global darken silhouettes the face.

- `studio-key.py` — clean key of a matted talking head over a generated backdrop: min(temporal-avg, current) alpha, MinFilter choke, feather, levels, **edge-extend** (boundary band recoloured from the interior so hair/shoulder edges are not wall-white), y-ramp darkening of hands, behind/front layers. JSON spec in the file header.

- Cut-up voice takes: `rubberband=tempo=X` for speed (never `atempo` above ~1.08), `acrossfade=d=0.012` at joins, 60ms fades around any inserted silence, `loudnorm=...:linear=true`. Verify with a sample-diff click scan and a spectral-flux check at each join (recipe in formats/kumar-method-reel-format.md v12).

- `story-qa.py --segs --cuts --tail` — pre-render gate wired into `build-story-reel.sh` (set `QA_FORCE=1` to override): flags speaker flashes (cutaway gaps < 0.6s), a cutaway from the take that is speaking under it, cuts landing inside a segment's first 0.4s / last 0.3s, seeks past the source end. After every story build also run a reviewer agent (the QA prompt in `formats/story-reel-qa.md`) before sending.

## Analysis
- `music-map.py <mp3…>` — drop time, loud-start, peaks → where the payoff must land. `beats.py <mp3> [n]` — beat grid.
- `force-align.py` — whisperx alignment (whisper alone pins word 1 to 0.00 and jitters ±0.3s).
- `contact-sheet.py <dir>` — look at a folder before using it; writes an index of tile→file+timestamp.
- `scan-stability.py <win> <dir>` — steadiest window per clip. `ig-safe.py view <mp4> <out.jpg> [t…]` — IG chrome over real frames.
- Reference reels: `uvx yt-dlp` is the only path that works (IG's player won't buffer in an automated tab; canvas grabs are CORS-tainted). Then contact-sheet, transcribe, and *measure* type with strict-colour pixel bboxes.

- Voice removal from a reference bed: `uvx --with numpy --with torchaudio --with soundfile --from demucs demucs --two-stems=vocals -n htdemucs -o <dir> <audio>` (plain `--from demucs` fails on a missing numpy). ~1 min for 27s on this Mac. Verify with whisper on `no_vocals.wav`.

## Delivery
- `color-normalize.sh inspect <video>` — shows pixel format and color tags. `raw <in> <out>` tonemaps tagged iPhone HLG/PQ footage and writes a Rec.709 H.264 intermediate. `retag <in> <out>` is metadata-only for display-ready pixels that were already tonemapped but inherited an HDR tag; never use `retag` on actual untonemapped HDR pixels.
- `remix-story-audio.sh <picture.mp4> <voice.wav> <out.mp4>` — rebuilds a story reel soundtrack from stems. Set `MUSIC`, `MUSIC_SS`, and preferably `MUSIC_TARGET_DBFS=-36` for an automatically calibrated quiet bed; unlike a fixed `MUSIC_VOL`, this measures the selected section so differently mastered songs remain equally quiet. `MUSIC_VOL`, `MUSIC_INTRO_GAIN`, `INTRO_GAIN`, `WHOOSH_TIMES`, and `SFX_STEM` remain available. It levels quiet dialogue and starts music at 0:00. Default `DUCKING=1` side-chains the bed; use `DUCKING=0` when the bed must stay fixed and never rebound during pauses.
- `export-ig.sh <master.mp4> <name_IG.mp4>` — creates the upload copy at the house Instagram spec and explicitly stamps Rec.709 metadata. Builders must tonemap HLG/PQ footage first; this prevents already-tonemapped pixels from retaining an iPhone HLG tag.
- Intermediate work defaults to `${TMPDIR:-/tmp}/video-edits`. Set `VIDEO_EDITS_WORK_ROOT` to keep it elsewhere. Nothing depends on a Claude session directory.

## Assets
`fonts/` (63; `Anton`, `DMSerifDisplay-Regular` = Kumar serif, `PlayfairDisplay-BlackItalic`, `Montserrat-*`, `AvenirNext`), `logos/` (transparent; `*_w.png` white wordmarks; `jachacks/` event photos + sponsor marks), `~/Downloads/music-good/` (his tracks, profiled in its README), `sfx/` (click, key1-3 keystrokes, `sizzle.wav` 5s synthesised pan sizzle, `whoosh.wav` 0.45s transition sweep -- placeholders until licensed SFX are verified).

## Effects inventory — what exists vs what does not (be honest when asked)
Have: daily-routine bounce (`bounce-reel.sh`: slow open then hard-cut A/B, held italic caption), word-level kinetic type (slide/punch/scale/cut, echo stack, X-squash, behind-body), typewriter (+SFX), fisheye warp, glow/bloom, stacked hero serif, word-by-word typed hook, running captions with highlight word (two styles) and hyperframes embedded-captions (pop-in), label stickers with logos, logo/photo cards, title cards, CTA outro, loading dots, aura, greyscale→colour drop, letterbox/cover/black stills, behind-body matte, two-layer grade (inline ffmpeg in the reel-34 chain), vidstab, beat/drop mapping.
Do NOT have yet: a standalone grade tool with presets (grading is per-chain ffmpeg), letter-by-letter kinetic (only word-level + typewriter), counter/number roll, handwritten underline/scribble, glitch/RGB split, blur-in/blur-out text, zoom-punch or shake on cuts, a transition library (only hard cuts), whoosh/impact SFX (only `sfx/click.wav`, `key1-3.wav`). Build the one the reel needs, then list it here.

## Batch
`batch/build-all.sh [yc|lessons|success|travel]` rebuilds `~/Downloads/reel-batch/` themed folders; incremental, `FORCE=1` re-renders.
