# YC interview question list

## Proven treatment

Reference: Instagram Reel `DfSh3x-igpc`, a fixed talking-head with a progressively revealed numbered question list. This adaptation uses the creator's own interview footage and condenses his spoken outline into ten rows.

- Canvas: 1080x1920, 30 fps, 9:16.
- Hook plate: x180–900, y280–630; 720x350 px. YC mark 84x84 px; headline in Switzer Bold 70 px, supporting serif 54 px.
- Persistent question rail: x59–465, y300–1520; 406x1220 px, rounded dark translucent panel.
- Header: YC icon 58x58 px at x70/y325, “YC INTERVIEW” 21 px and “10 QUESTIONS” 17 px.
- Ten rows: 101 px vertical pitch, beginning at y418; two lines of Switzer Bold 24 px; number 22 px. Current row uses a dark fill and orange outline, completed rows are white, future rows are muted.
- All type stays in the IG safe box (x59–918, y278–1536). The left panel's 11 px edge is background only; inspect alpha bounds on the final plates and phone preview.
- Left-side black gradient fades to transparent by x650; keep the face center-right. YC orange #FF6600, warm white #FFFAF4.
- Timing: trigger each highlight on the corresponding spoken question. Start the rail after the hook; let it resolve to all-white at the end. End card may use a keyword CTA only when the campaign automation is configured for that keyword.

## Reusable renderer

`bin/yc-interview-list.py <asset-dir>` renders `hook.png`, `q01.png` through `q10.png`, `done.png`, and `cta.png` as 1080x1920 RGBA plates. This project established the measurements from the supplied reference and the output of the renderer; inspect all plates with `bin/ig-safe.py view` or alpha-bound checks before reuse. The project build script and source cut list are in `videos/yc-interview-questions/build.py`.

## Audio and picture

Tonemap tagged iPhone HLG to Rec.709 before crop, grade, or overlays. Keep the voice forward; use a locally curated track from `~/Downloads/music-good/`, ducked under speech. Deliver a 1080x1920 H.264 master and a separate Instagram upload export via `bin/export-ig.sh`.
