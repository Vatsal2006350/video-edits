# Forest & cream editorial (measured from instagram.com/reel/DehbdDYssBE)

Reference: Justin's "Claude edited this video" reel, 56.3s 1080x1920@30. Built as
`videos/claude-edit-english/render_layers.py` (PIL layers -> `composite-layers.py`).

| element | reference | ours |
|---|---|---|
| palette | forest green ≈ #1d3a2a, cream ≈ #f3eee2, sage for unspoken words | GREEN (28,58,41), CREAM (244,239,228), SAGE (139,164,146), GOLD accent (196,170,96) |
| display | tall high-contrast Didone caps, X-compressed | Bodoni Moda VF wght 520 opsz 96, squash 0.80 (words) / 1.0 (numerals) |
| two-tone hero | same glyph cream over dark bg, green over bright bg | per-pixel luma key on the base frame, thr 100 ±12 (`paint_two_tone`) |
| hero placement | behind the head, top 300-750 | behind layer + person matte; caps ≤724 px wide, centred |
| captions | serif on green box, spoken cream / upcoming sage | Instrument Serif 60, box green a=0.95, centre y 1462, ≤4 words/20 chars |
| UI cards | cream paper cards, spaced-caps sans labels | PAPER (246,242,233) r=26-30, Inter labels tracking 0.28em; centred x=495 so card+shadow fits the 59-918 box |
| takeovers | full-bleed green with small cards | green band opening from centre in 0.16s, whoosh on the same frame |

Traps hit:
- Bodoni Moda VF instance has **no '+' glyph** at wght 520 -> `text_mask` falls back to Playfair per char.
- Cards centred at x=540 fail SAFE-BOX once the shadow is counted (box centre is 488.5): centre at 495.
- Hero numerals must sit ≤ ~600 px tall on a close-up or the head swallows them (8M at 380px reads; 470 did not).
- `click.wav` is a near-raw impulse: lowpass 4.5k + 4 ms fade, or the IG export's true peak jumps to +4 dBFS.
- `alimiter` defaults to `level=true` (auto makeup to 0 dBFS) — pass `level=false` in mixes.
