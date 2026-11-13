# Travel quote sticker

Measured source: Instagram Da3a4RuyiL6. 15.21 seconds, one travel shot, music starts at zero and stays continuous, no scene cuts. Narrow black sans-serif inside a held rounded white card near y370, small centred heart tab below. Example substitutes parents for siblings.

Tool `bin/travel-quote-reel.py PROJECT`, spec `videos/parents-across-time-zones/spec.json`. Oswald variable font regular, starts at46 and shrinks only if a line exceeds660px. Card x178–902, total724px. Line pitch fontsize+14, 22px top inset. Heart54px, pleading-face42px from local Twemoji PNGs, source twitter/twemoji GitHub assets (CC-BY4.0). Alpha bbox persisted and asserted. No shadow. HLG natural Rec709 tone mapping, no additional grade. Master, export-ig upload version, mobile preview, and safe-view sheet included. Explicit source start/end review and denylist hash required. Never imply a specific flight destination from a generic aircraft shot.

Revision support: optional `shots` array with source/source_in/duration provides unique beat-cut scenes; each original is hash-checked and individually tonemapped before concatenation. `heart_inline:true` puts the42px heart beside the final sentence inside the main rectangle, removing the tab. Current preferred example is `videos/parents-across-time-zones/v2/`. Preserve previous versions by changing `name`; the export tool refuses silent upload-copy replacement.

Reference remake `De33VzmovRu`: `caption_style:"gold-italic"` adds the fixed
two-line warm-yellow (#F7D002) bold italic caption with a 3px dark keyline,
measured at 44px and 0.16 shear. Set `caption_top` and `line_pitch` in the spec.
The type layer remains inside the centered 724px rail-safe width. Use this style
only when the source reference calls for the yellow outlined italic look.
