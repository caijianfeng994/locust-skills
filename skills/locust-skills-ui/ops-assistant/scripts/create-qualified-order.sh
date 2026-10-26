#!/usr/bin/env bash

set -eo pipefail

CONFIG_PY="$(cd "$(dirname "$0")/../../scripts" && pwd)/read_config_value.py"
config_get() { python3 "$CONFIG_PY" "$1"; }
GOODS_LIST_URL="${GOODS_LIST_URL:-$(config_get ops.goods_list_url)}"
NORMAL_GOOD_URL="${NORMAL_GOOD_URL:-$(config_get ops.normal_good_url)}"
ORDER_URL="${ORDER_URL:-$(config_get ops.order_url)}"

USER_ID=""
COMBO_GOOD_ID=""
PAID_TIME=""
ORDER_ID=""
LIMIT="5"

GROUP_IDS=()
LEVEL2_IDS=()
LEVEL3_IDS=()

usage() {
  cat <<'EOF'
Usage:
  create-qualified-order.sh --user-id "USER_ID" --combo-good-id "COMPOSITE_GOOD_ID"

Input modes, choose exactly one:
  --combo-good-id ID
  --group-id ID
  --level2-kind-id ID
  --level3-kind-id ID

Optional flags:
  --paid-time "YYYY-MM-DD HH:mm:ss"
  --order-id ID
  --limit N
  --goods-list-url URL
  --normal-good-url URL
  --order-url URL

Examples:
  bash ".claude/skills/api/ops-assistant/scripts/create-qualified-order.sh" \
    --user-id "69ce363b6159180001bf11db" \
    --combo-good-id "78e3b52b-546b-4b2e-a361-d6ff45c4c627"

  bash ".claude/skills/api/ops-assistant/scripts/create-qualified-order.sh" \
    --user-id "69ce363b6159180001bf11db" \
    --group-id "channel_group_purchase_goods" \
    --group-id "channel_platform_goods"

  bash ".claude/skills/api/ops-assistant/scripts/create-qualified-order.sh" \
    --user-id "69ce363b6159180001bf11db" \
    --level2-kind-id "49173400-ba23-40f3-a71d-1aeab441439b"
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

require_commands() {
  local cmd
  for cmd in curl python3 date; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "Missing required command: $cmd" >&2
      exit 1
    fi
  done
}

generate_order_id() {
  python3 - <<'PY'
import time

value = str(time.time_ns())
print("P" + value[:18])
PY
}

extract_candidate_good_ids_from_list_response() {
  JSON_INPUT="$1" python3 - <<'PY'
import json
import os
import sys

raw = os.environ["JSON_INPUT"]

try:
    obj = json.loads(raw)
except json.JSONDecodeError as exc:
    sys.stderr.write(f"Failed to parse list response as JSON: {exc}\n")
    sys.exit(1)

paths = [
    ("data",),
    ("data", "list"),
    ("data", "records"),
    ("data", "rows"),
    ("result",),
    ("result", "list"),
    ("result", "records"),
    ("list",),
    ("records",),
    ("rows",),
]

def get_path(source, path):
    value = source
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value

def extract_id_from_item(item):
    if not isinstance(item, dict):
        return None
    for key in ("id", "goodId", "skuGoodId"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None

def item_priority(item):
    if not isinstance(item, dict):
        return 2
    status = item.get("status")
    is_enabled = item.get("isEnabled")
    is_deleted = item.get("isDeleted")
    if status == "已上架" and is_enabled is not False and is_deleted is not True:
        return 0
    if is_enabled is not False and is_deleted is not True:
        return 1
    return 2

items = None
for path in paths:
    candidate = get_path(obj, path)
    if isinstance(candidate, list):
        items = candidate
        break

if items is None and isinstance(obj, list):
    items = obj

if isinstance(items, list):
    ranked = []
    seen = set()
    for index, item in enumerate(items):
        good_id = extract_id_from_item(item)
        if not good_id or good_id in seen:
            continue
        seen.add(good_id)
        ranked.append((item_priority(item), index, good_id))
    ranked.sort()
    if ranked:
        for _, _, good_id in ranked:
            print(good_id)
        raise SystemExit(0)

def walk(value):
    if isinstance(value, dict):
        direct = extract_id_from_item(value)
        if direct:
            return [direct]
        for nested in value.values():
            found = walk(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = walk(nested)
            if found:
                return found
    return []

fallback = []
for good_id in walk(obj):
    if good_id not in fallback:
        fallback.append(good_id)

if fallback:
    for good_id in fallback:
        print(good_id)
    raise SystemExit(0)

sys.stderr.write("Could not find any composite good ids in list response\n")
sys.exit(1)
PY
}

extract_normal_good_id() {
  JSON_INPUT="$1" python3 - <<'PY'
import json
import os
import sys

raw = os.environ["JSON_INPUT"]

try:
    obj = json.loads(raw)
except json.JSONDecodeError as exc:
    sys.stderr.write(f"Failed to parse normal good response as JSON: {exc}\n")
    sys.exit(1)

def walk(value):
    if isinstance(value, dict):
        for key in ("id", "goodId", "skuGoodId"):
            direct = value.get(key)
            if isinstance(direct, str) and direct:
                return direct
        for nested in value.values():
            found = walk(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = walk(nested)
            if found:
                return found
    return None

for candidate in (obj.get("data") if isinstance(obj, dict) else None, obj.get("result") if isinstance(obj, dict) else None, obj):
    if isinstance(candidate, str) and candidate:
        print(candidate)
        raise SystemExit(0)
    found = walk(candidate)
    if found:
        print(found)
        raise SystemExit(0)

sys.stderr.write("Could not find a normal good id in create-normal-good response\n")
sys.exit(1)
PY
}

resolve_candidate_composite_good_ids() {
  if [[ -n "$COMBO_GOOD_ID" ]]; then
    printf '%s\n' "$COMBO_GOOD_ID"
    return 0
  fi

  local curl_args=()
  local group_id
  local kind_id

  for group_id in "${GROUP_IDS[@]}"; do
    curl_args+=(--data-urlencode "groupList=${group_id}")
  done

  for kind_id in "${LEVEL2_IDS[@]}"; do
    curl_args+=(--data-urlencode "goodKindIdLevel2List=${kind_id}")
  done

  for kind_id in "${LEVEL3_IDS[@]}"; do
    curl_args+=(--data-urlencode "goodKindIdLevel3List=${kind_id}")
  done

  curl_args+=(--data-urlencode "limit=${LIMIT}")

  local response
  response=$(
    curl --silent --show-error --location --request GET --get "$GOODS_LIST_URL" \
      "${curl_args[@]}"
  )

  extract_candidate_good_ids_from_list_response "$response"
}

create_normal_good() {
  local composite_good_id="$1"
  local payload
  local response
  local normal_good_id

  payload=$(
    cat <<EOF
{
  "id": $(json_escape "$composite_good_id")
}
EOF
  )

  response=$(
    curl --silent --show-error --location --request POST "$NORMAL_GOOD_URL" \
      --header 'Content-Type: application/json' \
      --data-raw "$payload"
  )

  if ! normal_good_id="$(extract_normal_good_id "$response" 2>&1)"; then
    log "Failed to create normal good from composite good id: ${composite_good_id}"
    log "Normal good parse error: ${normal_good_id}"
    log "Normal good API response: ${response}"
    return 1
  fi

  printf '%s\n' "$normal_good_id"
}

create_order() {
  local normal_good_id="$1"
  local payload

  payload=$(
    cat <<EOF
{
  "userId": $(json_escape "$USER_ID"),
  "goodId": $(json_escape "$normal_good_id"),
  "paymentCredentials": {
    "orderId": $(json_escape "$ORDER_ID"),
    "channel": $(json_escape "微信"),
    "paidTime": $(json_escape "$PAID_TIME")
  },
  "creationWay": {
    "os": $(json_escape "other"),
    "productId": $(json_escape "428"),
    "channel": $(json_escape "xiaohongshu"),
    "platform": $(json_escape "h5"),
    "shopId": $(json_escape ""),
    "shopName": $(json_escape "")
  },
  "address": {},
  "paymentPlatform": $(json_escape "xiaohongshu"),
  "extra": {
    "sellfrom": $(json_escape "xinmeiti_xiaohongshu"),
    "publicsellfrom": $(json_escape "xinmeiti_xiaohongshu")
  }
}
EOF
  )

  curl --silent --show-error --location --request POST "$ORDER_URL" \
    --header 'Content-Type: application/json' \
    --data-raw "$payload"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    --combo-good-id)
      COMBO_GOOD_ID="$2"
      shift 2
      ;;
    --group-id)
      GROUP_IDS+=("$2")
      shift 2
      ;;
    --level2-kind-id)
      LEVEL2_IDS+=("$2")
      shift 2
      ;;
    --level3-kind-id)
      LEVEL3_IDS+=("$2")
      shift 2
      ;;
    --paid-time)
      PAID_TIME="$2"
      shift 2
      ;;
    --order-id)
      ORDER_ID="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --goods-list-url)
      GOODS_LIST_URL="$2"
      shift 2
      ;;
    --normal-good-url)
      NORMAL_GOOD_URL="$2"
      shift 2
      ;;
    --order-url)
      ORDER_URL="$2"
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

require_commands

if [[ -z "$USER_ID" ]]; then
  echo "--user-id is required" >&2
  usage >&2
  exit 1
fi

mode_count=0
if [[ -n "$COMBO_GOOD_ID" ]]; then
  mode_count=$((mode_count + 1))
fi
if [[ ${#GROUP_IDS[@]} -gt 0 ]]; then
  mode_count=$((mode_count + 1))
fi
if [[ ${#LEVEL2_IDS[@]} -gt 0 ]]; then
  mode_count=$((mode_count + 1))
fi
if [[ ${#LEVEL3_IDS[@]} -gt 0 ]]; then
  mode_count=$((mode_count + 1))
fi

if [[ "$mode_count" -ne 1 ]]; then
  echo "Provide exactly one source condition: --combo-good-id, --group-id, --level2-kind-id, or --level3-kind-id" >&2
  usage >&2
  exit 1
fi

if [[ -z "$PAID_TIME" ]]; then
  PAID_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
fi

if [[ -z "$ORDER_ID" ]]; then
  ORDER_ID="$(generate_order_id)"
fi

CANDIDATE_COMPOSITE_IDS=()
while IFS= read -r candidate_composite_id; do
  if [[ -n "$candidate_composite_id" ]]; then
    CANDIDATE_COMPOSITE_IDS+=("$candidate_composite_id")
  fi
done < <(resolve_candidate_composite_good_ids)

if [[ ${#CANDIDATE_COMPOSITE_IDS[@]} -eq 0 ]]; then
  echo "Could not resolve any candidate composite good ids" >&2
  exit 1
fi

NORMAL_GOOD_ID=""
COMPOSITE_ID=""
for candidate_composite_id in "${CANDIDATE_COMPOSITE_IDS[@]}"; do
  log "Trying composite good id: ${candidate_composite_id}"
  if NORMAL_GOOD_ID="$(create_normal_good "$candidate_composite_id")"; then
    COMPOSITE_ID="$candidate_composite_id"
    break
  fi
done

if [[ -z "$COMPOSITE_ID" || -z "$NORMAL_GOOD_ID" ]]; then
  echo "Failed to create a normal good from all candidate composite goods" >&2
  exit 1
fi

log "Resolved composite good id: ${COMPOSITE_ID}"
log "Created normal good id: ${NORMAL_GOOD_ID}"

log "Creating order for user: ${USER_ID}"
log "Using paidTime: ${PAID_TIME}"
log "Using orderId: ${ORDER_ID}"

create_order "$NORMAL_GOOD_ID"
