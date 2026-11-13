#!/usr/bin/env bash
# podcast-clip.sh <spec.json> [more specs...]
# Runs bin/podcast-clip.py under uvx so OpenCV (shot + face detection) is available
# without touching the system python. See formats/faceless-podcast-clip.md.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
for spec in "$@"; do
  uvx --with "opencv-python-headless<4.13" --with numpy --with pillow python "$HERE/podcast-clip.py" "$spec" || echo "FAILED $spec"
done
