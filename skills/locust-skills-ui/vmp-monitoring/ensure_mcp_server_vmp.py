#!/usr/bin/env python3
"""确保本地存在可运行的 mcp_server_vmp（缺失时从 GitHub sparse clone）。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VMP_MONITORING_DIR = Path(__file__).resolve().parent
VMP_SERVER_DIR = VMP_MONITORING_DIR / "volcengine-mcp-server" / "server" / "mcp_server_vmp"
VMP_SERVER_SRC_DIR = VMP_SERVER_DIR / "src"
VMP_SERVER_MODULE = VMP_SERVER_SRC_DIR / "mcp_server_vmp" / "server.py"
VMP_REPO_URL = "https://github.com/volcengine/mcp-server.git"
VMP_SPARSE_PATH = "server/mcp_server_vmp"


def is_vmp_server_ready(server_dir: Path = VMP_SERVER_DIR) -> bool:
    """本地 mcp_server_vmp 是否已就绪（含 mcp_server_vmp.server 模块）。"""
    src_dir = server_dir / "src"
    server_py = src_dir / "mcp_server_vmp" / "server.py"
    return (
        server_dir.is_dir()
        and (server_dir / "pyproject.toml").is_file()
        and server_py.is_file()
    )


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_vmp_server_downloaded(
    *,
    force: bool = False,
    server_dir: Path = VMP_SERVER_DIR,
    repo_url: str = VMP_REPO_URL,
) -> Path:
    """
    若本地缺少 mcp_server_vmp，则 sparse clone 官方仓库并落盘到 server_dir。
    已就绪且 force=False 时直接返回路径。
    """
    if is_vmp_server_ready(server_dir) and not force:
        return server_dir

    if not shutil.which("git"):
        raise RuntimeError("缺少 git，无法下载 mcp_server_vmp。请先安装 git。")

    server_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mcp_server_vmp_") as tmp:
        repo = Path(tmp) / "mcp-server"
        try:
            _run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--filter=blob:none",
                    "--sparse",
                    repo_url,
                    str(repo),
                ]
            )
            _run(["git", "sparse-checkout", "set", VMP_SPARSE_PATH], cwd=repo)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"下载 mcp_server_vmp 失败（git exit={exc.returncode}）：{repo_url}"
            ) from exc

        src = repo / VMP_SPARSE_PATH
        if not (src / "src" / "mcp_server_vmp" / "server.py").is_file():
            raise RuntimeError(
                f"仓库中未找到 {VMP_SPARSE_PATH}/src/mcp_server_vmp/server.py"
            )

        if server_dir.exists():
            shutil.rmtree(server_dir)
        shutil.copytree(src, server_dir)

    if not is_vmp_server_ready(server_dir):
        raise RuntimeError(
            f"下载完成但仍未就绪：缺少 {server_dir / 'src' / 'mcp_server_vmp' / 'server.py'}"
        )
    return server_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="确保本地 mcp_server_vmp 已下载（对应模块 mcp_server_vmp.server）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="即使本地已存在也重新下载覆盖",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查是否就绪，不下载；未就绪时退出码为 1",
    )
    args = parser.parse_args(argv)

    if args.check:
        ready = is_vmp_server_ready()
        print(f"ready={ready}")
        print(f"path={VMP_SERVER_DIR}")
        return 0 if ready else 1

    path = ensure_vmp_server_downloaded(force=args.force)
    print(f"mcp_server_vmp ready: {path}")
    print(f"module: {path / 'src' / 'mcp_server_vmp' / 'server.py'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
