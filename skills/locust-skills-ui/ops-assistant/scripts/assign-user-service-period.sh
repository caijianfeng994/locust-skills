#!/usr/bin/env bash

set -euo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
LOOKUP_ENDPOINT="${USER_ALLOCATION_FIND_FAMILY_URL:-$(config_get ops.user_allocation_find_family_url)}"
APPLY_ENDPOINT="${USER_ALLOCATION_APPLY_PRESALES_URL:-$(config_get ops.user_allocation_apply_presales_url)}"
USER_ID=""
TEAM_ID=""
TEAM_NAME=""
NO_VERIFY_CALM="true"

usage() {
  cat <<'EOF'
Usage:
  assign-user-service-period.sh --user-id "USER_ID" (--team-id "TEAM_ID" | --team-name "TEAM_NAME")

Optional flags:
  --lookup-endpoint URL
  --apply-endpoint URL
  --no-verify-calm true|false   Defaults to true

Supported team names:
  入校
  电销/网销
  奥德赛
  体验营
  新媒体视频
  研学
  本地化
  商业化-公域
  商业化-APP
  阿拉丁

Example:
  bash ".claude/skills/api/ops-assistant/scripts/assign-user-service-period.sh" \
    --user-id "6a06f3eb87922400012b3dda" \
    --team-name "电销/网销"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lookup-endpoint)
      LOOKUP_ENDPOINT="$2"
      shift 2
      ;;
    --apply-endpoint)
      APPLY_ENDPOINT="$2"
      shift 2
      ;;
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    --team-id)
      TEAM_ID="$2"
      shift 2
      ;;
    --team-name)
      TEAM_NAME="$2"
      shift 2
      ;;
    --no-verify-calm)
      NO_VERIFY_CALM="$2"
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

resolve_team_id() {
  case "$1" in
    "1"|"入校")
      echo "1"
      ;;
    "2"|"电销/网销"|"电销网销")
      echo "2"
      ;;
    "3"|"奥德赛")
      echo "3"
      ;;
    "4"|"体验营")
      echo "4"
      ;;
    "5"|"新媒体视频")
      echo "5"
      ;;
    "6"|"研学")
      echo "6"
      ;;
    "7"|"本地化")
      echo "7"
      ;;
    "8"|"商业化-公域"|"商业化公域")
      echo "8"
      ;;
    "9"|"商业化-APP"|"商业化APP")
      echo "9"
      ;;
    "10"|"阿拉丁")
      echo "10"
      ;;
    *)
      return 1
      ;;
  esac
}

resolve_team_name() {
  case "$1" in
    "1")
      echo "入校"
      ;;
    "2")
      echo "电销/网销"
      ;;
    "3")
      echo "奥德赛"
      ;;
    "4")
      echo "体验营"
      ;;
    "5")
      echo "新媒体视频"
      ;;
    "6")
      echo "研学"
      ;;
    "7")
      echo "本地化"
      ;;
    "8")
      echo "商业化-公域"
      ;;
    "9")
      echo "商业化-APP"
      ;;
    "10")
      echo "阿拉丁"
      ;;
    *)
      return 1
      ;;
  esac
}

if [[ -n "$TEAM_ID" ]]; then
  if ! TEAM_ID="$(resolve_team_id "$TEAM_ID")"; then
    echo "--team-id must be one of 1-10" >&2
    exit 1
  fi
fi

if [[ -n "$TEAM_NAME" ]]; then
  if ! RESOLVED_FROM_NAME="$(resolve_team_id "$TEAM_NAME")"; then
    echo "--team-name is not recognized: $TEAM_NAME" >&2
    exit 1
  fi

  if [[ -n "$TEAM_ID" && "$TEAM_ID" != "$RESOLVED_FROM_NAME" ]]; then
    echo "--team-id and --team-name do not match" >&2
    exit 1
  fi

  TEAM_ID="$RESOLVED_FROM_NAME"
fi

if [[ -z "$TEAM_ID" ]]; then
  echo "Either --team-id or --team-name is required" >&2
  usage >&2
  exit 1
fi

if [[ "$NO_VERIFY_CALM" != "true" && "$NO_VERIFY_CALM" != "false" ]]; then
  echo "--no-verify-calm must be true or false" >&2
  exit 1
fi

TEAM_NAME="$(resolve_team_name "$TEAM_ID")"

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

lookup_payload=$(
  cat <<EOF
{
  "userIds": [
    $(json_escape "$USER_ID")
  ]
}
EOF
)

echo "Resolving familyId for userId=$USER_ID" >&2

lookup_response="$(
  curl --silent --show-error --location --request POST "$LOOKUP_ENDPOINT" \
    --header 'x-md-global-refresh-cache: false' \
    --header 'Content-Type: application/json' \
    --data-raw "$lookup_payload"
)"

family_id="$(
  FAMILY_LOOKUP_RESPONSE="$lookup_response" python3 - <<'PY'
import json
import os
import sys

raw = os.environ["FAMILY_LOOKUP_RESPONSE"]

try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"Failed to parse family lookup response as JSON: {exc}", file=sys.stderr)
    sys.exit(1)

items = data.get("list") or []
if not items:
    print("Family lookup returned an empty list", file=sys.stderr)
    sys.exit(2)

first = items[0]
if not isinstance(first, dict):
    print("Family lookup response has an invalid list[0] value", file=sys.stderr)
    sys.exit(3)

family = first.get("family") or {}
if not isinstance(family, dict):
    print("Family lookup response has an invalid family object", file=sys.stderr)
    sys.exit(4)

family_id = family.get("id")
if not family_id:
    print("Family lookup response does not contain list[0].family.id", file=sys.stderr)
    sys.exit(5)

print(family_id)
PY
)"

echo "Resolved familyId=$family_id" >&2
echo "Applying service period: teamId=$TEAM_ID teamName=$TEAM_NAME noVerifyCalm=$NO_VERIFY_CALM" >&2

apply_payload=$(
  cat <<EOF
{
  "teamId": $TEAM_ID,
  "familyId": $(json_escape "$family_id"),
  "noVerifyCalm": $NO_VERIFY_CALM
}
EOF
)

curl --location --request POST "$APPLY_ENDPOINT" \
  --header 'x-md-global-refresh-cache: false' \
  --header 'Content-Type: application/json' \
  --data-raw "$apply_payload"
