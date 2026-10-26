# API Reference for Course Product Creation

接口 1：查询 SKU；接口 2：创建组合商品；接口 3：立即上架；接口 4：获取审核列表；接口 5：审核通过。组装时先把 SKU 的 `list` 转成 `requiredItemList`，再拼成创建请求体。若用户说明了商品分组，则创建时一并写入 `groupList`；若用户未说明具体科目，则默认按 **初中数学同步课 1 年** 查 SKU，即 `shortName=初中数学`、`kind=vip`、`addTime=1 年毫秒值`。**创建成功后，默认继续执行上架和审核通过，直到组合商品变成已上架状态。**

---

## 接口 1：查询 SKU

**请求示例：**

```bash
curl --location --request GET '${ops.gateway_base_url}/backend/zlb/api/sku?shortName=初中数学&addTime=128563200000&kind=vip'
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| `shortName` | 当用户描述中有清晰学段+科目时：shortName = 学段+科目，如 `小学数学`、`初中数学`；若未说明具体科目，默认 `初中数学` |
| `addTime` | 时长，**单位毫秒**。换算方式：1 年 ≈ 12×31×24×60×60×1000；1 个月 ≈ 31×24×60×60×1000（1 月有 31 天）；若未说明具体科目且需要默认 SKU，则默认取 1 年 |
| `kind` | 同步课 `vip`；同步课到期型 `timingVip`；专项课 `specialCourse`；专项课到期型 `timingSpecialCourse`；周边 `derivativeProduct`；学案 `textbook`；平板 PAD `pad`；打印机 `printer`；硬件配件 `accessory`；电子试卷 `examPaper`；电子试卷到期型 `timingExamPaper`；洋葱服务暖暖 `selfService`；学习规划 `zhiYuan`；学习规划到期型 `timingZhiYuan`；洋葱服务care+ `insurance`；优惠券 `deduct`；研学 `research`；配件 `component`；助教 `studypartner`；助教到期型 `timingStudypartner`；虚拟平板 `virtualPad`。若未说明具体科目且需要默认 SKU，则默认取同步课 `vip`。 |

**注意**：① **任何到期型**商品在查询 SKU 时**不传 addTime**，获取到返回值后，根据 **name** 字段**过滤出包含 `0-144` 的那条记录**。② **时长型**商品在查询 SKU 时**传 addTime**。③ **若未说明具体科目**，默认按 **初中数学同步课 1 年** 查询，即默认 `shortName=初中数学`、`kind=vip`、`addTime=1 年毫秒值`。④ **若返回的 list 中无有效 SKU，则直接停止**，告知用户无法创建并说明原因。

**返回值结构（节选）：**

- `list`：JSON 数组，每项为 SKU 单品，含：
  - `id`：SKU 单品 ID（组装 requiredItemList 时必用）
  - `shortName`、`name`、`amount`、`stage`、`subject`、`addTime`、`courseType`、`kind` 等

```json
"list": [
  {
    "id": "6396d310ea1042b3af5a8f80",
    "name": "虚拟-VIP-初中-物理-48个月",
    "shortName": "初中物理同步课",
    "amount": 1952,
    "stage": "2",
    "subject": "2",
    "addTime": "128563200000",
    "courseType": "vip",
    "kind": "vip",
    ...
  }
]
```

---

## 接口 2：创建组合商品（AddSkuGood）

**请求：** `POST ${ops.gateway_base_url}/backend/zlb/api/v3/skuGood`（或 127.0.0.1:8000 等项目配置的 base）

**调用方式：** 请求体须内联传入（如 `curl -d '...'` 或管道），不得依赖写入 `req-*.json` 等固定路径再用 `-d @文件`。

**请求体示例：**

把 SKU 查询出的 `list` 转成 `requiredItemList`：每个 SKU 对应 `itemDetailList` 中的一条，字段：`id`、`skuType: 1`、`isGift`、`isJiagou`、`count`、`checkDelay`。**到期型**时二选一：用户指明**具体哪天到期** → 填 `endTime`（**上海时区**：该日 23:59:59 上海 = UTC 同日 15:59:59，即 `YYYY-MM-DDT15:59:59.000Z`）并**同时填 `endTimeType: 1`**（绝对时间）；用户指明**多少天到期** → 填 `endTimeAddDays`（天数，如 `100`）并**同时填 `endTimeType: 2`**（相对时间/天数）；否则接口报「到期时间类型必填」。再将 Phase 1 收集的配置填入对应字段。

```json
{
  "goodKindIdLevel3": "6791c2c2-bf39-4f53-93a7-d6b3f3c3da92",
  "goodType": "Duration",
  "name": "测试商品",
  "imageConfig": "",
  "note": "",
  "copyEffectAt": "",
  "groupList": ["26暑研学商品"],
  "amount": 1,
  "originalAmount": 1,
  "amountRange": { "min": "1.00", "max": "1.00" },
  "iosPayScene": "不支持",
  "requiredItemList": [
    {
      "itemDetailList": [
        {
          "id": "68d0fd23ce18c54a9e2ffc6b",
          "skuType": 1,
          "isGift": false,
          "isJiagou": false,
          "count": 1,
          "endTime": "",
          "checkDelay": null,
          "endTimeAddDays": 0
        }
      ]
    }
  ],
  "mandatoryItemList": [],
  "additionalItemList": [],
  "typeAfterSales": "DEFAULT",
  "isLimit": false,
  "buyLimit": 0,
  "isBusinessLimit": false,
  "saleLimitTypeList": [],
  "business": [],
  "typeUserAttributionLimit": "",
  "typeUserFeatureLimit": "FALSE",
  "isSaleLimit": false,
  "isGrayIndustryLimit": false,
  "isPhoneLimit": false,
  "isContinueApply": false,
  "createdBy": "c0b3cf05-4e5d-4556-b037-ecbb0c1d5886"
}
```

- **endTimeType**：到期型必填。`1` = 绝对时间（具体哪天），需填 **endTime**；`2` = 相对天数，与 **endTimeAddDays** 相关。
- **endTimeAddDays**：仅当用户选择**到期型**且指明**多少天到期**时使用，填天数（如 100），并**同时填 `endTimeType: 2`**。
- **endTime**：仅当用户选择**到期型**且指明**具体哪天到期**时使用。**时区**：到期日按 **上海时区（UTC+8）** 理解，即用户说「某日到期」= 该日 23:59:59 上海时间；请求体填 **UTC** 的 ISO 时间：上海 23:59:59 = UTC 同日 15:59:59，格式为 `YYYY-MM-DDT15:59:59.000Z`（例如用户说 2026-04-01 到期 → 填 `"2026-04-01T15:59:59.000Z"`）。并**同时填 `endTimeType: 1`**；二者按用户表述二选一，时长型可不填或填空。

**组装规则：**

1. 用接口 1 的 `list` 构建 `requiredItemList`：可一个分组一个对象，其 `itemDetailList` 为多个 SKU 的条目（每条含 `id`、`skuType: 1`、`isGift`、`isJiagou`、`count`、`checkDelay`；到期型且指明具体到期日时填 `endTime`（上海时区该日 23:59:59 → UTC `YYYY-MM-DDT15:59:59.000Z`）**及 `endTimeType: 1`**，指明多少天到期时填 `endTimeAddDays` **及 `endTimeType: 2`**）。
2. `mandatoryItemList`、`additionalItemList` 无则传 `[]`。
3. **groupList**：若用户说明了商品分组，则创建请求里必须带上该 `groupList`；未说明则传 `[]` 或沿用默认值。
4. **amount**：必须由用户说明；若用户给的是价格区间，如 `100 到 200`，则直接取中值 `150`，并同时填 `originalAmount`、`amountRange.min/max`。
5. **createdBy**、**goodKindIdLevel3**：用户未提供时使用默认值 — `createdBy` = `c0b3cf05-4e5d-4556-b037-ecbb0c1d5886`，`goodKindIdLevel3` = `6791c2c2-bf39-4f53-93a7-d6b3f3c3da92`；**business** 未提供时为 `[]`。
6. 其余字段（goodType、iosPayScene、buyLimit、typeUserAttributionLimit、typeUserFeatureLimit、typeAfterSales、isSaleLimit、isGrayIndustryLimit、isPhoneLimit 等）按 Phase 1 收集结果与 name 等填写；未提及时直接走默认值，无需逐项向用户确认。

---

## 接口 3：立即上架

**请求：** `PUT ${ops.gateway_base_url}/backend/zlb/api/v3/skuGood/shelve`

**请求体示例：**

```json
{
  "id": "eb74ab3b-d5bf-4f0b-aa97-777c2b965231",
  "updatedBy": "c0b3cf05-4e5d-4556-b037-ecbb0c1d5886",
  "isContinueApply": true
}
```

**规则：**

1. `id` 使用上一步创建成功返回的组合商品 id。
2. `updatedBy` 固定为 `c0b3cf05-4e5d-4556-b037-ecbb0c1d5886`。
3. `isContinueApply` 固定为 `true`。
4. 创建成功后默认立即执行这一步，无需额外征求用户确认。

---

## 接口 4：获取审核列表

**请求：** `POST ${ops.gateway_base_url}/backend/zlb/good/skuGood/review/list`

**请求体示例：**

```json
{}
```

**规则：**

1. 调用后遍历返回值，找到 `goodId` 等于创建出的组合商品 id 的那一条记录。
2. 一旦命中就停止继续过滤，并取该记录中的 `id` 作为审核单 id。
3. 如果审核列表里没有对应 `goodId`，则停止后续审核通过操作，并明确告知用户卡在审核列表匹配这一步。

---

## 接口 5：审核通过

**请求：** `PUT ${ops.gateway_base_url}/backend/zlb/good/skuGood/review/set`

**请求体示例：**

```json
{
  "id": "1140",
  "approvalName": "张丽宾",
  "approval": true
}
```

**规则：**

1. `id` 使用接口 4 返回并匹配到的审核单 id。
2. `approvalName` 固定为 `张丽宾`。
3. `approval` 固定为 `true`。
4. 接口 4 命中审核单后，默认立即执行这一步，无需额外征求用户确认。

---

## Proto 路径（项目内）

- ListSKU：`/Users/zhanglibin/myproject/good/api/sku/sku.proto`
- AddSkuGood：`/Users/zhanglibin/myproject/good/api/sku_good/sku_good.proto`
