#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8765}"
URL="http://127.0.0.1:${PORT}/library"

if command -v open >/dev/null 2>&1; then
  (sleep 0.8; open "$URL") &
fi

exec python3 "$ROOT/bin/editor/server.py" "$PORT"
