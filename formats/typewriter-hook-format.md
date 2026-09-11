
Vatsal sent `Dcq29SSRGLV` ("why I think everyone should live away from home at least once") for its opening typography, with the explicit goal that it become **infra** — a tool any agent can call for future reels, not a one-off. It is `~/Code/video-edits/bin/typewriter.py`; the toolkit map is `~/Code/video-edits/TOOLS.md`.

**Measured (yt-dlp pull → per-frame ink-width curve in the top band; the text is DARK on a bright wall, so a white-pixel probe finds nothing — that was the first clue):**
- Sentence split into 2–4 word phrases; each types **character by character at ~24 chars/s** (20 chars in 0.80s, 16 in 0.73s, 18 in 0.74s, 5 in 0.20s).
- The full line is laid out and **centred once**, then revealed left→right: left edge fixed at x169, right edge grows to 911. Not re-centred per character.
- **Hold until the next phrase is due**, then a **0.13s fade** — four frames of the ink luminance lifting 43→89 toward the wall (210,211,210) — and the next phrase types immediately into the same slot.
- Line spans x 169–911 (**742px**), top y≈325, colour warm near-black **(47,30,8)**. Last phrase ("ONCE!") upper-cased, same size. **Do not measure the height with a dark-pixel bbox on this reel** — her hair sits under the text band and it reported 194px, then 233px, both wrong (real ink ≈100px). Width is the reliable number; the side-by-side is the truth for height.
- Face: **Instrument Serif Regular** — narrow, tight, moderate contrast; Times/Georgia/Hoefler are wider and lighter, Playfair too high-contrast, DM Serif too heavy. No caret visible in the reference (`caret` is optional in the tool).
- After the hook the body is ordinary bottom captions, white with yellow keywords and the odd emoji sticker — `promo-caption.py` already does that.

**Tool contract:** `phrases:[{t, at, caps?, until?}]` with `at` = the first word's aligned start; `cps`, `fade`, `y_top`, `fill`, `font`, `size`; if a phrase would overrun the next `at` at 24 c/s the rate rises to fit. **Instrument Serif at size 103** reproduces the 742px line exactly and the side-by-side shows identical height and weight — the tool's default. y_top 325. Dark ink needs a bright background — on graded/dark footage set `fill` to white. See [[kumar-method-reel-format]] and [[promo-reel-format]] for the other two typographic systems; keep them separate.
