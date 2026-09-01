# Reel pipeline workspace

Repeatable, fully-local (free) AI reel finishing for Vatsal's videos. No cloud,
no API keys: mlx-whisper transcription, CoreML ONNX matte, Chromium render.

## Division of labor — read this first
Vatsal does the **raw edit** (scene cuts, sequencing, screenshots, audio mix,
usually in CapCut). This pipeline does ONLY the finishing layer:
**overlays, hero typography, captions, animations, transitions, CTA.**
- NEVER re-cut, re-time, re-grade, or remix his footage/audio.
- Audio: verify with bin/check-audio.sh and REPORT problems; don't fix.
- If footage has a problem (clipped last word, loudness jump), tell him —
  he re-exports; you re-apply (cheap: authoring carries over).

## Layout
- `bin/` — driver scripts (see below)
- `fonts/` — Anton (hero), Montserrat (captions)
- `.agents/skills/` — hyperframes skill packs. PATCHED: make-theme.cjs has a
  `lastOut` cap (final caption line vs trailing outro). Keep patches here;
  re-check after `hyperframes skills update`.
- `HOUSE-STYLE.md` — the validated look. Follow it.
- `<NNNN>/` — one folder per reel (e.g. 0820). 0820 is the reference project:
  its theme.json is the canonical example of the house style.
- Engine: `~/Downloads/hyperframes` (HYPERFRAMES_ROOT; built with bun).

## Workflow for a new video
1. `bin/new-reel.sh <name> <raw.mov>` — normalize + probes + matte/transcribe/
   safe-zones. (~5 min for 45s of video; matte dominates.)
2. Review `sheet.png`, `scene-cuts.txt`, `transcript.json` (fix misheard
   names — Whisper writes "Butso" for "Vatsal"), `safe-zones.json`.
3. Author `theme.json` per HOUSE-STYLE.md (copy 0820/theme.json as base).
4. `node .agents/skills/embedded-captions/scripts/make-theme.cjs <project>`
5. Preview + QA per HOUSE-STYLE.md — including the head-edge zoom check;
   run `bin/refine-matte.sh` if the subject is small (wide shot).
6. `bash .agents/skills/embedded-captions/scripts/render-theme.sh <project>`
7. CTA if wanted: `bin/cta-overlay.sh final_fx.mp4 FINAL_reel.mp4 <t> ...`
8. `bin/check-audio.sh FINAL_reel.mp4 <segments around each cut>` + spot-check
   frames, then deliver FINAL_reel.mp4 via SendUserFile.

## Hard-won gotchas (cost hours; don't rediscover)
- Wide shots: segmentation runs at 320x320 — a distant head is ~18px to the
  model and mattes as a blurry blob. bin/refine-matte.sh (crop→4x→re-matte)
  is the fix; sharpening the low-res alpha is NOT (crisp blob still a blob).
- Changing source video: if frames identical (re-export), all authoring
  carries over; but a re-export may be REMIXED (different loudness) — then
  the new file must become the single source; never splice audio across mixes.
- frames_fg/bg are per-source: `rm -rf frames_bg frames_fg matte.fps` when
  source.mp4 changes duration, else matte.cjs skips ("already complete").
- Hero must exit before burned-in screenshots; scan dark-pixel fraction to
  find their onset precisely (see 0820 session; ~0.05s resolution).
- github.com git clone can die (early EOF) on this network — use codeload
  tarballs: `curl codeload.github.com/<org>/<repo>/tar.gz/refs/heads/main`.

## AI shot generation (Kerala reel workflow)
Generate NEW scenes featuring Vatsal (identity-locked) to intercut with real footage:
Real prices (ai.google.dev/gemini-api/docs/pricing, 2026-08-22): veo-3.1-lite
$0.05/s, veo-3.1-fast $0.10/s @720p ($0.12 @1080p), veo-3.1 $0.40/s, sora-2
$0.10/s. (amplify's lib/video/cost.ts says 2.5c/s — that is 4x LOW, do not trust.)
Cheapest identity-capable routes, best first:
1. UNTESTED ~$0.45/8s: gemini flash image edit (~$0.04) + veo-3.1-lite i2v
   ($0.40) — docs conflict on whether lite takes an input image; test costs $0
   if it 400s. Needs valid GEMINI_API_KEY (INVALID as of 2026-08-21).
2. $0.80/8s: `bin/gen-veo.mjs` — veo-3.1-fast, his reference photos native, no
   image step. Same key blocker. Use GA model id veo-3.1-fast-generate-001
   (the -preview ids retire 2026-04-02… already past; verify on first run).
3. $1.05/8s WORKS NOW: gpt-image-2 edit ($0.25 high / $0.06 medium) →
   `bin/gen-sora.sh` sora-2 ($0.80). Uses amplify OPENAI_API_KEY.
- Identity recipe: back-facing shots only (no face drift), the cream Goku/kanji
  tee is the anchor — always name "same cream oversized t-shirt with orange-and-black
  anime print, same dark wavy hair" in prompts. Crop refs to content band first
  (his phone exports are letterboxed: content rows ~875-1684 of 2560).
- His real Kerala shots: lake, boat shore, misty hills (Munnar area). Generated
  spots to use: Alleppey backwaters (done, sample), Athirappilly falls, Varkala
  cliffs, Fort Kochi fishing nets, Munnar tea gardens.
- Cost-minimized Sora recipe (validated): still at quality=medium ($0.06, high
  adds nothing at 720p) + sora-2 4s ($0.40) = ~$0.46/shot. Prompt stills for
  "MEDIUM SHOT from mid-thigh up, camera close behind" — matches his real
  framing and avoids post-zoom. Post-zoom trick (free, for wide gens): 2.1x
  center crop + lanczos + light unsharp, e.g. crop=608:342:336:93 on 1280x720.
  Medium stills can drift the shirt print — spot-check; redo at high if wrong.

## Receipt-reel mass production (see VIRAL-FORMAT.md)
The proven viral template: bin/receipt-reel.sh + manifest. Keep output
silent; audio is attached in the IG composer ("Wishes" segment = 10.912s).
