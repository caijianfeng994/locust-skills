---
name: gitlab-upload
description: Use when Locust 压测脚本、配置、运行脚本或报告产物需要推送到 GitLab 项目，并需要创建或推送 tag。
---

# GitLab Upload Skill

## 目标

把当前 Locust 工程变更推送到固定 GitLab 项目，并按压测批次创建 tag、推送 tag，触发 GitLab CI 构建和部署流程。

固定远程仓库：

```text
${gitlab.project_url}
```

## 触发条件

- 用户要求“推送 GitLab”“上传 GitLab”“提交到 commlocust”。
- 用户要求“新增 tag”“推送 tag”“触发 GitLab CI”。
- 主流程执行到 Locust 脚本、配置、`start.sh`、MinIO 上传脚本或压测说明需要交付 GitLab 的阶段。

## 输入上下文

| 字段 | 用途 |
| --- | --- |
| `gitlab_project_path` | 默认 `${gitlab.project_url}` |
| `gitlab_branch` | 要推送的分支；未提供时使用当前分支 |
| `gitlab_remote_name` | 默认 `origin`，如果当前 `origin` 不是目标仓库，可使用 `commlocust` |
| `gitlab_tag` | 要创建并推送的 tag；未提供时按 `locust-YYYYMMDD-HHMMSS` 生成 |
| `commit_message` | 提交信息；未提供时使用中文说明本次压测脚本或配置变更 |

## 推送流程

1. 查看当前分支、远程仓库和工作区状态：

```bash
git branch --show-current
git remote -v
git status --short
```

2. 确认远程地址。如果没有目标远程，新增 `commlocust`；如果已有远程但不是目标地址，不要覆盖用户配置，优先新增独立远程：

```bash
git remote add commlocust ${gitlab.project_url}.git
```

如果远程已存在，校验地址：

```bash
git remote get-url commlocust
```

3. 检查工作区变更，并只提交本次 Locust 交付相关文件：

```text
locustfile.py
start.sh
requirements.txt
setting/setting.py
scripts/upload_locust_reports_to_minio.py
config/*.csv
.gitlab-ci.yml
```

不要执行无差别 `git add .`。提交前必须检查 `git status --short` 和 `git diff`，只暂存本次需要部署的 Locust 交付文件；不要误提交密钥、Token、临时报告、`__pycache__`、`.pyc`、本地 IDE 文件、子仓库或无关 CSV。

```bash
git add locustfile.py
git commit -m "feat: 更新 Locust 压测脚本"
```

4. 推送分支到 GitLab：

```bash
git push commlocust HEAD:<gitlab_branch>
```

如果使用当前分支同名推送：

```bash
git push -u commlocust HEAD
```

5. 创建 tag。tag 必须指向当前提交，推荐格式：

```text
locust-YYYYMMDD-HHMMSS
```

命令：

```bash
git tag -a "$GITLAB_TAG" -m "Locust 压测交付 $GITLAB_TAG"
```

如果 tag 已存在，停止并让用户确认是否换名；不要删除或覆盖远程 tag。

6. 推送 tag：

```bash
git push commlocust "$GITLAB_TAG"
```

7. 验证远程分支和 tag：

```bash
git ls-remote --heads commlocust
git ls-remote --tags commlocust "$GITLAB_TAG"
```

## Tag 命名规则

默认使用时间戳：

```bash
GITLAB_TAG="locust-$(date +%Y%m%d-%H%M%S)"
```

如果本次压测有明确业务名，可用：

```text
locust-<业务名>-YYYYMMDD-HHMMSS
```

业务名只使用小写英文、数字和短横线，例如：

```text
locust-summer-draw-20260714-172000
```

## GitLab CI 触发说明

当前 `.gitlab-ci.yml` 使用 tag 触发构建、部署和 K8S 压测：

```yaml
only:
  - tags
```

因此必须推送 tag 才会触发镜像构建、K8S 发布和压测 Job。只推送分支不会触发当前 CI 的 tag 流程。

CI 中的 `【预发布】K8S压测` 会在集群内创建一次性分布式压测资源：

1. 创建 master Service，暴露 Locust master `5557/5558`。
2. 创建 master Job，设置 `LOCUST_MODE=master` 与 `LOCUST_EXPECT_WORKERS=<worker数量>`。
3. 创建 worker Job，按 `LOADTEST_WORKERS` 并行启动多个 worker，并通过 `LOCUST_MASTER_HOST=<master service>` 连接 master。
4. master 先执行 `LOCUST_ENABLE_SMOKE=true` 的 `1` 用户 smoke 压测。
5. smoke 通过后才继续执行 `200、300、500` 三轮正式压测。
6. smoke 命令失败、未产生请求或 CSV 中存在失败请求时，master Job 直接失败，正式压测不会运行。
7. smoke 和正式压测都必须在 K8S 分布式 Job 中执行，不作为本地压测步骤。

## 成功输出

完成后输出：

```yaml
gitlab_upload_context:
  project: "${gitlab.project_url}"
  remote: "commlocust"
  branch: "<gitlab_branch>"
  tag: "<gitlab_tag>"
  commit: "<commit_sha>"
  push_status: success
  ci_trigger: tag
```

## 失败处理

- 远程鉴权失败：提示检查 GitLab 凭证、SSH key、Token 或当前网络。
- tag 已存在：停止，要求用户提供新 tag；不要覆盖远程 tag。
- push 被拒绝：先 `git fetch commlocust` 查看远程状态，不要强推。
- 工作区存在无关变更：只提交本次 Locust 交付文件，保留用户其他变更。
