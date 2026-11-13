# Shot-truth gate for autobiographical reels

Before an autobiographical reel is checked or rendered, maintain a `shot-manifest.json` beside its `BRIEF.md`. Run `python3 bin/shot-guard.py videos/<project>/shot-manifest.json` from the repo root, or wire it before `hyperframes check` as `milestones-and-moments/package.json` does.

For every selected cut, record its staged asset, source in/out, who is visible, **what the proposed trimmed frames visibly show**, a story/emotion label (editorial judgment), and a saved midpoint review frame. Set `human_verified` only after actually looking at that frame. Every literal caption/premise action must appear under `required_visual_claims` and be backed by a shot's `action_tags`.

The guard checks the manifest, media ranges, existing review frames, and literal claim coverage. It does **not** infer emotion or identity automatically; claiming that would be false confidence. A reviewer must still check the start, middle, and end of every critical action, exclude denylisted people/UUIDs/hashes, and inspect Instagram safe-area chrome over the rendered draft.

Known failure: the September airport reel labeled a terminal exterior “boarding,” and a later draft substituted unrelated walking clips for a walk onto the plane. Until a frame-verified jet-bridge/aircraft-threshold clip exists, do not tag any local clip `walking_onto_plane` or `boarding_plane`, and do not publish a reel whose hook promises that action.
