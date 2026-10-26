# 商品类目造数

本文件覆盖一个任务：

- 获取商品类目列表（`skuGoodKind/list`）

## 1. 获取商品类目列表

### 触发词

商品类目、类目列表、`skuGoodKind`、`skuGoodKind/list`、商品类目造数

### 必要输入

- `limit`（必传，且必须为正整数）

默认值建议：

- 当用户未指定时，建议补齐为 `5` 再执行（并在输出中说明使用了默认值）

### 默认接口

```bash
curl --location --request GET --get '${ops.good_base_url}/api/skuGoodKind/list' \
  --data-urlencode 'limit=5'
```

### 执行规则

1. `limit` 必传，不允许省略。
2. `limit` 必须是大于 0 的整数。
3. 用户未提供 `limit` 时，可默认补齐 `5` 并继续执行，但要在结果中明确说明。
4. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/list-sku-good-kind.sh" \
  --limit 5
```

5. 若用户明确只要命令或 payload，则只返回命令文本，不直接执行。

### 输出规则

- 回报请求参数（尤其是 `limit`）和接口结果摘要。
- 若 `limit` 使用默认值，必须明确标注“默认补齐”。
- 失败时返回关键错误和可复用的重试命令。
