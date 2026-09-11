# "N things I did at N" list reel (dara.miao format, built for Vatsal's 18/19)

`bin/list-reel.sh` + `bin/list-label.py`. One still or clip per beat with a label
sticker, the payoff lands on the drop, music from `~/Downloads/music-good/`.

- `ITEMS` lines: `path|seek|text|logo.png|cy|logo_y`. `STILL_MODE` = letterbox |
  cover | black (YC photo uses black bars, per Vatsal). Hook via `hero-type.py`
  with `HOOK_FADE/HOOK_GHOST/HOOK_AT2`; `FINAL` text optional; end when the music ends.
- Labels: no scrim, stacked offset shadows, width capped at
  `min(SAFE_R - X0, 2*(SAFE_R - W//2))`; logo sits at `logo_y` (never over the face).
- Pacing lesson from his feedback: rest on each item, do not stack many clips per
  beat; the transformation image is his own edited before/after; bungee shows the
  jump then the hang; never repeat the YC image at the end.
- Verified footage for it lives in `FOOTAGE.md` (bungee IMG_2583, skydive FullHD,
  guitar = BOM airport clips, projector clip for "3 startups").
