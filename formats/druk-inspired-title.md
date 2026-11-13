# Tall condensed display title

`bin/druk-inspired-title.py` renders a bold, vertically elongated title layer
using the bundled SIL OFL Anton font. The renderer scales the rasterized glyphs
to a taller and narrower proportion, adds a restrained dark keyline, checks the
alpha bounds against Instagram's safe box, and saves a transparent 1080×1920 PNG.

This reproduces the broad visual direction of a heavy, tall condensed headline.
It is not the proprietary Druk typeface and does not copy its glyph outlines.
Use the commercial font only when a properly scoped license is available.

Example:

```sh
python3 bin/druk-inspired-title.py \
  --line 'I AUTOMATED' --line 'MY INSTAGRAM' \
  --color '#FFFCF6' --color '#FF7127' \
  --top 1245 --gap 120 --out /tmp/hook.png
```

Current reel setting: Anton Regular at 105 px, width scale 0.86, height scale
1.20, 3 px stroke, line gap 120 px. Text stays centered and within x=59..918,
y=278..1536. Keep the red handwritten overlay off this reel.
