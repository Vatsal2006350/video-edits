# YC founder-video chapter map

`bin/yc-video-map.py OUTDIR SEGMENT_DIR ASSEMBLED_VIDEO --music-seek SECONDS`
renders a transparent RGBA frame sequence for a talking-head YC advice reel.
It reads the exact durations of the 13 speech cuts, then aligns opening cards,
chapter states, CTA, and progress animation to those cuts.

- Canvas: 1080 × 1920 at 30fps. Graphic alpha bounds are checked against the
  Instagram safe box x 59–918, y 278–1536, every second.
- Palette: YC orange `#ff6600`, near black, warm white. Use `logos/yc.png` for
  the actual YC mark and flatten its transparent Y over white.
- Opening: YC deadline card, then a five-things founder-video card. Keep the
  five-things card through the spoken YC-at-18 line. The cover uses the first
  card. Suppress word captions until the chapter map starts so they cannot overlap.
- Upper progress strip: five nodes, y 287–392, with an orange fill that advances
  within the active chapter. Stage cards enter and fade near y 1116.
- Chapters: Product → Founders → Founder Fit → Traction → Vision. Each stage
  starts from the spoken source segment, never from estimated reference timing.
- Payoff: orange product-clarity card starts on the measured music drop and
  persists to the end of the Product point. CTA
  uses the actual YC logo and remains tied to the creator's spoken call to action.
- Speech captions: Instrument Serif in warm white with an orange current word;
  split groups at segment boundaries so a prior line cannot linger into a new
  chapter. Keep music ducked under speech.

Inspect `timing.json` and `bin/ig-safe.py view` output after each rebuild.
