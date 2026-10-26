#!/usr/bin/env python3
"""CLI wrapper for the canonical Locust generator implementation."""

from __future__ import annotations

try:
    from locust_skills.generator.locustfile import (
        build_backup_path,
        build_task_name,
        collect_valid_interfaces,
        fields_to_dict,
        infer_host_from_path,
        load_rag_context,
        main,
        normalize_method,
        render_locustfile,
        to_snake_case,
        write_locustfile,
    )
except ImportError as error:
    raise SystemExit(
        "无法导入 locust_skills，请先在项目根目录执行 `python -m pip install -e .`"
    ) from error


if __name__ == "__main__":
    raise SystemExit(main())
