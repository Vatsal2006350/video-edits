# video-edits

A local-first factory for producing short-form vertical videos with FFmpeg, Python, and
small declarative manifests. It contains reusable builders for receipt reels, founder
stories, talking-head edits, travel montages, captions, typography, audio mixing, QA, and
Instagram-ready exports.

Raw footage, private photos, rendered videos, account analytics, credentials, and music are
deliberately excluded from Git. The repository is the production system and editorial
knowledge base—not the media archive.

## What is included

- `bin/` — builders, renderers, analyzers, and delivery checks.
- `batch/` — repeatable themed batch builds.
- `formats/` — measured specifications for proven reel formats.
- `projects/` and `receipts/` — declarative edit specs and manifests.
- `research/` — dated, cited trend and production research.
- `FOOTAGE.md` — local-only private-library editorial index; filenames and verified seeks.
- `TOOLS.md` — tool selection and operating notes.

## Requirements

- macOS or Linux with Bash
- FFmpeg and FFprobe
- Python 3 with Pillow and NumPy for the image-based tools
- `uvx` for isolated transcription and media utilities
- `jq`, `rg`, and Node.js for supporting workflows

The working setup uses local font, music, logo, and footage directories. These assets are
not redistributable and are not included. Set paths in a manifest or through the builder's
documented environment variables.

## Start here

Read these files in order:

1. `CLAUDE.md` for the production contract and non-negotiable delivery rules.
2. `TOOLS.md` for the tool inventory.
3. Your local `FOOTAGE.md` before selecting any private-library clip.
4. The matching file in `formats/` before building a known format.

Run a syntax-only health check:

```bash
for file in bin/*.sh batch/*.sh; do bash -n "$file"; done
python3 - <<'PY'
import ast, glob
for path in glob.glob("bin/*.py") + glob.glob("bin/editor/*.py"):
    ast.parse(open(path, encoding="utf-8").read(), filename=path)
print("source parses")
PY
```

Render a receipt reel:

```bash
bash bin/receipt-reel2.sh receipts/example.manifest output.mp4 10.912
```

Create the final upload copy from a mastered reel:

```bash
bash bin/export-ig.sh master.mp4 reel_IG.mp4
```

## Production guarantees

- 1080×1920 at 30 fps.
- Instagram-safe text placement is verified against rendered pixels.
- Tagged iPhone HLG/PQ footage is tonemapped before grading.
- Claims and captions must be verifiable from footage or source material.
- Final upload copies use the repository's standardized Instagram encode.
- Generated media and paid APIs are optional, never implicit.

## Analytics loop

The repository includes an account-level research pilot and an analytics schema under
`analytics/`. Capture each reel at 24 and 72 hours so future batches optimize normalized
retention, sends, saves, and follows—not raw likes alone.

## Privacy and security

Do not commit `.env` files, API credentials, raw footage, exports, customer dashboards,
private analytics, or licensed music. Optional Sora and Veo helpers read credentials from a
separate local project; no credentials belong in this repository.
