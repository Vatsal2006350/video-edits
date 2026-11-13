# Reel harness

One entry point, `python3 harness/hx.py`, for the stages that repeat on every reel. Read this file
first. Everything else in the repo (builders, skills, formats) is a tool the harness calls.

## The pipeline

```
discover  ->  brief  ->  effects  ->  script/caption  ->  build  ->  verify  ->  queue  ->  cleanup
 scout        pick        effects         caption          bin/*    reel-qc,     publishing/   cleanup
 ingest/      (reel-      check           check            builders  ig-safe,    queue/        scan/apply
 fetch/rank   picker)                                              export-ig
```

Each stage has one command, one input, and one output. A stage never publishes and never deletes
on its own. Only `cleanup apply --yes` deletes, and only what a reviewed plan lists.

| stage | command | input | output | rule it enforces |
|---|---|---|---|---|
| status | `hx.py status` | — | sizes, queue count, scout runs, catalog | shows storage pile-up at a glance |
| discover | `hx.py scout ingest <run.json>` | search results (see below) | `research/scout-runs/<run>.json` | one row per reel, deduped by reel ID |
| discover | `hx.py scout fetch <run.json>` | a scout run | metrics added to the run, cache in `.work/scout-cache` | public metadata only; backs off on Instagram rate limits |
| discover | `hx.py scout rank <run.json> [--md]` | a scout run | ranked table (and `research/scout-<run>.md`) | engagement score; repeats across queries count |
| brief | `bin/reel-pick` (browser) or `hx.py effects brief "<brief>"` | a brief | shortlist of templates, effects, reference reels | catalog in `bin/reel-picker/catalog_data.py` |
| brief (motion) | `hx.py motion brief -- --subject ... --words "A|B"` | the user's words, facts keys, optional track/brand/footage | `motion/<film>/BRIEF.md` + `beats.json` | taste pack chosen; numbers only from channel-facts.json; open questions listed, never guessed |
| verify (motion) | `hx.py motion check motion/<film> --render out.mp4 [--ref ref.mp4]` | a motion film and its render | pass/fail + motion stats vs. the reference | seek-safe (no tl.call), no pixel-snapping tweens, no ../ assets, no hold over 0.6 s, no cuts |
| effects | `hx.py effects check <pick.json>` | `videos/<slug>/pick.json` | pass/fail + warnings | effects that need numbers need real ones |
| caption | `hx.py caption check <caption.txt> [--source transcript.json]` | caption text | pass/fail | every number is in `channel-facts.json` or said on camera; no ages or heights |
| build | `bin/*` builders, `videos/<job>/build.sh` | a pick and footage | `~/Downloads/reel-batch/<theme>/` | 1080x1920 30fps, Rec.709, IG safe box |
| verify | `bin/reel-qc.py`, `bin/ig-safe.py view`, `bin/export-ig.sh` | the build | QC report, safe-area sheet, IG copy | see CLAUDE.md "Deliverables" |
| queue | `publishing/queue/<name>/` (`reel.mp4`, `caption.txt`, `publish.json`) | verified deliverable | queue item | `bin/validate-instagram-reel.sh` |
| cleanup | `hx.py cleanup scan` then `cleanup apply <plan> --yes` | the disk | a reviewed plan, then deletions | protected: queue refs, under 60 min, raw footage, denylist, music, fonts, logos |

## Scout input format

`hx.py scout ingest` takes a JSON list. Each item is one search and what it returned. Produce it
with WebSearch or with Chrome Google search (`udm=7`, `"<keyword>" instagram reel`):

```json
[
  {"query": "\"yc interview\" instagram reel",
   "results": [{"url": "https://www.instagram.com/reel/DfaI3lqTRLg/", "title": "...", "snippet": "..."}]}
]
```

Keep the run file in `.work/` while you iterate. Ingest writes the cleaned run to
`research/scout-runs/`, which is the only copy worth keeping.

## Rules any agent must follow

1. **Facts.** Numbers on screen come only from `channel-facts.json` (verified) or from his own speech in
   the footage. `hx.py caption check` enforces this. Unknown means ask, or leave it off.
2. **Never publish or post from a harness.** Posting comments, DMs, or uploads needs his explicit OK in
   that turn, even if an earlier turn approved something similar.
3. **Denylist.** Run `bin/check-denylist.py` on any footage before it is used. `FOOTAGE-DENYLIST.md`
   is law.
4. **Other people's reels are reference.** Scout data and downloaded reels are research. Never reuse their
   footage, captions or music. Music comes from `~/Downloads/music-good/` or the official upload.
5. **One output per decision.** Write a new file, or a new `_vN`. Never overwrite a delivered file.
6. **Clean up your own job.** When a job is delivered, its intermediates are candidates for `cleanup scan`.
   Run `scan`, read the plan, and only then `apply`.

## Adding to the harness

- New discovery source: add a producer that writes the scout input format. Do not add a new ranker.
- New effect or template: add it to `bin/reel-picker/catalog_data.py`, then `bin/reel-pick rebuild`.
- New check: add it to `hx.py` next to the stage it guards. Each check must have a comment saying which
  past failure it prevents, the way `bin/reel-qc.py` does.
- Keep the stage contract table above in sync with any change.

## Known limits

- Instagram views are not in public metadata for most reels. Rank on likes and comments, and say so.
- `yt-dlp` gets rate-limited in bursts. `scout fetch` spaces requests and backs off. Rerun later
  instead of forcing it. Cached results are reused.
- Google results give snippets, not counts. A scout run is a shortlist, not a measurement.
- `cleanup` only knows the two rules in CLAUDE.md. Anything it does not recognise is protected.
