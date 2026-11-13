#!/usr/bin/env bash
# Safe Codex entry point for the local third-party effect pack.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$ROOT/effects/video-effects/run.cjs"
PYTHON="$ROOT/effects/video-effects/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python3)"
if [[ ! -d "$ROOT/effects/video-effects/node_modules" ]]; then
  echo "installing the effect engine packages (once)..." >&2
  (cd "$ROOT/effects/video-effects" && npm ci --silent)
fi
if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  echo 'Usage: bin/run-visual-effect.sh EFFECT INPUT.mp4 NEW_OUTPUT.mp4 [engine options]'
  echo 'Example: bin/run-visual-effect.sh liquid-glass /path/to/normalized-clip.mp4 videos/project/previews/glass-r01.mp4 --at 2.4'
  echo 'Effects: run bin/run-visual-effect.sh list'
  exit 0
fi
if [[ "$1" == "list" ]]; then
  PYTHON="$PYTHON" node "$ENGINE" list
  exit 0
fi
if [[ $# -lt 3 ]]; then
  echo 'Need an effect, source media, and a new output path.' >&2
  exit 2
fi
effect="$1"; input="$2"; output="$3"
if [[ ! -f "$input" ]]; then echo "Source file not found: $input" >&2; exit 2; fi
if [[ -e "$output" || -e "$output.work" ]]; then
  echo "Refusing to overwrite $output or its work directory. Use a new revision filename." >&2
  exit 2
fi
python3 "$ROOT/bin/check-denylist.py" "$input"
transfer="$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of default=nw=1:nk=1 "$input" 2>/dev/null || true)"
if [[ "$transfer" == "arib-std-b67" || "$transfer" == "smpte2084" ]]; then
  echo "HDR source ($transfer). Normalize first: bin/color-normalize.sh raw '$input' /path/to/new-rec709-source.mp4" >&2
  exit 2
fi
PYTHON="$PYTHON" node "$ENGINE" "$@"
