#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
ENDPOINT="${BATCH_REGISTER_URL:-$(config_get ops.batch_register_url)}"
ROLE="student"
PASSWORD=""
SIGNUP_TYPE="name"
OS_NAME="mac"
REGIST_ENTRANCE_ID="51"
CHANNEL="shadow"

usage() {
  cat <<'EOF'
Usage:
  batch-register-users.sh --password "PASSWORD" user1 user2 user3

Optional flags:
  --endpoint URL
  --role ROLE
  --signup-type TYPE
  --os OS
  --regist-entrance-id ID
  --channel CHANNEL

Example:
  bash ".claude/skills/api/ops-assistant/scripts/batch-register-users.sh" \
    --password "your-password-here" \
    libin005 libin006 libin007
EOF
}

USERS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    --role)
      ROLE="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --signup-type)
      SIGNUP_TYPE="$2"
      shift 2
      ;;
    --os)
      OS_NAME="$2"
      shift 2
      ;;
    --regist-entrance-id)
      REGIST_ENTRANCE_ID="$2"
      shift 2
      ;;
    --channel)
      CHANNEL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        USERS+=("$1")
        shift
      done
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      USERS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$PASSWORD" ]]; then
  echo "--password is required" >&2
  usage >&2
  exit 1
fi

if [[ ${#USERS[@]} -eq 0 ]]; then
  echo "At least one username is required" >&2
  usage >&2
  exit 1
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

user_json="["
for i in "${!USERS[@]}"; do
  if [[ "$i" -gt 0 ]]; then
    user_json+=", "
  fi
  user_json+="$(json_escape "${USERS[$i]}")"
done
user_json+="]"

payload=$(
  cat <<EOF
{
  "userList": $user_json,
  "role": $(json_escape "$ROLE"),
  "password": $(json_escape "$PASSWORD"),
  "signupType": $(json_escape "$SIGNUP_TYPE"),
  "os": $(json_escape "$OS_NAME"),
  "registEntranceId": $(json_escape "$REGIST_ENTRANCE_ID"),
  "channel": $(json_escape "$CHANNEL")
}
EOF
)

curl --location --request PUT "$ENDPOINT" \
  --header 'Content-Type: application/json' \
  --data-raw "$payload"
