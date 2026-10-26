#!/usr/bin/env bash

set -euo pipefail

USER_ID=""
IDENTITY=""
PAID_TIME=""
ORDER_ID=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREATE_ORDER_SCRIPT="${SCRIPT_DIR}/create-qualified-order.sh"

usage() {
  cat <<'EOF'
Usage:
  assign-researcher-identity.sh --user-id "USER_ID" --identity "研究员|高级研究员|首席研究员"

Optional flags:
  --paid-time "YYYY-MM-DD HH:mm:ss"
  --order-id ID

Example:
  bash ".claude/skills/api/ops-assistant/scripts/assign-researcher-identity.sh" \
    --user-id "69ce363b6159180001bf11db" \
    --identity "高级研究员"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user-id)
      USER_ID="$2"
      shift 2
      ;;
    --identity)
      IDENTITY="$2"
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

if [[ -z "$IDENTITY" ]]; then
  echo "--identity is required" >&2
  usage >&2
  exit 1
fi

case "$IDENTITY" in
  "研究员")
    printf '%s\n' '{"identity":"研究员","skipped":true,"reason":"每个新用户默认是研究员，无需创建订单"}'
    exit 0
    ;;
  "高级研究员")
    COMBO_GOOD_ID="e8f5b7a8-d77e-4868-90bf-ad92b29b05b3"
    ;;
  "首席研究员")
    COMBO_GOOD_ID="4a9e56c1-b339-4892-b687-c4bc1155c3d3"
    ;;
  *)
    echo "--identity must be one of: 研究员, 高级研究员, 首席研究员" >&2
    exit 1
    ;;
esac

if [[ ! -f "$CREATE_ORDER_SCRIPT" ]]; then
  echo "Missing required helper script: $CREATE_ORDER_SCRIPT" >&2
  exit 1
fi

command=(
  bash "$CREATE_ORDER_SCRIPT"
  --user-id "$USER_ID"
  --combo-good-id "$COMBO_GOOD_ID"
)

if [[ -n "$PAID_TIME" ]]; then
  command+=(--paid-time "$PAID_TIME")
fi

if [[ -n "$ORDER_ID" ]]; then
  command+=(--order-id "$ORDER_ID")
fi

printf 'Resolved identity: %s\n' "$IDENTITY" >&2
printf 'Mapped composite good id: %s\n' "$COMBO_GOOD_ID" >&2

"${command[@]}"
