
Vatsal's preferred opening for talking-head reels (2026-09-02): the first sentence he speaks appears as **serif text typing out word by word in sync with his voice**, then normal captions take over. "those work well for opening hooks when u type them out as i actually say those words."

`bin/typed-hook.py` does it — reads forced-aligned word timings, lays the whole sentence out once so words never reflow as they appear, and fades each word in at the moment it is spoken. Optional `glow` param blooms the words in gold.

**Why DM Serif Display, not Instrument Serif:** Instrument is too light to read over footage at hook size. DM Serif Display at ~102px is the pick.

**How to apply:** `bin/build-story-reel.sh` is the generic builder — pass `SEGS` (speech cuts), `HOOK_T` (seconds of hook), optional `CUTS` (b-roll). It force-aligns the assembled audio, suppresses normal captions under the hook via `skip_before`, and burns captions in speech time before any opening is prepended. First use: the Spirit Airlines story reel (49s). Note that clip already contains his own b-roll of the empty Spirit counters, so external cutaways were unnecessary and the Mumbai road shot I first tried was geographically wrong for a Detroit story — check that cutaways match the story's location. See [[verify-rendered-not-intermediate]] and [[reel-font-repo]].
