# Faceless podcast clip (clip-page look)

> Newer look for the same clips: **layercut** (`bin/clip-edit.sh`, `formats/layercut-clip.md`): the speaker full-frame,
> a huge word behind the head each sentence, and concept cards that draw the idea. It reuses this tool's
> `qc.json` cuts and `words.json` timings, so a re-edit is one `edit` block in the same spec.

Someone else's long 16:9 interview cut into a 1080x1920 reel: one emotional or funny moment,
30-60 s, with a clip-page top caption, a square picture box that follows the speaker, captions and
a ducked music bed. Tool: `bin/podcast-clip.sh <spec.json>` (wraps `bin/podcast-clip.py` under uvx
with OpenCV). First batch: `videos/faceless-podcast/specs/*.json` → `~/Downloads/reel-batch/faceless-podcast/`.

## Measured reference
`instagram.com/reel/DNyGGvo2HFN` (Raj Shamani Daily, Karan Aujla × Raj, **225K likes**, 1.6K comments):
- flat **black** canvas, no blur, no logo, **no source credit on screen** (credit goes in the caption);
- top text at **y≈300**: bold sans, white, lowercase, first person, one emoji
  ("this moment got me tears 🥹"), ~800 px wide; second line smaller, a curiosity tease ("wait for raj...");
- picture box **full width, square (1080x1080) starting y≈420**, directly under the text;
- no burned captions on that one. `DfKlSanIANN` (9K likes) used big centred white condensed captions.

## Numbers the tool uses
| thing | value | why |
|---|---|---|
| top line | Inter Bold 58 px (shrinks to 46 to fit 2 lines), white, centred, ≤724 px wide, starts y=300 | reference; IG safe box |
| second line | Inter SemiBold 38 px, 85% white | reference "wait for..." line |
| emoji | Apple Color Emoji drawn at 160 px then scaled to the line height | PIL only renders that font at 160 |
| picture box | 1080x1080 at `BOX_Y = clamp(text bottom + 28, 430, 560)` | sits under the text like the reference |
| single speaker | 1:1 crop of the 1080p source at native size (no upscale), centred on the face | sharp; no reframing blur |
| two people within 820 px | crop centred between them | otherwise the frontal host wins and the speaking guest is cropped out (reel 02 first pass) |
| wide / no face | the 16:9 shot scaled 1.3x into the box, centred on detected faces | reads as a shot, not a letterbox |
| punch | hard 1.14x cut-in on `punch` ranges | zoom-cut on punchlines, no zoompan |
| captions | inside the box, bottom at `BOX_Y+930` | |
| canvas | black | a blurred copy pulled the source's sponsor pop-ups into the background |
| music | loudnorm -20 then style volume (0.16-0.30), side-chain ducked under the voice, fades in 0.25 s, out 1.6 s | audible from frame one, voice stays clean |

## Styles
- `emotional`: Instrument Serif captions, word reveal (spoken words solid, upcoming 44% alpha), warm low-sat grade.
- `funny`: Anton caps, active word sky-blue and 108%, punch-ins.
- `bold`: Anton caps, maize active word, contrasty grade.
- `hindi-emotional` / `hindi-funny`: same looks with hand-written English phrase subtitles (`lines`).

## Spec
```json
{"name": "01_altman_coffee", "src": ".../src/<youtube-id>.mp4", "style": "emotional",
 "top": ["he runs openai and still misses this 🥹", "wait for the coffee shop part..."],
 "hook": [2817.36, 2818.80],                 // optional flash-forward played first, then a white dip
 "clips": [[2747.34, 2753.36], ...],         // source seconds, in story order; cut pauses out
 "punch": [[3519.34, 3522.10]],              // source ranges to punch in
 "fix": {"opening": "OpenAI"},               // whisper mishearings
 "lines": [[t0, t1, "English subtitle", true?]], // instead of whisper words; true = belongs to the hook
 "music": {"file": "...mp3", "seek": 0, "vol": 0.2},
 "out": "~/Downloads/reel-batch/faceless-podcast/NN_slug.mp4"}
```
Word timings: whisper large-v3-turbo per range (cached in `specs/work/_cache`). Find moments with
`videos/faceless-podcast/work/scout.sh <src> <name> <start> <end> [lang]`, which prints word@time.

## Rules
- Top text must be true to what is said in the clip (no invented numbers or claims). Phrase predictions
  as the speaker's ("elon says..."). Translate Hindi/Punjabi faithfully; keep it short.
- No source credit or watermark text on the reel; credit the show and guest in the IG caption.
- Hook: the top text is readable on frame 1 and names the stakes; the first spoken line is the question or
  the most striking line. Use `hook` only when the payoff line also makes sense out of context.
- Guest's own music under that guest when it exists (Anuv Jain, Karan Aujla); attach the IG library version when posting.
- These are third-party clips: claims/takedowns are possible. Keep edits transformative (re-cut, captions, framing).

## Cutting rules (Vatsal, 2026-11-11, after the first batch: "you're cutting off his speech, it sucks")
- **Let answers flow.** One range per thought; keep the speaker's natural pauses. Cut only between
  thoughts, or to drop the host re-phrasing a question (stop at "what version of you has died?").
- **Never clip a word.** The builder snaps every range *end* to the first real pause (80 ms below 10% of the
  range's speech level, up to +0.7 s) and re-checks the edge energy; starts stay where authored
  (whisper word start - 0.08) because snapping back pulls in the host's last word. `qc.json` lists anything left.
- **Music from frame one.** 0.5 s music-only lead-in (`music.lead`), voice muted under it, fade-in 0.05 s,
  lighter ducking (threshold 0.06, ratio <= 3) so the bed stays audible.
- **Cuts on the beat.** Speech is never moved; instead the music start is shifted 0-4 s so its onsets land
  within 70 ms of our cuts (`music.beat_align`, default on; the log prints hits/cuts).
- **QC as you go:** after every render, transcribe the master (`videos/faceless-podcast/qc.sh`) and read it
  top to bottom for half words before sending anything.

## Shot reading (what failed and the fix)
- Dark Raj Shamani set: real cuts only reach 0.29 Bhattacharyya → cut = hist > 0.24 or mean pixel jump > 8.
- Profile close-ups have no Haar face → "no face but lit pixels" = close-up, cropped on the lit mass.
- Wides have small faces (< 7.5% of frame width) → framed 1.3x zoom, never a native 1:1 crop.

## v3 (2026-11-11, after "average 45 s, max 50 s; one opens with no music; money emoji on Elon's laughs")
- **Length:** 50 s hard cap (`max_len`), aim ~45 s. The builder prints `QC TOO LONG` otherwise.
- **Opening music:** quiet intros are skipped (`loud_seek`), then the 0.5 s lead-in is measured and lifted to
  -18 dB, easing to bed level over 1 s once the voice starts; if the bed is still under -40 dB the seek steps
  2 s in and retries. Every render prints `opening <dB>`; under -26 dB is flagged. All 15 measure -17 dB.
- **Laugh bursts** (`"bursts": ["auto", <source times>]`): money emoji (🤑💸💰💵) pop from the lower middle of the
  box, spray up, fall and fade (1.1-1.5 s), clamped inside the safe box. `auto` = loud stretches >= 0.4 s with
  no whisper word; add YouTube `[laughter]` cue times because laughs under speech are missed by `auto`.
- **Push-in:** held single-speaker shots (>= 2.5 s) get a slow 4% push-in. **Progress bar:** 6 px white line on
  the bottom edge of the box. **Emphasis:** `"emph": [words]` stay yellow in word captions.
- `REUSE_PICTURE=1 OVERWRITE=1 bin/podcast-clip.sh <spec>` re-mixes audio only (seconds, not minutes).
