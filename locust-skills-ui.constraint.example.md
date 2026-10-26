# 本地 VMP 约束表示例

复制为 `locust-skills-ui.constraint.local.md` 后填写。该本地文件已加入 `.gitignore`，不要提交真实实例。

| 类型 | 配置键 |
| --- | --- |
| 容器 workspace | `vmp.stage_workspace_id` |
| Redis / PG workspace | `vmp.cloud_workspace_id` |
| 预发布集群 | `vmp.preprod_cluster` |
| 命名空间 | `vmp.namespace` |

| 容器服务 | 命名空间 | Redis | PG |
| --- | --- | --- | --- |
| `example-service` | `<vmp.namespace>` | `example-redis` / `redis-example` | `example-pg` / `postgres-example` |
