# Reel math overlay

Reusable animated calculations for narration-led Reels. The renderer is
`bin/math-story-overlay.py`; sequence specs contain `duration` and a series of
timed equation/result states. One card stays visible while its text slides to
the next state and named integer values count from `from` to `to` after `delay`
over `duration` seconds. Rendered overlays are transparent 1080x1920 QuickTime
Animation files, so they can be composited over an existing video without
rebuilding its dialogue or music. The earlier independent-card layout remains
available for specs using `cards`.

## Layout and motion

- Persistent sequence card bounds: `(210, 390, 870, 645)` before its soft shadow,
  measured from the rendered alpha layer. The shadow remains inside the IG safe
  box `(59..918, 278..1536)`.
- Dark translucent charcoal card, maize outline/result and bold white Inter
  equation. The sequence layout has no labels or footnotes. Use it when the
  narration supplies the assumptions and the calculation can stay legible by
  itself.
- Keep the card continuously visible from the first calculation line through
  the final result. Change only the equation and answer, aligned to each spoken
  cue; hold the last answer through the closing line.
- Generate representative layer frames with `--proof-dir`, then view a
  composite using `bin/ig-safe.py view` at every card transition.

## Parents calculation example

The parents-reel scenario uses parent age 50 and an 80-year horizon: 30 years
remain. One two-week visit each year gives `30 × 2 = 60` weeks. Dividing by
`4.35` weeks per month gives about 14 months in person. Its sequence spec is
`videos/day2-day6-putting-myself-out-there/parents-math-sequence.json`; the card
starts at 31.02s and stays until the reel ends at 58.67s, with the final answer
appearing at the closing line.
