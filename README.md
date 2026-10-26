# locust-skills

`locust-skills` 是面向 Locust Web UI 压测流程的 CLI 与 Cursor Skills 集合。它把接口定义读取、Locust 脚本生成、Web UI 压测触发、可选 VMP 监控采集和 Markdown 报告生成串成一条命令。

## 安装与使用

```bash
# 1. 安装当前项目
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

# 2. 复制配置并先改完，再执行后面的命令。字段见下方「使用前配置」
cp locust-skills-ui.example.yaml locust-skills-ui.yaml
cp locust-skills-ui.constraint.example.md locust-skills-ui.constraint.local.md

# 3. 使用 YApi 链接执行 Web UI 压测
locust-skills-ui run \
  --yapi-url "https://yapi.example.com/project/<project-id>/interface/api/<interface-id>" \
  --duration 20m \
  --users 200 \
  --spawn-rate 20 \
  --branch master \
  --tag "locust-20260722-164000" \
  --config locust-skills-ui.yaml

# 4. 或使用 cURL 文件执行 Web UI 压测
locust-skills-ui run \
  --curl-file requests.curl \
  --duration 20m \
  --users 200 \
  --spawn-rate 20 \
  --branch master \
  --tag "locust-20260722-164000" \
  --config locust-skills-ui.yaml
```

安装完成后，也可以在 Cursor 中输入 `/locust_skills_ui`，按项目内置 command 和 skill 执行同一套流程。Cursor 与 CLI 都读取同一份 `locust-skills-ui.yaml`，使用前先改完配置。

## 使用前配置

第一次压测前，把示例复制成下面两个本地文件并填写。它们已在 `.gitignore` 中，只留在本机。

```bash
cp locust-skills-ui.example.yaml locust-skills-ui.yaml
cp locust-skills-ui.constraint.example.md locust-skills-ui.constraint.local.md
```

默认读取仓库根目录的 `locust-skills-ui.yaml`。换路径时设置 `LOCUST_SKILLS_UI_CONFIG`。

### 凭证

同一项同时存在时，环境变量优先，否则读取配置字段。

| 用途 | 环境变量 | 配置字段 |
| --- | --- | --- |
| YApi Token | `YAPI_GLOBAL_TOKEN` | `yapi.token` |
| YApi 站点 | `YAPI_BASE_URL` | `yapi.base_url` |
| YApi MCP | `YAPI_COMMON_MCP_URL` | `yapi.mcp_url` |
| 火山引擎 Access Key | `VOLCENGINE_ACCESS_KEY` | `volcengine.access_key` |
| 火山引擎 Secret Key | `VOLCENGINE_SECRET_KEY` | `volcengine.secret_key` |
| 火山引擎地域 | `VOLCENGINE_REGION` | `vmp.region` |

```bash
export YAPI_GLOBAL_TOKEN="<yapi-token>"
export YAPI_BASE_URL="https://yapi.example.com"
export YAPI_COMMON_MCP_URL="http://yapi-mcp.example/mcp"
export VOLCENGINE_ACCESS_KEY="<access-key>"
export VOLCENGINE_SECRET_KEY="<secret-key>"
export VOLCENGINE_REGION="cn-beijing"
```

用环境变量提供凭证时，把 `locust-skills-ui.yaml` 里对应字段留空。

### 需要提前填写的地址

| 配置字段 | 何时需要 |
| --- | --- |
| `locust.web_url` | 打开 Locust Web UI |
| `service.host_suffix` | 由服务名拼被压测 `host`，示例为 `.internal` |
| `gitlab.project_url` | 推送 `locustfile.py` |
| `gitlab.remote_name` | Git 远程名，默认 `origin` |
| `feishu.report_folder_url` | 上传压测报告的飞书目录 |
| `feishu.report_folder_token` | 同上，目录 token |
| `vmp.stage_workspace_id` | 查预发布容器指标 |
| `vmp.cloud_workspace_id` | 查 Redis / PG 云指标 |
| `vmp.preprod_cluster` | 容器 PromQL 的集群 |
| `vmp.namespace` | 容器 PromQL 的命名空间 |
| `vmp.project_name` | 云指标的 `ProjectName`，默认 `stage` |
| `vmp.metrics_mcp_url` | 应用侧指标 MCP，可空 |
| `ops.*` | 造数脚本的接口地址，不用造数可留空 |

`vmp.workspace_id` 保留给 CLI 监控插件。Cursor 技能查容器用 `vmp.stage_workspace_id`，查 Redis / PG 用 `vmp.cloud_workspace_id`。

监控对照表写在 `constraint.file` 指向的文件，默认是 `locust-skills-ui.constraint.local.md`。按 `locust-skills-ui.constraint.example.md` 的表头，填入真实的容器服务、Redis、PG 实例名和实例 ID。表里没有的服务不要手写猜测 ID。

造数脚本在对应环境变量为空时，会调用 `skills/locust-skills-ui/scripts/read_config_value.py` 读取 `ops.*`。例如 `BATCH_REGISTER_URL` 为空时读取 `ops.batch_register_url`。

## Cursor 命令

当前项目内置 Cursor command：

```text
.cursor/
└── commands/
    └── locust_skills_ui.md
```

在 Cursor 对话框中输入 `/locust_skills_ui`，并附带接口来源（`yapi_links` 与 `curl_file` 二选一）及可选压测参数。命令会读取：

- `.cursor/commands/locust_skills_ui.md`
- `skills/locust-skills-ui/SKILL.md`

使用 YApi 链接：

```text
/locust_skills_ui
YApi: https://yapi.example.com/project/<project-id>/interface/api/<interface-id>
分支 master，users=200，spawn-rate=20，跑 20m
```

使用 cURL 文件：

```text
/locust_skills_ui
curl 文件：./requests.curl
分支 master，users=200，spawn-rate=20，跑 20m
```

阶梯压测（多轮）：

```text
/locust_skills_ui
YApi: https://yapi.example.com/project/<project-id>/interface/api/<interface-id>
users=[200, 300, 500]，spawn-rate=20，每轮 20m
```

常用对话参数（对应 `skills/locust-skills-ui/SKILL.md` 的 `context_schema`）：

| 对话参数 | 字段 | 说明 |
| --- | --- | --- |
| YApi 链接 | `yapi_links` | 与 `curl_file` 二选一 |
| curl 文件路径 | `curl_file` | 同 host 的一条或多条 cURL |
| 分支 | `gitlab_branch` | GitLab 交付分支 |
| users / 阶梯列表 | `locust_users` | 未传默认单轮 `200`；可传 `[200, 300, 500]`；先归一为 `users_list` |
| spawn-rate / Ramp up | `locust_spawn_rate` | 未传默认 `20` |
| 时长 / 每轮时长 | `locust_run_time` | 未传默认 `20m` |
| 轮间冷却 | `locust_cooldown` | 可选；仅多轮有意义 |

未传 `users` 时默认单轮 `200`，不会自动变成 `200/300/500`。Web UI、GitLab、飞书目录、VMP 与造数地址都从仓库根目录 `locust-skills-ui.yaml` 读取（由 `locust-skills-ui.example.yaml` 复制，该文件不提交）。

## CLI 命令

### `locust-skills-ui run`

`locust-skills-ui run` 是 Web UI 全流程入口。`--yapi-url` 与 `--curl-file` 必须二选一。

```bash
locust-skills-ui run \
  --yapi-url "https://yapi.example.com/project/<project-id>/interface/api/<interface-id>" \
  --config locust-skills-ui.yaml
```

```bash
locust-skills-ui run \
  --curl-file requests.curl \
  --config locust-skills-ui.yaml
```

常用选项：

| 选项 | 说明 |
| --- | --- |
| `--yapi-url` | YApi 接口链接，与 `--curl-file` 二选一 |
| `--curl-file` | 包含一条或多条同 host cURL 命令的文件 |
| `--duration` | 单轮压测持续时间，默认 `20m` |
| `--users` | Locust Web UI 的 Number of users，默认 `200` |
| `--spawn-rate` | Locust Web UI 的 Ramp up，默认 `20` |
| `--branch` | GitLab 交付分支 |
| `--tag` | Git Tag 名称 |
| `--config` | Web UI 流程配置文件 |
| `--monitoring-plugin` | 可选监控插件入口名，例如 `vmp` |

### 查看帮助

```bash
locust-skills-ui --help
locust-skills-ui run --help
```

## 执行流程

`locust-skills-ui run` 的执行顺序：

1. 生成 `rag_context` 和 `locustfile.py`。
2. 按 `locust-skills-ui.yaml` 等待部署完成，并检查 Locust Web API。
3. 按 `--users`、`--spawn-rate`、`--duration` 启动并停止压测。
4. 下载 Locust Web UI 报告与统计 JSON。
5. 如果启用监控插件，采集同一时间窗口的 VMP 监控。
6. 生成 Markdown 压测报告。

默认产物：

```text
reports/locust_ui_report.html
reports/locust_ui_stats.json
reports/vmp_context.json
reports/load_test_report.md
```

## 包含的 Skills

| Skill | 用途 |
| --- | --- |
| `locust-skills-ui` | Web UI 全流程编排 |
| `yapi-rag` | 读取 YApi 接口详情并生成 `rag_context` |
| `generator-locust` | 生成 Locust 2.45.0 脚本 |
| `playwright-cli` | 操作 Locust Web UI |
| `vmp-monitoring` | 采集 VMP 监控上下文 |
| `generator-report` | 生成 Markdown 压测报告 |

## 打包与验证

本项目可直接打包为 CLI：

```bash
python -m build
```

本地安装构建产物：

```bash
python -m pip install --force-reinstall --no-deps dist/locust_skills-0.1.0-py3-none-any.whl
```

检查命令入口：

```bash
locust-skills-ui --help
locust-skills-ui run --help
```

运行测试：

```bash
python -m pytest
```

升级本地代码后重新安装：

```bash
python -m pip install --upgrade -e .
```

## 项目结构

```text
.
├── .cursor/commands/locust_skills_ui.md  # Cursor 斜杠命令
├── src/locust_skills_ui/                 # Web UI 全流程 CLI
├── skills/locust-skills-ui/              # Web UI 压测 Skill
├── tests/                                # 自动化测试
├── pyproject.toml                        # Python 包和 CLI 入口配置
└── README.md
```

## 迁移与更新

如果只需要更新本项目的 CLI 和 Skills，重新安装即可：

```bash
python -m pip install --upgrade -e .
```

如果要刷新 Cursor 命令内容，检查并更新：

```text
.cursor/commands/locust_skills_ui.md
skills/locust-skills-ui/SKILL.md
```

## 常见问题

### 命令不存在

确认已经激活安装项目时使用的虚拟环境，并重新执行：

```bash
python -m pip install -e .
```

### 生成脚本后无法请求目标服务

自动推断的 `host` 仅作为初始值。压测前应检查 `locustfile.py`、Locust Web UI 中填写的 Host，以及目标预发布环境是否可访问。

### VMP 数据缺失

VMP 失败不会丢弃 Locust 结果，最终报告会标记监控数据缺失。请检查 `VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`（或 `volcengine.access_key`、`volcengine.secret_key`）、`vmp.stage_workspace_id`、`vmp.cloud_workspace_id`、时间窗口和服务名是否已写入 `locust-skills-ui.yaml`。

## 安全注意事项

- 不要在代码、README、`rag_context`、Locust 脚本或报告中提交 Access Key、Secret Key、Token、Cookie 等凭证。
- 测试数据不得使用真实手机号、身份证、地址等个人敏感信息。
- 压测只应针对已授权的测试或预发布环境，禁止直接对生产环境执行。
- 对外分享报告前，应对用户标识、设备标识和业务敏感字段做脱敏处理。
