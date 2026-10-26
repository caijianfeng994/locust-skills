---
name: locust-skills-ui
description: Use when 用户输入 /locust_skills_ui，或需要从 YApi 链接或 cURL 接口定义生成 Locust 2.45.0 压测脚本，并通过 GitLab 发布、Locust Web UI 与 Playwright 执行压测。环境地址从 locust-skills-ui.yaml 读取。
---

# Locust Web UI 压测主入口

## 目标

把用户需求中的 YApi 或 cURL 接口定义、Locust 压测脚本、GitLab 交付、普通 Locust Web UI 启动、阶梯压测触发、火山云 VMP 监控和压测报告串成一条可追踪流程。所有接口字段、压测数据和监控数据必须来自工具返回或用户上下文，不能随意编造。

用户输入 `/locust_skills_ui` 时，启动本技能。先收集接口来源、目标分支、被压测服务 host、并发数、启动速率和持续时间；已存在上下文时优先使用，不要反复询问。

本技能用于“GitLab 发布 + Web UI 操作”方式：生成脚本后推送 GitLab，部署成功后访问 Locust Web UI 地址：

```text
${locust.web_url}
```

## 运行上下文

智能体通过 `context_schema` 接收运行参数。已存在上下文时优先使用，不要反复询问用户。

| 字段 | 用途 |
| --- | --- |
| `yapi_links` | 用户需求中的 YApi 接口链接列表 |
| `curl_file` | 包含一条或多条同 host cURL 命令的文件路径；与 `yapi_links` 二选一 |
| `gitlab_project_path` | Locust 脚本要推送的 GitLab 项目 |
| `gitlab_branch` | 目标分支，默认按用户上下文 |
| `locust_file` | Locust 脚本路径，默认 `locustfile.py` |
| `locust_web_url` | Locust Web UI 地址，固定优先使用 `${locust.web_url}` |
| `locust_target_host` | 被压测服务的 host，启动压测时填入 Web UI |
| `locust_users` | Web UI 的 Number of users；未传默认 `200`（单轮）；可传单值或阶梯列表如 `[200, 300, 500]` |
| `locust_spawn_rate` | Web UI 的 Ramp up；未传默认 `20`；列表压测时各轮共用 |
| `locust_run_time` | 每轮持续时间；未传默认 `20m`；列表压测时各轮共用同一时长 |
| `locust_cooldown` | 轮间冷却（可选）；未传默认不冷却；仅 `users_list` 长度 > 1 时有意义 |
| `locust_enable_smoke` | 是否先运行 Web UI smoke 压测，默认 `true` |
| `locust_smoke_users` | smoke 并发数，固定默认 `1` |
| `locust_smoke_run_time` | smoke 持续时间，默认 `1m` |
| `locust_master_host` | worker 连接的 master Service，例如 `comm-locust-master` |
| `locust_expect_workers` | 期望启动的 worker 数，默认按部署上下文 |
| `locust_run_id` | 压测批次 ID，默认按执行时间生成；同一批次（含阶梯多轮）复用同一个 ID |
| `locust_report_dir` | 报告保存目录，默认当前项目 `reports/` |
| `locust_download_report_name` | 单轮下载文件名提示；实际落盘必须用 `locust_ui_{users}_report.html` |
| `load_test_report_path` | Markdown 性能压测报告路径；默认按 `{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md` 生成，落盘到 `reports/`。服务名优先取 `vmp_service_names[0]`，否则从压测脚本 `host` 提取（如 `good-order`）；时间戳用报告生成时刻本地时间。禁止固定覆盖 `load_test_report.md` |
| `feishu_report_folder_url` | 性能压测报告归档的飞书云盘目录，固定优先使用 `${feishu.report_folder_url}` |
| `feishu_report_folder_token` | 飞书云盘目录 token，默认 `${feishu.report_folder_token}` |
| `preprod_environment` | 预发布环境标识 |
| `vmp_workspace_id` | Redis / PG 用 `constraint/SKILL.md` 的 Name=`prod`（`${vmp.cloud_workspace_id}`）。容器用 Name=`stage`（`${vmp.stage_workspace_id}`）。都不是从 `host` 提取的服务名 |
| `vmp_service_names` | 需要查询的压测服务名；默认从压测脚本 `host` 提取，例如 `host = "http://<service>${service.host_suffix}"` → `good-order` |
| `vmp_constraint_targets` | VMP 查询约束，必须以 `constraint/SKILL.md` 为准：先从 `host` 推导服务名，Redis、PG 实例名称都写成 `bj-{服务名}`，再分别到资源表取实例 ID。例如 `order-plus` 的 Redis 是 `redis-cn02lygtazmc6ag7s`，PG 是 `postgres-b7e8f04eca78a5eb`。「容器服务」表已写出另一套名称时以该行为准；都没有时不臆造 |
| `enable_vmp_mcp` | 是否加载 `volcengine_mcp_tools.py` 中的 VMP MCP 工具 |

### `locust_users` 归一化（强制）

执行 Web UI 压测前，必须先把 `locust_users` 归一成数组 `users_list`，后续只按 `for users in users_list` 执行，单轮与多轮同一套逻辑：

| 输入 | `users_list` |
| --- | --- |
| 未传入 | `[200]` |
| `200` / `"200"` | `[200]` |
| `[200, 300, 500]` | `[200, 300, 500]` |

- 未传：默认**单轮** 200 用户、Ramp up `20`、持续 `20m`。
- 传入单值或列表：按传入执行；列表时按顺序逐轮，每轮持续 `locust_run_time`（未传则 `20m`）。
- **不要**在未传时擅自改成 `[200, 300, 500]`。

每轮产物命名（`{users}` 为当前并发）：

```text
reports/locust_ui_{users}_start_time.txt
reports/locust_ui_{users}_stop_time.txt
reports/locust_ui_{users}_metadata.txt
reports/locust_ui_{users}_report.html
```

## 标准流程

1. 接口来源二选一：提取 `yapi_links` 并使用 `yapi-rag` 调用 YApi MCP，或解析 `curl_file` 中同一 host 的多条 cURL；统一产出结构化 `rag_context`。解析 cURL 时只读取定义，不真实调用接口。
2. 使用 `generator-locust` 基于 `rag_context` 编写 Locust 2.45.0 脚本。脚本必须符合 `HttpUser`、`@task`、`catch_response=True` 和稳定 `name` 聚合规则。
3. `run` 生成并校验脚本后，直接推送 GitLab 到 `gitlab_project_path` / `gitlab_branch`。推送前必须确认不会提交密钥、Token、真实手机号、身份证、Cookie、临时文件或无关压测数据。
4. GitLab 推送成功后，优先使用 `playwright-cli` 操作 Locust Web UI：打开 `${locust.web_url}`，校验是否进入 Locust 初始化页面，并确认页面 Host 输入框显示的是 `locustfile.py` 中的 `host`。
5. 如果页面未初始化成功，或 Host 输入框显示的不是 `locustfile.py` 的 `host`，继续刷新页面并等待部署生效，直到页面初始化成功且 Host 显示正确；不要手动填写错误 Host 或提前开始压测。
6. 按「`locust_users` 归一化」得到 `users_list`。对每个 `users`：在 Web UI 填写 Number of users=`users`、Ramp up=`locust_spawn_rate`（未传 `20`），点击 `START`；立即写入 `reports/locust_ui_{users}_start_time.txt` 与 `metadata.txt`；持续 `locust_run_time`（未传 `20m`）后点击 `STOP`，写入 `stop_time.txt`；下载报告为 `reports/locust_ui_{users}_report.html`。下一轮前确认已 STOP；若配置了 `locust_cooldown` 则等待后再 START。
7. `users_list` 全部轮次结束后，校验每一档的 start/stop/report 产物齐全且非空。
8. 使用 `vmp-monitoring`：先读并遵循 `constraint/SKILL.md`；对 `users_list` 中每一档，用该档 start/stop 作为时间窗各查一次服务/Redis/PG，写入 `vmp_context.rounds[]`（禁止只用「首轮开始～末轮结束」一个大窗作为唯一结论依据）。
9. 使用 `generator-report`：汇总全部 Locust 轮次报告、时间记录与 `vmp_context.rounds`，生成**一份** `reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md`（单轮摘要一行；多轮按并发分节对比）。每次生成新文件，不覆盖本地已有报告。
10. 报告生成后使用飞书 CLI 将上述 Markdown 报告**新增**写入飞书云盘目录 `${feishu.report_folder_url}`；优先使用 `lark-cli`（`@larksuite/cli`），若存在 `feishu-cli` 别名也可；上传前先确认文件存在且非空。飞书侧只新增、不覆盖已有文档（禁止传 `--file-token`）；上传失败时保留本地报告并记录失败原因。

## 子 Skill 调用

- `yapi-rag`：只负责读取 YApi 接口详情并生成 `rag_context`。优先用已注入的 YApi MCP；若无注入则必须执行 `yapi-rag/scripts/fetch_interface.py` 脚本代理。读取失败时记录失败原因，不要补造字段。
- `generator-locust`：只负责把 `rag_context` 转为 Locust 2.45.0 脚本；本技能的运行方式以 GitLab 发布后的 Web UI 为准。
- `playwright-cli`：发布后 Web UI 压测的首选操作方式；负责打开页面、填写表单、点击 `START`/`STOP`、切换 `DOWNLOAD DATA` 并保存 `Download Report` 到 `reports/`。
- `vmp-monitoring`：只负责通过 VMP MCP 查询压测窗口内的服务、Redis、数据库监控，并输出 `vmp_context`；查询目标必须受 `constraint/SKILL.md` 约束，禁止绕过约束表自行指定 Redis/PG。
- `generator-report`：只负责基于本地 Locust 报告、时间记录和 `vmp_context` 生成专业压测报告，并将 Markdown 报告保存为 `reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md`。
- 飞书 CLI（优先 `lark-cli`，兼容 `feishu-cli` 别名）：只负责把已生成的带时间戳报告**新增**到指定飞书云盘目录（不覆盖已有同名或历史报告）；执行前按飞书 CLI 认证规则检查登录态和 Drive 权限，不要把临时报告、HTML 原始报告、VMP 原始 JSON 一并上传，除非用户明确要求。
- `ops-assistant`：只有在接口压测需要可靠业务数据造数时使用。

## GitLab 发布后 Web UI 初始化规范

脚本推送 GitLab 并触发部署后，必须打开：

```text
${locust.web_url}
```

Web UI 初始化检查：

- 页面可以打开且不是网关错误。
- 页面进入 Locust 初始化状态，可看到并发、启动速率和 Host 输入框。
- Host 输入框显示 `locustfile.py` 中的 `host`；如果不是，继续刷新页面等待部署生效。
- 不要手动填写错误 Host 或提前开始压测；`${locust.web_url}` 是 Web UI 地址，不是被压测服务地址。

## 发布后 Playwright UI 压测规范

发布到预发布环境后，本技能默认使用 `playwright-cli` 真实操作 Locust Web UI。执行前必须已读取 `playwright-cli` 子技能；如果 `playwright-cli` 不可用，再尝试 `npx --no-install playwright-cli`。

以下命令必须在当前项目根目录执行，确保时间记录和下载报告都保存到当前项目 `reports/`。

参数约定：

- Web UI：`${locust.web_url}`
- `users_list`：按「`locust_users` 归一化」；未传为 `[200]`，传入列表则按列表循环
- Ramp up：`locust_spawn_rate`（未传 `20`）
- 每轮持续：`locust_run_time`（未传 `20m`）
- 报告目录：当前项目 `reports/`
- 文件名中的 `{users}` / 下方 `USERS` 替换为当前轮并发

推荐流程：先打开页面并确认 Host，再对 `users_list` 中每个 `users` 执行一轮「填表 → START → 记时 → 等待 → STOP → 下载」。

```bash
mkdir -p reports
playwright-cli open "${locust.web_url}"
playwright-cli snapshot
```

单轮模板（将 `USERS` / `SPAWN` / `DURATION` 换成实际值；默认示例为未传参时的 200 / 20 / 20m）。若 `users_list` 有多项，对每个并发重复整段模板：

```bash
# USERS=200 SPAWN=20 DURATION=20m  （示例：未传 locust_users）
playwright-cli run-code "async page => {
  await page.getByLabel(/Number of users/i).fill('USERS');
  await page.getByLabel(/Ramp up/i).fill('SPAWN');
  await page.getByRole('button', { name: /^START$/i }).click();
}"

date '+%Y-%m-%d %H:%M:%S %Z' | tee reports/locust_ui_USERS_start_time.txt
printf 'web_url=${locust.web_url}\nusers=USERS\nramp_up=SPAWN\nduration=DURATION\n' > reports/locust_ui_USERS_metadata.txt
```

等待 `DURATION`（默认 `20m`）。等待期间不要刷新或关闭页面；只汇报进度，不要提前停止。结束后：

```bash
playwright-cli goto "${locust.web_url}"
playwright-cli run-code "async page => {
  await page.getByRole('button', { name: /^STOP$/i }).click();
}"
date '+%Y-%m-%d %H:%M:%S %Z' | tee reports/locust_ui_USERS_stop_time.txt
```

下载报告到当前项目 `reports/`：

```bash
playwright-cli run-code "async page => {
  await page.getByRole('link', { name: /DOWNLOAD DATA/i }).click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Download Report/i }).click();
  const download = await downloadPromise;
  await download.saveAs('reports/locust_ui_USERS_report.html');
  return download.suggestedFilename();
}"
```

若 `Download Report` 不是浏览器下载事件，改用：

```bash
curl -L "${locust.web_url}stats/report?theme=light" -o reports/locust_ui_USERS_report.html
```

每轮（及全部轮次）结束后必须确认：

- `reports/locust_ui_{users}_start_time.txt` / `stop_time.txt` / `report.html` 均存在且非空。
- start 与 stop 间隔约等于本轮 `locust_run_time`。
- 页面已 STOP；多轮时确认可再次填写并发并 START，再进入下一档。
- 阶梯示例：`locust_users=[200,300,500]` 时产物为 `locust_ui_200_*`、`locust_ui_300_*`、`locust_ui_500_*`。

如果 locator 失效，先执行 `playwright-cli snapshot`，根据 snapshot 中的 ref 完成同一流程。不要切换到接口调用方式，除非用户明确要求。

## VMP 监控采集规范

必须使用 `vmp-monitoring` 执行 VMP 监控采集。只允许使用查询类 VMP MCP 工具。执行 VMP 步骤前**必须先读取** `constraint/SKILL.md`，并以该文件为唯一默认目标来源；本主技能不写死 Redis/PG 实例 ID。

约束读取顺序（强制）：

1. 读取 `constraint/SKILL.md`。
2. 确认 workspace：Redis、PG 用 `constraint/SKILL.md` 的 Name=`prod`，Id=`${vmp.cloud_workspace_id}`。服务容器用 Name=`stage`，Id=`${vmp.stage_workspace_id}`，并带 `cluster="${vmp.preprod_cluster}"`。不要把服务名当 workspaceId。
3. 从当前压测脚本 `host` 提取服务名：去掉协议，取第一个域名段。例如：

```python
host = "http://<service>${service.host_suffix}"
```

提取为服务名 `good-order`。服务容器 PromQL 同时带预发布集群、命名空间和 Pod，例如 `cluster="${vmp.preprod_cluster}"`、`namespace="${vmp.namespace}"`、`pod=~"good-order-.*"`、`container="good-order"`。不要只按 namespace 汇总。

4. 用服务名取 Redis、PG 实例 ID。实例名称都写成 `bj-{服务名}`，分别到 `constraint/SKILL.md` 的「Redis 资源基础信息」「PG 资源基础信息」按实例名称精确匹配。
   - 示例：服务名 `order-plus` 的 Redis 是 `bj-order-plus` / `redis-cn02lygtazmc6ag7s`，PG 是 `bj-order-plus` / `postgres-b7e8f04eca78a5eb`。查询时 `Name` 和 `ResourceID` 只用这一对。
   - 「容器服务 ↔ Redis ↔ PG」里该服务已经写了另一套名称和 ID 时，以那一行为准。
   - 两张表都没有该实例：不查询对应依赖，写入 `empty_results` / `risks`，说明约束表未登记。禁止猜测实例 ID。
   - 命名空间只从「容器服务 ↔ Redis ↔ PG」读取。该表没有该服务时不编造命名空间。云指标不依赖命名空间。
5. 其他示例（仍以 constraint 表当前值为准）：`good-order` 的 Redis=`bj-good-order` / `redis-cnlfkgbb8gf6gcfla`，PG=`bj-revenue` / `rds-pg-hc1a58511fb760dc9`。`layer` 的 Redis=`bj-layer` / `redis-cnlffgzdo7azk53ez`，PG=`bj-layer` / `postgres-fe12859d181d`。

时间窗与输出（强制）：

- 对 `users_list` 每一档，用该档 `locust_ui_{users}_start_time.txt` / `stop_time.txt` 作为查询窗口；默认 `step=60s`。
- 单轮时 `vmp_context.rounds` 仅一项；多轮时每档一项。
- 禁止把多轮糊成「首轮开始～末轮结束」单一窗口作为唯一结论依据。
- `vmp_context` 必须记录：`workspace_id`、`workspace_name`、`service_names`、约束表采用的 Redis/PG、以及 `rounds[]`（含 `users`、`time_range`、各类 metrics）。

指标名或标签不确定时，先查元数据和 series，再写 PromQL；优先窄查询。若标签与实例 ID 不一致，记录实际标签与空结果原因，不要编造结论。

建议按压测窗口对齐查询：

- 服务：CPU、内存、QPS、错误率、P95/P99 延迟、实例数、重启数。
- Redis：CPU、内存、连接数、命中率、OPS、慢查询、网络 IO（仅当约束表有 Redis）。
- 数据库：CPU、内存、连接数、QPS/TPS、慢查询、锁等待、磁盘 IO（仅当约束表有 PG）。

查询结果为空时说明可能原因：指标不存在、标签不匹配、时间范围无数据、权限或凭证异常、约束表未登记。服务容器、Redis 云指标、PG 云指标都用 `mcp_server_vmp` 的 `query_range_metrics`。容器的 `workspaceId` 为 `${vmp.stage_workspace_id}`，并带 `cluster="${vmp.preprod_cluster}"`；Redis、PG 的 `workspaceId` 为 `${vmp.cloud_workspace_id}`。禁止把 workspace `prod` 中 `cluster="${vmp.prod_cluster}"` 的 Pod 合计写成预发布容器水位。`mcp-metrics` 只可选补充应用侧 `yc_redis_*`、`gorm_dbstats_*`，不能代替云指标。结果写入 `vmp_context`，由 `generator-report` 写入压测报告。

## 报告输出

报告必须保存到当前项目 `reports/`，文件名格式（强制）：

```text
reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md
```

命名规则：

- `{服务名称}`：优先 `vmp_service_names[0]`；否则从压测脚本 `host` 提取（例：`http://<service>${service.host_suffix}` → `good-order`）；仍无法确定时用 `unknown-service`。
- `{YYYYMMDD_HHMMSS}`：报告生成时刻的本地时间戳，保证每次压测一份新文件。
- 示例：`reports/good-order压测报告_20260813_144530.md`
- 禁止再写死为 `reports/load_test_report.md`；禁止覆盖本地已有同路径报告（若极端情况下文件名冲突，在时间戳后追加 `-2`、`-3`…）。

报告须同时引用 Locust 和火山云数据，至少包含：

1. 压测背景：接口、环境、**实际**并发列表（来自 `users_list` / 落盘报告，未传则为单轮 200）、每轮持续时间、数据来源。
2. 结果摘要：各并发下 RPS、失败率、P95/P99、错误类型（单轮一行，多轮分档）。
3. 资源表现：按 `vmp_context.rounds` 对齐各并发窗口的服务、Redis、数据库 CPU/内存等指标。
4. 瓶颈判断：用数据说明瓶颈来源，不确定时标记为待验证。
5. 容量建议：推荐稳定并发、水位阈值、扩容或优化建议。
6. 数据完整性说明：明确缺失数据、监控不完整项、对结论可信度的影响。

报告正文不要默认追加“附录”章节，也不要把本地产物路径、完整 PromQL、Playwright 操作日志作为正文尾部内容；这些信息只在用户明确要求审计或复核时单独补充。

## 飞书报告归档

生成 `reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md` 后，必须使用飞书 CLI 将该 Markdown 报告**新增**到以下飞书云盘目录：

```text
${feishu.report_folder_url}
```

默认目录 token：

```text
${feishu.report_folder_token}
```

归档策略（强制，只新增不覆盖）：

1. 每次上传使用带时间戳的本地文件名，作为云端新文件创建；飞书目录里已有的历史压测报告一律保留。
2. **禁止**传 `--file-token`（该参数会原地覆盖已有文件）。
3. **禁止**为“同名更新”去检索并覆盖目录中已有的 `{服务名称}压测报告*.md` / 旧版 `load_test_report.md`。
4. 上传失败时不得回退为覆盖已有飞书文件；保留本地报告并记录失败原因。

命令解析（强制）：

1. 优先使用 `lark-cli`（本机常见安装：`npm i -g @larksuite/cli`，可执行文件名为 `lark-cli`）。
2. 若存在 `feishu-cli` 且能执行同等 `drive +upload`，也可使用。
3. 不要因为找不到名为 `feishu-cli` 的二进制就判定“未安装飞书 CLI”；先检查 `command -v lark-cli`。

推荐命令（将 `REPORT_PATH` 换成本次实际报告路径）：

```bash
REPORT_PATH="reports/good-order压测报告_20260813_144530.md"  # 示例；以本次生成的文件名为准
test -s "$REPORT_PATH"
lark-cli drive +upload --folder-token "${feishu.report_folder_token}" --file "$REPORT_PATH"
# 不要加 --file-token
```

遇到未登录、缺少 Drive 权限或 scope 不足时，按飞书 CLI 认证流程处理并向用户说明需要授权。上传完成后，在最终结果中给出飞书返回的文件链接或 token，以及本地 `report_path`；如果上传失败，报告仍必须保留在本地带时间戳路径，并说明失败原因。

## 安全要求

- 不要输出或提交 `VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`、YApi token、GitLab token。
- 不要硬编码真实手机号、身份证、地址、Cookie、Token。
- 预发布环境数据只用于压测分析，报告中对用户标识、设备标识和敏感业务字段做脱敏。
