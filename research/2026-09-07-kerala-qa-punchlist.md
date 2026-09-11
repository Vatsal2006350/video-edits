# Reviewer-agent punch list, Kerala reels 22-25 (2026-09-07) -- what it found and what was applied

Mechanics that produced findings: full-frame diff cut detection + 5-frame tiles around every cut; 0.5s contact sheets;
speech-band envelope vs aligned.json; RMS per 0.5s; safe-box overlays. Worth keeping as the reviewer method.

Applied (v4 rebuild):
- 22: c1 panned off the forest onto a white curtain under "greenery" -> steady balcony/forest seek; guide shown headless
  (arm + trousers) for 3s -> a seek with his head in frame; walk-away shot followed by the same walk from 0.8s earlier
  (jump cut) -> the walk cutaway now starts at the segment boundary; forest line got the balcony chairs + forest instead of
  the hazy sheer-curtain shot.
- 23: bunting/sky under "middle of the jungle, trees everywhere" -> tree-lined lake; the grass-bank clip used twice and the
  koi close-up used twice -> tail 1 is the raft-on-pond (IMG_4515), second koi becomes him paddling; bonfire kept to its 2
  bright seconds (it went near-black then a blurry whip pan); caption "safari to the boat" -> "from the boat".
- 24: three 6-frame speaker flashes (all cutaway-gap / short-piece artefacts) -> contiguous cutaways + frame-exact pieces;
  harness/helmet shots under "waterfall called River Valley / views are beautiful" -> valley view, clouds over hills,
  viewpoint; zipline moved to the tail; the smeared through-the-window car clip dropped; hook size 96 -> 80 (it ran under
  the right rail at x 1025).
- 25: same eating take twice around a cut -> different shot; the speech ended on an unanswered question -> ends on
  "traditional cuisine"; "uh" captioned -> dropped; "kerala" -> "Kerala"; 3.5s static leaf -> 2s; corn-stall tail (another
  location, strangers in frame) -> ends at the table; bed seek moved to a steadier passage so the post-speech dip is gone.

Checked and NOT changed:
- "Audio hot, +1.1 dBFS, clipped samples": the IG exports measure -1.9/-2.0 dBFS true peak, -14 to -18 LUFS (loudnorm
  TP=-2 + limiter). The reviewer measured something upstream; keep verifying on the delivered file.
- Head above y=278 in the talking segments: that is the source framing (he shot himself close); a push-down would cost
  picture. Left as is; flagged to Vatsal.
- Captions ~0.4s early on 24 / "So now we" on 23: forced alignment (whisperx venv) was lost in the scratchpad wipe, raw
  whisper timings are in use. Recreate `$S/wxenv` when there is time.
- Three reels on the same song at the same offset: intentional set feel; 25 now starts the bed at 20s.
