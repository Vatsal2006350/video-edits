# Ramayana re-watch in the IMAX THEATRE pods

Format: `formats/cinema-flex-reel.md`. Builder: `bin/cinema-flex-reel.py`.

1. `bash bin/fetch-epic-fonts.sh`
2. `python3 bin/contact-sheet.py ~/Downloads` (or the AirDrop folder) and pick 7 shots by role
   (roles are written into `spec.template.json`). Keep the film itself to brief wide glimpses.
3. Copy `spec.template.json` to `spec.json`, fill `src`/`in`, then
   `python3 bin/cinema-flex-reel.py projects/ramayana-imax-pod/spec.json --frames 1.6,7.6,11.5,14.2`, look, then full render.
4. `python3 bin/ig-safe.py view <master> safe.jpg 1.6 7.6 14.2` and
   `bash bin/export-ig.sh <master> 01_ramayana-pod_IG.mp4`.
5. Post with the song attached in the composer, title at the swell (~7s).

Caption draft: Someone had to protect the ₹4,000 crore budget 🙏 Comment POD and I'll send you where this is.
#Ramayana #RamayanaPart1 #IMAX #RanbirKapoor #ARRahman #MangalRang

`standin.json` renders the same timeline over generated bokeh plates (type and timing test only).
