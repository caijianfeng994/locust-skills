# 服务期与订单操作

本文件覆盖两个任务：

- 指定用户服务期
- 创建合格订单

## 1. 指定用户服务期

### 触发词

指定用户服务期、服务期、业务方、`teamId`、`applyFamilyPreSales`

### 必要输入

- `userId`
- `teamId` 或业务方名称

### 业务方映射

- `1` = `入校`
- `2` = `电销/网销`
- `3` = `奥德赛`
- `4` = `体验营`
- `5` = `新媒体视频`
- `6` = `研学`
- `7` = `本地化`
- `8` = `商业化-公域`
- `9` = `商业化-APP`
- `10` = `阿拉丁`

如果用户给的是业务方名称，先映射成 `teamId` 再继续。

### 默认接口

先查 `familyId`：

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/userAllocation/familyAllocation/findFamilyDetailsByFamilyMemberUserIds' \
--header 'x-md-global-refresh-cache: false' \
--header 'Content-Type: application/json' \
--data-raw '{
  "userIds": [
    "6a06f3eb87922400012b3dda"
  ]
}'
```

再提交服务期：

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/userAllocation/familyAllocation/applyFamilyPreSales' \
--header 'x-md-global-refresh-cache: false' \
--header 'Content-Type: application/json' \
--data-raw '{
  "teamId": 2,
  "familyId": "0fcd23b2-baf1-4cdd-9c1d-80e45f83909e",
  "noVerifyCalm": true
}'
```

### 执行规则

1. 先调用 `findFamilyDetailsByFamilyMemberUserIds`。
2. 从返回值里取 `list[0].family.id` 作为 `familyId`。
3. 若未取到 `familyId`，立即停止，不执行第二步。
4. 调用 `applyFamilyPreSales` 时保持字段名为 `teamId`、`familyId`、`noVerifyCalm`。
5. `noVerifyCalm` 默认固定为 `true`。
6. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/assign-user-service-period.sh" \
  --user-id "6a06f3eb87922400012b3dda" \
  --team-name "电销/网销"
```

### 输出规则

- 回报 `userId`、业务方名称、`teamId`、`familyId` 和接口结果摘要。

## 2. 创建合格订单

### 触发词

创建订单、普通商品、组合商品、`comboGoodId`、`groupList`、`goodKindIdLevel2List`、`goodKindIdLevel3List`、`skuGood/normal`、`skuGood/list`

### 必要输入

- `userId`
- 以下四类条件中恰好一种：
  - `comboGoodId`
  - `groupList`
  - `goodKindIdLevel2List`
  - `goodKindIdLevel3List`

可选输入：

- `paidTime`

### 默认值

- `paymentCredentials.channel`: `微信`
- `creationWay.os`: `other`
- `creationWay.productId`: `428`
- `creationWay.channel`: `xiaohongshu`
- `creationWay.platform`: `h5`
- `paymentPlatform`: `xiaohongshu`
- `extra.sellfrom`: `xinmeiti_xiaohongshu`
- `extra.publicsellfrom`: `xinmeiti_xiaohongshu`

### 默认接口

组合商品转普通商品：

```bash
curl --location --request POST ${ops.gateway_base_url}/backend/zlb/api/v3/skuGood/normal' \
--header 'Content-Type: application/json' \
--data-raw '{
  "id": "78e3b52b-546b-4b2e-a361-d6ff45c4c627"
}'
```

创建订单：

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/order' \
--header 'Content-Type: application/json' \
--data-raw '{
  "userId": "69ce363b6159180001bf11db",
  "goodId": "69ce1f54ed23580c2b16035d",
  "paymentCredentials": {
    "orderId": "P781663258714023511",
    "channel": "微信",
    "paidTime": "2026-04-03 12:29:00"
  },
  "creationWay": {
    "os": "other",
    "productId": "428",
    "channel": "xiaohongshu",
    "platform": "h5",
    "shopId": "",
    "shopName": ""
  },
  "address": {},
  "paymentPlatform": "xiaohongshu",
  "extra": {
    "sellfrom": "xinmeiti_xiaohongshu",
    "publicsellfrom": "xinmeiti_xiaohongshu"
  }
}'
```

### 执行规则

1. 如果用户给了 `comboGoodId`，直接使用该组合商品 id。
2. 如果用户给了 `groupList`、`goodKindIdLevel2List` 或 `goodKindIdLevel3List`，先查询 `skuGood/list`，优先选第一个已发布且可用的组合商品。
3. 选定组合商品后，调用 `skuGood/normal` 获取普通商品 id。
4. 若某个候选组合商品转普通商品失败，自动尝试同一列表中的下一个候选。
5. 再调用 `go-order` 创建订单。
6. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/create-qualified-order.sh" \
  --user-id "69ce363b6159180001bf11db" \
  --combo-good-id "78e3b52b-546b-4b2e-a361-d6ff45c4c627"
```

### 输出规则

- 回报组合商品 id、普通商品 id、`userId`、`paidTime` 和订单结果摘要。
- 如果是通过分组或类目命中的，要说明是否跳过了不可用候选。
