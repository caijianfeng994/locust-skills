# 删除 locust-skills 功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从仓库中干净删除 `locust-skills` Skill、Python 包、CLI 入口与专用测试，并同步 README / `pyproject.toml`，同时不改动 `locust-skills-ui` 相关内容。

**Architecture:** 按设计文档做最小删除：移除 `src/locust_skills/` 与 `skills/locust-skills/`，删掉仅依赖它们的测试，从包装配置去掉 `locust-skills` 控制台入口与包发现项，再从 README 去掉对应引导。包名仍保持 `locust-skills`；`locust-skills-ui` 入口、Skill、插件与 UI 测试一律不动。

**Tech Stack:** Python packaging (`pyproject.toml` / setuptools)、Markdown 文档、pytest（仅做删除后残留校验与既有 UI 测试存在性核对）

**Spec:** `docs/superpowers/specs/2026-08-12-remove-locust-skills-design.md`

## Global Constraints

- 只删除 `locust-skills` 功能；禁止修改 `skills/locust-skills-ui/**` 与 `.cursor/commands/locust_skills_ui.md` 的业务内容
- 禁止恢复或继续清理 `src/locust_skills_ui/`（保持当前工作区已删除状态即可）
- 禁止改动 `plugins/`、`locust-skills-ui.example.yaml`
- 项目 `name` 保持 `locust-skills`，不重命名包
- Commit 信息使用简体中文 Conventional Commits；未获用户明确要求时不要 `git push`
- 文档正文使用中文，专有名词与命令保留英文

## File Structure

| 路径 | 本轮操作 | 职责 |
| --- | --- | --- |
| `src/locust_skills/` | 删除整目录 | 基础 CLI/库 |
| `skills/locust-skills/` | 删除整目录 | 基础 Skill |
| `tests/test_cli_run.py` 等 7 个文件 | 删除 | 仅测 `locust_skills` |
| `pyproject.toml` | 修改 | 去掉 `locust-skills` script / package include / pytest path |
| `README.md` | 修改 | 去掉 `locust-skills` 引导，保留 ui 描述 |
| `skills/locust-skills-ui/**` | 不动 | Web UI Skill |
| `tests/test_ui_*.py` 等 | 不动 | UI 测试（既有失败可接受） |

---

### Task 1: 删除 locust-skills 源码与 Skill

**Files:**
- Delete: `src/locust_skills/`（整目录）
- Delete: `skills/locust-skills/`（整目录）

**Interfaces:**
- Consumes: 无
- Produces: 工作区不再包含上述两目录

- [ ] **Step 1: 确认待删路径存在**

Run:

```bash
test -d src/locust_skills && test -d skills/locust-skills && echo OK
```

Expected: 输出 `OK`

- [ ] **Step 2: 删除目录**

Run:

```bash
rm -rf src/locust_skills skills/locust-skills
```

- [ ] **Step 3: 验证目录已消失**

Run:

```bash
test ! -d src/locust_skills && test ! -d skills/locust-skills && echo GONE
```

Expected: 输出 `GONE`

- [ ] **Step 4: Commit（若用户要求提交；否则跳过并继续）**

```bash
git add -u src/locust_skills skills/locust-skills
git commit -m "$(cat <<'EOF'
chore(locust-skills): 删除基础 CLI 包与 Skill 目录

EOF
)"
```

---

### Task 2: 删除仅依赖 locust_skills 的测试

**Files:**
- Delete: `tests/test_cli_run.py`
- Delete: `tests/test_curl_parser.py`
- Delete: `tests/test_fixed_parameter_generation.py`
- Delete: `tests/test_locust_245_baseline.py`
- Delete: `tests/test_minio_parse.py`
- Delete: `tests/test_report_generator.py`
- Delete: `tests/test_services.py`

**Interfaces:**
- Consumes: Task 1 已删除 `src/locust_skills`
- Produces: `tests/` 中不再存在 import `locust_skills`（非 `locust_skills_ui`）的测试文件

- [ ] **Step 1: 删除测试文件**

Run:

```bash
rm -f \
  tests/test_cli_run.py \
  tests/test_curl_parser.py \
  tests/test_fixed_parameter_generation.py \
  tests/test_locust_245_baseline.py \
  tests/test_minio_parse.py \
  tests/test_report_generator.py \
  tests/test_services.py
```

- [ ] **Step 2: 确认文件已删除**

Run:

```bash
for f in \
  tests/test_cli_run.py \
  tests/test_curl_parser.py \
  tests/test_fixed_parameter_generation.py \
  tests/test_locust_245_baseline.py \
  tests/test_minio_parse.py \
  tests/test_report_generator.py \
  tests/test_services.py
do
  test ! -f "$f" || exit 1
done
echo TESTS_GONE
```

Expected: 输出 `TESTS_GONE`

- [ ] **Step 3: 确认 tests 目录无 `from locust_skills.` / `import locust_skills`（允许 `locust_skills_ui`）**

Run:

```bash
rg -n 'from locust_skills[^._]|import locust_skills$|from locust_skills import|import locust_skills\.' tests || true
rg -n 'from locust_skills\.|import locust_skills$' tests || true
```

更精确校验：

```bash
rg -n 'locust_skills(?!_ui)' tests || echo NO_LOCUST_SKILLS_REFS
```

Expected: 输出 `NO_LOCUST_SKILLS_REFS`（或无匹配行）

- [ ] **Step 4: Commit（若用户要求提交；否则跳过）**

```bash
git add -u tests
git commit -m "$(cat <<'EOF'
test: 移除仅覆盖 locust-skills 的用例

EOF
)"
```

---

### Task 3: 更新 pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: Task 1–2 已删除包与测试
- Produces: 无 `locust-skills` console script；packages.find 不再包含 `locust_skills*`；pytest 不再扫描 `skills/locust-skills/generator-locust`

- [ ] **Step 1: 将 `[project.scripts]` 改为只保留 ui 入口**

把：

```toml
[project.scripts]
locust-skills = "locust_skills.cli:app"
locust-skills-ui = "locust_skills_ui.cli:app"
```

改成：

```toml
[project.scripts]
locust-skills-ui = "locust_skills_ui.cli:app"
```

- [ ] **Step 2: 更新 packages.find.include**

把：

```toml
include = ["locust_skills", "locust_skills.*", "locust_skills_ui"]
```

改成：

```toml
include = ["locust_skills_ui"]
```

- [ ] **Step 3: 更新 pytest testpaths**

把：

```toml
testpaths = [
    "tests",
    "skills/locust-skills/generator-locust",
]
```

改成：

```toml
testpaths = [
    "tests",
]
```

- [ ] **Step 4: 核对未改动的约束项仍在**

确认以下仍存在且未改名：

- `name = "locust-skills"`
- `locust-skills-ui = "locust_skills_ui.cli:app"`
- `[tool.setuptools.package-data]` 下的 `locust_skills_ui = [...]` 整块不动

- [ ] **Step 5: 校验 toml 关键字段**

Run:

```bash
python - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
scripts = data["project"]["scripts"]
assert "locust-skills" not in scripts
assert scripts["locust-skills-ui"] == "locust_skills_ui.cli:app"
includes = data["tool"]["setuptools"]["packages"]["find"]["include"]
assert includes == ["locust_skills_ui"]
assert data["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
assert data["project"]["name"] == "locust-skills"
print("PYPROJECT_OK")
PY
```

Expected: 输出 `PYPROJECT_OK`

- [ ] **Step 6: Commit（若用户要求提交；否则跳过）**

```bash
git add pyproject.toml
git commit -m "$(cat <<'EOF'
chore(build): 从包装配置移除 locust-skills 入口

EOF
)"
```

---

### Task 4: 更新 README.md

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 3 已无 `locust-skills` CLI
- Produces: README 不再引导 `locust-skills` CLI/Skill；仍描述 `locust-skills-ui`

- [ ] **Step 1: 删除 `### locust-skills run` 整节（含两个示例代码块）**

删除从 `### \`locust-skills run\`` 起，到该节结束（下一节 `### 查看帮助` 之前）的全部内容。

- [ ] **Step 2: 更新「查看帮助」代码块**

把：

```bash
locust-skills --help
locust-skills run --help
locust-skills-ui --help
locust-skills-ui run --help
```

改成：

```bash
locust-skills-ui --help
locust-skills-ui run --help
```

- [ ] **Step 3: 更新「包含的 Skills」表**

删除行：

```markdown
| `locust-skills` | 基础脚本生成与压测规则 |
```

其余 ui 子 skill 行保留。

- [ ] **Step 4: 更新「检查命令入口」**

把：

```bash
locust-skills --help
locust-skills-ui --help
locust-skills-ui run --help
```

改成：

```bash
locust-skills-ui --help
locust-skills-ui run --help
```

- [ ] **Step 5: 更新「项目结构」**

把结构树改成（注意：本轮不宣称已删除 ui CLI 源码状态，按「保留 ui、去掉基础包」写）：

```text
.
├── .cursor/commands/locust_skills_ui.md  # Cursor 斜杠命令
├── src/locust_skills_ui/                 # Web UI 全流程 CLI
├── skills/locust-skills-ui/              # Web UI 压测 Skill
├── tests/                                # 自动化测试
├── pyproject.toml                        # Python 包和 CLI 入口配置
└── README.md
```

即删除这两行：

```text
├── src/locust_skills/                    # 基础脚本生成 CLI
├── skills/locust-skills/                 # 基础压测 Skill
```

- [ ] **Step 6: 删除 FAQ「只想生成脚本，不想启动压测」整节**

删除从 `### 只想生成脚本，不想启动压测` 到该节正文结束（下一节 `## 安全注意事项` 之前）。

- [ ] **Step 7: 轻量调整开篇（可选但推荐，仍属 README 同步）**

若开篇仍写「CLI 与 Cursor Skills 集合」且主要指向基础能力，保持以 Web UI 为主的现有表述即可；**不要**在本轮把 README 改写成纯 Skill-first 长文。禁止改动 `locust-skills-ui run` 使用示例的参数与流程描述意图。

- [ ] **Step 8: 校验 README 无 locust-skills CLI 引导**

Run:

```bash
rg -n 'locust-skills run|locust-skills --help|skills/locust-skills[^-]|`locust-skills`' README.md || echo README_OK
```

Expected: 输出 `README_OK`，或仅剩包名/仓库名 `locust-skills` 等无 CLI 语义命中。若仍命中仓库标题 `# locust-skills` 或 wheel 文件名 `locust_skills-0.1.0`，可接受；不得再出现 `locust-skills run`。

额外强制检查：

```bash
rg -n 'locust-skills run' README.md && exit 1 || echo NO_RUN_CMD
```

Expected: `NO_RUN_CMD`

- [ ] **Step 9: Commit（若用户要求提交；否则跳过）**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: 移除 README 中的 locust-skills 使用说明

EOF
)"
```

---

### Task 5: 最终验收

**Files:**
- Verify only（不修改 ui skill / command）

**Interfaces:**
- Consumes: Task 1–4 全部完成
- Produces: 满足设计文档验收标准的核对结果

- [ ] **Step 1: 路径与入口验收**

Run:

```bash
test ! -d src/locust_skills
test ! -d skills/locust-skills
test -d skills/locust-skills-ui
test -f .cursor/commands/locust_skills_ui.md
python - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
assert "locust-skills" not in data["project"]["scripts"]
assert "locust-skills-ui" in data["project"]["scripts"]
print("ACCEPT_PATHS_OK")
PY
```

Expected: 输出 `ACCEPT_PATHS_OK`

- [ ] **Step 2: 残留引用扫描（排除 ui 与设计/计划文档中的说明性引用）**

Run:

```bash
rg -n --glob '!docs/superpowers/**' --glob '!**/volcengine-mcp-server/**' \
  -e 'from locust_skills[.]' -e 'import locust_skills$' -e 'skills/locust-skills[^-]' \
  -e 'locust-skills = "locust_skills.cli' || echo NO_CODE_REFS
```

Expected: `NO_CODE_REFS`

- [ ] **Step 3: 确认 ui 资产未被本轮改动（相对 git，若有未提交 ui 改动则只报告，不回滚）**

Run:

```bash
git diff --name-only -- skills/locust-skills-ui .cursor/commands/locust_skills_ui.md plugins locust-skills-ui.example.yaml
```

Expected: 若输出非空，仅说明这些文件本轮前已有改动或被误改；若误改了 ui skill/command，必须还原这些路径后再继续。本计划任务不得主动编辑它们。

- [ ] **Step 4: 收集验收摘要发给用户**

列出：已删路径、`pyproject`/`README` 变更要点、已知未修复项（`src/locust_skills_ui` 缺失导致 UI 测试仍可能失败）。

---

## Spec coverage self-check

| Spec 要求 | Task |
| --- | --- |
| 删除 `skills/locust-skills/`、`src/locust_skills/` | Task 1 |
| 删除 7 个专用测试 | Task 2 |
| 更新 `pyproject.toml` scripts/include/testpaths，保留包名 | Task 3 |
| 更新 README，去掉 locust-skills 引导 | Task 4 |
| 不动 ui skill/command/plugins/example/ui 测试 | Task 1–5 约束 + Task 5 核对 |
| 验收标准 | Task 5 |
