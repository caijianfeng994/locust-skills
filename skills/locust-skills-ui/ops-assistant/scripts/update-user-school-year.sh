#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
BASE_URL="${USERCORE_BASE_URL:-$(config_get ops.usercore_base_url)}"
USER_ID=""
SCHOOL_YEAR=""

usage() {
  cat <<'EOF'
Usage:
  update-user-school-year.sh --user-id "USER_ID" --school-year "七年级"

Optional flags:
  --base-url URL

Example:
  bash ".claude/skills/api/ops-assistant/scripts/update-user-school-year.sh" \
    --user-id "69ce3c5f6159180001bf11e0" \
    --school-year "七年级"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    --school-year)
      SCHOOL_YEAR="$2"
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

if [[ -z "$SCHOOL_YEAR" ]]; then
  echo "--school-year is required" >&2
  usage >&2
  exit 1
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

payload=$(
  cat <<EOF
{
  "schoolYear": $(json_escape "$SCHOOL_YEAR")
}
EOF
)

curl --location --request PUT "${BASE_URL}/${USER_ID}" \
  --header 'Content-Type: application/json' \
  --data-raw "$payload"
