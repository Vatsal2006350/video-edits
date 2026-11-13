#!/usr/bin/env bash
# clip-edit.sh <spec.json> [--stills 2,9,14] [--out path]
# Runs bin/clip-edit.py in the venv that has torch (RobustVideoMatting). See formats/layercut-clip.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.agents/skills/video-effects/.venv/bin/python"
[[ -x "$PY" ]] || PY="$ROOT/effects/video-effects/.venv/bin/python"
[[ -x "$PY" ]] || { echo "need a python with torch, numpy and pillow (video-effects venv)" >&2; exit 2; }
exec "$PY" "$ROOT/bin/clip-edit.py" "$@"
