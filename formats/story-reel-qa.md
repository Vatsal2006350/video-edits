# Story-reel QA pass (the norm after every talking-head build, 2026-09-07)

Vatsal: "have another agent do a pass and this should be the norm to fix up these tiny stuff." Two layers:

1. `bin/story-qa.py` runs inside `build-story-reel.sh` before rendering. It refuses to render on: a gap < 0.6s between
   cutaways (the speaker flashes for a few frames), a cutaway taken from the take that is speaking under it (looks like the
   line said twice), a cut inside a segment's first 0.4s or last 0.3s (end a cutaway AT the segment end or >= 0.3s before),
   a seek that runs past the source. Root cause of the flashes was re-encoded trims coming out frames short; every cut piece
   is now `-frames:v` exact.
2. A reviewer subagent on the rendered file(s). Prompt it to: extract frames around every hard cut and every 0.5s; flag
   shots < 0.5s, the same angle twice around a cutaway, picture contradicting the words (exterior under "cupboard / made of
   wood", interior under "forest"), caption typos vs what is on screen (whisper: horrible->herbal, Fram Yard->Farmyard,
   Caroline->Kerala), cuts mid-word, voice level jumps, bed > -24 dBFS under speech, repeated facts across takes, the same
   clip in two reels, face/text outside the IG safe box. Output: timestamped punch list + what NOT to touch. Apply, rebuild, resend.

Rules learned on the Kerala set: never let two takes state the same fact; interior words get interior shots; cutaways are
contiguous blocks, not islands; the bed sits at MUSVOL 0.17 for a song; captions get `WORDFIX` for proper nouns.
