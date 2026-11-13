# Gym stat typography — Michigan tour

Built 2026-10-31 from the supplied finished 36.416667s gym edit. This is an overlay finishing format. Preserve its cuts and original soundtrack.

- Hero: Anton Regular, maize #FFCB05, `$165` at 300px, visible ink/shadow width about 560px. Top y1041 after rasterization. `MILLION` in warm white #FFF9EA, 105px at y1360. Price enters at spoken 2.00s, unit at 3.02s, both exit by 3.91s.
- Supporting stats: `5` 270px with `MASSIVE FLOORS` 77px; `260+` 205px with `FITNESS MACHINES` 68px; `3` 240px with `SWIMMING POOLS` 76px; `200,000` 158px with `SQUARE FEET` 86px. All shrink-to-fit before rasterization, max main glyph width660px.
- Captions: Instrument Serif Regular/Italic, 60–64px, sentence case, short phrases at y1370–1380. Never duplicate a stat with a competing subtitle.
- Shadows: navy-black 5px stroke blurred5px underneath, then2px dark outline on glyphs. Shadows included in measured alpha bounds.
- Motion: number-pop-in-inspired 24px lift and .82→1 scale, 0.20s power4.out with no overshoot; other phrases use 24px horizontal snap or22px rise, .08s exit. Motion applies inside timed wrappers, never to footage.
- Measured source layers all fit x59–918/y278–1500; conservative centered width660px. All 23 proof PNGs and numeric alpha bounds live in the project.
- Opening deliberately uses Michigan maize in place of the generic red brush overprint, so the price remains the sole hero.
- Base HLG must use `bin/color-normalize.sh raw` before staging. Never merely retag this input.
- Graphic reads `TURF COURT`, U-M's official name. Original voice says 'football court' and remains unchanged.

Rebuild: `bash bin/umich-gym-reel.sh`. Design source: `videos/umich-gym-165m/build-design.py`; cues: `design-spec.json`; HTML/GSAP timeline: `composition/index.html`; source/technical research: `research-notes.md`.

## V2 — user spacing/logo/font correction

The current builder is `videos/umich-gym-165m/rebuild-v2-design.py`. Anybody Black Wide (wght900,wdth115) replaces Anton for display lettering; the italic instance handles numerals. Price has a shallow navy extrusion and maize metallic face. Transparent U-M Block M at145×104px anchors the university name, which is left-aligned and tightly stacked at y1146/y1184. Removed the isolated spent word. Stat/unit spacing tightened throughout. Label reads INDOOR FOOTBALL COURT per user correction. V1 source/design and exports retained. V2 filenames contain `-v2`. Rebuild wrapper now selects v2. More research and actual footage comparisons: `research-v2/scout-notes.md` and `six-new-directions.jpg`.
