# House style — Vatsal's reels

The exact recipe validated on 0820 (the "Hi, I'm Vatsal" reel). Reuse verbatim
unless the clip demands otherwise; deviations should be deliberate, not drift.

## Identity
- embedded-captions **`anchor` theme** (quiet rail default + one earned hero).
- 1080x1920 @ 30fps pipeline resolution. Source normalized by `bin/new-reel.sh`.

## Hero (the movie-title moment, e.g. "HI, I'M VATSAL")
- Font: **Anton**, yellow `#FFD24A`, dark soft shadow, underline draws in,
  slow ~1.8% loom during hold, room dims ~16% while up.
- Composited **behind the subject** (matte occlusion) — this is the signature.
- Position: centered around the subject's eye-line. **Keep the glyph shapes
  readable**: subject's head should clip only the *bottom third* of letters.
  Compute head bbox from frames_fg, put hero baseline slightly above head top
  (0820: head top y=1011 → hero y=1028).
- **Exit before any burned-in screenshots/graphics appear** in the footage
  (`exitAt` in theme.json). Never let the hero co-exist with screen recordings.
- Scarcity: ONE hero per reel unless a long multi-section video.

## Captions (rail)
- Font: **Montserrat ExtraBold** (fonts/Montserrat.ttf), ~48px, ALL CAPS,
  white with dark stroke + shadow, bottom at ~86.5% height.
- Per-word pop-in: back.out(2.2) from scale 0.5. Emphasized words land 1.45x
  in yellow `#FFD24A`, settle to 1.14x.
- Rail hides while a hero/backdrop word is up.
- `lastOut` in theme.json caps the final caption at the outro cut.

## Outro CTA
- `bin/cta-overlay.sh` — Anton 86px, staggered rise+fade (0.3s apart),
  centered, lines at y 1400/1518/1636, middle line accent yellow.
  Text pattern: "1/ Follow me" / "2/ Comment <WORD>" / "3/ Repost".

## Finish
- 1.2% slow push-in + light film grain (theme _postfx handles it).
- Deliverable: `FINAL_reel.mp4`, h264 crf18, faststart, 192k AAC.

## Non-negotiable QA (all local, all cheap — run before rendering)
1. Contact sheet (`sheet.png`): find burned-in text/screenshot windows; keep
   hero + rail clear of them.
2. Head-edge zoom at hero time: crop ~420x300 around head from a preview
   frame, 2x nearest-neighbor upscale, LOOK at it. Halo/blob → run
   `bin/refine-matte.sh <project> <t0> <t1>` (mandatory when subject bbox
   width < ~200px in the hero window — wide shots always need it).
3. `bin/check-audio.sh` across every cut; >2 dB jump at a join → tell Vatsal
   (his CapCut export usually fixes it; never silently remix his audio).
4. Verify last caption vs outro cut (CapCut trims tails — the final word may
   end AFTER the scene cut; cap with lastOut and say so).
