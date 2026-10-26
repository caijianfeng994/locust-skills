#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
ENDPOINT="${XLAB_WRITE_ABGROUP_URL:-$(config_get ops.xlab_write_abgroup_url)}"
CODE=""
USER_ID=""
AB_CODE=""

usage() {
  cat <<'EOF'
Usage:
  write-user-abgroup.sh --code "EXPERIMENT_CODE" --user-id "USER_ID" [--ab-code "a|b"]

Optional flags:
  --endpoint URL
  --ab-code a|b   Defaults to a (实验组)

Example:
  bash ".claude/skills/api/ops-assistant/scripts/write-user-abgroup.sh" \
    --code "a668ecdd0f691f233f5e3d96a290fd8a" \
    --user-id "654a2733350ca30001036490"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    --code)
      CODE="$2"
      shift 2
      ;;
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    --ab-code)
      AB_CODE="$2"
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

if [[ -z "$CODE" ]]; then
  echo "--code is required" >&2
  usage >&2
  exit 1
fi

if [[ -z "$USER_ID" ]]; then
  echo "--user-id is required" >&2
  usage >&2
  exit 1
fi

if [[ -z "$AB_CODE" ]]; then
  AB_CODE="a"
fi

if [[ "$AB_CODE" != "a" && "$AB_CODE" != "b" ]]; then
  echo "--ab-code must be 'a' or 'b'" >&2
  exit 1
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

payload=$(
  cat <<EOF
{
  "code": $(json_escape "$CODE"),
  "userId": $(json_escape "$USER_ID"),
  "abCode": $(json_escape "$AB_CODE")
}
EOF
)

curl --location --request POST "$ENDPOINT" \
  --header 'Content-Type: application/json' \
  --data-raw "$payload"
