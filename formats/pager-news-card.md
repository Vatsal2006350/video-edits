# News "pager" card reel

Reference: The Sarcastic Page card `instagram.com/p/Dfm6D1Aoust` (image post): full-bleed photo fading into the
text panel, bold centred headline, key phrase on a solid highlight box (theirs is teal, white text), grey one-line dek,
their logo top-left, long explanatory caption. Ours: `bin/pager-reel.py`, first batch `videos/pager-reels/specs/`.

## Numbers
| thing | value | why |
|---|---|---|
| frame | 1080x1920, 9 s, 30 fps | short enough to replay |
| photo | top 1130 px, cover-crop at spec `focus`, slow 1.00→1.08 push-in, 470 px fade into panel | |
| panel | near-black `#0C0C0D` | IG's white username/caption text vanishes on a white bottom |
| kicker pill | Inter Black 34, accent fill, at (64, 300) | inside the IG safe box, readable on frame 1 |
| headline | Montserrat ExtraBold 76→50 px until <= 4 lines, centred, <= 724 px wide, line height 1.22 | IG safe box |
| highlight | rounded box in the company's colour (Nvidia #76B900 / black text, Anthropic #D97757, TSMC #E60012, India #FF9933), wipes in 0.15–0.6 s | |
| dek | Inter SemiBold 37, grey, block bottom <= y 1520 | above IG's bottom band (1536) |
| visuals | `chart` (real daily closes + red final point), `bars` (two-bar compare), `stat` (big number) in a dark card, x <= 880 | right rail starts at 918 |
| music | track's loudest 9 s window of the first 150 s, loudnorm -15, fade out 0.9 s | bed audible from frame one |

## Rules
- Every on-screen number and quote must be in the spec's `sources`, from the company itself or a named outlet. Use
  "says", "per CNBC" or a quote when it is a claim. Drop anything only one weak source has (OpenAI Q3 loss, Claude office app names were dropped this way).
- Photos: Wikimedia Commons with license recorded in `credits.json`. Credit CC BY / BY-SA photos in the caption.
- Own branding only. Never copy another page's logo or exact colour.
- News decays: post within 24–48 h. Anything with a date in it ("Nov 17") must post before that date.
