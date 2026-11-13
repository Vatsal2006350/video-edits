# Start here: what kind of video is it?

The first job of any agent working in this repo is to find out which kind of video the person wants. The kinds below are built differently. A talking-head edit is about cuts, captions and timing. A motion-design piece has no footage at all: one continuous camera, shapes that morph instead of cutting, and easing that never stops. Mixing up the two is the most common reason an edit feels wrong.

**Ask before you build.** If the brief does not already say which kind it is, ask one question with these options, then the follow-ups for that kind. Do not guess.

> Which kind of video is this?
> 1. Talking-head edit (you speak to camera)
> 2. Motion design (no footage: animated UI, shapes, type, data)
> 3. Hybrid (talking head with motion-design inserts)
> 4. Footage montage (travel, food, event, cut to music)
> 5. Faceless clip (podcast, news card, quote)

## 1. Talking-head edit

Cuts, captions, a hook and a few effects on top of real speech.

- **Ask:** the clip(s), the hook line, the language, any numbers that may go on screen (and where they come from).
- **Build with:** `bin/build-story-reel.sh`, `bin/make-captions.py`, the effect library (`bin/fx-extra.sh list`, 70 effects), `bin/run-visual-effect.sh` for the heavier ones.
- **Feels right when:** speech flows, captions sit in the safe box, effects land on words, not on silence.
- **Formats:** `formats/typed-serif-hook.md`, `formats/forest-cream-editorial.md`, `formats/energy-walk-talk.md`.

## 2. Motion design

Pure animation rendered from HTML. This is the look of the best "Claude made this video" posts: one line that becomes type, a curve, a shape, a honeycomb, a cube, a gear, a dashboard, a wave of light, without a single cut.

- **Ask:** the subject, the exact words for the screen (hero word first), which numbers are cleared to show, and optionally a track, brand files or footage. The brief generator measures the rest and lists what is still unknown.
- **Build with:** `bin/motion-brief.py` writes the full brief from your words (taste pack, beat map, words on bars); the film is built on `motion/engine/mg.js` in `motion/<name>/`, rendered by `bin/motion-reel.sh`, scored by `bin/motion-score.py`, gated by `hx.py motion check`. Start from `motion/one-line/`. The skill `motion-director` walks the whole flow.
- **Feels right when:** one element carries the eye the whole way, every move eases in and out, the camera drifts and never jumps, and the piece ends where it can loop.
- **Format:** `formats/motion-design.md` (the rules and numbers).

## 3. Hybrid

A talking head that hands off to motion-design moments: a card that explains the claim, a chart that builds as the number is said, a UI that types the prompt.

- **Ask:** the clip, and which sentences get a motion insert (usually two or three).
- **Build with:** the talking-head tools for the base, a HyperFrames comp per insert, timed to the word from the transcript, composited with `bin/composite-layers.py`.
- **Formats:** `formats/concept-explainer-overlay.md`, `formats/cover-orbit-claude-ui.md`.

## 4. Footage montage

Music-led cuts over travel, food or event footage.

- **Ask:** the folder of clips, the track, the payoff shot, the caption.
- **Build with:** `bin/music-map.py` (find the drop), `bin/beat-reel.sh`, `bin/travel-story-reel.sh`, `bin/list-reel.sh`.
- **Feels right when:** the payoff cut lands on the drop.

## 5. Faceless clip

No creator on camera: a podcast moment, a news card or a quote.

- **Ask:** the source and its link, the exact quote, the speaker's name.
- **Build with:** `bin/podcast-clip.sh`, `bin/pager-reel.py`.
- **Feels right when:** every claim is sourced, and the speaker is credited.

## Then, for every kind

1. Pick a look: `bin/reel-pick suggest "<brief>"` for a shortlist, or `bin/reel-pick` for the visual picker (http://localhost:8771).
2. Build, then check the safe area: `python3 bin/ig-safe.py view out.mp4`.
3. Export the upload copy: `bash bin/export-ig.sh master.mp4 name_IG.mp4`.
