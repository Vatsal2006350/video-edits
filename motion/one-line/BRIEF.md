# Motion brief: introduce my reel system: how one line becomes a reel

Written by bin/motion-brief.py from: subject, 4 words, style `drafting-inks` (matched), 24.0s at 120 BPM, 9:16.

<inputs>
Subject: introduce my reel system: how one line becomes a reel
Exact words, in order: REELS / ONE LINE / BECOMES / A REEL
Cleared numbers (channel-facts.json): effects_count = 88 (as of 2026-11-12)
Still to ask: nothing required. Optional: a track; without one the film gets an original synthesized score at 120 BPM (bin/motion-score.py).
</inputs>

<direction>
A 24.0-second looping 9:16 motion film, 1080x1920 at 30 fps. Taste pack: Drafting inks (one line, three inks) (from heyiamnick's Claude motion-designer showreel prompt (awesome-opus5-5-videos, heyiamnick-119558)).
Concept, in one line: one pencil line gets promoted twice (graphite on paper, wire on a blueprint, light on black) and never leaves the screen.
Every shot is made out of the previous one: shapes, type and colour transform into the next scene. No cuts, no fades.
Type: Geist. Big words weight 900; labels 600-800, 24-28 px, tracked 0.14-0.3 em.
Palette: paper #EDE6D5, blueprint #1B3ED2, hologram #45F0DD, black #07080A, graphite #16161A, white #FFFFFF.
Inks (the same geometry drawn in whichever ink is on screen):
- PAPER: cream, 60 px blue grid at 13% (every 5th at 26%), pencil lines wobbling on slow sines re-phased 8x a second, doubled, diagonal hatching fills, hatched type with a doubled outline
- BLUEPRINT: flat blue, white grid, clean 3-4 px white lines, hidden edges dashed, fine clean hatching
- HOLOGRAM: black, cyan grid, cyan lines with a 30% white core, fills are 8 px scan lines whose thickness follows the light; no glow
Camera: locked and front-on like a drafting table; objects turn, the camera never moves.
Transitions: paper to blueprint: a shape that floods the frame with a hard edge; blueprint to hologram and back to paper: one horizontal scan line.
On screen all film: top-left 'FIG. NN — BAR NAME'; bottom-right 'BEAT N / TOTAL'.
Frame: 1080x1920 at 30 fps (render 4 motion-blur sub-frames); text inside the Instagram safe box x 59-918, y 278-1536; nothing at rest within 90 px of the safe edges.
Honesty: every number, name and claim on screen comes from the user's words, their brand files, channel-facts.json or a cited source; ask or leave it off. the story must read with the sound off.
Banned: particle bursts, lens flares, camera shake, RGB split, crossfades between scenes, generic gradients, bouncy overshoot easing, stock template look, AI-generated text inside images, glows, any fourth colour.
</direction>

<structure>
120 BPM, 48 beats, 12 bars of 2 s. every move starts 0.05 s before its beat so it lands on it; something happens on every beat; no hold longer than half a second.
Easing: critically damped spring 1-(1+w t)e^(-w t), w 12-40, nothing passes its target; exponential ease-in/out for wipes, presses and exits.
Bar 1, DRAFT, 0-2 s: the hero word is pressed flat into the line. Words: "REELS" (hero: fitted to the safe width, the film's first and last frame).
Bar 2, TYPE, 2-4 s: words live in a slot between two rails that resize to fit each word. Words: "ONE LINE" (slot word: lives between the rails, the rails resize to fit it); "BECOMES" (slot word: lives between the rails, the rails resize to fit it).
Bar 3, CURVE, 4-6 s: pen-tool handles bend the line; copies fan; travelling sines. Words: "A REEL" (slot word: lives between the rails, the rails resize to fit it).
Bar 4, MORPH, 6-8 s: the line curls into a circle (length kept), then triangle, square, hexagon; hatching builds.
Bar 5, TILE, 8-10 s: honeycomb; hatching floods solid; the centre cell floods the frame into blueprint.
Bar 6, SOLID, 10-12 s: each hexagon becomes a cube seen corner-on; they merge; perspective turns on.
Bar 7, GEAR, 12-14 s: the front face grows teeth; a meshing gear train steps on eighth notes.
Bar 8, PANEL, 14-16 s: the cube unfolds into six panels that become a dashboard of the user's real numbers.
Bar 9, DATA, 16-18 s: a playhead runs at the real time; a cursor clicks a mode switch; a scan line turns it to light.
Bar 10, LIGHT, 18-20 s: the chart stands up as lit solids.
Bar 11, WAVE, 20-22 s: their tops join into a travelling surface that flattens into the line.
Bar 12, END, 22-24 s: the line lifts into the rail and the hero word rises back; the last frame is the first. Words: "REELS" (hero returns: the loop closes).
The last frame is the first frame, so it loops.
</structure>

<build>
1. A HyperFrames project in motion/one-line/ (index.html + film.js) on the shared engine motion/engine/mg.js (inks, pencil stroke, hatching, curl, polygon morph, cube, gear, flood and scan wipes). Copy the shape of motion/one-line.
2. film.js exports FILM = {W, H, DUR, BPM, draw, frame}; frame(ctx, t) draws one frame from t alone; draw() averages 4 motion-blur sub-frames over a 180° shutter.
3. A beat clock MG.beats(bpm); values are MG.track keyframes that spring in, landing on their beat.
4. Sound: an original score from motion/one-line/score.json via bin/motion-score.py (soft kick on beats, a sound on every visible action); the film must also read muted.
5. Stills first: http://127.0.0.1:8797/tools/sheet.html?film=one-line&t=... (serve motion/). Then render: bin/motion-reel.sh motion/one-line out.mp4.
6. Check: bin/motion-stats.py out.mp4 --ref <reference.mp4> (hard jumps per second, still-frame share, mean motion) and bin/ig-safe.py view; export with bin/export-ig.sh.
</build>

<gotchas>
- Every frame is a pure function of time (film.frame(ctx, t)). Never keep state between frames and never use tl.call(): HyperFrames seeks frame by frame and the motion-blur sub-frames run backwards in time.
- Animate transforms and canvas geometry, never margins or left/top: layout properties snap to whole pixels and stutter (hyperframes check flags gsap_non_transform_motion).
- HyperFrames refuses asset paths that climb above the project (../): bin/motion-reel.sh copies motion/engine/mg.js into the project as engine/mg.js.
- Wait for document.fonts.ready before the first paint, or frame 0 renders in a fallback face.
- A shape morph needs the same point count, the same start point and the same winding on both shapes (MG.resample + reversing to match), or it twists through itself.
- A flood that has covered the frame must become a full-frame fill; a shape that keeps growing still leaves corners on a tall frame.
- Counters and labels read the frame's time, not the sub-frame's, or the digits smear.
- Four sub-frames ghost on fast whips; use 8 for any move faster than a frame width in 0.2 s.
- Keep the last frame equal to the first frame, picture and sound, so Instagram's loop is invisible.
</gotchas>

<start>
Ask the questions in <inputs> that are still open (only those). Then show the beat map (beats.json) and 6 stills from the sheet before rendering. Render only after the stills read well at phone size.
</start>
