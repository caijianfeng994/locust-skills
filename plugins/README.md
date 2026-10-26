# Locust Skills UI 监控插件

监控插件通过 Python entry point `locust_skills_ui.monitoring` 注册，入口对象必须实现：

```python
def collect(config, start, end, service_name) -> dict:
    ...
```

返回值遵循 `vmp_context` 契约，至少包含 `fetch_status`、`workspace_id`、`time_range`、`service_metrics`、`redis_metrics`、`database_metrics`、`promql_queries`、`empty_results` 和 `risks`。

每个 MCP Server 使用独立 Python package 或容器维护依赖，禁止把 Python、Node.js、Go 运行时依赖合并进主 CLI wheel。首个实现位于 `plugins/vmp/`。
