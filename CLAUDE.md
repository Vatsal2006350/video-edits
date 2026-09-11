# video-edits — Vatsal's local reel factory

Read this, then `TOOLS.md` (what every tool does), `FOOTAGE.md` (what every clip
actually contains — folder names lie), and `formats/` (one file per proven reel
format with the measured numbers). `research/` holds dated trend/strategy briefs (agent research, cited). Everything is local and free: ffmpeg,
PIL/numpy, mlx-whisper via `uvx`, hyperframes for mattes. No API keys needed.

## Two modes
1. **Build from raw** (the current mode). Vatsal drops raw clips / a reference IG
   reel / a track; you cut, time, grade, type and deliver. Builders live in `bin/`,
   the master batch is `batch/build-all.sh`, output goes to
   `~/Downloads/reel-batch/<theme>/` with a `phone/` mirror (608x1080).
2. **Finish a CapCut edit** (older mode, hyperframes captions/hero): see
   `formats/_old-CLAUDE-finishing-pipeline.md` + `HOUSE-STYLE.md`. In that mode
   never re-cut or remix his audio.

## Non-negotiable rules (each one cost a rebuild)
- Frame 1080x1920 @30. IG safe box **x 59–918, y 278–1536**. Centred text is
  bounded by **724px** (2×(918−540)), not the box width. Verify on the rendered
  layer PNGs (alpha bbox), never by eyeballing a composite. `bin/ig-safe.py view`
  on every deliverable.
- iPhone "HDR video" clips are HLG 10-bit (`color_transfer=arib-std-b67`): tonemap to Rec.709 BEFORE any grade or the
  picture stays flat (`build-story-reel.sh` does it with TONEMAP=auto). For standalone work use `bin/color-normalize.sh raw`; use its explicit `retag` mode only when pixels are already tonemapped and merely carry the wrong tag.
- Stills: `lib-still.sh` (`still_vf` letterbox / `still_cover_vf` / `still_black_vf`).
  Never `scale:-1,zoompan s=` — it stretches.
- Never write a caption you cannot verify from his footage or words (no invented
  ages, heights, counts). Ask or use a neutral line.
- Music from `~/Downloads/music-good/` (his tracks; README has drop times), never
  the stock library. The payoff cut lands ON the drop; `bin/music-map.py` finds it.
- Reference reels: `uvx yt-dlp <url>` is the only fetch that works. Then
  `contact-sheet.py`, transcribe, and MEASURE the type with strict-colour pixel
  bboxes (width + side-by-side; height gets contaminated by hair/skin).
- Logos: `logos/` only, transparent, `*_w.png` for white wordmarks. Photos in
  cards get a soft halo, never a white plate.
- Whisper mishears proper nouns (JacHacks, UMich, Vatsal) and hallucinates after
  the audio ends — fix `aligned.json` by hand before rendering captions.
- macOS/zsh: no `timeout`, unquoted `$var` does not word-split (use arrays),
  APFS is case-insensitive. `~/.cache/uv/archive-v0` grows unbounded — prune it
  when disk is tight, but never while a `uvx` tool is running.

## Typographic systems that exist as tools (pick, don't reinvent)
| look | tool | format file |
|---|---|---|
| Mumbai promo: Anton kinetic hero words behind the body, UMich blue/yellow, running Anton captions, logo cards | `kinetic-hook.py` + `promo-caption.py` | `formats/promo-reel-format.md` |
| Kumar / chess-kid: flat red DM Serif, fixed cap height, X-compressed to ~90%, ×3 echo stack, hard cuts, 3-panel insert, two-layer grade | `kinetic-hook.py` (`cap_h squash_to echo from:cut`) | `formats/kumar-method-reel-format.md` |
| Typewriter opener: Instrument Serif 103, 24 cps into a pre-centred line, hold, 0.13s fade, optional keystroke SFX | `typewriter.py` + `keystroke-track.py` | `formats/typewriter-hook-format.md` |
| "X OR Y" gold fisheye hook | `fisheye-text.py` via `or-reel.sh` | `formats/or-choice-reel-format.md` |
| "N things at N" list stickers | `list-reel.sh` + `list-label.py` | `formats/list-reel-format.md` |
| Stacked light serif/Helvetica hero behind subject | `hero-type.py` | `formats/cinematic-hero-type.md` |
| Word-by-word typed DM Serif hook on talking head | `typed-hook.py` via `build-story-reel.sh` | `formats/typed-serif-hook.md` |
| Glow/bloom text | `glow-text.py` | `formats/reel-font-repo.md` |
| Receipt / glow-up / diptych / card / travel-story | `receipt-reel.sh glowup-reel.sh diptych-reel.sh card-reel.sh travel-story-reel.sh` | `formats/*.md`, `VIRAL-FORMAT.md` |
| Daily-routine bounce: typing open, then guitar/keyboard hard cuts, one italic caption | `bounce-reel.sh` | `formats/daily-routine-bounce.md` |

## Workflow for "make me a reel like <reference>"
1. `uvx yt-dlp` the reference → `bin/contact-sheet.py` → `uvx mlx-whisper` → measure type.
2. Pick footage from `FOOTAGE.md` (verified seeks). Unknown folder → contact sheet first.
3. Write a spec JSON, render layers (`k_/f_/t_` PNG sequences), check alpha bboxes.
4. Composite (ffmpeg overlay, or PIL when a matte is involved), mix audio.
   For a stem-based remix or a quiet opening, use `bin/remix-story-audio.sh`; keep the music audible from frame one and let its side-chain ducking protect the voice.
5. `ig-safe.py view` + phone mirror → `SendUserFile` the phone mp4 with the view sheet.
6. If it is a new look, make it a tool in `bin/`, add a row above, add `formats/<name>.md`
   with the measured numbers, and a line in `TOOLS.md`. That is the product.

## Deliverables
Two exports per reel, always:
- Master (archive): 1080x1920 30fps, libx264 crf 15 preset slow profile high, yuv420p, AAC 256k, faststart.
- **Instagram upload copy** (`*_IG.mp4`): stereo 44.1 kHz AAC 160k, `loudnorm I=-14:TP=-2:linear=true` + `alimiter
  0.79`, 30fps CFR, High 4.0, `-g 60 -keyint_min 60 -sc_threshold 0`, ~8 Mbps (`-b:v 8000k -maxrate 9000k -bufsize 18000k`),
  `-movflags +faststart+negative_cts_offsets -use_editlist 0`. A mono/48k/-0.4 dBFS master played fine locally but
  glitched after IG's transcode (reel 36, 2026-09-06). Verify: ebur128 peak <= -1.9, channels=2, sample_rate=44100,
  `ffprobe -v trace | grep -c elst` == 0.
  Create it with `bin/export-ig.sh <master.mp4> <name_IG.mp4>`; do not hand-roll the export. The tool also stamps Rec.709 metadata so an iPhone HLG tag cannot survive after tonemapping.
The `phone/` copy (608x1080 crf 26) is only for previewing in chat; never hand that one over as final.
`~/Downloads/reel-batch/README.md` lists every reel and what it is. Number files
`NN_slug.mp4`; keep the phone mirror in sync. Nothing here is committed
automatically — commit when Vatsal asks.
