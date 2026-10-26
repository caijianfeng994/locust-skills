#!/usr/bin/env python3
"""通过 yapi-common-mcp 拉取接口详情，并输出规范化 rag_context JSON。

用法:
  python scripts/fetch_interface.py --url "https://yapi.example.com/project/<project-id>/interface/api/<interface-id>"
  python scripts/fetch_interface.py --url URL1 --url URL2 --output rag_context.json
  python scripts/fetch_interface.py --keyword "商品列表"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from yapi_mcp_tools import aload_yapi_mcp_tools, find_tool  # noqa: E402

INTERFACE_URL_RE = re.compile(
    r"(?P<link>https?://[^\s]+?/project/(?P<project_id>\d+)/interface/api/(?P<interface_id>\d+))"
    r"|/project/(?P<project_id2>\d+)/interface/api/(?P<interface_id2>\d+)"
)

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _yapi_settings() -> tuple[str, str, str]:
    """token 优先环境变量，其次本地 locust-skills-ui.yaml 的 yapi.token。地址只读配置。"""
    config_path = Path(os.environ.get("LOCUST_SKILLS_UI_CONFIG", _repo_root() / "locust-skills-ui.yaml"))
    yapi: dict[str, Any] = {}
    if config_path.is_file():
        import yaml

        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict) and isinstance(loaded.get("yapi"), dict):
            yapi = loaded["yapi"]
    token = (os.environ.get("YAPI_GLOBAL_TOKEN") or str(yapi.get("token") or "")).strip()
    base_url = (os.environ.get("YAPI_BASE_URL") or str(yapi.get("base_url") or "")).strip()
    mcp_url = (os.environ.get("YAPI_COMMON_MCP_URL") or str(yapi.get("mcp_url") or "")).strip()
    return token, base_url, mcp_url


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_jsonish(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _unwrap_tool_payload(result: Any) -> Any:
    """兼容 LangChain / MCP content 包装。"""
    result = _parse_jsonish(result)
    if isinstance(result, dict):
        if "content" in result and isinstance(result["content"], list):
            texts: list[str] = []
            for item in result["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    texts.append(item)
            if texts:
                joined = "\n".join(texts).strip()
                return _parse_jsonish(joined) if joined else result
        if "rawData" in result or "method" in result or "path" in result:
            return result
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict) and first.get("type") == "text":
            return _unwrap_tool_payload({"content": result})
    return result


def _field_from_param(item: dict[str, Any]) -> dict[str, Any]:
    required = item.get("required")
    if isinstance(required, str):
        required = required in {"1", "true", "True", "yes"}
    return {
        "name": item.get("name") or item.get("field") or "",
        "required": bool(required),
        "example": item.get("example") or item.get("value") or "",
        "description": item.get("desc") or item.get("description") or "",
    }


def _schema_fields(schema: Any, prefix: str = "") -> list[dict[str, Any]]:
    schema = _parse_jsonish(schema)
    if not isinstance(schema, dict):
        return []
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    fields: list[dict[str, Any]] = []
    required = set(schema.get("required") or [])
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            continue
        path = f"{prefix}.{name}" if prefix else name
        fields.append(
            {
                "name": path,
                "type": prop.get("type") or "",
                "required": name in required,
                "description": prop.get("title") or prop.get("description") or "",
            }
        )
        if prop.get("type") == "object":
            fields.extend(_schema_fields(prop, path))
        if prop.get("type") == "array" and isinstance(prop.get("items"), dict):
            fields.extend(_schema_fields(prop["items"], f"{path}[]"))
    return fields


def _extract_ids_from_link(link: str) -> tuple[str, str]:
    match = INTERFACE_URL_RE.search(link or "")
    if not match:
        return "", ""
    project_id = match.group("project_id") or match.group("project_id2") or ""
    interface_id = match.group("interface_id") or match.group("interface_id2") or ""
    return str(project_id), str(interface_id)


def _empty_interface(source_link: str, error: str) -> dict[str, Any]:
    project_id, interface_id = _extract_ids_from_link(source_link)
    return {
        "source_link": source_link,
        "interface_id": interface_id,
        "project_id": project_id,
        "interface_name": "",
        "method": "",
        "path": "",
        "description": "",
        "tags": [],
        "request": {
            "path_params": [],
            "query_params": [],
            "headers": [],
            "body_fields": [],
            "examples": [],
        },
        "response": {
            "success_fields": [],
            "error_fields": [],
            "status_codes": [],
            "examples": [],
        },
        "locust_hints": {
            "auth_required": False,
            "required_fields": [],
            "randomizable_fields": [],
            "assertion_fields": [],
            "dependency_apis": [],
        },
        "fetch_status": "failed",
        "fetch_error": error,
    }


def normalize_interface(source_link: str, payload: Any) -> dict[str, Any]:
    payload = _unwrap_tool_payload(payload)
    if payload is None:
        return _empty_interface(source_link, "MCP 返回为空")

    if isinstance(payload, dict) and isinstance(payload.get("rawData"), dict):
        data = payload["rawData"]
        top = payload
    elif isinstance(payload, dict):
        data = payload
        top = payload
    else:
        return _empty_interface(source_link, f"无法解析 MCP 返回类型: {type(payload).__name__}")

    project_id, interface_id = _extract_ids_from_link(source_link)
    project_id = str(data.get("project_id") or top.get("project_id") or project_id or "")
    interface_id = str(
        data.get("_id") or data.get("id") or top.get("id") or interface_id or ""
    )
    method = str(data.get("method") or top.get("method") or "").upper()
    path = str(data.get("path") or top.get("path") or "")
    name = str(data.get("title") or top.get("title") or top.get("interface_name") or "")
    description = str(data.get("desc") or data.get("markdown") or top.get("description") or "")
    tags = [str(t) for t in _as_list(data.get("tag") or top.get("tags") or [])]

    path_params = [_field_from_param(x) for x in data.get("req_params") or [] if isinstance(x, dict)]
    query_params = [_field_from_param(x) for x in data.get("req_query") or [] if isinstance(x, dict)]
    headers = [_field_from_param(x) for x in data.get("req_headers") or [] if isinstance(x, dict)]

    body_fields: list[dict[str, Any]] = []
    if data.get("req_body_is_json_schema"):
        body_fields = _schema_fields(data.get("req_body_other") or data.get("req_body"))
    else:
        for item in data.get("req_body_form") or []:
            if isinstance(item, dict):
                body_fields.append(_field_from_param(item))

    success_fields: list[dict[str, Any]] = []
    if data.get("res_body_is_json_schema"):
        success_fields = [
            {"name": f["name"], "type": f.get("type", ""), "description": f.get("description", "")}
            for f in _schema_fields(data.get("res_body"))
        ]

    required_fields = [
        f["name"]
        for f in path_params + query_params + headers + body_fields
        if f.get("name") and f.get("required")
    ]
    randomizable_fields = [
        f["name"]
        for f in path_params + query_params + body_fields
        if f.get("name") and f["name"] not in {"Authorization", "Cookie", "token"}
    ]
    assertion_fields = [
        f["name"]
        for f in success_fields
        if f.get("name")
        and any(k in f["name"].lower() for k in ("code", "success", "message", "msg", "id"))
    ]
    auth_required = any(
        (h.get("name") or "").lower() in {"authorization", "cookie", "token", "x-token"}
        for h in headers
    ) or any("token" in (f or "").lower() for f in required_fields)

    fetch_error = ""
    if not method or not path:
        fetch_error = "缺少 method 或 path，生成 Locust 请求可能失败"

    return {
        "source_link": source_link,
        "interface_id": interface_id,
        "project_id": project_id,
        "interface_name": name,
        "method": method,
        "path": path,
        "description": description,
        "tags": tags,
        "request": {
            "path_params": path_params,
            "query_params": query_params,
            "headers": headers,
            "body_fields": body_fields,
            "examples": [],
        },
        "response": {
            "success_fields": success_fields,
            "error_fields": [],
            "status_codes": [],
            "examples": [],
        },
        "locust_hints": {
            "auth_required": auth_required,
            "required_fields": required_fields,
            "randomizable_fields": randomizable_fields,
            "assertion_fields": assertion_fields,
            "dependency_apis": [],
        },
        "fetch_status": "success" if not fetch_error else "failed",
        "fetch_error": fetch_error,
        "raw": data,
    }


def _invoke_kwargs_for_detail(tool: Any, link: str) -> list[dict[str, Any]]:
    project_id, interface_id = _extract_ids_from_link(link)
    return [
        {"interfaceURL": link},
        {"link": link},
        {"url": link},
        {"interfaceId": interface_id},
        {"interface_id": interface_id},
        {"projectId": project_id, "interfaceId": interface_id},
    ]


async def _ainvoke_with_fallbacks(tool: Any, attempts: list[dict[str, Any]]) -> Any:
    errors: list[str] = []
    for kwargs in attempts:
        try:
            return await tool.ainvoke(kwargs)
        except Exception as exc:  # noqa: BLE001 - 需尝试多种 schema
            errors.append(f"{kwargs}: {exc}")
    raise RuntimeError("; ".join(errors) or "工具调用失败")


async def fetch_one(link: str, tools: list[Any]) -> dict[str, Any]:
    detail_tool = find_tool(tools, "get_interface_detail", "interface_detail")
    if detail_tool is None:
        return _empty_interface(link, "未找到 get_interface_detail 工具")
    try:
        raw = await _ainvoke_with_fallbacks(detail_tool, _invoke_kwargs_for_detail(detail_tool, link))
        item = normalize_interface(link, raw)
        # raw 仅供调试，默认从契约输出中移除
        item.pop("raw", None)
        return item
    except Exception as exc:  # noqa: BLE001
        return _empty_interface(link, f"调用 get_interface_detail 失败: {exc}")


async def search_and_fetch(keyword: str, tools: list[Any]) -> list[dict[str, Any]]:
    search_tool = find_tool(tools, "search_interface", "search")
    if search_tool is None:
        return [_empty_interface("", f"未找到 search_interface，无法按关键字检索: {keyword}")]

    try:
        raw = await _ainvoke_with_fallbacks(
            search_tool,
            [{"keyword": keyword}, {"q": keyword}, {"query": keyword}, {"name": keyword}],
        )
    except Exception as exc:  # noqa: BLE001
        return [_empty_interface("", f"search_interface 失败: {exc}")]

    payload = _unwrap_tool_payload(raw)
    links: list[str] = []
    candidates = payload if isinstance(payload, list) else _as_list(
        payload.get("list") or payload.get("data") or payload.get("interfaces") if isinstance(payload, dict) else []
    )
    for item in candidates:
        if isinstance(item, str) and "interface/api" in item:
            links.append(item)
        elif isinstance(item, dict):
            link = item.get("source_link") or item.get("url") or item.get("interfaceURL") or ""
            if not link:
                project_id = item.get("project_id") or item.get("projectId")
                interface_id = item.get("_id") or item.get("id") or item.get("interface_id")
                if project_id and interface_id:
                    link = f"/project/{project_id}/interface/api/{interface_id}"
            if link:
                links.append(str(link))

    if not links:
        return [_empty_interface("", f"关键字未命中接口: {keyword}")]

    results: list[dict[str, Any]] = []
    for link in links:
        results.append(await fetch_one(link, tools))
    return results


def build_rag_context(source_links: list[str], interfaces: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [i.get("fetch_status") for i in interfaces]
    if not interfaces or all(s == "failed" for s in statuses):
        top_status = "failed"
    elif any(s == "failed" for s in statuses):
        top_status = "partial"
    else:
        top_status = "success"

    errors = [i.get("fetch_error") for i in interfaces if i.get("fetch_error")]
    scenario_hints: list[str] = []
    if any(i.get("locust_hints", {}).get("auth_required") for i in interfaces):
        scenario_hints.append("部分接口需要鉴权（Token/Cookie/签名），压测前需准备登录态或公共 Header")

    return {
        "source_type": "yapi",
        "source_links": source_links,
        "interfaces": interfaces,
        "scenario_hints": scenario_hints,
        "fetch_status": top_status,
        "fetch_error": "; ".join(errors) if top_status != "success" else "",
    }


async def amain(args: argparse.Namespace) -> int:
    links = list(args.url or [])
    try:
        token, base_url, mcp_url = _yapi_settings()
        tools = await aload_yapi_mcp_tools(
            token=token,
            base_url=base_url,
            mcp_url=mcp_url,
        )
    except Exception as exc:  # noqa: BLE001
        rag = {
            "source_type": "yapi",
            "source_links": links,
            "interfaces": [_empty_interface(link, f"连接 yapi-common-mcp 失败: {exc}") for link in (links or [""])],
            "scenario_hints": [],
            "fetch_status": "failed",
            "fetch_error": f"连接 yapi-common-mcp 失败: {exc}",
        }
        _emit(rag, args.output)
        return 2

    interfaces: list[dict[str, Any]] = []
    if links:
        for link in links:
            interfaces.append(await fetch_one(link, tools))
    elif args.keyword:
        interfaces = await search_and_fetch(args.keyword, tools)
        links = [i.get("source_link") or "" for i in interfaces if i.get("source_link")]
    else:
        print("必须提供 --url 或 --keyword", file=sys.stderr)
        return 1

    rag = build_rag_context(links, interfaces)
    _emit(rag, args.output)
    return 0 if rag.get("fetch_status") != "failed" else 2


def _emit(rag: dict[str, Any], output: str | None) -> None:
    text = json.dumps(rag, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 yapi-common-mcp 拉取接口并输出 rag_context")
    parser.add_argument("--url", action="append", help="YApi 接口链接，可重复")
    parser.add_argument("--keyword", help="无明确链接时按关键字 search_interface")
    parser.add_argument("--output", "-o", help="可选：写入 JSON 文件路径")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(asyncio.run(amain(args)))


if __name__ == "__main__":
    main()
