#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
ENDPOINT="${IDENTITY_HISTORY_BIGVIP_URL:-$(config_get ops.identity_history_bigvip_url)}"
USER_ID=""

usage() {
  cat <<'EOF'
Usage:
  add-history-bigvip.sh --user-id "USER_ID"

Optional flags:
  --endpoint URL

Example:
  bash ".claude/skills/api/ops-assistant/scripts/add-history-bigvip.sh" \
    --user-id "69ce363b6159180001bf11db"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      echo "Unexpected argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$USER_ID" ]]; then
  echo "--user-id is required" >&2
  usage >&2
  exit 1
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

payload=$(
  cat <<EOF
{
  "userId": $(json_escape "$USER_ID")
}
EOF
)

curl --location --request POST "$ENDPOINT" \
  --header 'Content-Type: application/json' \
  --data-raw "$payload"
