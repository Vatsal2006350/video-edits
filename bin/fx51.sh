#!/usr/bin/env bash
# Safe wrapper for the vendored claude-video-effects pack (51 Python effects).
#
#   bin/fx51.sh list
#   bin/fx51.sh <effect> <input.mp4> <NEW output.mp4> [--start S --end E --opt k=v ...]
#
# Upstream: github.com/Vibha-Ramprakash/claude-video-effects (MIT, @vibha.in.progress)
# Vendored at effects/claude-video-effects (commit in VENDORED-COMMIT.txt).
# House rules enforced here, not upstream: denylist guard on the input, never
# overwrite an existing output, and a reminder that output still needs ig-safe.
#
# Which ones actually suit a TIGHT talking-head (measured on IMG_5882, head ~half
# the frame width) — see formats/cover-orbit-claude-ui.md:
#   noise        reels pile up behind the head          GOOD, the pile reads
#   fan-build    covers deal into a fan behind the head cards fly off-frame top
#   orbit        covers ring the head                   cards clip at the edges
# Anything that rings or arcs around the head needs a WIDER shot than this one.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$ROOT/effects/claude-video-effects"
PY="$SKILL/.venv/bin/python"

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  sed -n '2,20p' "$0"; exit 0
fi
if [[ ! -x "$PY" ]]; then
  echo "setting up the vendored effect venv (once)..." >&2
  python3 -m venv "$SKILL/.venv"
  "$PY" -m pip -q install --upgrade pip
  "$PY" -m pip -q install -r "$SKILL/requirements.txt"
fi
if [[ "$1" == "list" ]]; then
  grep -E '^\| [0-9]+ \| `' "$SKILL/SKILL.md" | sed 's/|/ /g'
  exit 0
fi
[[ $# -ge 3 ]] || { echo "need: effect input.mp4 NEW-output.mp4" >&2; exit 2; }
effect="$1"; input="$2"; output="$3"; shift 3
[[ -s "$input" ]] || { echo "missing input: $input" >&2; exit 2; }
[[ ! -e "$output" ]] || { echo "refusing to overwrite: $output" >&2; exit 1; }
if [[ -x "$ROOT/bin/check-denylist.py" ]]; then
  python3 "$ROOT/bin/check-denylist.py" "$input" || { echo "input is denylisted" >&2; exit 1; }
fi
mkdir -p "$(dirname "$output")"
"$PY" "$SKILL/scripts/fx.py" "$effect" "$input" "$output" "$@"
echo "now check it: python3 $ROOT/bin/ig-safe.py view $output <sheet.jpg> <times...>"
