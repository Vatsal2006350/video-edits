
`~/Code/video-edits/bin/glowup-reel.sh` builds the transformation format from Vatsal's **2018 childhood photos** (`~/Downloads/photos-broll/before-jpg`, 48 stills of him at ~10-11) into present-day footage.

Structure: `STILLS` ("path|cut_out") cut hard on beats from `bin/beats.py`, pushed through a slow zoompan so a photo never sits dead on screen, graded `hue=s=0.18` + contrast; then `MOTION` ("path|seek|cut_out") where **colour returning is the turn**; then `PAYOFF` ("path|cut_out|caption") with a gold-glow card. Phonk tracks suit it (`phonk-hard` 9.57s, `phonk-gym`, `phonk-dark` — the last needs `AUDIO_SS=5.5`, its first beats are sparse).

`glow-text.py` gained `max_w`, which fits against the text width **plus the bloom** (`spread + radius`, doubled) — the glow extends ~70px past the glyphs, so fitting the glyph box alone puts the bloom under the like button. See [[ig-safe-area]].

**Keep the claims true.** A first pass captioned one reel "Dropped out at 19" — he has not dropped out, he is at Michigan Ross. Captions on his own account are claims about his real life; verify each one (4 countries and 8000 miles are true, "3 continents" was not) rather than reaching for whatever sounds punchiest.
