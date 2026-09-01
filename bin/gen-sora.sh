#!/usr/bin/env bash
# gen-sora.sh <prompt> <out.mp4> [--ref still.png] [--sec 8] [--size 1280x720] [--model sora-2]
# Sora 2 video gen via OpenAI API (key from ~/Code/amplify/.env).
# Cost: sora-2 720p ~$0.10/s ($0.80 per 8s); sora-2-pro ~$0.30/s.
# --ref conditions the video on a first-frame image (identity transfer: make the
# still with gpt-image-2 edits first, then animate it here). Ref size must match --size.
set -euo pipefail
PROMPT="${1:?prompt}"; OUT="${2:?out}"; shift 2
REF=""; SEC=8; SIZE="1280x720"; MODEL="sora-2"
while [ $# -gt 0 ]; do case "$1" in
  --ref) REF="$2"; shift 2;; --sec) SEC="$2"; shift 2;;
  --size) SIZE="$2"; shift 2;; --model) MODEL="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 1;; esac; done
KEY=$(grep '^OPENAI_API_KEY=' "$HOME/Code/amplify/.env" | cut -d= -f2)

ARGS=(-F "model=$MODEL" -F "prompt=$PROMPT" -F "size=$SIZE" -F "seconds=$SEC")
[ -n "$REF" ] && ARGS+=(-F "input_reference=@$REF")
R=$(curl -s https://api.openai.com/v1/videos -H "Authorization: Bearer $KEY" "${ARGS[@]}")
ID=$(echo "$R" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id') or exit(json.dumps(d)[:400]))")
echo "[sora] job $ID (${SEC}s $SIZE $MODEL)"
while :; do
  sleep 10
  S=$(curl -s https://api.openai.com/v1/videos/$ID -H "Authorization: Bearer $KEY")
  ST=$(echo "$S" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'), d.get('progress',''))")
  printf "\r[sora] %s   " "$ST"
  case "$ST" in completed*) break;; failed*) echo; echo "$S" | head -c 400; exit 1;; esac
done
echo
curl -s https://api.openai.com/v1/videos/$ID/content -H "Authorization: Bearer $KEY" -o "$OUT"
echo "[sora] → $OUT ($(du -h "$OUT" | cut -f1))"
