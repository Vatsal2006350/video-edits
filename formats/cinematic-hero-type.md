
The look Vatsal wants for standout lines (referenced from @sanskartech, IG reel DcYevQTyKbn): **large lowercase Helvetica Neue Light**, left-aligned, words arriving one line at a time, with earlier lines settling back to ~34% opacity as the newest arrives, all sitting **behind** him via matte occlusion.

Built 2026-09-02 as `bin/hero-type.py` (renders the transparent PNG sequence) plus `bin/embed-behind-seq.sh` (the animated-sequence version of `embed-behind.sh`, which only took a static PNG). Helvetica Neue Light is face **index 7** in `/System/Library/Fonts/HelveticaNeue.ttc`; index 12 is Thin, 5 is UltraLight.

**Why:** this is deliberately NOT the caption style. Vatsal's rule is that ordinary speech keeps the bold Montserrat karaoke captions, and only a couple of sentences per reel get the hero treatment — "not for all text or captions but for some, still I need that style in between with sentences". Using it everywhere would kill the effect.

**How to apply:** place the block high (top ~330-430) so the lines read but their descenders pass behind his hair, which starts around y 690 in the Amplify footage. Time each line's `at` to the actual word from the transcript. The renderer auto-shrinks the size so no line reaches the frame edge — trust that over a hand-picked size. Each matte window costs ~40s of hyperframes `remove-background`, so settle the type position on a still composite BEFORE running the matte. See [[local-reel-pipeline]] and [[silent-embed-segments-trap]] — any new embed window must still be paired with the base audio.
