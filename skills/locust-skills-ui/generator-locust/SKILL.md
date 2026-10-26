---
name: generator-locust
description: Use when 根据 YApi 接口链接、接口定义或 rag_context 生成 Locust 2.45.0 压测脚本，尤其是用户提到 Locust、压测脚本、YApi、yapi-rag、HttpUser、接口压测。
---

# Generator Locust Skill

## 目标

根据用户提供的 YApi 接口链接或 `rag_context`，生成可执行、可维护、符合 Locust 2.45.0 写法的 Python 压测脚本。生成时优先沿用用户选中的示例风格：`HttpUser` 类、类级别 `CycleDataProvider`、`on_start` 初始化、统一 `handle_response`、`@task` 方法、中文 `name` 分组。

**REQUIRED SUB-SKILL:** 使用 `yapi-rag` 读取 YApi 接口详情并产出结构化 `rag_context`。

## 触发条件

- 用户提供 YApi 链接，如 `https://yapi.example.com/project/<projectId>/interface/api/<interfaceId>`。
- 用户要求“根据 YApi 生成 Locust 脚本”“生成压测脚本”“补充 Locust skill”。
- 用户已有 `rag_context`，要求转成 Locust `HttpUser` 脚本。
- 用户选中示例脚本并要求按该示例生成。

## 工作流程

1. 提取用户输入中的 YApi 接口链接、目标环境域名、压测数据文件、鉴权字段和脚本命名要求。
2. 调用 `yapi-rag`：按其 MCP 调用规则读取接口详情，得到 `rag_context.interfaces[]`。
3. 校验 `rag_context.fetch_status`：
   - `success`：继续生成脚本。
   - `partial`：仅为成功接口生成任务，并在脚本注释中标记失败接口。
   - `failed`：不要编造接口字段，向用户说明缺失信息或生成仅含 TODO 的骨架。
4. 根据 `method`、`path`、`request`、`locust_hints` 映射 Locust 请求。
5. 按“脚本结构规范”和“示例风格”输出完整 Python 代码。
6. 给出脚本校验命令、必需的 `config/*.csv` 数据文件说明，以及后续 GitLab/Web UI 流程提示。

## 本目录生成器脚本

本技能目录提供 `generate_locustfile_from_rag.py`，用于把 `yapi-rag` 产出的 `rag_context.json` 转成完整 `locustfile.py`：

```bash
python .cursor/skills/locust-skills-ui/generator-locust/generate_locustfile_from_rag.py \
  --rag-context reports/rag_context.json \
  --output locustfile.py
```

生成器会：

- 从 `rag_context.interfaces[]` 读取接口名称、`method`、`path`、请求参数、Header 和 Body 字段。
- 从第一个有效接口的 `path` 第一段推导 `host`，例如 `/go-revenue/...` → `http://<service>${service.host_suffix}`。
- 为每个有效接口生成一个 `@task`，请求包含 `catch_response=True` 和稳定 `name`。
- 跳过读取失败、缺少 `method` 或缺少 `path` 的接口，并在生成文件顶部写入跳过原因。
- 生成整文件版本的 `locustfile.py`；如果输出目录已存在 `locustfile.py`，必须先将旧文件重命名为 `locustfile_<时间戳>.py`，再创建新的 `locustfile.py`，禁止直接覆盖。

生成后必须执行：

```bash
python -m py_compile locustfile.py
```

## YApi 到 Locust 映射

| YApi / `rag_context` 字段 | Locust 生成规则 |
| --- | --- |
| `interface_name` | 作为请求 `name`，中文名称优先 |
| `method` | 映射为 `self.client.get/post/put/delete/patch` |
| `path` | 作为相对 `url`，不要拼接 `host`；同时可用于推导运行命令的 `--host` |
| `query_params` | 生成 `params = {...}` |
| `body_fields` | `POST/PUT/PATCH` 默认生成 `json = {...}`；仅表单接口使用 `data = {...}` |
| `headers` | 生成 `header = {...}`，保留 `Content-Type`、`uid`、`token`、`client-version` 等 |
| `required_fields` | 必填字段必须有可用默认值、固定数据提供者或 TODO |
| `randomizable_fields` | 仅 `userId`、`goodGroupId` 使用固定 CSV 参数化，其他字段不得自行扩展 |
| `assertion_fields` | 在 `handle_response` 或任务内补充业务断言 |

## 脚本结构规范

生成的脚本应包含：

- 必要 import：`from locust import HttpUser, task`，需要限流等待时加 `import gevent`；存在固定参数字段时生成 `CsvDataProvider`，并导入 `csv`、`queue` 和 `StopUser`。
- 一个业务语义清晰的 `HttpUser` 子类，类名使用接口分组或业务名的拼音/英文。
- `host` 使用用户指定值；未提供时从 YApi MCP 返回的 `path` 第一段推断服务名，并生成 `http://<service>${service.host_suffix}`。例如 `path` 为 `/go-revenue/activity/2026-summer-promotion/info` 时，服务名为 `go-revenue`，`host` 和运行命令 `--host` 都使用 `http://<service>${service.host_suffix}`；无法推断则写 TODO。
- 连接配置：`connection_timeout`、`network_timeout`、`max_retries`、`max_redirects`、`insecure`。
- 类级别数据提供者：仅识别 `userId` 和 `goodGroupId`，分别使用独立队列。
- `load_test_data()`：类级别只加载一次数据。
- `on_start()`：为每个虚拟用户绑定数据。
- `handle_response()`：统一 JSON 解析、HTTP 状态码、429 限流、业务断言与 `res.success()/res.failure()`。
- 每个接口一个 `@task` 方法；方法名使用英文/拼音 snake_case。
- 请求必须使用 `catch_response=True`，动态 URL 用 `name` 聚合统计。

## 固定参数化规则

- 识别到 `userId` 时加载 `./config/userId.csv`，绑定为 `self.userId`。
- 识别到 `goodGroupId` 时加载 `./config/goodGroupId.csv`，绑定为 `self.goodGroupId`。
- 同时存在两个字段时使用两个独立队列，不合并 CSV。
- 其他字段保留 YApi 或 cURL 中的原始值，不增加随机值、CSV 路径或 CLI 参数。
- 所有生成脚本都必须包含 `load_test_data()` 和 `on_start()`；没有固定参数字段时只执行一次初始化，不读取 CSV。
- CSV 每行读取第一列，允许首行为与文件名一致的表头，例如 `userId` 或 `goodGroupId`。
- 数据队列为空时输出“数据队列为空...”并抛出 `StopUser`，禁止使用未初始化字段继续请求。

## 示例风格

生成脚本时参考以下形态，不要逐字复制示例中的真实手机号、地址、订单号等敏感数据：

```python
import queue

from locust import HttpUser, task
from locust.exception import StopUser
import gevent

# 生成脚本会包含 CsvDataProvider 的最小实现。


class SummerPromotionUser(HttpUser):
    host = "http://<service>${service.host_suffix}"

    connection_timeout = 5.0
    network_timeout = 5.0
    max_retries = 1
    max_redirects = 5
    insecure = False

    queue_user_id = CsvDataProvider()
    _data_loaded = False

    @classmethod
    def load_test_data(cls):
        if not cls._data_loaded:
            cls.queue_user_id.load_from_file("./config/userId.csv")
            cls._data_loaded = True
            print("测试数据加载完成")

    def on_start(self):
        self.load_test_data()
        try:
            self.userId = self.queue_user_id.get()
        except queue.Empty:
            print("数据队列为空...")
            raise StopUser()

    def handle_response(self, res, assertion=None):
        try:
            resp = res.json()
        except Exception:
            resp = res.text

        if res.status_code == 429:
            gevent.sleep(1)
            res.failure(f"请求被限流（429），响应: {resp}")
        elif res.status_code >= 400:
            res.failure(f"请求失败，状态码: {res.status_code}，请求url:{res.url}, 响应: {resp}")
        elif assertion and not assertion(resp):
            res.failure(f"业务断言失败，响应: {resp}")
        else:
            res.success()

    @task
    def interface_task_name(self):
        url = "/api/path/from/yapi"
        params = {"example": "value"}
        header = {"Content-Type": "application/json", "userId": self.userId}

        with self.client.get(url, params=params, name="接口中文名称", catch_response=True, headers=header) as res:
            self.handle_response(res)
```

## 生成要求

- 不要编造 YApi 未返回的必填字段；除 `userId`、`goodGroupId` 外，缺失时用 `TODO` 注释标出。
- 不要硬编码真实手机号、身份证、收货地址、Token、Cookie；使用测试数据文件、环境变量或脱敏占位值。
- `GET/DELETE` 参数优先放 `params`；`POST/PUT/PATCH` 的 JSON 请求体放 `json`，查询参数仍放 `params`。
- 未显式指定目标环境域名时，必须从 YApi MCP 返回的 `path` 第一段提取服务名，按 `http://<service>${service.host_suffix}` 生成 `host` 与 `--host`，不要使用泛化占位值。
- 同一接口有路径参数时，先在 `url` 中格式化路径，再通过 `name` 使用归一化名称聚合统计。
- 如果接口依赖登录、签名、前置订单或业务状态，在脚本顶部注释“前置条件”，并在 `on_start()` 或数据文件说明中体现。
- 如果生成多个接口任务，按业务链路顺序排列；无链路关系时按 YApi 链接顺序排列。
- 中文说明、注释和请求 `name` 使用中文；Python 标识符、参数名、URL、Header key 保持原文。

## 输出格式

回复用户时按以下顺序输出：

1. 简要说明已使用 `yapi-rag` 的接口信息来源和成功/失败状态。
2. 给出完整 Locust 脚本代码块。
3. 列出需要准备的配置文件，如 `./config/userId1000.csv`。
4. 给出脚本校验和 Web UI 后续流程：

```bash
python -m py_compile locustfile.py
```

脚本校验通过后进入 GitLab 推送和 Web UI 初始化流程。Web UI 并发以主技能 `locust_users` 归一化后的 `users_list` 为准：未传默认单轮 `200`，传入单值或列表则按传入执行；Ramp up 默认 `20`、每轮持续默认 `20m`，均可被 `locust_spawn_rate` / `locust_run_time` 覆盖。

## 自检清单

- [ ] 已读取 YApi 接口详情或明确说明读取失败原因。
- [ ] `method`、`path`、请求参数、Header 与 YApi 一致。
- [ ] 未指定目标域名时，已从 YApi MCP 返回的 `path` 第一段推导 `host` 和运行命令 `--host`，例如 `/go-revenue/...` → `http://<service>${service.host_suffix}`。
- [ ] 每个请求都有 `catch_response=True` 和稳定的 `name`。
- [ ] `handle_response()` 能处理非 JSON 响应、429、4xx/5xx 和业务断言。
- [ ] 动态/敏感数据没有硬编码真实值。
- [ ] 生成脚本符合 Locust 2.45.0 `HttpUser`、`@task`、`client` 用法。
- [ ] 已给出 `python -m py_compile locustfile.py` 校验命令，并说明后续进入 GitLab/Web UI 流程。

LOCUST_LANGUAGE = "zh"