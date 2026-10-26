# 身份与实验操作

本文件覆盖三个任务：

- 补发历史大会员
- 写入 AB 实验组
- 分配研究员身份

## 1. 补发历史大会员

### 触发词

历史大会员、`bigvip`、会员身份补发、`add/history/bigvip`

### 必要输入

- `userId`

### 默认接口

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/identity/client/add/history/bigvip' \
--header 'Content-Type: application/json' \
--data-raw '{
  "userId": "69ce363b6159180001bf11db"
}'
```

### 执行规则

1. 保持字段名为 `userId`。
2. `userId` 齐全时默认直接执行。
3. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/add-history-bigvip.sh" \
  --user-id "69ce363b6159180001bf11db"
```

### 输出规则

- 回报提交的 `userId` 和接口结果摘要。

## 2. 写入 AB 实验组

### 触发词

实验组、AB实验、`abCode`、对照组、实验组写入、`xlab-new/shadow/abgroup/write`

### 必要输入

- `code`
- `userId`
- `abCode`，默认 `a`

### 组别含义

- `a` = 实验组
- `b` = 对照组

### 默认接口

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/xlab-new/shadow/abgroup/write' \
--header 'Content-Type: application/json' \
--data-raw '{
  "code":"a668ecdd0f691f233f5e3d96a290fd8a",
  "userId":"654a2733350ca30001036490",
  "abCode":"a"
}'
```

### 执行规则

1. 保持字段名为 `code`、`userId`、`abCode`。
2. 缺少 `abCode` 时默认补成 `a`。
3. 三个参数可解析时默认直接执行。
4. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/write-user-abgroup.sh" \
  --code "a668ecdd0f691f233f5e3d96a290fd8a" \
  --user-id "654a2733350ca30001036490"
```

### 输出规则

- 回报提交的 `code`、`userId`、`abCode`。
- 如果 `abCode` 是默认补齐的，要明确说明。

## 3. 分配研究员身份

### 触发词

研究员、高级研究员、首席研究员、指定用户身份

### 必要输入

- `userId`
- `identity`

可选输入：

- `paidTime`

### 身份映射

- `研究员`：所有新用户默认已有该身份，不创建订单
- `高级研究员`：组合商品 id 为 `e8f5b7a8-d77e-4868-90bf-ad92b29b05b3`
- `首席研究员`：组合商品 id 为 `4a9e56c1-b339-4892-b687-c4bc1155c3d3`

### 执行规则

1. 目标身份是 `研究员` 时，直接说明无需创建订单。
2. 目标身份是 `高级研究员` 或 `首席研究员` 时，先按上表映射组合商品 id。
3. 然后复用 `reference/allocation-and-orders.md` 中“创建合格订单”的流程：
   - 先把组合商品转成普通商品
   - 再创建订单
4. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/assign-researcher-identity.sh" \
  --user-id "69ce363b6159180001bf11db" \
  --identity "高级研究员"
```

### 输出规则

- 若目标是 `研究员`，明确说明没有创建订单。
- 若目标是 `高级研究员` 或 `首席研究员`，回报身份名称、映射出的组合商品 id、普通商品 id、订单结果摘要。
