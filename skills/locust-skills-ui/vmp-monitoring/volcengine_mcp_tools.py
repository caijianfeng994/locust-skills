import asyncio
import importlib.util
import os
import shutil
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

def _ui_config() -> dict:
    config_path = Path(
        os.environ.get(
            "LOCUST_SKILLS_UI_CONFIG",
            Path(__file__).resolve().parents[3] / "locust-skills-ui.yaml",
        )
    )
    if not config_path.is_file():
        return {}
    import yaml

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _config_value(*keys: str) -> str:
    current: object = _ui_config()
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return "" if current is None else str(current)


def _credential(env_name: str, *config_keys: str) -> str:
    return (os.getenv(env_name) or _config_value(*config_keys)).strip()


VMP_WORKSPACE_NAME = _config_value("vmp", "project_name") or "prod"
VMP_WORKSPACE_ID = _config_value("vmp", "cloud_workspace_id")


VMP_MONITORING_DIR = Path(__file__).resolve().parent
VMP_SERVER_DIR = VMP_MONITORING_DIR / "volcengine-mcp-server" / "server" / "mcp_server_vmp"
VMP_SERVER_SRC_DIR = VMP_SERVER_DIR / "src"
VMP_SERVER_NAME = "mcp_server_vmp"


def _load_ensure_module():
    path = VMP_MONITORING_DIR / "ensure_mcp_server_vmp.py"
    spec = importlib.util.spec_from_file_location("ensure_mcp_server_vmp", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ensure = _load_ensure_module()
is_vmp_server_ready = _ensure.is_vmp_server_ready
ensure_vmp_server_downloaded = _ensure.ensure_vmp_server_downloaded


def build_vmp_mcp_connection() -> dict:
    access_key = _credential("VOLCENGINE_ACCESS_KEY", "volcengine", "access_key")
    secret_key = _credential("VOLCENGINE_SECRET_KEY", "volcengine", "secret_key")
    region = _credential("VOLCENGINE_REGION", "vmp", "region") or "cn-beijing"
    if not access_key or not secret_key:
        raise RuntimeError(
            "缺少火山引擎凭证：请设置 VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY。"
        )

    env = {
        "VOLCENGINE_ACCESS_KEY": access_key,
        "VOLCENGINE_SECRET_KEY": secret_key,
        "VOLCENGINE_REGION": region,
    }

    # 本地缺失时先下载 mcp_server_vmp（含 mcp_server_vmp.server），优先走本地。
    download_error: Exception | None = None
    if not is_vmp_server_ready(VMP_SERVER_DIR):
        try:
            ensure_vmp_server_downloaded(server_dir=VMP_SERVER_DIR)
        except Exception as exc:  # noqa: BLE001 - 下载失败时尝试 uvx 兜底
            download_error = exc

    if shutil.which("uv") and is_vmp_server_ready(VMP_SERVER_DIR):
        return {
            "transport": "stdio",
            "command": "uv",
            "cwd": str(VMP_SERVER_DIR),
            "env": env,
            "args": ["run", "-m", "mcp_server_vmp.server", "-t", "stdio"],
        }

    if is_vmp_server_ready(VMP_SERVER_DIR) and VMP_SERVER_SRC_DIR.exists():
        return {
            "transport": "stdio",
            "command": sys.executable,
            "cwd": str(VMP_SERVER_SRC_DIR),
            "env": env,
            "args": ["-m", "mcp_server_vmp.server", "-t", "stdio"],
        }

    if shutil.which("uvx"):
        return {
            "transport": "stdio",
            "command": "uvx",
            "env": env,
            "args": [
                "--from",
                "git+https://github.com/volcengine/mcp-server#subdirectory=server/mcp_server_vmp",
                "mcp-server-vmp",
            ],
        }

    detail = f"；本地下载失败: {download_error}" if download_error else ""
    raise RuntimeError(
        "未找到 VMP MCP Server 启动方式：请先运行 "
        "`python3 ensure_mcp_server_vmp.py` 下载本地 mcp_server_vmp，"
        "或安装 uv/uvx。"
        f"{detail}"
    )


def create_vmp_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {VMP_SERVER_NAME: build_vmp_mcp_connection()},
        tool_name_prefix=True,
    )


@asynccontextmanager
async def get_vmp_mcp_tools() -> AsyncIterator[list]:
    client = create_vmp_mcp_client()
    async with client.session(VMP_SERVER_NAME) as session:
        tools = await load_mcp_tools(
            session,
            server_name=VMP_SERVER_NAME,
            tool_name_prefix=True,
        )
        yield tools


async def aload_vmp_mcp_tools() -> list[BaseTool]:
    return await create_vmp_mcp_client().get_tools(server_name=VMP_SERVER_NAME)


@lru_cache(maxsize=1)
def load_vmp_mcp_tools() -> tuple[BaseTool, ...]:
    return tuple(asyncio.run(aload_vmp_mcp_tools()))


async def get_vmp_mcp_tool_names() -> list[str]:
    return [tool.name for tool in load_vmp_mcp_tools()]


__all__ = [
    "VMP_WORKSPACE_NAME",
    "VMP_WORKSPACE_ID",
    "is_vmp_server_ready",
    "ensure_vmp_server_downloaded",
    "build_vmp_mcp_connection",
    "create_vmp_mcp_client",
    "get_vmp_mcp_tools",
    "aload_vmp_mcp_tools",
    "load_vmp_mcp_tools",
    "get_vmp_mcp_tool_names",
]
