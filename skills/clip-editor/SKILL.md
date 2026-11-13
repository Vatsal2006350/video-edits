---
name: clip-editor
description: Re-edit or make interview / podcast / talk clips as "layercut" reels: speaker full-frame, a huge word behind their head on every sentence, chest captions with serif-italic emphasis, and concept cards that draw the idea (slider, compare, list, stat, curve, prospect, loop, venn, chips, quote). Use when the user asks to edit or re-edit a podcast clip, an interview, a Sam Altman / Elon / founder clip, "big text behind the person", "make clips like lapoz", or to visualise a psychological or theoretical concept a speaker explains. Spec-driven: write ~25 lines of JSON, never a new renderer.
---

# clip-editor: one spec, one command

Everything that repeats lives in `bin/clip-edit.py`. Your job per clip is the `edit` block. Read
`formats/layercut-clip.md` once (the look, the card table, the rules).

## Re-edit an existing clip (specs in videos/faceless-podcast/specs/)
1. Read the clip's words: `python3 -c "import json;print(' '.join(w['w'] for w in json.load(open('videos/faceless-podcast/specs/work/<name>/words.json'))))"`
2. Add an `edit` block to the spec:
   - `behind`: one word per sentence, the noun or the stake: `[["COMPOUNDING", "on:compounding"], ...]`
   - `italic`: 2-4 words that carry the point
   - `cards`: pick from the card table by what the sentence *does* (rates, compares, lists, counts, grows,
     loops, overlaps). Anchor each with `"on"` (+ `"nth"`). Say only what the speaker says.
3. Stills, look, then render:
```bash
bin/clip-edit.sh videos/faceless-podcast/specs/<name>.json --stills 1.5,6,9.5,13,19,26
bin/clip-edit.sh videos/faceless-podcast/specs/<name>.json      # -> <out>_layercut.mp4
bash bin/export-ig.sh <out>_layercut.mp4 <out>_layercut_IG.mp4
```

## A new clip from YouTube
```bash
cd videos/faceless-podcast/src && uvx yt-dlp -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]" --merge-output-format mp4 -o "%(id)s.%(ext)s" <url>
```
Transcribe once to choose the moment (mlx-whisper with `--word-timestamps True`), cut at word ends, then
write a spec with `name, src, clips, emph, prompt (proper nouns for whisper), music, out, edit`. The tool
transcribes the cut itself and caches `words.json`. Pick moments where one idea is explained start to
finish in 30-50 s; never cut the speaker mid-thought.

## Why this is cheap
The base cut, the matte, the person track and the words are cached per clip; a change to `edit` only
re-composites (~90 s for 40 s). Do not write new drawing code for one clip. If an idea needs a card that
does not exist, add it once to `CARDS` in `bin/clip-edit.py` and to the table in the format note.

## Checks before sending
- Look at a sheet of the render (every 2.5 s): nobody half out of frame, a word on frame 1, cards readable.
- `bin/export-ig.sh` for the upload copy (-14 LUFS, true peak <= -1.9).
- Credit the show and guest in the IG caption, not on screen.
