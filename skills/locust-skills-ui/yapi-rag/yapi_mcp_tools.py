"""YApi MCP 客户端封装：供 scripts/fetch_interface.py 与 Agent 降级调用。

连接信息由调用方传入。地址与 token 从环境变量或 locust-skills-ui.yaml 的 yapi 段解析，不在代码里写死。
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

YAPI_SERVER_NAME = "yapi-common-mcp"


def resolve_yapi_mcp_config(
    *,
    token: str | None = None,
    base_url: str | None = None,
    mcp_url: str | None = None,
) -> tuple[str, str, str]:
    resolved_token = (os.getenv("YAPI_GLOBAL_TOKEN") or token or "").strip()
    resolved_base_url = (os.getenv("YAPI_BASE_URL") or base_url or "").strip()
    resolved_mcp_url = (os.getenv("YAPI_COMMON_MCP_URL") or mcp_url or "").strip()
    if not resolved_token:
        raise ValueError("缺少 YAPI_GLOBAL_TOKEN，无法连接 yapi-common-mcp。")
    if not resolved_mcp_url:
        raise ValueError("缺少 YAPI_COMMON_MCP_URL，无法连接 yapi-common-mcp。")
    if not resolved_base_url:
        raise ValueError("缺少 YAPI_BASE_URL，无法连接 yapi-common-mcp。")
    return resolved_token, resolved_base_url, resolved_mcp_url


def build_yapi_mcp_connection(
    *,
    token: str | None = None,
    base_url: str | None = None,
    mcp_url: str | None = None,
) -> dict[str, Any]:
    resolved_token, resolved_base_url, resolved_mcp_url = resolve_yapi_mcp_config(
        token=token,
        base_url=base_url,
        mcp_url=mcp_url,
    )
    return {
        "transport": "http",
        "url": resolved_mcp_url,
        "headers": {
            "x-yapi-base-url": resolved_base_url,
            "x-yapi-global-token": resolved_token,
        },
    }


def create_yapi_mcp_client(
    *,
    token: str | None = None,
    base_url: str | None = None,
    mcp_url: str | None = None,
) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            YAPI_SERVER_NAME: build_yapi_mcp_connection(
                token=token,
                base_url=base_url,
                mcp_url=mcp_url,
            )
        }
    )


async def aload_yapi_mcp_tools(
    *,
    token: str | None = None,
    base_url: str | None = None,
    mcp_url: str | None = None,
) -> list[BaseTool]:
    client = create_yapi_mcp_client(
        token=token,
        base_url=base_url,
        mcp_url=mcp_url,
    )
    return await client.get_tools()


def find_tool(tools: list[BaseTool], *candidates: str) -> BaseTool | None:
    names = {name.lower(): name for name in candidates}
    for tool in tools:
        short = tool.name.split("_")[-1].lower() if "_" in tool.name else tool.name.lower()
        full = tool.name.lower()
        for candidate in names:
            if full == candidate or full.endswith(candidate) or short == candidate:
                return tool
    return None


__all__ = [
    "YAPI_SERVER_NAME",
    "resolve_yapi_mcp_config",
    "build_yapi_mcp_connection",
    "create_yapi_mcp_client",
    "aload_yapi_mcp_tools",
    "find_tool",
]
