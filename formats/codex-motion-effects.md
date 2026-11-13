# Codex motion-effects toolbox

**Added 2026-10-31.** A local MIT-licensed effect pack is installed at `effects/video-effects/`, with Codex skills at `effects/{video-effects,liquid-glass,title-orbit,ribbon-wrap,depth-ui,behind-my-head}/`. Follow the house motion rules in `formats/` to apply it within the the creator reel workflow.

## Available effects

The shared engine includes `grid-dive`, `title-orbit`, `magnifying-lens`, `portal`, `clone-room`, `infinite-zoom`, `cube-spin`, `liquid-glass`, `screen-in-screen`, `frame-break`, `tile-tunnel`, `depth-ui`, `vertigo`, `phone-fan`, `shatter`, `spotlight`, `pull-back-reveal`, `ribbon-wrap`, `zoom-through`, and `head-pop-out`.

```bash
bin/run-visual-effect.sh list
bin/run-visual-effect.sh liquid-glass INPUT.mp4 videos/PROJECT/previews/glass-r01.mp4 --at 2.4
```

Use the result as an effect prototype or insert. For a final reel, keep the normal master/IG/phone pipeline and inspect safe-area layers. The wrapper checks the denylist and HLG/PQ tags and protects existing outputs.

## Design guidance

- Reference effect-demo reels use big, persistent titles, then demonstrate each concept with a fast contextual visual insert. The subject remains visible and the graphics explain the edit.
- Use the effect at a specific spoken reveal or music change. Do not put glass transitions between every shot.
- Pair one display face for the large opening hook with a calm caption face; use the approved pairing in `fonts/README.md` and the specific reel format.
- Keep captions under 724px centered width and inside the 1080x1920 Instagram safe box (x 59–918, y 278–1536).
- Do not use the pack's default blue stage/ribbon or demo copy unless it fits the reel's brand. Keep YC orange and UMich maize/blue for those topics.
- For YC effect inserts, use `--stage yc` for a warm cream stage and YC-orange orbit/grid accents.
- Preserve complete speech and exact beat timing. Do not let an effect obscure a face, caption, logo, or meaningful source footage.

## Runtime notes

The pack requires Node, Puppeteer/Chrome, ffmpeg, and a local Python venv with torch/torchvision/Pillow/numpy. The first matte may fetch RobustVideoMatting through Torch Hub. Outputs from `run.cjs` are 1080x1920 H.264 prototypes with audio and are not house IG masters. See `formats/motion-design.md` for safety and assembly instructions.
