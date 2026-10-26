---
name: vmp-monitoring
description: Use when 需要通过火山云 VMP MCP 查询预发布压测窗口内的服务、Redis、数据库监控指标，并把监控数据用于 Locust 压测报告分析。
---

# VMP Monitoring Skill

## 目标

通过本技能目录下的 `vmp-monitoring/volcengine_mcp_tools.py` 或已注入的火山云 VMP MCP 查询预发布环境监控数据，并输出可被压测报告直接消费的 `vmp_context`。所有监控数据必须来自 MCP 工具返回或用户上下文，不能编造指标、标签或结论。

**查询目标必须以 `constraint/SKILL.md` 为唯一默认约束来源**；执行本技能前必须先读取该文件，禁止绕过约束表写死或猜测 Redis/PG 实例。

## 前置条件

- 运行环境必须配置 `VOLCENGINE_ACCESS_KEY` 和 `VOLCENGINE_SECRET_KEY`；`VOLCENGINE_REGION` 未配置时按 `cn-beijing`。
- Agent 上下文中 `enable_vmp_mcp` 为 `true` 时才加载 VMP MCP 工具。
- 必须先读取 `../constraint/SKILL.md`（相对本技能）或主技能同级 `constraint/SKILL.md`。
- `vmp_workspace_id` 默认使用约束中的预发布 workspace：Name=`prod`，Id=`${vmp.cloud_workspace_id}`。
- 服务名从 `locustfile.py` 的 `host` 提取：去掉协议后取第一个域名段，例如 `host = "http://<service>${service.host_suffix}"` → `good-order`。该值是服务名，不是 workspaceId。
- Redis：实例名称写成 `bj-{服务名}`，到约束表「Redis 资源基础信息」按实例名称取实例 ID。例如服务名 `order-plus` → `bj-order-plus` → `redis-cn02lygtazmc6ag7s`。「容器服务 ↔ Redis ↔ PG」已写出另一套 Redis 时以该行为准；两张表都没有则不查 Redis。
- PG：实例名称写成 `bj-{服务名}`，到约束表「PG 资源基础信息」按实例名称取实例 ID。例如服务名 `order-plus` → `bj-order-plus` → `postgres-b7e8f04eca78a5eb`。「容器服务 ↔ Redis ↔ PG」已写出另一套 PG 时以该行为准；两张表都没有则不查 PG。命名空间只从「容器服务」表读取，没有则不编造。
- 压测并发列表以主技能归一化后的 `users_list` 为准（未传 `locust_users` 时为 `[200]`）；VMP 必须按每一档各自的 start/stop 时间窗查询。
- **本地 `mcp_server_vmp`（模块 `mcp_server_vmp.server`）必须提前就绪**；缺失时先下载，再查询（见下节）。

## 本地 mcp_server_vmp 下载（强制）

启动 VMP MCP 前，必须确保本技能目录下存在可运行的本地 server：

```text
vmp-monitoring/volcengine-mcp-server/server/mcp_server_vmp/
└── src/mcp_server_vmp/server.py   # 对应 python -m mcp_server_vmp.server
```

检查与下载（在本技能目录执行）：

```bash
# 仅检查
python3 ensure_mcp_server_vmp.py --check

# 缺失则从官方仓库 sparse clone 下载；已存在则跳过
python3 ensure_mcp_server_vmp.py

# 强制重新下载覆盖
python3 ensure_mcp_server_vmp.py --force
```

规则：

1. 执行查询流程前先 `--check`；未就绪必须先 `python3 ensure_mcp_server_vmp.py`。
2. `volcengine_mcp_tools.build_vmp_mcp_connection()` 在本地缺失时会自动调用 `ensure_vmp_server_downloaded()`；Agent 仍应在加载 MCP 前显式跑一遍下载命令，避免首次查询卡在 git clone。
3. 下载源：`https://github.com/volcengine/mcp-server.git` 的 `server/mcp_server_vmp`。
4. 优先使用本地下载结果 + `uv run -m mcp_server_vmp.server`；仅当本地下载失败且本机有 `uvx` 时才允许兜底。
5. 下载失败（无 git、GitHub 不可达等）时，记录原因到 `vmp_context.risks` / `fetch_status=failed`，不要编造监控数据。

## 安全边界

- 只允许使用查询类 VMP MCP 工具。
- 禁止创建、更新、删除工作区、实例、告警、规则、BasicAuth、Quota、公网访问、删除保护等资源配置。
- 不要输出、提交或写入报告 `VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`、YApi token、GitLab token。
- 监控数据只用于压测分析；涉及用户标识、设备标识、手机号、Cookie、Token 等字段时必须脱敏。

## 查询流程

1. 在本技能目录执行 `python3 ensure_mcp_server_vmp.py --check`；未就绪则先 `python3 ensure_mcp_server_vmp.py`，确认 `mcp_server_vmp.server` 本地可用。
2. 读取 `constraint/SKILL.md`，确认 workspace、服务名推导规则和 Redis/PG 映射表（整次压测只读一次约束表）。
3. 确认 `users_list` 与每轮时间窗：对每个 `users`，读取 `reports/locust_ui_{users}_start_time.txt` 与 `stop_time.txt`；缺失时要求用户补充，或明确只能查询近实时窗口。
4. Redis、PG 调用 `query_metrics`、`query_range_metrics`、`query_metric_names`、`query_metric_labels`、`query_series` 时，`workspaceId` 传 `volcengine_mcp_tools.VMP_WORKSPACE_ID`：Name=`prod`，Id=`${vmp.cloud_workspace_id}`。不要把服务名当作 `workspaceId`。服务容器按 `constraint/SKILL.md` 的「用服务名查容器指标」，`workspaceId` 用 Name=`stage`、Id=`${vmp.stage_workspace_id}`，PromQL 带 `cluster="${vmp.preprod_cluster}"`。不要用 `stage` workspace 查 Redis / PG。
5. 确认服务名：从 `locustfile.py` 的 `host` 提取。Redis、PG 的实例名称都写成 `bj-{服务名}`，分别到「Redis 资源基础信息」「PG 资源基础信息」按实例名称取实例 ID。服务名 `order-plus` 的 Redis 是 `bj-order-plus` / `redis-cn02lygtazmc6ag7s`，PG 是 `bj-order-plus` / `postgres-b7e8f04eca78a5eb`。「容器服务 ↔ Redis ↔ PG」已写出另一套名称和 ID 时，以那一行为准。两张表都没有则不查对应依赖。命名空间只从「容器服务」表读取，没有则不编造。
6. 查询可用指标名和标签：指标名不确定时先查元数据，不要直接拼 PromQL；优先窄查询。
7. **按轮循环**（`for users in users_list`）：用该轮 start/stop 作为 `time_range`，采集核心指标（仅查询约束允许的目标）：
   - 服务容器：按 `constraint/SKILL.md`「用服务名查容器指标」，在 Name=`stage` 的 workspace 上查 CPU、内存、实例数、重启数、CPU limit、内存 limit。PromQL 必须带 `cluster="${vmp.preprod_cluster}"`。
   - Redis：命中实例 ID 后，用 `query_range_metrics` 查云实例 CPU、内存、QPS、延迟、连接数。`order-plus` 使用 `bj-order-plus` / `redis-cn02lygtazmc6ag7s`。
   - 数据库：命中实例 ID 后，用 `query_range_metrics` 查云实例 CPU、内存、TPS、连接数。`order-plus` 使用 `bj-order-plus` / `postgres-b7e8f04eca78a5eb`。
8. 默认 `step` 使用 `60s`；数据过密或单轮窗口过长时可增大。禁止把多轮糊成「首轮开始～末轮结束」单一窗口作为唯一结论依据（可另附总览，但 `rounds[]` 必须按轮齐全）。
9. 结果为空时不要下结论，必须记录可能原因：指标不存在、标签不匹配、时间范围无数据、权限或凭证异常、约束表未登记。
10. 服务容器、Redis 云指标、PG 云指标都走 `mcp_server_vmp` 的 `query_range_metrics`。容器用预发布 workspace `${vmp.stage_workspace_id}`；Redis、PG 用 Name=`prod` 的 `${vmp.cloud_workspace_id}`。`mcp-metrics` 只作为应用侧 `yc_redis_*`、`gorm_dbstats_*` 的可选补充，不决定云指标是否查询。

## 输出契约

返回给主流程的内容统一命名为 `vmp_context`：

```json
{
  "fetch_status": "success | partial | failed",
  "workspace_id": "${vmp.cloud_workspace_id}",
  "workspace_name": "prod",
  "service_names": ["从 host 提取的服务名，例如 good-order"],
  "constraint_targets": {
    "redis": "来自 constraint 表的实例，或 null",
    "postgres": "来自 constraint 表的实例，或 null"
  },
  "rounds": [
    {
      "users": 200,
      "time_range": {
        "start": "ISO-8601 或 reports/locust_ui_200_start_time.txt",
        "end": "ISO-8601 或 reports/locust_ui_200_stop_time.txt",
        "step": "60s"
      },
      "service_metrics": [],
      "redis_metrics": [],
      "database_metrics": [],
      "promql_queries": [],
      "empty_results": []
    }
  ],
  "empty_results": [],
  "risks": []
}
```

字段说明：

- `fetch_status`：全部关键指标成功为 `success`；部分指标缺失为 `partial`；凭证、workspace 或工具不可用为 `failed`。
- `workspace_id`：实际 MCP 查询用的 UUID，不是服务名。
- `rounds`：与 `users_list` 一一对应；未传 `locust_users` 时仅含 `users=200` 一项；传入 `[200,300,500]` 时含三项。
- 顶层可保留汇总用的 `empty_results` / `risks`；轮内明细优先写在对应 `rounds[]` 项中。
- `service_metrics`、`redis_metrics`、`database_metrics`：保留 MCP 返回的核心数值、标签和时间范围，不要只写自然语言总结。
- `promql_queries`：记录使用过的 PromQL 或 MCP 查询参数，便于报告复核。
- `empty_results`：记录空结果对应的指标、标签、时间范围和可能原因。
- `risks`：记录数据不足、指标口径不一致、窗口未对齐、约束表未登记等影响结论可信度的问题。

兼容说明：若历史产物仍使用顶层单一 `time_range` + 顶层 metrics，报告阶段应视为「仅单轮」并写入 `risks`；新执行必须产出 `rounds[]`。

## Redis / PG 云指标

Redis、PG 云实例指标始终调用 `mcp_server_vmp` 的 `query_range_metrics`。不要先判断 `${vmp.metrics_mcp_url}` 是否存在。`mcp-metrics` 返回 `not_integrated` 或 `no_data` 时，云指标查询照常进行。

每次调用：

- `workspaceId`：`${vmp.cloud_workspace_id}`（Name=`prod`）
- `start`、`end`：该轮 `locust_ui_{users}_start_time.txt` 与 `stop_time.txt` 的 Unix 秒
- `step`：`60s`

PromQL 标签：

- `ProjectName="stage"`。这是实例上的项目标签，不是 VMP workspace 名。
- `Name` 使用约束表实例名称。
- `ResourceID` 使用约束表实例 ID。

`order-plus`：

```promql
AggregatedCpuUtil_aggregated_server_VCM_Redis{ProjectName="stage",Name="bj-order-plus",ResourceID="redis-cn02lygtazmc6ag7s"}
CpuUtil_resource_monitor_VCM_RDS_PostgreSQL{ProjectName="stage",Name="bj-order-plus",ResourceID="postgres-b7e8f04eca78a5eb"}
```

至少查这些指标，把上面的 `Name`、`ResourceID` 套到每个指标名上：

- Redis：`AggregatedCpuUtil_aggregated_server_VCM_Redis`、`AggregatedMemUtil_aggregated_server_VCM_Redis`、`AggregatedCpuUtil_aggregated_proxy_VCM_Redis`、`AggregatedReadQps_aggregated_proxy_VCM_Redis`、`AggregatedWriteQps_aggregated_proxy_VCM_Redis`、`TotalQps_proxy_VCM_Redis`、`AggregatedAvgQueryLatency_aggregated_proxy_VCM_Redis`、`AggregatedP99QueryLatency_aggregated_proxy_VCM_Redis`、`PeakUsedConn_proxy_VCM_Redis`、`PeakConnUtil_proxy_VCM_Redis`。
- PostgreSQL：`CpuUtil_resource_monitor_VCM_RDS_PostgreSQL`、`MemUtil_resource_monitor_VCM_RDS_PostgreSQL`、`TPS_engine_monitor_VCM_RDS_PostgreSQL`、`ActiveConnection_engine_monitor_VCM_RDS_PostgreSQL`、`IdleConnection_engine_monitor_VCM_RDS_PostgreSQL`。

CPU、内存、连接数使用率按百分比记录。Redis `QueryLatency` 原值单位是微秒。主节点和备节点分开写。返回序列的 `ResourceID` 与约束表不一致时丢弃。

`query_range_metrics` 失败或序列为空时，写入该轮 `empty_results`，注明指标名、PromQL 和时间窗。不要改走 `metrics_query`，也不要改走 Nightingale。

结果写入 `vmp_context.rounds[].redis_metrics` 和 `database_metrics`，注明 `source=mcp_server_vmp`。

## 应用侧补充：`metrics_query`

可选。只补充应用进程里的 Redis 客户端和 PG 连接池，不替代上一节云指标。

地址是 `${vmp.metrics_mcp_url}`。`env` 只用 `metrics_available_servers` 返回的 `prod`。云监控名 `AggregatedCpuUtil_aggregated_server_VCM_Redis`、`CpuUtil_resource_monitor_VCM_RDS_PostgreSQL` 在这里是 `not_integrated`，不要查询，也不要用它代替 `query_range_metrics`。

有命名空间时才查，例如：

```text
metrics_query(
  env="prod",
  promql='sum(gorm_dbstats_in_use{app="<服务名>",namespace="<命名空间>"})',
  start="<该轮 start unix 秒>",
  end="<该轮 end unix 秒>",
  step="60s"
)
```

Redis 客户端指标从 `metrics_list(env="prod", prefix="yc_redis_")` 抄，例如 `yc_redis_pool_active_current`。没有命名空间时跳过本节。`no_data`、`not_integrated`、工具不可用都写入 `empty_results`，云指标结果保留。应用侧结果注明 `source=metrics_query`。

## 报告交付

生成压测报告时，必须同时引用 Locust 结果和 `vmp_context`。如果 `vmp_context.fetch_status` 不是 `success`，报告中要明确说明缺失项和对瓶颈判断的影响，不要把监控缺失解释成系统无瓶颈。
