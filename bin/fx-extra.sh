#!/usr/bin/env bash
# Safe wrapper for the extra effects (effects/reel-effects/scripts/fx_extra.py), which plug
# into the vendored claude-video-effects engine: all 51 vendored effects PLUS spotify-scroll,
# tech-widgets, glass-tunnel, notes-app, story-portal, yap-headline.
#
#   bin/fx-extra.sh list
#   bin/fx-extra.sh <effect> <input.mp4> <NEW output.mp4> [--start S --end E --text ".." --opt k=v ...]
#   bin/fx-extra.sh --plan plan.json <input.mp4> <NEW output.mp4> [--still 1.8,4.2]   (stills -> PNG check frames)
#
# Same house rules as fx51.sh: denylist guard on the input, never overwrite, input must already be
# Rec.709 (tonemap iPhone HLG first: bin/color-normalize.sh raw), output still needs ig-safe.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/effects/claude-video-effects/.venv/bin/python"
EX="$ROOT/effects/reel-effects/scripts/fx_extra.py"
if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then sed -n '2,12p' "$0"; exit 0; fi
if [[ ! -x "$PY" ]]; then
  echo "setting up the vendored effect venv (once)..." >&2
  python3 -m venv "$ROOT/effects/claude-video-effects/.venv"
  "$PY" -m pip -q install --upgrade pip
  "$PY" -m pip -q install -r "$ROOT/effects/claude-video-effects/requirements.txt"
fi
if [[ "$1" == "list" ]]; then "$PY" "$EX" --list; exit 0; fi
# the input is the 2nd-from-last positional unless --plan is used; find the first existing media file argument
input=""; output=""; pos=()
skip=0
for a in "$@"; do
  if [[ $skip -eq 1 ]]; then skip=0; continue; fi
  case "$a" in
    --plan|--start|--end|--text|--images|--opt|--still|--width) skip=1;;
    --*) ;;
    *) pos+=("$a");;
  esac
done
n=${#pos[@]}
if [[ $n -ge 2 ]]; then input="${pos[$((n-2))]}"; output="${pos[$((n-1))]}"; fi
[[ -s "$input" ]] || { echo "missing input: $input" >&2; exit 2; }
if [[ "$output" == *.mp4 || "$output" == *.mov ]]; then
  [[ ! -e "$output" ]] || { echo "refusing to overwrite: $output" >&2; exit 1; }
  mkdir -p "$(dirname "$output")"
fi
[[ -x "$ROOT/bin/check-denylist.py" ]] && { python3 "$ROOT/bin/check-denylist.py" "$input" || { echo "input is denylisted" >&2; exit 1; }; }
"$PY" "$EX" "$@"
echo "now check it: python3 $ROOT/bin/ig-safe.py view $output <sheet.jpg> <times...>"
