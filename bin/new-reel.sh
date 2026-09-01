#!/usr/bin/env bash
# new-reel.sh <project-name> <raw-video> — scaffold a reel project and run all
# deterministic pre-processing. After this, the agent authors theme.json.
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?usage: new-reel.sh <project-name> <raw-video>}"
RAW="${2:?usage: new-reel.sh <project-name> <raw-video>}"
P="$WS/$NAME"
[ -e "$P/source.mp4" ] && { echo "[new-reel] $P/source.mp4 exists — refusing to clobber"; exit 1; }
mkdir -p "$P"
cp -R "$WS/fonts" "$P/fonts" 2>/dev/null || true

echo "[new-reel] normalizing → 1080x1920@30 h264 (pipeline source)…"
ffmpeg -y -v error -i "$RAW" \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -r 30 -c:v libx264 -preset medium -crf 18 -g 30 -keyint_min 30 -movflags +faststart \
  -c:a aac -b:a 192k -ar 48000 -ac 2 "$P/source.mp4"

echo "[new-reel] probes…"
ffmpeg -y -v error -i "$P/source.mp4" -vf "fps=1,scale=160:-1,tile=10x5" "$P/sheet.png"
ffmpeg -v error -i "$P/source.mp4" -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 \
  | grep -oE "pts_time:[0-9.]+" | sed 's/pts_time:/scene-cut @ /' > "$P/scene-cuts.txt" || true

echo "[new-reel] prepare (matte ∥ transcribe ∥ envelope → safe-zones)…"
export HYPERFRAMES_ROOT="${HYPERFRAMES_ROOT:-$HOME/Downloads/hyperframes}"
bash "$WS/.agents/skills/embedded-captions/scripts/prepare.sh" "$P"

echo; echo "[new-reel] READY: $P"
echo "  next: review sheet.png + scene-cuts.txt + transcript.json, then author theme.json"
cat "$P/scene-cuts.txt" 2>/dev/null | head -8
