# Daily-routine bounce (decoded 2026-09-10)

Two Instagram references, hybrid:

- **DdHB2auJ5Fd** (8.15s) — caption "My daily routine" in white italic serif, held the whole time. Alternates a laptop (hand on the trackpad) with him playing guitar. Hard cuts, no transitions. Energy is the A/B bounce, not motion graphics.
- **DblxlZ1TzCV** (6.53s, audio `igexport-DblxlZ1TzCV.mp3`) — slower single desk shot, caption "Switching between reels and hitting accept". This is the Claude-code meme. Use it only for the **opening hold**; then switch to the bounce.

## Structure
1. **Typing open** until the first switch beat (~2.25s on this MP3): UMich Ross tee, hands on the RGB keyboard. Do not cut away before that beat. Do not use the laptop screen.
2. **Flicker** from that beat: hard cuts guitar → keyboard → guitar → keyboard, ~0.20s (6 frames), snapped to 30fps. First cut is guitar.
3. **Drop** (this audio: **4.83s**): guitar looking at camera, slight punch-in (`zoom=1` on that row).
4. Keep the same 0.20s A/B after the drop until the track ends.

Output length equals the burned audio. This MP3 is 6.48s; do not pad.

## Type
Playfair Display Black Italic, white, centred, two lines at the **same size**. Line 1 `switching between guitar`, line 2 `and accepting on claude`. Max width **724px**. Soft scrim + shadow so it survives the airport window. Sits near y 292, inside the IG header floor (y 278). Same job as the reference's "My daily routine" sticker — it does not change on the cuts.

## Footage
Two clips only:
- Typing: `~/Downloads/content/IMG_8286.mov` (10.23s, UMich Ross tee, RGB keyboard, HLG). Hands on keys at 0.3, 2.0, 7.0, 9.5. Skip ~5.0 (hands leave the keys). Do **not** use `IMG_8346.mov` (black sweater + the smile take).
- Guitar: `photos-broll/bom/IMG_4949.MOV` (58s airport, rotation -90, HLG). Down at the strings ~0.8; look-to-camera ~18 and ~36. Caption sits just under the IG header; on the airport shots it grazes the hair because his head is high in frame.

Do not cut to the laptop screen (`IMG_2627`). Both sources are iPhone HLG. The builder tonemaps per shot.

## Tool
`SHOTS="path|seek|dur|zoom" L1= L2= AUDIO= OUT= bash bin/bounce-reel.sh`
`zoom=1` punches the drop shot. Then `bin/export-ig.sh` for the upload copy.
