
The "X OR Y" trend reel, decoded 2026-09-02 from instagram.com/reel/DZRjqRCxhKL (@sanskartech, 20.2K likes). Two parts keyed to the audio drop:

- **0 to ~4.75s**: full-bleed vertical shot of the creator in their space, static. Gold italic serif text centred, three lines: `TEMPTING WRONG CHOICE` / `OR` / `ASPIRATIONAL WIN`. Text is ~53% of frame width in the original because the shot is WIDE.
- **4.75s (just before the drop, not on it)**: hard cut out of the hook.
- **1s of three-dot loading animation on black** (`bin/loading-dots.py`, typing-indicator pulse), then a run of **letterboxed 16:9** receipt shots cut on the track's beats, no text. Multiple receipts beat much better than one still: Vatsal's runs YC sign photo -> him presenting on stage -> the packed room.

Generator: `~/Code/video-edits/bin/or-reel.sh`. Env vars L1/L2/L3, HOOK, AUDIO, CUT, DUR, DOTS, TARGET_W/CY/K, and PAYOFFS as newline-separated `path|seek|end_time` rows where end_time is a beat from `bin/beats.py`.

Two shell traps cost a build each: macOS bash 3.2 has no `${var,,}`, and **ffmpeg inside a `while read` loop eats the loop's stdin** — it silently truncated the next iteration's path until `-nostdin` was added.

The text is the **IG 'fisheye' look**: gold italic serif, barrel-warped so lines bow outward. ffmpeg's drawtext cannot do this, so `bin/fisheye-text.py` renders the block with PIL (stroke_width gives the black outline) and applies a numpy radial warp, writing a transparent PNG that or-reel.sh overlays. K=-0.26 is the sweet spot; past about -0.32 the outer words smear and clip.

**Why:** the letterboxing and the cut-before-the-drop are the two things that make it read as the trend rather than a generic text-over-video reel. Both are easy to miss.

**How to apply:** font is Playfair Display Black Italic — the variable Google font renders as Regular in ffmpeg, so it must be instanced with `fonttools varLib.instancer wght=900` (already done, at `fonts/PlayfairDisplay-BlackItalic.ttf`). The warp EXPANDS the text (target_w 670 renders ~800px wide), so size against the warped bbox the script reports, not the target. Keep it inside x 136-935 / y 999-1223: IG's action buttons sit around x 975-1045 and the caption block starts near y 1500. Vatsal's first build used the desk shot in his Michigan Ross shirt for "Talk to her again OR Become a YC founder", with the YC-sign photo (`~/Downloads/yc_announcement.JPG`, Sep 2025) letterboxed as the receipt. See [[receipt-reel-format]] and [[local-reel-pipeline]].
