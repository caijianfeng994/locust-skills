---
name: ops-assistant
description: Handle common business operations in this workspace, including batch user registration, schoolYear updates, 历史大会员补发, AB实验写组, 用户服务期指定, 研究员身份分配, 合格订单创建, 课程商品创建, and 商品类目查询造数. Use when the user mentions 用户注册, 年级, schoolYear, bigvip, 实验组, abCode, 服务期, 业务方, 研究员, 创建订单, 组合商品, 创建课程商品, 商品上架, 商品审核, 商品类目, or skuGoodKind.
---

# 运营操作助手

## 用途

这是项目内的统一入口 skill，用来处理用户运营、身份分配、服务期分配、订单创建和课程商品创建。

默认先识别用户意图，再只读取一个最相关的参考文档继续执行；如果同一请求同时包含多个任务，则按依赖顺序逐个完成。

## 执行原则

1. 先识别任务类型，再读取对应的参考文档：
   - `reference/account-and-profile.md`
   - `reference/identity-and-experiment.md`
   - `reference/allocation-and-orders.md`
   - `reference/course-product.md`
   - `reference/sku-good-kind.md`
2. 已有 helper script 的任务优先使用脚本直接执行。
   - 在 API Agent 中优先使用工具：`preview_ops_test_data_plan`、`prepare_ops_test_data`、`prepare_endpoint_test_data`。
3. 用户明确只要命令、`curl`、JSON payload 时，只返回文本，不直接执行。
4. 必要输入已经齐全时，默认直接执行，不做二次确认。
5. 请求体字段名必须保持与接口约定一致，不擅自改名。
6. 执行失败时，明确说明失败步骤、关键错误和可复用的重试命令。
7. 如果用户目标是创建课程商品，Agent 必须自行完成接口调用，不把脚本或 `curl` 转交给用户执行。

## 路由规则

### 账户与资料

出现以下意图时，读取 `reference/account-and-profile.md`：

- 批量注册测试用户
- 生成学生账号
- 更新 `schoolYear`
- 修改年级

### 身份与实验

出现以下意图时，读取 `reference/identity-and-experiment.md`：

- 补发历史大会员
- 写入 AB 实验组
- 指定 `研究员`、`高级研究员`、`首席研究员`

### 服务期与订单

出现以下意图时，读取 `reference/allocation-and-orders.md`：

- 指定用户服务期
- 按业务方分配服务团队
- 创建合格订单
- 通过组合商品、商品分组、二级类目、三级类目创建订单

### 课程商品

出现以下意图时，读取 `reference/course-product.md`：

- 创建课程商品
- 创建课程类组合商品
- 商品上架
- 商品审核

### 商品类目

出现以下意图时，读取 `reference/sku-good-kind.md`：

- 获取商品类目列表
- 商品类目造数
- `skuGoodKind/list`
- `skuGoodKind`

## 快速判断

- 用户只给了 `userId` + `schoolYear`，直接走“更新年级”。
- 用户只给了 `userId` + `teamId` 或业务方，直接走“指定服务期”。
- 用户给了 `userId` + `identity`，直接走“研究员身份分配”。
- 用户给了 `comboGoodId`、`groupList`、`goodKindIdLevel2List`、`goodKindIdLevel3List` 之一，直接走“创建合格订单”。
- 用户描述的是课程商品属性、金额、SKU、上架、审核，直接走“课程商品”。
- 用户描述 `skuGoodKind` 或商品类目列表，直接走“商品类目”并确保 `limit` 必传。

## 输出要求

- 默认回报关键入参、解析结果、核心接口结果。
- 对于带默认值的任务，要说明哪些值是默认补齐的。
- 对于多步任务，要说明每一步的关键产物，例如 `familyId`、组合商品 id、普通商品 id、审核单 id。
