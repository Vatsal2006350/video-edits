# Street-food interview reel (Khau Galli, Ghatkopar — 2026-11-08)

Builder: `videos/khau-galli/build.py <reel>` (EDL -> tonemap -> grade -> ASS captions + PNG graphics -> mix -> master). Export with `bin/export-ig.sh`.

## What went super viral in this genre (downloaded + measured 2026-11-08, `uvx yt-dlp` on reel URLs found in news articles)
| reel | likes | length | structure |
|---|---|---|---|
| @sarthaksachdeva vada pav (DAqxk6moqcY) | 5.8M | 60s | "I'll see how much I can make selling vada pav in a day" challenge hook, POV cuts every 2-3s, small white lower-case captions, numbers as plain text, "Follow for pt3" |
| @vijay_vox_ pani puri profit (C0eawidR0vX) | 2.56M | 17s | question as hook in huge colored captions ("what is your daily profit"), the number as a giant yellow ₹ pop, then a Rajpal Yadav meme punchline ("investing lakhs for college / me with no job") |
| @cassypereira "pani puri wala vs B.Com" (DWG8ZFTCnkH) | 124K | 51s | hook = "does a pani puri wala make more than a B.Com graduate?", first-person day, number ladder ₹3,000/day -> ₹90,000/month -> ₹10,80,000/year, yellow numerals |
| @sakshigadhave water-gun pani puri (DVD6my5CMsp) | 60K | 27s | novelty object (jaljeera water gun), brand tie-in |
Pattern: money/status question hook in frame 1, ONE concrete number as the payoff, a relatable punchline (degree vs street vendor), captions as the hero.
Our Khau Galli interviews contain no earnings numbers, so we hook on the true story (one cart -> whole lane) and use the verified hours as the number moment.

## Our look (better than the references)
- Hook: Anton white stack (ink 6px stroke + soft shadow) with a large red SignPainter accent word on its own line, centred <=724, top of the safe box.
- Captions: Instrument Serif 76 cream, 4.2px ink outline, gold italic emphasis word, bottom y~1440 (inside safe box), 2-3 lines.
- Graphics: cream location pin chip (top), dark "OPEN HOURS 4 PM -> 11:30 PM" card in Anton with a gold arrow.
- Audio: voice clean (highpass 85 + light afftdn, static gain), Hindi instrumental bed (`~/Downloads/music-good/hindi-street/`) at 0.17 side-chain COMPRESSED by the voice, audible from frame 0.
- Punch-in per segment (1.18-1.30x) centred on the speaker so each jump cut reads as a cut.

## Gotchas
- Whisper large-v3-turbo on street audio loops ("ab ab ab") and mangles numbers. Chunk into 7s pieces with `condition_on_previous_text=False`, `compression_ratio_threshold=2`, denoised audio (`afftdn`), and treat all numbers as UNVERIFIED until the creator confirms.
- Source clips are iPhone HLG 4K60 rotated -90: crop BEFORE scale, tonemap AFTER scale (fast), fps=30 last.
- Photos downloads: `bin/photos-pull.sh <uuid-file> <dest>` (runs in Terminal.app, which holds the Photos permission).
