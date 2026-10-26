---
name: generator-report
description: Use when 需要基于 Locust CSV 指标、MinIO 压测结果、VMP 服务监控、Redis 或数据库监控生成专业压测报告。
---

# Generator Report Skill

## 目标

基于 Locust Web UI 下载的报告/统计数据、可选的本地 CSV 指标，以及 `vmp-monitoring` 产出的 `vmp_context`，生成专业压测报告。报告必须用数据支撑结论，不能编造 RPS、响应时间、失败率、CPU、内存、Redis 或数据库指标。

## 触发条件

- 已完成 Locust 压测（单轮或阶梯），需要输出压测报告。
- 已从 Locust Web UI 下载报告或统计数据，或已解析本地 Locust CSV。
- 已通过 VMP MCP 获取服务、Redis、PG/数据库监控信息。
- 用户要求“生成压测报告”“分析瓶颈”“给出容量建议”“汇总压测结论”。

## 输入要求

报告生成前必须具备以下上下文：

| 字段 | 来源 | 用途 |
| --- | --- | --- |
| `locust_csv_context` | Web UI 下载结果或本地 CSV | Locust 指标、失败明细、趋势数据 |
| `locust_report_files` | Web UI 下载结果或本地文件 | HTML 报告、统计 JSON、CSV 路径，便于报告复核 |
| `vmp_context` | `vmp-monitoring` | 服务、Redis、PG/数据库等资源监控 |
| `rag_context` | `yapi-rag` | 接口背景、接口名称、服务名称 |
| `gitlab_upload_context` | `gitlab-upload` | 分支、tag、CI 触发信息 |

如果其中任一上下文缺失，报告仍可生成，但必须在“数据完整性”章节说明缺失项和对结论可信度的影响。

## Locust 数据要求

`locust_csv_context` 至少包含：

```yaml
locust_csv_context:
  fetch_status: success | partial | failed
  data_source: web_ui | local_csv | missing
  run_id: ""
  users_list: [200]   # 与主技能归一化一致；未传 locust_users 时为 [200]
  summary:
    - users: 200
      request_count: 0
      failure_count: 0
      average_response_time: 0
      median_response_time: 0
      p95_response_time: 0
      p99_response_time: 0
      requests_per_second: 0
      failures_per_second: 0
      failure_rate: 0
  failures: []
  history: []
  minio_report_objects: []
  download_errors: []
  parse_errors: []
```

使用要求：

- `summary` 必须覆盖实际跑过的每一档并发（由 `users_list` / `reports/locust_ui_{users}_report.html` 决定），不要假设一定是 200/300/500。
- 结果摘要优先使用 `summary` 中各并发的 `Aggregated` 汇总行。
- 失败率必须按 `failure_count / request_count` 计算；`request_count=0` 时标记为不可计算。
- 趋势分析使用 `history`，不要只看最终汇总。
- 错误类型来自 `failures`，不得把 HTTP 失败、业务断言失败和下载/解析失败混为一类。

## VMP 监控数据要求

`vmp_context` 至少包含：

```yaml
vmp_context:
  fetch_status: success | partial | failed
  workspace_id: "${vmp.cloud_workspace_id}"
  workspace_name: "prod"
  container_workspace_id: "${vmp.stage_workspace_id}"
  container_workspace_name: "stage"
  service_names: ["从 locustfile.py host 提取的服务名，例如 good-order"]
  constraint_targets:
    redis: "来自 constraint/SKILL.md 表，或 null"
    postgres: "来自 constraint/SKILL.md 表，或 null"
  rounds:
    - users: 200
      time_range:
        start: ""
        end: ""
        step: "60s"
      service_metrics: []
      redis_metrics: []
      database_metrics: []
      empty_results: []
  empty_results: []
  risks: []
```

分析重点：

- 服务：CPU、内存、QPS、错误率、P95/P99 延迟、实例数、重启数。容器指标来自 `container_workspace_id`（Name=`stage`），不要和 Redis / PG 的 `workspace_id` 混用。
- Redis：CPU、内存、连接数、命中率、OPS、慢查询、网络 IO。
- PG/数据库：CPU、内存、连接数、QPS/TPS、慢查询、锁等待、磁盘 IO。
- 必须将 VMP 各轮 `time_range` 与对应 Locust 并发窗口对齐；单轮只对一档，多轮按档对比；无法对齐时必须标记风险。
- 不要把「默认阶梯 200/300/500」写进报告背景，除非本次 `users_list` 确实是该列表。

## 报告结构

输出 Markdown 报告，使用以下结构：

```markdown
# 压测报告：<接口或服务名称>

## 1. 压测背景

## 2. 数据来源与完整性

## 3. 结果摘要

## 4. Locust 指标分析

## 5. 服务资源监控分析

## 6. Redis 监控分析

## 7. PG/数据库监控分析

## 8. 瓶颈判断

## 9. 容量建议

## 10. 风险与后续动作

## 11. 附录
```

## 各章节要求

### 1. 压测背景

必须说明：

- 压测接口或业务链路。
- 目标环境。
- 并发列表：以实际 `users_list` / 已落盘 `locust_ui_{users}_*` 为准（未传 `locust_users` 时为单轮 `200`；传入如 `[200, 300, 500]` 则写实际列表）。
- 每轮持续时间：以实际 `locust_run_time` 为准（未传默认 `20m`）。
- Locust 执行方式：Web UI、并发数、Ramp up、持续时间、报告下载方式。
- GitLab tag 或 CI 信息（如果有）。

### 2. 数据来源与完整性

必须列出：

- Locust 数据来源：Web UI 下载、本地 CSV 或缺失。
- HTML 报告、统计 JSON 或 CSV 路径。
- VMP workspace、时间窗口、PromQL 或 MCP 查询参数。
- `download_errors`、`parse_errors`、`empty_results`、`risks`。

### 3. 结果摘要

按并发输出核心指标：

- RPS
- 请求数
- 失败数
- 失败率
- 平均响应时间
- P95 / P99
- 主要错误类型

不得使用 Markdown 表格很宽时影响阅读；可用简短列表或分并发小节。

### 4. Locust 指标分析

分析：

- 单轮：说明该并发下的 RPS、延迟、失败率是否可接受。
- 多轮：RPS 是否随并发增长；P95/P99 是否明显劣化；失败率是否超过可接受范围。
- 哪些接口是主要慢接口或失败接口。
- `history` 中是否出现抖动、突刺、阶段性退化。

### 5. 服务资源监控分析

结合 VMP 服务指标说明：

- CPU 是否接近瓶颈。
- 内存是否持续上涨或接近限制。
- QPS、错误率、服务 P95/P99 是否与 Locust 趋势一致。
- 实例数、重启数是否影响压测结果。

### 6. Redis 监控分析

说明：

- CPU、内存、连接数是否异常。
- 命中率是否下降。
- OPS 是否随并发增长。
- 是否出现慢查询、网络 IO 饱和或连接数瓶颈。

### 7. PG/数据库监控分析

说明：

- CPU、内存、连接数是否接近上限。
- QPS/TPS 是否随并发增长。
- 是否有慢查询、锁等待、磁盘 IO 压力。
- 数据库指标是否能解释接口延迟或失败。

### 8. 瓶颈判断

必须用证据表达，不确定时写“待验证”：

- 如果 Locust 延迟升高且服务 CPU/内存/QPS 同步异常，可判断为服务侧瓶颈。
- 如果接口延迟升高且 Redis/PG 指标异常，可判断为依赖组件瓶颈。
- 如果 VMP 指标缺失，不得推断“资源无瓶颈”，只能说明监控数据不足。

### 9. 容量建议

至少包含：

- 推荐稳定并发。
- 推荐 RPS 水位。
- 失败率阈值。
- P95/P99 阈值。
- 扩容或优化建议。
- 下一轮压测建议。

### 10. 风险与后续动作

列出：

- 数据缺失风险。
- 压测数据造数或业务状态风险。
- 监控时间窗口不一致风险。
- 建议补充的指标或验证动作。

### 11. 附录

包含：

- Locust 命令。
- MinIO 对象路径。
- 本地 CSV 路径。
- VMP PromQL 或 MCP 查询参数。
- GitLab tag / commit / pipeline 信息（如果有）。

## 输出契约

最终产物命名为 `load_test_report`（逻辑名）；落盘文件名必须带服务名与时间戳：

```text
reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md
```

规则：

- `{服务名称}`：优先 `vmp_context.service_names[0]` / `vmp_service_names[0]`，否则从 `host` 提取；无法确定时用 `unknown-service`。
- `{YYYYMMDD_HHMMSS}`：报告生成时刻本地时间；每次生成新文件，不覆盖本地已有报告。
- 示例：`reports/good-order压测报告_20260813_144530.md`

```yaml
load_test_report:
  format: markdown
  title: ""
  fetch_status: success | partial | failed
  data_sources:
    locust: web_ui | local_csv | missing
    vmp: success | partial | failed
  report_path: "reports/{服务名称}压测报告_{YYYYMMDD_HHMMSS}.md"
  summary:
    conclusion: ""
    stable_users: 0
    max_observed_rps: 0
    main_bottleneck: ""
  risks: []
```

## 质量要求

- 报告正文使用中文；指标名、字段名、命令、对象路径保留英文。
- 所有数字必须来自 `locust_csv_context` 或 `vmp_context`。
- 缺失数据必须说明，不能补造。
- 结论必须和数据对应，不能只给泛泛建议。
- 容量建议要明确可执行，不要只写“建议优化性能”。
