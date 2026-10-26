# 删除 locust-skills 功能设计

日期：2026-08-12  
状态：待用户确认后实施

## 背景

仓库同时存在两套能力：

- `locust-skills`：无头/脚本生成 CLI + Skill（`src/locust_skills/`、`skills/locust-skills/`）
- `locust-skills-ui`：Web UI 全流程 Skill（`skills/locust-skills-ui/`），另有已删除工作区中的 UI CLI 源码

目标收敛为只保留 `locust-skills-ui` 技能方向。本轮采用**最小干净删除**：只移除 `locust-skills` 功能，其余先不动。

## 目标

1. 删除 `locust-skills` Skill、Python 包、CLI 入口及专用测试。
2. 更新 `README.md` / `pyproject.toml` 中对上述能力的引用，避免文档与入口仍引导用户使用已删命令。
3. 不改动 `locust-skills-ui` 技能正文、Cursor 命令、插件、示例配置，以及当前已删除的 `src/locust_skills_ui/` 工作区状态。

## 非目标（本轮明确不做）

- 不恢复或不继续重构 `src/locust_skills_ui/`
- 不改写 `skills/locust-skills-ui/**` 与 `.cursor/commands/locust_skills_ui.md`
- 不改 `plugins/`、`locust-skills-ui.example.yaml`
- 不重命名 PyPI/项目包名（可暂时仍为 `locust-skills`，避免牵动 `plugins/vmp` 依赖声明）
- 不在本轮把仓库改造成完整 Skill-first 分发方案

## 删除清单

| 路径 | 说明 |
| --- | --- |
| `skills/locust-skills/` | 基础压测 Skill |
| `src/locust_skills/` | 基础 CLI 与库代码（含 curl、generator、minio、report 等） |
| `tests/test_cli_run.py` | 依赖 `locust_skills.cli` |
| `tests/test_curl_parser.py` | 依赖 `locust_skills.curl` / generator |
| `tests/test_fixed_parameter_generation.py` | 依赖 `locust_skills.generator` |
| `tests/test_locust_245_baseline.py` | 依赖 `locust_skills` 与 `skills/locust-skills` |
| `tests/test_minio_parse.py` | 依赖 `locust_skills.minio` |
| `tests/test_report_generator.py` | 依赖 `locust_skills.report` |
| `tests/test_services.py` | 依赖 `locust_skills.services` |

## 修改清单

### `pyproject.toml`

- 移除 script：`locust-skills = "locust_skills.cli:app"`
- `tool.setuptools.packages.find.include` 去掉 `locust_skills` / `locust_skills.*`，保留现有 `locust_skills_ui` 相关声明不动（即使工作区源码已缺，本轮不处理）
- `tool.pytest.ini_options.testpaths` 去掉 `skills/locust-skills/generator-locust`
- 项目 `name` 保持 `locust-skills`（本轮不改名）

### `README.md`

- 删除或改写所有 `locust-skills run`、基础 Skill、`skills/locust-skills`、仅生成脚本入口的说明
- 删除「只想生成脚本则用 `locust-skills run`」类 FAQ
- 项目结构与「包含的 Skills」表中去掉 `locust-skills` 行
- **保留**现有 `locust-skills-ui` 安装/命令/流程描述原文意图（本轮不做 Skill-first 文案重构）

## 保留清单（本轮不动）

- `skills/locust-skills-ui/**`
- `.cursor/commands/locust_skills_ui.md`
- `plugins/**`
- `locust-skills-ui.example.yaml`
- `tests/test_ui_*.py`、`tests/test_locust_ui_client.py`
- 工作区中已删除的 `src/locust_skills_ui/*` 状态（不 `git checkout` 恢复，也不额外清理 UI 测试）

## 验收标准

1. 仓库中不再存在 `skills/locust-skills/` 与 `src/locust_skills/`。
2. `pyproject.toml` 不再注册 `locust-skills` 控制台入口。
3. README 不再引导使用 `locust-skills` CLI / Skill。
4. 仅依赖 `locust_skills` 的测试文件已删除。
5. `skills/locust-skills-ui/` 与 `.cursor/commands/locust_skills_ui.md` 内容相对本轮开始时无新增业务改动。

## 风险与后续

- UI 相关测试与 `locust-skills-ui` CLI 源码缺失导致的失败，属于既有问题，本轮不修复。
- 包名仍为 `locust-skills` 可能造成语义混淆，可在后续 Skill-first 专项中改名。
- 完整「只保留 UI Skill、去掉 UI CLI」改造另开设计，不在本轮范围。

## 实施顺序建议

1. 删除 `src/locust_skills/` 与 `skills/locust-skills/`
2. 删除上表所列测试文件
3. 更新 `pyproject.toml`
4. 更新 `README.md`
5. 快速核对：无残留 `from locust_skills`（UI 包 `locust_skills_ui` 除外）、无 `locust-skills` script 入口
