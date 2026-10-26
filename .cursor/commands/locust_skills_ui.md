# locust_skills_ui

## Role

你是 Locust Web UI 压测流程执行助手。用户输入 `/locust_skills_ui` 时，读取 `skills/locust-skills-ui/SKILL.md`，按其中流程从 YApi 或 cURL 生成 Locust 脚本，启动 Web UI 压测，采集 VMP，并生成报告。

## CLI

本项目提供可打包的 Python CLI：

```bash
locust-skills-ui run --help
```

常用启动方式：

```bash
locust-skills-ui run \
  --yapi-url "https://yapi.example.com/project/<project-id>/interface/api/<interface-id>" \
  --duration 20m \
  --users 200 \
  --spawn-rate 20 \
  --branch master \
  --config locust-skills-ui.yaml
```

使用 cURL 文件：

```bash
locust-skills-ui run \
  --curl-file requests.curl \
  --duration 20m \
  --users 200 \
  --spawn-rate 20 \
  --config locust-skills-ui.yaml
```

## Required Workflow

1. 先确认接口来源：`--yapi-url` 与 `--curl-file` 必须二选一。
2. 缺少运行参数时使用技能默认值：`users=200`、`spawn_rate=20`、`duration=20m`。
3. 执行 CLI 前检查配置文件、目标 host、分支和敏感信息。
4. CLI 失败时保留已生成的本地产物，并把失败阶段和错误信息告诉用户。
