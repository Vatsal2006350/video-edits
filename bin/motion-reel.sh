#!/usr/bin/env bash
# Render a motion-design composition (a HyperFrames HTML project) to a vertical MP4.
#
#   bin/motion-reel.sh motion/one-shape out/one-shape.mp4
#   bin/motion-reel.sh motion/one-shape out/one-shape.mp4 --ig   # also writes out/one-shape_IG.mp4
#
# Lints first (hyperframes check), refuses to overwrite, then renders at delivery quality.
# Rules for the look: formats/motion-design.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HF="hyperframes@0.8.225"
if [[ $# -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then sed -n '2,8p' "$0"; exit 0; fi
comp="$(cd "$1" && pwd)"; out="$2"; ig="${3:-}"
[[ -f "$comp/index.html" ]] || { echo "no index.html in $comp" >&2; exit 2; }
[[ ! -e "$out" ]] || { echo "refusing to overwrite: $out" >&2; exit 1; }
mkdir -p "$(dirname "$out")"
out="$(cd "$(dirname "$out")" && pwd)/$(basename "$out")"
(cd "$comp" && npx --yes "$HF" check) || { echo "check failed: fix the errors above first" >&2; exit 1; }
(cd "$comp" && npx --yes "$HF" render --quiet -q delivery -o "$out")
echo "rendered $out"
if [[ "$ig" == "--ig" ]]; then
  bash "$ROOT/bin/export-ig.sh" "$out" "${out%.mp4}_IG.mp4"
fi
