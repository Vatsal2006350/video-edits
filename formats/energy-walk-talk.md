# Energy pass: walk-and-talk sound design + whips + punches (2026-11-09)

Reference: GP Multimedia, instagram.com/reel/DdHguJfhYSU (27 s real-estate walk-and-talk). Downloaded, stem-split with
Demucs (`uvx --python 3.11 --from demucs ... -d cpu --two-stems vocals`), every event in the music+SFX stem measured.

## What makes it feel energetic (measured)
- **~90 sound events in 27 s (3.3/s)** on top of a 172 BPM (86 half-time) beat with hats on every off-beat.
- **Pops/ticks**: ~50 ms, centroid 3.5-4 kHz, one on every word or graphic that appears; tick trains under counters.
- **Whooshes**: 0.3-0.7 s swells that PEAK ON the cut, centroid 4-5 kHz, panned L->R, then a low thump on the landing
  (whips at 4.6 / 10.1 / 18.1 / 20.9 s, i.e. only on location changes, not every jump cut).
- **Sub booms**: sub share 0.4-0.6, ~0.7 s decay, only on the 2 biggest slams ("ALL", the phone-number card).
- **Mix**: music+SFX only ~3 dB under the voice (loud). The creator prefers a quiet bed, so keep the BED low and let the
  SFX carry the energy instead.
- **Visuals every 0.5-2 s**: giant 3D words behind the subject on key words (we have `kinetic-hook.py`), time-of-day swap
  of the same shot on "all day", whip-blur transitions, proof cards with a ticking view counter + flying hearts, logo slam,
  B&W flash on one word, neon icons around the head, glass pill chips, phone-call card, one-word white captions.

## The tools (repeatable)
1. `python3 bin/sfx-kit.py` -> `sfx/energy/*.wav` (17 sounds, all synthesized = no licences):
   pop / pop_hi / pop_lo, click_ui, tick1-3, whoosh_short / whoosh / whoosh_long, whip, swipe_up, impact_punch,
   impact_sub, riser, heart_pop, ding. `kit.json` stores each sound's measured duration / peak time / centroid.
2. `python3 bin/sfx-auto.py spec.json sfx.wav [--words aligned.json]` -> one SFX stem + `sfx_cues.json`.
   Spec keys: `cuts whips pops hero_words slams ticks hearts risers dings extra`. Whooshes/whips/risers are placed
   so their PEAK lands on the time you give; pops never closer than 0.12 s; default levels are tuned (measured on the
   demo) to sit: pops ~8 dB under the voice, transitions ~5-7 dB under, sub hits ~3 dB under.
3. `python3 bin/energy-pass.py in.mp4 out.mp4 --whips t,t --punches t,t [--bw start:dur] [--audio mix.wav]`
   on a finished 1080x1920 master: 0.10 s slide-out + 0.12 s slide-in with horizontal motion blur at each whip,
   1.10x snap zoom easing back over ~0.35 s at each punch, optional B&W flash. Base zoom 1.04 keeps edges hidden.
4. Mix the SFX stem as its own input next to voice + bed (no ducking on SFX), then `bin/export-ig.sh` as always.

## Rules
- Whips only where the LOCATION or SECTION changes (3-4 per 30 s). Plain jump cuts get `cuts` (soft whoosh) or nothing.
- One pop per thing that appears on screen; hero words from the transcript via `hero_words`.
- Sub booms max 2 per reel. Risers end exactly on a whip or payoff.
- Always frame-check the delivered file at a whip time before sending (see memory: verify-export-is-new-build).

Demo: `videos/claude-edit-english/energy_demo.py` -> `~/Downloads/reel-batch/claude-edit-english/02_claude_edited_200_reels_energy_v2*.mp4`.
