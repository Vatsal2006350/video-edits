# video-edits

**A local, free toolkit for making short-form vertical videos** (Instagram Reels, TikTok, Shorts) with FFmpeg, Python, and a few open-source helpers. Everything runs on your machine. No cloud rendering, and no API keys are needed for the core workflow.

It grew out of one creator's reel factory and has been cleaned up so you can run the same builders on your own footage.

> **In this repo now:** the builder scripts (`bin/`), a local timeline editor, the Instagram export and safe-area checks, the measured format specs (`formats/`), and research notes (`research/`).
> **Not in this repo yet:** the 57-effect overlay library and the Claude skill packs described below. They live in a private working copy. They are listed here so you can see what the full toolkit does. See [Status](#status).

---

## Contents

- [What it does](#what-it-does)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Builders (bin/)](#builders-bin)
- [Overlay effects (57)](#overlay-effects-57)
- [Claude skill packs](#claude-skill-packs)
- [Format specs (formats/)](#format-specs-formats)
- [Repo layout](#repo-layout)
- [Status](#status)
- [Privacy and what stays out of git](#privacy-and-what-stays-out-of-git)

---

## What it does

- **Talking-head reels** with word-accurate captions, a typed serif hook, music ducked under the voice, and cut-safe speech edits.
- **Text-led formats**: "X OR Y" hooks, "N things at N" lists, receipts, glow-ups, before/after diptychs, travel montages, and typewriter openers.
- **Music-led cuts**: detect beats and the drop in a track, then place each cut on the beat.
- **Delivery that passes platform checks**: 1080×1920 at 30 fps, Rec.709 colour (iPhone HLG is tonemapped first), an Instagram safe-area check, and a standard upload encode with loudness normalisation.
- **Review tools**: a contact sheet to see what is in a folder, and a local editor.

---

## Quick start

### 1. Requirements

| Tool | Why | Install (macOS / Linux) |
|---|---|---|
| Bash, Python 3 | scripts | preinstalled on macOS; `apt install python3` on Linux |
| FFmpeg + FFprobe | every render | `brew install ffmpeg` / `apt install ffmpeg` |
| Pillow, NumPy | text and image layers | `python3 -m pip install pillow numpy` |
| `uv` / `uvx` | isolated transcription and media tools | `brew install uv`, or the [uv installer](https://docs.astral.sh/uv/) |
| `jq`, `rg`, Node.js | some workflows | `brew install jq ripgrep node` |

Optional:
- `cloudflared`: only for the Instagram API publisher, which tunnels your local file to Meta.
- `HyperFrames`: for the HTML-rendered motion layers used by some builders.

### 2. Clone and check

```bash
git clone https://github.com/Vatsal2006350/video-edits.git ~/Code/video-edits
cd ~/Code/video-edits
for f in bin/*.sh; do bash -n "$f"; done
python3 -m py_compile bin/*.py && echo "scripts parse"
```

### 3. Put your own media in place

Keep footage, music, and fonts **outside** the repo. Point the tools at them with the environment variables in [Configuration](#configuration).

### 4. Make a reel

```bash
# See what is in a folder of clips before you cut anything
python3 bin/contact-sheet.py ~/Movies/raw-clips

# Check the loudness of a cut
bash bin/check-audio.sh my_cut.mp4

# Build a receipt-style reel from your own manifest
bash bin/receipt-reel2.sh my.manifest out.mp4 10.9

# Make the Instagram upload copy from a master
bash bin/export-ig.sh master.mp4 reel_IG.mp4

# Check the Instagram safe area (text must sit inside it)
python3 bin/ig-safe.py view out.mp4
```

### 5. Open the local editor

```bash
python3 bin/editor/server.py        # http://localhost:8765/
```

The server binds to `127.0.0.1`. It does not publish or upload anything.

---

## Configuration

Set these in your shell profile or in a local `.env` file that you do not commit.

| Variable | Default | Used by |
|---|---|---|
| `VIDEO_EDITS_ROOT` | `~/Code/video-edits` | scripts that refer to the repo or its fonts |
| `DOWNLOADS_DIR` | `~/Downloads` | one-off builders that read from Downloads |
| `IG_USER_ID` | *(none, required)* | Instagram publisher: your professional account ID |
| `IG_ACCOUNT` | `your_handle` | Instagram publisher: account label |
| `IG_KEYCHAIN_ACCOUNT` | `$IG_ACCOUNT` | macOS Keychain entry that holds the token |
| `IG_ACCESS_TOKEN` | read from Keychain | Instagram publisher: long-lived token (never commit it) |
| `IG_KEYCHAIN_SERVICE` | `com.video-edits.instagram-access-token` | Keychain service name |

Publishing to Instagram is optional and always explicit. The publisher defaults to a **manual Trial Reel**, and it publishes a normal Reel only with `--public`.

---

## Builders (bin/)

Each builder is a single command. Run it with no arguments to see its usage, or read the first lines of the script.

### Talking-head and story reels
| Tool | What it does |
|---|---|
| `build-story-reel.sh` | Generic talking-head reel with forced-aligned captions and a typed serif hook. Speech cuts, cutaways, b-roll tail, caption fixes, and ducked music are set by environment variables. |
| `typed-hook.py` | Serif opening hook that types out word by word in sync with the speech. |
| `typewriter.py`, `keystroke-track.py` | Typewriter hook, with an optional keystroke sound track. |
| `kinetic-hook.py` | Kinetic serif hook: words arrive where they are spoken and cascade around the frame. |
| `dynamic-hook.py` | Short phrases that replace each other, with hero words blown up. |
| `hero-type.py` | Stacked light serif or sans hero type that reveals word by word. |
| `title-card.py` | Opening card: serif lead-in, then a big bold line. |
| `make-captions.py` | Builds caption ASS files from force-aligned word timings. |
| `promo-caption.py` | Burned-in captions with logo cards that pop in on cue. |
| `studio-key.py` | Clean key of a matted talking head over a generated backdrop, with no white fringe. |
| `remix-story-audio.sh` | Rebuilds a story reel's soundtrack from a clean voice stem and a music bed. |

### Text-led formats
| Tool | What it does |
|---|---|
| `or-reel.sh` + `fisheye-text.py` | "X OR Y" gold fisheye hook, loading dots, then beat-cut payoffs. |
| `list-reel.sh` + `list-label.py` | "N things I did at N" list, one beat per item. |
| `receipt-reel.sh`, `receipt-reel2.sh` | Meme hook into receipt shots, cut on the track's beats. (`2` is the current version.) |
| `card-reel.sh` | One line of hero type per shot, no talking head. |
| `glowup-reel.sh` | Stills desaturated; colour returns on the drop. |
| `diptych-reel.sh` | Then/now split, top and bottom, cut together. |
| `travel-story-reel.sh`, `travel-reel.sh` | Quiet opening line, then a beat-cut montage. |
| `bounce-reel.sh` | Hard-cut bounce between shots, with one italic caption held across. |
| `beat-reel.sh` | Beat-synced cuts with a caption and a transition. |
| `alternating-reaction-reel.sh` | Reaction meme: a vertical reaction clip beside a horizontal product shot. |
| `glow-text.py` | Bold caption with a coloured outer glow. |
| `greyscale-drop.sh` | Greyscale clip that snaps to colour on a drop. |
| `make-card.py` | Floating rounded card for a photo or screenshot on a transparent 1080×1920 canvas. |
| `embed-behind.sh`, `embed-behind-seq.sh` | Puts a text PNG or PNG sequence behind the subject, using a matte. |
| `cta-overlay.sh` | Three-line call-to-action overlay, with an optional scrim. |
| `timeline-reel.py` | Builds a reel from a JSON spec where every cut sits on an exact timestamp. |
| `make-aura.py` | "Disappeared" reel: hook, drop, then achievement cards. |

### Music and timing
| Tool | What it does |
|---|---|
| `beats.py` | Detects beat times with spectral-flux onsets. |
| `music-map.py` | Profiles a track: beats, energy envelope, and where the drop is. |
| `audio-map.py` | Reports structure: RMS envelope, the drop, and the beats after it. |
| `pick_cuts.py` | Chooses n+1 beat boundaries at least 1.6 s apart for n scenes. |
| `safe-cuts.py` | Shows where you can cut without clipping speech. |
| `trend-remix.sh` | Retimes an existing vertical edit so its main transition lands on a beat. |
| `ig-audio.py` | Extracts MP3 reference tracks from public Instagram Reel URLs. |

### Analysis and media review
| Tool | What it does |
|---|---|
| `contact-sheet.py` | Contact sheet of a folder of clips or stills, so you can see what is in them before editing. |
| `scan-stability.py` | Finds the steadiest window of a given length in each clip. |
| `group-shoots.py` | Clusters clips into shoots by date and visual similarity. |
| `find-clip.sh` | Finds a talking-head clip by what is said in it. |
| `transcribe-clips.py` | Word-level transcripts for cut safety. |
| `watch-transcribe.sh` | Watches a folder and transcribes new clips as they arrive. |
| `force-align.py` | Forced alignment of Whisper output against the audio. |
| `color-normalize.sh` | Rec.709 handling: tonemaps iPhone HLG/PQ before any grade. |
| `refine-matte.sh` | Refines a matte for a project between two timestamps. |
| `check-audio.sh` | Integrated LUFS and per-segment mean volume. |

### Delivery and QA
| Tool | What it does |
|---|---|
| `export-ig.sh` | Instagram upload copy: stereo 44.1 kHz AAC, loudness normalised, CFR 30 fps, faststart, Rec.709 tagged. |
| `ig-safe.py` | Instagram safe-area viewer and checker. Text must sit inside the safe box. |
| `validate-instagram-reel.sh` | Checks a reel folder: dimensions, codec, audio, duration, caption length. |
| `story-qa.py` | Mechanical QA for `build-story-reel.sh` specs, run before rendering. |

### Publishing (optional)
| Tool | What it does |
|---|---|
| `instagram-api-publish.sh` | Publishes a validated reel folder through the Instagram Graph API. Defaults to a manual Trial Reel. Needs `IG_USER_ID` and a token. |
| `comment-dm/` | A small dashboard and webhook service for keyword-triggered private replies on a published Reel. Needs a Meta app and a public HTTPS endpoint. See `bin/comment-dm/README.md`. |

### Generative helpers (optional, paid APIs)
| Tool | What it does |
|---|---|
| `gen-sora.sh` | Text or image to video with an OpenAI video model. Needs your own API key. |
| `gen-veo.mjs` | Text or image to video with a Google Veo model. Needs your own API key. |

Generative tools never run implicitly. You have to call them.

### macOS-only tools
| Tool | What it does |
|---|---|
| `photos-fetch.sh`, `fetch-from-photos.sh` | Pulls clips from the Photos library. Run from Terminal.app, because macOS privacy rules block Photos access from other shells. |
| `get-purple.sh`, `get-dm-and-purple.sh` | Screen-recording helpers that must run in Terminal.app. |

### One-off builders (worked examples)
These were written for specific reels. Read them as examples of how the builders combine, not as general tools.

`birthday-trial-loop.py`, `prepare-birthday-batch3.sh`, `prepare-birthday-media.sh`, `build-amplify.sh`, `build-t20-reel.sh`, `exams-overlays.sh`, `fetch-kerala-missing.sh`, `whimsy-year-off-recut.sh`, `wishes-yc-reel.sh`, `yc-diverse-reel.sh`, `yc-drop-reel.sh`, `yc-shirt-transition.sh`, `yc-trend-variant.sh`, `new-reel.sh`.

---

## Overlay effects (57)

These are overlay animations that sit on a talking head. Each layer is rendered and then composited on top of the picture. They are part of the full toolkit and **are not yet in this public repo** (see [Status](#status)).

<details>
<summary><b>Show all 57 effects</b></summary>

| # | Effect | What it does |
|---|---|---|
| 1 | `noise` | reels pile up behind your head, one every quarter second |
| 2 | `lineup` | numbered tiles fan out in an arc above your head |
| 3 | `locked-on` | corner brackets snap onto your face and the camera follows you |
| 4 | `orbit` | your reels circle your head: in front at the bottom, behind at the top |
| 5 | `lean-in` | a fast punch-in on one word |
| 6 | `backdrop-word` | a giant word drops in behind you |
| 7 | `spotlight` | kill the lights, keep you lit |
| 8 | `the-bill` | prints every instruction like a ticket into the wall above your head |
| 9 | `moody` | a moody colour grade: darker, softer, teal shadows |
| 10 | `swipe` | a before-and-after slider that sweeps across you |
| 11 | `todo` | a checklist card beside your head that ticks off as you talk |
| 12 | `tap` | a Follow button pops up and flips to Following |
| 13 | `pause-point` | freeze the frame and point at something with a hand-drawn arrow |
| 14 | `uninstall` | a glitchy uninstall bar that breaks the frame apart |
| 15 | `reel-frame` | your video shrinks into an Instagram reel card |
| 16 | `shortcut-rain` | keyboard keys rain down behind you |
| 17 | `reject-stamp` | a big red stamp slams onto the screen |
| 18 | `countdown-flip` | a 3-2-1 flip clock above your head |
| 19 | `rabbit-hole` | the frame tunnels into itself, spinning |
| 20 | `cover-star` | you become a magazine cover, with the title behind your head |
| 21 | `scribble` | marker doodles draw themselves around you |
| 22 | `red-collage` | black-and-white you, a giant red word behind, kinetic type stacked beside you |
| 23 | `split-headline` | a clean headline card slides down and pushes you into the bottom of the frame |
| 24 | `pastel-word` | a soft lavender backdrop, a giant word behind you, and a profile card |
| 25 | `check-pills` | grid-paper room, your reels pinned behind you, blue pills get clicked |
| 26 | `headline-box` | a punch-in with a clean two-line headline, the second line in a white box |
| 27 | `profile-wall` | your profile grid fills the wall behind you while a counter ticks up |
| 28 | `tier-list` | a tier list drops in front of you and lands in S tier |
| 29 | `broll-split` | split screen: b-roll on top with a price-tag sticker, you on the bottom |
| 30 | `phone-fan` | your reels fan out like a hand of phones under a two-line headline |
| 31 | `dot-reveal` | your shot builds itself out of glowing dots, then snaps into the full picture |
| 32 | `headline-wall` | a wall of headlines piles up behind your head, then a total pops in front |
| 33 | `checklist` | a task list builds under your chin: each step spins, then ticks green |
| 34 | `glass-widgets` | frosted-glass phone widgets float around your head |
| 35 | `timeline` | a dark red cinematic grade with an editing timeline, REC timecode, and playhead |
| 36 | `comment-box` | an Instagram comments sheet types your word, posts it, gets a heart and a reply |
| 37 | `liquid-glass-graph` | a liquid-glass card under your chin while a graph climbs and the number counts up |
| 38 | `carousel-spin` | your reels spin around you in a 3D carousel, then slow to a stop |
| 39 | `match-cut` | news pages cut on one word, locked in place behind your head |
| 40 | `apple-toggles` | an iPhone settings card under your chin flips its switches, one line at a time |
| 41 | `led-sign` | the lights drop and a glowing LED sign types itself out behind you |
| 42 | `slow-push` | a slow cinematic push-in from the wide shot to your face |
| 43 | `over-the-shoulder-zoom` | the camera pushes into one corner, a liquid-glass graph pops beside your head, then the other corner |
| 44 | `messages` | iMessage notifications pop in one after another, stacking above the bottom of the frame |
| 45 | `place-in-grid` | you shrink into the centre tile of a 3×3 profile grid, then reels pop in around you |
| 46 | `tape-label` | a strip of yellow tape with your line lands on your chest |
| 47 | `select-resize` | a blue selection box grabs your number and a cursor drags it bigger |
| 48 | `wave-trim` | the silent parts of your voice are trimmed away on screen until only your words remain |
| 49 | `huge-strike` | one huge serif word fills the wall behind you, then a red line crosses it out |
| 50 | `crayon-write` | a red crayon writes your word behind your head, then underlines it |
| 51 | `fan-build` | cover cards deal into a fan behind your head, one at a time |
| 52 | `spotify-scroll` | a tilted Spotify-style list scrolls behind you, the active row glows |
| 53 | `tech-widgets` | an iOS calendar widget and a black reel-views widget pop in above your head |
| 54 | `glass-tunnel` | reel cards fly outward past you like a tunnel, behind your head |
| 55 | `notes-app` | an Apple Notes card types a checklist and ticks it off |
| 56 | `story-portal` | an orange dot portal, then your clip lands inside an Instagram feed |
| 57 | `yap-headline` | a bubbly pink headline pops in letter by letter with sticker stars |

</details>

Each effect has a `--check` mode that renders a stills sheet, so you can look at it before a full render.

---

## Claude skill packs

If you use [Claude Code](https://claude.com/claude-code), the private workspace also carries a set of skills (house rules and step-by-step workflows) that call the builders above. They are **not in this repo yet**.

**Reel workflow skills**
- `reel-effects`: the 57-effect library above, with a stills check before each render
- `claude-edit-reel`: forest-green and cream explainer reel with Claude UI cards
- `talking-head-recut`, `reel-audio-sync` (music-led cuts), `embedded-captions`, `captions-overlay`, `video-sound` (audio clean-up and ducking)
- `vatsal-motion-effects`: house rules for restraint and typography in motion work (rename it for your own fork)

**Motion and layout skills**
- `behind-my-head`, `title-orbit`, `ribbon-wrap`, `liquid-glass`, `depth-ui`, `shatter`, `portal`, `vertigo`, `zoom-through`, `tile-tunnel`, `grid-dive`, `cube-spin`, `frame-break`, `head-pop-out`, `magnifying-lens`, `pull-back-reveal`, `screen-in-screen`, `phone-fan`, `spotlight`, `infinite-zoom`, `oversized-cursor`, `word-highlight`, `zoom-cut`, `cut-the-curve`, `seam-craft`

**Explainer and content-type skills**
- `opening-hook`, `call-to-action`, `call-clips`, `explainer-video`, `faceless-explainer`, `product-demo`, `product-launch-video`, `news-reaction`, `tier-list`, `stripe-style`, `apple-style`, `animated-numbers`, `big-idea-video`, `changelog-video`, `slideshow`, `clone-room`, `every-format`, `toolkit-video`, `video-intake`, `video-check`, `brand-setup`, `music-to-video`, `pr-to-video`

**Motion-graphics frameworks**
- `hyperframes` and its sub-skills (`-animation`, `-audio`, `-cli`, `-core`, `-creative`, `-keyframes`, `-registry`), `motion-graphics`, `motion-doctrine`, `remotion-to-hyperframes`, `media-use`, `general-video`

**Third-party packs (credit and licence)**
- Effects from **Vibha's `claude-video-effects`** (51 effects), and the skills from **Charlie Hills' `reel-editing-skills`** (MIT, © 2026 Charlie Hills). They are vendored outside this repo, and this repo's house rules take priority over them. Keep the upstream licence notices if you redistribute them.

---

## Format specs (formats/)

Each file is a measured format: the numbers, timings, and rules that made it work. They are the best place to start if you want a look that already works.

| File | Format |
|---|---|
| `alternating-reaction-meme.md` | reaction meme |
| `cinematic-hero-type.md` | stacked light serif/sans hero type |
| `daily-routine-bounce.md` | hard-cut bounce with one caption |
| `food-reel-format.md` | food reel with a verdict beat |
| `footage-folder-names-lie.md` | why you check footage by eye, not by folder name |
| `glowup-reel-format.md` | glow-up transformation |
| `ig-safe-area.md` | the Instagram safe box and text width rules |
| `kumar-method-reel-format.md` | flat serif, fixed cap height, echo stack, hard cuts |
| `list-reel-format.md` | "N things at N" list |
| `or-choice-reel-format.md` | "X OR Y" fisheye hook |
| `promo-reel-format.md` | kinetic hero words, running captions, logo cards |
| `receipt-reel-format.md` | receipt reel |
| `reel-font-repo.md` | font presets and the gold-glow look |
| `reel-typography-standard.md` | the house type standard across reels |
| `story-reel-qa.md` | QA layers for talking-head specs |
| `typed-serif-hook.md` | serif hook that types word by word |
| `typewriter-hook-format.md` | typewriter opener |
| `zoompan-squashes-stills.md` | why `zoompan` stretches stills, and what to use instead |
| `_old-CLAUDE-finishing-pipeline.md` | older finishing pipeline (kept for reference) |

---

## Repo layout

```
bin/            builders, analysers, QA and delivery tools
bin/editor/     local timeline editor (server.py, editor.html, compositor.js)
bin/comment-dm/ optional comment-to-DM dashboard and webhook service
formats/        measured format specs
research/       dated research notes (trends, production, audio)
analytics/      performance-logging template and a trend simulation
fonts/          font setup notes (font files are not included)
CLAUDE.md       production contract for AI agents working in this repo
TOOLS.md        tool selection notes
HOUSE-STYLE.md  house style rules
VIRAL-FORMAT.md format notes
```

---

## Status

| Part | In this repo | Notes |
|---|---|---|
| Builders (`bin/`) | yes | some are one-off examples; see above |
| Local editor | yes | `bin/editor/server.py` |
| Instagram export and safe-area checks | yes | `export-ig.sh`, `ig-safe.py`, `validate-instagram-reel.sh` |
| Format specs and research | yes | `formats/`, `research/` |
| 57-effect overlay library (`fx-extra`) | **no** | in a private workspace; planned |
| Claude skill packs | **no** | local to the author's machine; planned |
| Reel library server | **no** | planned |
| Licence | **not yet chosen** | do not reuse the code until a licence file is added |

---

## Privacy and what stays out of git

The repo is built to keep private material out of version control. `.gitignore` excludes raw footage, exports, rendered media, the `.work/` cache, font and music files, account analytics, and credentials.

Rules for contributors and for your own fork:
- Never commit `.env` files, API keys, or tokens. Read them from the environment or the macOS Keychain.
- Never commit footage, rendered video, or licensed music. Keep them in your own folders and point the tools at them.
- Never hard-code account IDs, handles, or home-directory paths. Use the variables in [Configuration](#configuration).
- Generated and paid AI media is optional, and it runs only when you call it.
