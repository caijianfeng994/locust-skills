#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
ENDPOINT="${SKU_GOOD_KIND_LIST_URL:-$(config_get ops.sku_good_kind_list_url)}"
LIMIT=""

usage() {
  cat <<'EOF'
Usage:
  list-sku-good-kind.sh --limit 5

Optional flags:
  --endpoint URL

Example:
  bash ".claude/skills/api/ops-assistant/scripts/list-sku-good-kind.sh" \
    --limit 5
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
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

if [[ -z "$LIMIT" ]]; then
  echo "--limit is required" >&2
  usage >&2
  exit 1
fi

if ! [[ "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "--limit must be a positive integer" >&2
  exit 1
fi

if [[ "$LIMIT" -le 0 ]]; then
  echo "--limit must be greater than 0" >&2
  exit 1
fi

curl --location --request GET --get "$ENDPOINT" \
  --data-urlencode "limit=${LIMIT}"
