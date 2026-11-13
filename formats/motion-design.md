# Motion design (no footage, no cuts)

The look of the "Opus made this video" posts: an animation written as code, where one element keeps changing shape instead of the edit cutting to a new shot. It reads as smooth because the frame never resets. The eye follows one thing from the first frame to the last.

Starter: `motion/one-shape/` (12 s, 1080×1920, a pill button → loader → text card → bar chart → pill again).
Render: `bin/motion-reel.sh motion/one-shape out/one-shape.mp4`.

## The rules

1. **One carrier.** A single element carries the eye through every state. It changes width, height, radius and colour. It is never replaced. If a new element must appear, it grows out of the carrier.
2. **No cuts.** Every change is a tween. Hard cuts belong to talking-head edits.
3. **Transforms, not layout.** Move with `x`, `y`, `scale`, `rotation`, `opacity`. Centre the carrier with `xPercent: -50, yPercent: -50`. Margins and `left/top` snap to whole pixels and stutter when the renderer seeks frame by frame (`hyperframes check` flags this as `gsap_non_transform_motion`).
4. **One easing family.** `expo.inOut` for state changes, `power4.out` for things arriving, `power3.in` for things leaving, `back.out(3)` only for a press. Mixing families makes the motion feel like several animators.
5. **Overlap the states.** Start the next morph 0.1–0.2 s before the last one settles, so there is never a dead frame.
6. **The camera drifts.** A background (dot grid, glow) moves slowly and linearly for the whole piece. It gives depth and hides the fact that the carrier is centred.
7. **Stagger the insides.** Lines, bars and list items enter 0.08–0.12 s apart, never all at once.
8. **End where you began.** The last state matches the first so the reel can loop on Instagram.
9. **Words in time.** One word per state, in a serif italic, swapped with a 0.35 s exit and 0.5 s entry on the morph, not between morphs.

## Numbers (the starter's values)

| Thing | Value |
|---|---|
| Frame | 1080×1920 at 30 fps |
| State length | 1.6–2.4 s each, 5 to 12 states |
| Morph duration | 0.9–1.1 s |
| Press | 0.18 s down, 0.4 s back with `back.out(3)` |
| Background drift | 160–260 px over the whole piece, `ease: none` |
| Carrier radius | pill = height / 2; card 44–56 px |
| Type | label 52 px bold sans; word 84 px serif italic at y 1360; kicker 30 px, tracking 0.32 em |
| Safe area | keep text inside x 59–918, y 278–1536 |

## Asking the user

Ask for: the subject, the 5–12 states it should become, one accent colour (or black and white), the length, and the track or BPM. With a track, put each morph on a beat (`bin/music-map.py` finds them).

## Where this came from

The brief comes from the prompts in the public collection of Claude Opus 5.5 videos (yihui-dev/awesome-opus5-5-videos): the strongest motion pieces ask for one shape, no cuts, Dribbble-level UI states and a loop. The numbers in the table are the ones the starter uses; change them per piece and record what worked.
