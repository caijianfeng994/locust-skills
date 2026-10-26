# 课程商品创建

本文件覆盖课程类商品的完整链路：

1. 查询 SKU
2. 创建组合商品
3. 立即上架
4. 获取审核列表
5. 审核通过

## 触发词

创建课程商品、课程类商品、生成商品、商品上架、商品审核

## 总原则

1. Agent 自行发起接口调用，不要求用户执行脚本或 `curl`。
2. 创建成功后默认继续完成上架和审核通过，不停在中间状态。
3. 请求体必须内联传入，不依赖 `req-*.json` 之类固定文件。
4. 只在必填信息缺失时追问；其余能默认的字段直接补齐。

## 首要校验

### 必须明确

- 商品金额 `amount`
- 商品类型

### 通常也必须明确

- `时长型` 还是 `到期型`
- 全科商品的具体时长或到期规则

### 可以默认补齐

- 若用户未说明具体科目，默认按 `初中数学同步课 1 年`
- `createdBy` 默认 `c0b3cf05-4e5d-4556-b037-ecbb0c1d5886`
- `goodKindIdLevel3` 默认 `6791c2c2-bf39-4f53-93a7-d6b3f3c3da92`
- 苹果支付、限购、B/C 端限制、指定用户限制、限售、灰产限制、手机号限制、售后方式、`business`、`groupList` 未提及时都走默认值

## SKU 查询规则

查询接口：

```bash
curl --location --request GET '${ops.gateway_base_url}/backend/zlb/api/sku?shortName=初中数学&addTime=128563200000&kind=vip'
```

规则：

- `shortName` 按学段+科目确定；缺科目时默认 `初中数学`
- 时长型必须传 `addTime`
- 到期型不传 `addTime`
- 到期型返回后，从 `list` 中优先过滤 `name` 含 `0-144` 的 SKU
- 若查不到有效 SKU，立即停止并说明原因

`kind` 映射的常见值：

- 同步课：`vip`
- 同步课到期型：`timingVip`
- 专项课：`specialCourse`
- 专项课到期型：`timingSpecialCourse`
- 电子试卷：`examPaper`
- 电子试卷到期型：`timingExamPaper`
- 洋葱服务暖暖：`selfService`
- 学习规划：`zhiYuan`
- 学习规划到期型：`timingZhiYuan`
- 洋葱服务care+：`insurance`
- 优惠券：`deduct`
- 研学：`research`
- 配件：`component`
- 助教：`studypartner`
- 助教到期型：`timingStudypartner`
- 周边：`derivativeProduct`
- 学案：`textbook`
- PAD：`pad`
- 打印机：`printer`
- 硬件配件：`accessory`
- 虚拟平板：`virtualPad`

## 创建商品规则

创建接口：

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/api/v3/skuGood' \
--header 'Content-Type: application/json' \
--data-raw '{...}'
```

组装规则：

1. 把 SKU 查询结果中的 `list` 转成 `requiredItemList`。
2. 时长型使用 `goodType="Duration"`。
3. 到期型使用 `goodType="Timing"`，并且二选一：
   - 给了具体到期日：填 `endTime`，同时填 `endTimeType: 1`
   - 给了多少天到期：填 `endTimeAddDays`，同时填 `endTimeType: 2`
4. 用户给了价格区间时，直接取中值作为 `amount`、`originalAmount`、`amountRange.min/max`。
5. 用户给了商品分组时，原样写入 `groupList`。

## 上架与审核规则

### 立即上架

接口：

```bash
curl --location --request PUT '${ops.gateway_base_url}/backend/zlb/api/v3/skuGood/shelve' \
--header 'Content-Type: application/json' \
--data-raw '{
  "id": "组合商品id",
  "updatedBy": "c0b3cf05-4e5d-4556-b037-ecbb0c1d5886",
  "isContinueApply": true
}'
```

### 查询审核列表

接口：

```bash
curl --location --request POST '${ops.gateway_base_url}/backend/zlb/good/skuGood/review/list' \
--header 'Content-Type: application/json' \
--data-raw '{}'
```

从结果里找到 `goodId == 组合商品id` 的那条记录，取其审核单 `id`。

### 审核通过

接口：

```bash
curl --location --request PUT '${ops.gateway_base_url}/backend/zlb/good/skuGood/review/set' \
--header 'Content-Type: application/json' \
--data-raw '{
  "id": "审核单id",
  "approvalName": "张丽宾",
  "approval": true
}'
```

## 输出规则

- 成功时回报：SKU 命中结果、组合商品 id、上架结果、审核单 id、最终审核结果。
- 失败时说明卡在哪一步，不把未完成状态说成成功。
- 若用户未给科目且用了默认 `初中数学同步课 1 年`，要明确说明这是默认值。

## 额外参考

更完整的接口字段说明见：

- `reference/course-product-api.md`
