from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient


class VmpMonitoringPlugin:
    async def _collect(
        self,
        config: Any,
        start: str,
        end: str,
        service_name: str,
    ) -> dict[str, Any]:
        access_key = os.getenv("VOLCENGINE_ACCESS_KEY")
        secret_key = os.getenv("VOLCENGINE_SECRET_KEY")
        if not access_key or not secret_key:
            raise RuntimeError(
                "缺少火山引擎凭证：请设置 VOLCENGINE_ACCESS_KEY 和 "
                "VOLCENGINE_SECRET_KEY"
            )
        env = dict(os.environ)
        env.update({
            "VOLCENGINE_ACCESS_KEY": access_key,
            "VOLCENGINE_SECRET_KEY": secret_key,
            "VOLCENGINE_REGION": config.region,
        })
        client = MultiServerMCPClient({
            "vmp": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "mcp_server_vmp.server", "-t", "stdio"],
                "env": env,
            }
        })
        tools = await client.get_tools(server_name="vmp")
        query_tool = next(
            (tool for tool in tools if tool.name.endswith("query_range_metrics")),
            None,
        )
        if query_tool is None:
            raise RuntimeError("VMP 插件未找到 query_range_metrics 工具")

        context: dict[str, Any] = {
            "fetch_status": "success",
            "workspace_id": config.workspace_id,
            "time_range": {"start": start, "end": end, "step": config.step},
            "service_metrics": [],
            "redis_metrics": [],
            "database_metrics": [],
            "promql_queries": [],
            "empty_results": [],
            "risks": [],
        }
        groups = (
            ("service_metrics", config.service_queries),
            ("redis_metrics", config.redis_queries),
            ("database_metrics", config.database_queries),
        )
        for target, queries in groups:
            for template in queries:
                query = template.replace("$service", service_name)
                context["promql_queries"].append(query)
                try:
                    result = await query_tool.ainvoke({
                        "workspaceId": config.workspace_id,
                        "query": query,
                        "start": start,
                        "end": end,
                        "step": config.step,
                        "region": config.region,
                    })
                    if result:
                        context[target].append({"query": query, "result": result})
                    else:
                        context["empty_results"].append({"query": query})
                except Exception as error:
                    context["risks"].append(f"{query}: {error}")
        if context["risks"] or context["empty_results"]:
            context["fetch_status"] = "partial"
        return context

    def collect(
        self,
        config: Any,
        start: str,
        end: str,
        service_name: str,
    ) -> dict[str, Any]:
        return asyncio.run(self._collect(config, start, end, service_name))


plugin = VmpMonitoringPlugin()
