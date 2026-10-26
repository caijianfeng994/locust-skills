---
name: yapi-rag
description: Use when Locust 压测链路需要从用户输入的 YApi 接口链接读取接口定义，并生成压测脚本所需的接口 RAG 上下文。
---

# YApi RAG Skill

## 目标

根据用户输入中的 YApi 接口链接，读取接口详情并输出结构化 `rag_context`，供 `generator-locust` 使用。

优先使用 Cursor 已注入的 YApi MCP；若当前会话没有 `get_interface_detail`，**必须**降级执行本技能目录下的脚本代理，禁止只报「yapi-mcp 不可用」后停止。

## 触发条件

- 用户输入包含 YApi 接口链接，如 `/project/.../interface/api/...`
- 用户明确要求“根据 YApi 接口生成 Locust 脚本”“读取 YApi 接口信息”“从 YApi 获取接口定义”
- 上游节点已识别出 `source_type=yapi_doc` 或传入 `yapi_context`

## 目录结构

```text
yapi-rag/
├── SKILL.md
├── yapi_mcp_tools.py              # MultiServerMCPClient 连接封装
└── scripts/
    └── fetch_interface.py         # CLI：拉取接口并输出 rag_context JSON
```

## 链接识别

从用户输入中提取所有 YApi 接口链接，保持原始顺序：

- 完整 URL：`http(s)://.../project/<projectId>/interface/api/<interfaceId>`
- 相对路径：`/project/<projectId>/interface/api/<interfaceId>`
- 若只有接口 ID，可作为降级参数传给 `interfaceId` / `interface_id`

多链接场景逐个读取，单个失败不得中断其他接口处理。

## 执行方式（强制）

按顺序尝试，命中即停：

### 1) Cursor 已注入 YApi MCP

1. 优先调用 `get_interface_detail`，参数首选 `{"interfaceURL": "<YApi链接>"}`。
2. schema 不兼容时依次尝试 `link` / `url` / `interfaceId` / `interface_id`。
3. 链接直查不优先使用 `search_interface`；仅当用户只给接口名/关键字时才先搜索再读详情。
4. 将返回值归一化为下方 `rag_context` 契约。

### 2) 脚本代理（本地未注入 MCP 时必走）

在项目根目录执行（路径相对仓库根）：

```bash
python .cursor/skills/locust-skills-ui/yapi-rag/scripts/fetch_interface.py \
  --url "<YApi链接1>" \
  --url "<YApi链接2>" \
  --output reports/rag_context.json
```

仅关键字时：

```bash
python .cursor/skills/locust-skills-ui/yapi-rag/scripts/fetch_interface.py \
  --keyword "<接口名或关键字>" \
  --output reports/rag_context.json
```

脚本会连接 `yapi-common-mcp`，调用 `get_interface_detail`，并直接打印/写入规范化后的 `rag_context`。Agent 读取该 JSON 即可，不要把原始 MCP 返回值直接传给 `generator-locust`。

依赖：本机 Python 需可 import `langchain_mcp_adapters`（与 `locust-skills` 依赖一致）。

连接信息只从环境变量或仓库根目录 `locust-skills-ui.yaml` 的 `yapi` 段读取，脚本内不写死地址或 token：

| 变量 | 配置键 | 说明 |
| --- | --- | --- |
| `YAPI_COMMON_MCP_URL` | `yapi.mcp_url` | MCP HTTP 地址 |
| `YAPI_BASE_URL` | `yapi.base_url` | 请求头 `x-yapi-base-url` |
| `YAPI_GLOBAL_TOKEN` | `yapi.token` | 请求头 `x-yapi-global-token`；优先环境变量 |

网络要求：本机须能访问 `YAPI_COMMON_MCP_URL`（通常需公司内网/VPN）。连不上时脚本会返回 `fetch_status=failed` 与明确 `fetch_error`。

### 3) 仍失败时

保留 `source_links` 与逐接口 `fetch_error`，顶层 `fetch_status=failed`，继续让主流程决定是否改用 `curl_file`；禁止静默编造接口字段。

## MCP 调用规则

1. 优先 `get_interface_detail`。
2. 首选参数 `{"interfaceURL": "<YApi链接>"}`。
3. schema 不兼容时依次尝试 `link` / `url` / `interfaceId` / `interface_id`。
4. 链接直查不优先 `search_interface`。
5. 仅无明确链接、只有名称/关键字时，才允许 `search_interface`。
6. 工具不可用、鉴权失败、链接无效或结构不可解析时，记录失败原因并输出降级 `rag_context`。

## 字段归一化

从 MCP / 脚本返回值中尽量提取以下信息，缺失字段保留为空数组或空字符串：

- 基础信息：接口名称、`method`、`path`、接口描述、项目 ID、接口 ID、标签/分组
- 请求信息：`path_params`、`query_params`、`headers`、`body_fields`、示例请求
- 响应信息：成功响应字段、错误响应字段、状态码、示例响应
- 压测信息：鉴权要求、必填参数、可随机化字段、适合断言的响应字段、潜在依赖接口

脚本 `fetch_interface.py` 已内置归一化；若走 Cursor 原生 MCP，Agent 必须按同一契约组装。

## 输出契约

```yaml
rag_context:
  source_type: yapi
  source_links: []
  interfaces:
    - source_link: ""
      interface_id: ""
      project_id: ""
      interface_name: ""
      method: ""
      path: ""
      description: ""
      tags: []
      request:
        path_params: []
        query_params: []
        headers: []
        body_fields: []
        examples: []
      response:
        success_fields: []
        error_fields: []
        status_codes: []
        examples: []
      locust_hints:
        auth_required: false
        required_fields: []
        randomizable_fields: []
        assertion_fields: []
        dependency_apis: []
      fetch_status: success | failed
      fetch_error: ""
  scenario_hints: []
  fetch_status: success | partial | failed
  fetch_error: ""
```

## Locust 生成提示

- `method` 与 `path` 是生成请求方法和 URL 的核心字段，缺失时必须在 `fetch_error` 中说明。
- `required_fields` 用于构造最小可用请求数据。
- `randomizable_fields` 用于生成参数化或随机化数据，避免所有虚拟用户使用同一请求体。
- `assertion_fields` 优先来自响应中的 `code`、`success`、`message`、业务 ID 等稳定字段。
- 若接口需要登录态、Token、Cookie 或签名，在 `locust_hints.auth_required` 标记为 `true`，并在 `scenario_hints` 说明依赖。

## 回退要求

- 任一接口读取失败时，该接口写入 `fetch_status=failed` 与 `fetch_error`。
- 部分接口成功时，顶层 `fetch_status=partial`。
- 全部接口失败时，顶层 `fetch_status=failed`，但仍保留 `source_links` 与失败原因。
- 禁止静默降级；后续生成 Locust 脚本时必须能识别哪些接口信息不可用。
- Cursor 未注入 YApi MCP 时，必须先跑 `scripts/fetch_interface.py`，不得直接判定链路失败。
