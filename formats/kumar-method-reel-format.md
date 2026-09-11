
Two reels Vatsal sent as style targets are the same format: `DZN5Njzo-Yh` (@thekumarmethod, "message to all finance bros", the original) and `DZ4Bw2dPM2R` (aaravsarbalia, 12-year-old chess kid, 172K likes, "inspired by @thekumarmethod"). Decoded from `yt-dlp` pulls (the only path that worked — IG's player never buffers in the automated Chrome tab, the extension redacts tokened CDN URLs, and canvas grabs are CORS-tainted).

**Structure (26.6s, music drop at 11.77s — Vatsal supplied `music-good/ref2_DZN5Njzo.mp3`, which is the whole reel audio WITH Kumar's voice; the usable bed is `music-good/kumar_bed_novoice.wav` (demucs stem, see the music README)):**
1. 0–2s: small bold-sans caption builds word by word, just below centre. Red `RGB(252,10,2)`; a second speaker later gets yellow `(231,216,6)`.
2. ~2.6s: hard cut to a backlit black silhouette insert, music only.
3. 3.7s: back to camera; hero word above the head. "My name is KUMAR."
4. 7–11.6s: **one hero word per beat, each hard-cutting to the next** (IM / JOBS / BIGGEST / INFLUENCER / WORLD). The last word lands ON the drop.
5. 11.8–19.5s: music-only montage of silhouette/detail shots on the beat grid, with the **name stacked ×3 down the frame** (opacity falling) across split panels — the signature move.
6. 19.5–24s: second voice (wife/mother: "my husband/son wants to be famous, so please follow him"), yellow captions.
7. 25–26.6s: closer — name top, DEBUT bottom, red serif, full-body silhouette on white.

**Measured numbers (from `ref2.mp4`, strict-red pixel bbox; the loose red detector was contaminated by the map/poster behind him and reported a 756px cap — restrict to y200–650 and R>225,G<45,B<45):**
- Hero cap height **277px = 14.4% of frame**, identical for KUMAR / IM / BIGGEST / INFLUENCER / WORLD. Top y≈312 (just inside the IG header line), bottom y≈590 = his hairline.
- Width **~965–975px = 90% of frame for every word regardless of letter count** → the editor **horizontally compresses** long words to fill the box at a fixed cap. Short words (JOBS, 855px) stop at natural width. Implemented as `squash_to` in `kinetic-hook.py`. This *does* run under the like/comment rail; the reference does it and it worked — a deliberate exception to the safe-box rule for ~1s hero beats, said out loud to Vatsal.
- **Flat red, no shadow, no stroke** (6× edge zoom). **Hard cut** in and out — red pixel count jumps 21k→61k between adjacent frames, no ramp. Track ≈0.
- Caption: bold humanist sans, red, block **top-anchored at y≈906 and grows downward** as words arrive (one line 906–997, two lines 906–1227), ≈92px size, pitch ≈1.3, centred, max width ≈772px. `anchor:'top'`+`line_pitch` in `promo-caption.py`.
- ×3 echo at 15.0s: three equal copies, ~204px tall, centres y≈336/977/1602 over three split panels, **all full opacity** (`echo_alpha` defaults to 1.0 now; the maize reel's 55% falloff read as washed on dark panels). The panels must be three *different* shots — the first build used `photo_DSC06792` and `umich_winners`, which are two frames of the same moment, and it showed; `panel3.png` is room / stage / winning team. The insert *replaces* the talking-head frames for that beat (frames 742–829), so the copies go on the front layer.
- Closer 25.6s: name top band 210–514 (15.8%H), DEBUT bottom 1513–1733 (11.5%H).
- On Vatsal's lake clip his head sits higher (top ≈450 vs Kumar's ≈590), so a 277 cap above the hairline would breach the header → cap 260 with `y_bottom` 560 on the **behind** layer (full-clip matte), bottom of the word tucked behind the hair like SARBALIA in the chess copy.

**Grade (measured, `ref2.mp4`, red-text pixels excluded):** talking shots luma mean **≈20, median ≈10, shadows RGB≈(15,11,13)**, sat 0.4–0.5, warm/magenta cast — a dark room with a side key on the face, not a LUT. Silhouette inserts are bimodal (median 181 bg, shadows 3–5). Closer: luma 132, median 146, p98 183, **sat 0.11** — bright, flat, no true whites. Vatsal's lake clip starts at luma 150 / sat 0.16 (overcast daylight).
**A global darken cannot reproduce the talking look:** the recipe that hits L19/median 4 turns his face into a silhouette, because Kumar's face is lit and his room isn't. The fix is the matte: grade the **background hard** and **him gently**, which fakes a key light. Recipes in ffmpeg (`bin` has them inline in the reel-34 chain):
- bg: `eq=brightness=-0.42:contrast=1.6:saturation=1.25,colorbalance=rs=0.1:gs=-0.03:bs=-0.04:rm=0.06:bm=-0.05,curves=all='0/0 0.35/0.08 0.7/0.45 1/0.85',vignette=PI/3.6`
- fg (colour only, then `alphaextract`/`alphamerge` to keep the matte): `eq=brightness=-0.16:contrast=1.3:saturation=1.25,colorbalance=rs=0.08:gs=-0.01:bs=-0.05:rm=0.05:bm=-0.04,curves=all='0/0 0.3/0.18 0.7/0.62 1/0.95'`
  → composite measures L20 / median 5 with the face band at luma 44 (2× the frame).
- closer: `eq=saturation=0.30:contrast=0.85:brightness=-0.03,curves=all='0/0.05 0.5/0.55 1/0.72'` on daylight beach → ≈L150 sat 0.05, close to Kumar's 132 / 0.11.
Grade the layers **before** compositing the hero text; grading after would tint the red. **Compositor trap:** an insert or closer clip that replaces the matted shot has no fg/bg split, so a word that lives on the *behind* layer (`k_`) vanishes unless the compositor lays `k_` *and* `f_` over that clip — the first graded render lost JACHACKS from the closer this way.

**Type:** hero = upright high-contrast serif, all caps, tracked — **DM Serif Display Regular** is the match on disk (bracketed serifs, hairline inner strokes on the W; Times/Georgia Bold are too even-weight, Playfair italic is wrong). Hero sits at y≈300–460, above the face, sometimes tucking behind the hair. Caption = bold humanist sans (Montserrat-Bold stands in), no stroke in the ref; add a 3px dark stroke on bright footage. Colour is one accent only — the Michigan maize/blue pairing from [[promo-reel-format]] is a different system; do not mix them.

**What this format needs from Vatsal that cannot be faked:** a take scripted to the beat ("This is a message to all ___. My name is Vatsal Shah. I'm ___. And I'm going to ___ by becoming the biggest ___ in the world." — ~11s, last word on 11.77), 3–4 stylised inserts (hackathon footage, JacHacks site images, a backlit silhouette, a full-body-on-plain closer), and optionally a second voice. The editing — captions, hero words, hard cuts, ×3 echo, beat-cut montage, closer — is all in `bin/kinetic-hook.py` (`leave_fade` 0.06 for hard cuts, `echo`/`echo_gap`) + `promo-caption.py` (`font`, `mute`) + `lib-still.sh`.

## Vatsal's own take (2026-09-06, reel 36 `36_kumar_debut_vatsal.mp4`)
Source IMG_5217.MOV (4K60, white wall, JacHacks tee). Script: "This is a message to all hackathon
organisers. My name is Vatsal Shah. I'm a nineteen-year-old YC founder. And I'm going to make Ann
Arbor the AI capital of hackathons and become the biggest student influencer in the world."
- His read was 18s vs Kumar's 11.3s. Fix = hard-cut the inter-phrase pauses (they are cut points in
  the format anyway) + `atempo`/`setpts` 1.12 → 15.3s, then **extend the bed's intro** by repeating
  2.16→5.69s once with a 40ms crossfade so the drop moves 11.77→15.26 and lands right after "world".
  The intro is a pad, not a bar loop (autocorr found no beat), so any seam on a strong onset works.
- His head top sat at y=405 (Kumar 590) → push the frame down 185px with a **mirrored top band of
  the wall** (`crop=1080:185,vflip` + `vstack`), invisible once graded. Then cap 277 / y_bottom 600.
- White wall needs a harder bg grade than the lake recipe: `eq=brightness=-0.52:contrast=1.7`,
  curves `0/0 0.35/0.05 0.7/0.36 1/0.72`, vignette PI/3.4 → frame L31 / median 11, face 73.
- Silhouette insert = the matte alpha filled (6,4,5) over a grey radial wall (196→126), 1.15 zoom;
  a moving one for the 0.9s insert (per-frame alpha), stills for the montage.
- Captions muted under every hero word (the reference shows none there); the yellow "second voice"
  is a synthetic `aligned.json` fed to `promo-caption.py` (size 72, max_words 3).
- Montage cuts on the bed's post-drop onsets (15.27 15.82 16.17 16.65 17.10 17.57 18.00 18.47 …),
  stills get a 1.00→1.07 push-in. Listening footage for the yellow section = the unused head/tail
  of the same take (0.2–3.2s, 21.85–23.8s), matted and graded with the rest.
- Mix: voice loudnorm I=-16, bed at 0.42 under the voice and 1.0 from the drop, alimiter.
- v2 (same day): Vatsal rejected the black silhouettes ("don't just show the black cut-out") -> every silhouette slot is a
  Maldives clip of him not talking (walking toward camera 1863 @7.6, walking away 1864 @2.0, feet on sand IMG_1770 @14.3,
  profile/behind IMG_1775/1782), 9:16 crops of the landscape clips (he stands in the left 608px), 0.5x slow-mo via
  `minterpolate=fps=60,setpts=2*PTS`, graded `eq=brightness=-0.10:contrast=1.3:saturation=0.85,vignette=PI/4`.
  The x3 stack sits over three 1080x640 native-scale bands of three different clips of him (IMG_1775/1781/1782, crop y 0/60/0).
  v3: the montage is Maldives-only (Vatsal: "when you're showing the three VATSALs, only B-roll of me"); the hackathon material
  is NOT cut into the debut. What gets appended after DEBUT is reel 34 (the JacHacks promo shot at the Kerala lake), regraded to
  its original colour with a mild beautify pass and the logo cards pinned at y=830 (`card_top`, below the face). Total ~61s.
  Panel bands: 1620x960 windows scaled to 1080x640 so the whole head fits (a 1080x640 native crop clipped his face).
  Bed = demucs no_vocals stem (the mp3 had Kumar's voice under Vatsal's); 0.55 under speech, 1.15 after the drop.
- v4 (final, 52.7s): Vatsal cut everything after the x3 panel ("I'm not even saying anything"): debut = 0-21.22s (panel end),
  hard cut into reel 34. The listening/yellow section and the DEBUT closer are dropped in this build. JacHacks half bed =
  Tyler, The Creator "Gone, Gone / Thank You" from 4:45 (`~/Downloads/05 — Audio/`), volume 0.30 under the voice.
- v5: "dark shadow effect looks chopped near my hands" -> the graded real wall is replaced by a generated **studio backdrop**
  (charcoal (9,7,8) + warm key pool (34,26,24) behind the head, r-falloff^1.6, 1.6-sigma grain) and he is keyed over it with a
  **cleaned matte**: 3-frame temporal average of the u2net alpha, MinFilter(5) choke (kills the bright wall fringe along the
  arms), GaussianBlur(2), levels (0.10..0.90); fg colour darkened 55% below y~1250-1450 so hands/desk sink into the backdrop.
  Hands-band frame-to-frame flicker went 0.54 -> 0.16. Behind-layer words: composite k_ over the backdrop, then key the
  subject back by |pro - backdrop| > 18. Name beat is VATSAL (0.40s) then SHAH.
- v6 (2026-09-06, after a scratchpad wipe -- rebuilt from the shipped mp4s, talking-head frames reused verbatim):
  bed only under b-roll (0.10 under speech, 1.0 for the 3.21-4.10 insert, 1.15 from the drop); bed re-timed with a 1.05s
  lead so its 2.16s hit lands on the insert cut, then 5.76-8.20 repeated -> drop 15.21. Montage = portrait clips only with
  his face in the safe box (1863 walk @7.6 and standing @3.4; 1864 shoreline walk @8/@20/@30 -- mic in hand but face to
  camera); the landscape 1775/1781 9:16 crops clipped his head and are OUT of the montage (they survive only as panel bands).
  JacHacks half: shipped reel 34 to 28.40 ("register now in the link in bio" dropped) + 1864 @38.55 "so be sure to sign up
  and comment JAC to get the link" with JACHACKS / COMMENT JAC in the lower half (his head sits at y~287 in that shot).
  Tyler bed at 0.18. Total 53.2s.
  1864 walk segments put his head above the IG header (he walks close to the lens) -> `push_down(170)`: mirror a 170px band of sky at the top and drop the frame, same trick as the talking head. Verify every slot's first frame with `ig-safe.py view`; a dark-row detector is NOT reliable on sea/shadows.
- v7: bed is DIGITAL SILENCE under speech (volume 0, verified -91 dB on the bed stem; gaps between his words measure
  -45/-63 dBFS in the delivered file), on only for the 3.17-4.12 insert and from 15.14. Montage = side profiles and walking,
  at most one talking-to-camera shot: landscape profile clips (IMG_1775/1781) are shown FULL FRAME letterboxed over a
  blurred, darkened copy of themselves (`split; gblur=40 + eq -0.25 | scale=1080:-2; overlay centred`) so the profile sits
  mid-frame inside the safe box -- the 9:16 crop of those clips clipped his head. Standing-side 1863 @3.4 gets push_down(230).
  zsh trap: `$G[v]` inside a filtergraph string is an ARRAY SUBSCRIPT -- write `${G}[v]`.
- v8 (white rim fix): the u2net matte is fully OPAQUE over a ~30px band of hair-plus-wall (luma ~110, sat ~0.15), so no
  choke short of eating the glasses removes it and edge-extending interior colour smears skin into the hair (tested, worse).
  What works: `bin/studio-key.py` with choke 9, feather 2.5, `extend 26` band, `edge_k 0.65` (band multiplied toward the
  backdrop) and a colour-targeted **despill** in that band (luma>70 and sat<0.26 = wall-tinted, crushed 90%). sat 0.40 /
  edge_k 0.35 killed the rim too but put a grey band on the cheeks and jaw -- skin at the graded edge sits at sat ~0.3. Judge by a 2x zoom of the hair top, not by a rim-pixel count -- the count barely moved while
  the rim visibly vanished.
- v9: Vatsal preferred 9:16 crops over the letterboxed profiles -> `crop=608:1080:x:0` with x chosen per clip by LOOKING at an
  ig-safe sheet of candidate x offsets (1775 x=500, 1781 x=430, 1782 x=0; a dark-column detector picked wrong every time).
  Head above the header -> push_down 300/260; for 1775 the mirrored band showed an upside-down copy of his hair, so that band
  is a blurred stretch of the top 30 rows instead (`push_down_blur`). Closer extended to 4.35s so "link" finishes before the cut.
- v10: black flicker at the hands = the matte opening/closing between his arm and torso against the desk. Fix = `floor` in
  `studio-key.py`: below a y-ramp (1180-1320) the output is the graded ORIGINAL frame, no key at all; hands-band frame-diff
  0.16 -> 0.12 which equals the real motion (original clip 0.51 at 4x the brightness). Two traps: the hard bg grade crushes the
  hands to black (use the gentle fg grade at -0.22 brightness for the floor), and the wall beside the shoulders shows as a grey
  band -> limit the floor fill to a dilated matte (MaxFilter 31 + blur 12); outside it the zone keeps the hard grade (~backdrop).
  Also: 1.5s aura insert after HACKATHONS (Kerala lake wall walk, IMG_4230 @5.2, half speed) via `insert:[335,45]`: voice gets
  1.5s of silence, the bed a 1.5s stretch (concat, NOT acrossfade -- that came out 2s short), captions/hero times +1.5 after 11.16,
  drop moves to 16.72. The Tahoe "hiking with red backpack" clips in aura-new are a FRIEND filmed by Vatsal, not him.
- v11 (final): Tyler bed 0.10 under the JacHacks voice (-36 dB alone; 0.18 was 'still a little loud'); the cut into the
  Maldives closer is a 0.3s `xfade=fade` + `acrossfade` (xfade needs `fps=30` on both inputs after trim or it errors on
  'constant frame rate'). 55.2s. Vatsal signed off.
- v12 audio: Vatsal heard a 'glitch in the voice'. No sample-level clicks anywhere; the one abnormal point was the voice
  resuming hard after the 1.5s insert (spectral flux 4x speech). Voice track is now built with `rubberband=tempo=1.12` (not
  atempo -- atempo smears consonants at 1.1x+), 12ms `acrossfade` at every segment join, 60ms fades either side of the insert
  hole, `loudnorm ... linear=true` (dynamic mode pumps on a 15s clip). Crossfades pull later words ~0.1s earlier than the
  hero-word cues; still inside each word, acceptable. Use this as the default voice chain for cut-up takes.
- v13: the 'glitch only on Instagram' = IG transcode of a MONO 48 kHz master peaking at -0.4 dBFS with edit lists. Fixed by the
  IG export spec now in CLAUDE.md (stereo 44.1k, -2 dBTP/-14 LUFS, level 4.0, 2s GOP, `-use_editlist 0`). Always ship `_IG.mp4`.
