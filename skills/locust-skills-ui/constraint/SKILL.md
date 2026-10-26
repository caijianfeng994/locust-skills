---
name: locust-vmp-constraint
description: Provides default VMP monitoring constraints for Locust reports, including container, Redis and PG targets. Use when collecting VMP metrics for locust-skills-ui.
disable-model-invocation: true
---

# Locust VMP 监控约束

环境相关的 workspace、集群、命名空间、服务与 Redis/PG 实例对照，只从本地配置读取，不写在本技能正文里。

## 读取顺序

1. 读取仓库根目录 `locust-skills-ui.yaml`（由 `locust-skills-ui.example.yaml` 复制，且已被 gitignore）。
2. 使用其中的 `vmp.stage_workspace_id`、`vmp.cloud_workspace_id`、`vmp.preprod_cluster`、`vmp.namespace`、`vmp.project_name`。
3. 打开 `constraint.file` 指向的本地文件（默认 `locust-skills-ui.constraint.local.md`）。该文件保存容器服务、Redis、PG 对照表。
4. 本地文件不存在或目标服务不在表中时，停止查询对应 Redis/PG，写入 `empty_results` / `risks`，向用户确认。禁止猜测实例 ID，禁止把示例占位写成真实实例。

## 服务名

从 `locustfile.py` 的 `host` 去掉协议，取第一个域名段作为服务名。域名后缀以配置项 `service.host_suffix` 为准，不要在技能里写死后缀。

## PromQL

容器查询必须同时带配置中的集群、命名空间、`pod=~"<服务名>-.*"` 和 `container="<服务名>"`。Redis/PG 的 `Name` 与 `ResourceID` 只取本地约束表对应行。表中为 `—` 或空则跳过该项。

云实例 `workspaceId` 使用 `vmp.cloud_workspace_id`，并带 `ProjectName`=`vmp.project_name`。容器 `workspaceId` 使用 `vmp.stage_workspace_id`，并带 `cluster`=`vmp.preprod_cluster`。
