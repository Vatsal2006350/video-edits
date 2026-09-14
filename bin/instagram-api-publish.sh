#!/usr/bin/env bash
set -euo pipefail

publish_dir=""
trial_mode="manual"
dry_run="false"
api_version="${IG_API_VERSION:-v26.0}"
graph_host="${IG_GRAPH_HOST:-graph.instagram.com}"
keychain_service="${IG_KEYCHAIN_SERVICE:-com.video-edits.instagram-access-token}"

usage() {
  echo "Usage: $0 PUBLISH_DIR [--trial manual|auto] [--public] [--dry-run]" >&2
}

while (($#)); do
  case "$1" in
    --trial)
      trial_mode="${2:-}"
      shift 2
      ;;
    --public)
      trial_mode="none"
      shift
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    *)
      if [[ -z "$publish_dir" ]]; then
        publish_dir="$1"
        shift
      else
        usage
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$publish_dir" ]]; then
  usage
  exit 2
fi

case "$trial_mode" in
  none|manual|auto) ;;
  *)
    echo "Trial mode must be none, manual, or auto" >&2
    exit 2
    ;;
esac

"$(dirname "$0")/validate-instagram-reel.sh" "$publish_dir"

video="$publish_dir/reel.mp4"
caption_file="$publish_dir/caption.txt"
caption="$(<"$caption_file")"

if [[ "$dry_run" == "true" ]]; then
  echo "Dry run complete"
  echo "Trial mode: $trial_mode"
  exit 0
fi

if [[ -z "${IG_ACCESS_TOKEN:-}" ]]; then
  IG_ACCESS_TOKEN="$(security find-generic-password \
    -a your_handle \
    -s "$keychain_service" \
    -w 2>/dev/null || true)"
fi

: "${IG_ACCESS_TOKEN:?Set IG_ACCESS_TOKEN or store it in macOS Keychain}"
IG_USER_ID="${IG_USER_ID:-${IG_USER_ID}}"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

video_url="${IG_VIDEO_URL:-}"
http_pid=""
tunnel_pid=""
staging_dir=""

cleanup() {
  [[ -z "$tunnel_pid" ]] || kill "$tunnel_pid" 2>/dev/null || true
  [[ -z "$http_pid" ]] || kill "$http_pid" 2>/dev/null || true
  [[ -z "$staging_dir" ]] || rm -rf "$staging_dir"
}
trap cleanup EXIT

if [[ -z "$video_url" ]]; then
  command -v cloudflared >/dev/null || {
    echo "cloudflared is required when IG_VIDEO_URL is not set" >&2
    exit 1
  }
  command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

  staging_dir="$(mktemp -d "${TMPDIR:-/tmp}/instagram-publish.XXXXXX")"
  port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"
  python3 -m http.server "$port" --bind 127.0.0.1 \
    --directory "$publish_dir" >"$staging_dir/http.log" 2>&1 &
  http_pid="$!"
  cloudflared tunnel --no-autoupdate --protocol http2 --url "http://127.0.0.1:${port}" \
    >"$staging_dir/tunnel.log" 2>&1 &
  tunnel_pid="$!"

  for _ in {1..30}; do
    tunnel_base="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$staging_dir/tunnel.log" | grep -v '^https://api\.' | head -1 || true)"
    if [[ -n "$tunnel_base" ]]; then
      video_url="${tunnel_base}/reel.mp4"
      break
    fi
    sleep 1
  done
  [[ -n "$video_url" ]] || { echo "Could not create temporary HTTPS tunnel" >&2; exit 1; }

  tunnel_ready="false"
  for _ in {1..60}; do
    # Fresh tunnel names can be negatively cached by the local DNS resolver.
    # Resolve the public readiness check over HTTPS without altering system DNS.
    if curl --fail --silent --show-error --doh-url https://cloudflare-dns.com/dns-query --connect-timeout 5 --max-time 10 --head "$video_url" >/dev/null 2>&1; then
      tunnel_ready="true"
      break
    fi
    sleep 2
  done
  [[ "$tunnel_ready" == "true" ]] || {
    echo "Temporary HTTPS tunnel did not become ready" >&2
    echo "Transfer endpoint: $video_url" >&2
    tail -n 12 "$staging_dir/tunnel.log" >&2
    tail -n 8 "$staging_dir/http.log" >&2
    curl --silent --show-error --connect-timeout 5 --max-time 10 --head "$video_url" >&2 || true
    exit 1
  }
fi

create_args=(
  --data-urlencode "media_type=REELS"
  --data-urlencode "video_url=${video_url}"
  --data-urlencode "caption=${caption}"
)
if [[ "$trial_mode" == "manual" ]]; then
  create_args+=(--data-urlencode 'trial_params={"graduation_strategy":"MANUAL"}')
elif [[ "$trial_mode" == "auto" ]]; then
  create_args+=(--data-urlencode 'trial_params={"graduation_strategy":"SS_PERFORMANCE"}')
fi

create_response="$(curl --fail-with-body --silent --show-error \
  -X POST "https://${graph_host}/${api_version}/${IG_USER_ID}/media" \
  -H "Authorization: Bearer ${IG_ACCESS_TOKEN}" \
  "${create_args[@]}")"

container_id="$(jq -er '.id' <<<"$create_response")"

status=""
for attempt in {1..30}; do
  status_response="$(curl --fail-with-body --silent --show-error \
    "https://${graph_host}/${api_version}/${container_id}?fields=status_code,status" \
    -H "Authorization: Bearer ${IG_ACCESS_TOKEN}")"
  status="$(jq -r '.status_code // empty' <<<"$status_response")"
  echo "Processing status: ${status:-unknown}"

  case "$status" in
    FINISHED) break ;;
    ERROR|EXPIRED)
      jq . <<<"$status_response" >&2
      exit 1
      ;;
  esac

  sleep 4
done

if [[ "$status" != "FINISHED" ]]; then
  echo "Media did not finish processing in time" >&2
  exit 1
fi

publish_response="$(curl --fail-with-body --silent --show-error \
  -X POST "https://${graph_host}/${api_version}/${IG_USER_ID}/media_publish" \
  -H "Authorization: Bearer ${IG_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg creation_id "$container_id" '{creation_id:$creation_id}')")"

echo "Published Instagram media"
jq . <<<"$publish_response"
