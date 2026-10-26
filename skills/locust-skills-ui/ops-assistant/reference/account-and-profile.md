# 账户与资料操作

本文件覆盖两个任务：

- 批量注册测试用户
- 更新用户 `schoolYear`

## 1. 批量注册测试用户

### 触发词

`batch user registration`、批量注册、测试账号、自动注册用户、`user/me/batch/users`

### 必要输入

- `userList`
- `password`

默认值：

- `role`: `student`
- `signupType`: `name`
- `os`: `mac`
- `registEntranceId`: `51`
- `channel`: `shadow`

### 默认接口

```bash
curl --location --request PUT '${ops.gateway_base_url}/backend/zlb/user/me/batch/users' \
--header 'Content-Type: application/json' \
--data-raw '{
  "userList": ["user1", "user2"],
  "role": "student",
  "password": "your-password-here",
  "signupType": "name",
  "os": "mac",
  "registEntranceId": "51",
  "channel": "shadow"
}'
```

### 执行规则

1. 保持字段名为 `userList`、`role`、`password`、`signupType`、`os`、`registEntranceId`、`channel`。
2. `userList` 与 `password` 都齐全时，默认直接执行。
3. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/batch-register-users.sh" \
  --password "your-password-here" \
  libin005 libin006 libin007
```

4. 保持用户名顺序与用户输入一致。
5. 如果用户只给用户名，其他值按默认值补齐；如果连 `password` 都没给，再追问。

### 输出规则

- 回报提交的用户名列表和接口结果摘要。
- 如果使用了默认值，要说明用了哪些默认值。

## 2. 更新用户年级

### 触发词

年级、`schoolYear`、更新年级、修改 `schoolYear`、`usercore/user/{userId}`

### 必要输入

- `userId`
- `schoolYear`

### 默认接口

```bash
curl --location --request PUT '${ops.gateway_base_url}/backend/zlb/usercore/user/69ce3c5f6159180001bf11e0' \
--header 'Content-Type: application/json' \
--data-raw '{
  "schoolYear": "九年级"
}'
```

### 执行规则

1. 保持字段名为 `schoolYear`。
2. `userId` 与 `schoolYear` 都齐全时，默认直接执行。
3. 优先使用脚本：

```bash
bash ".claude/skills/api/ops-assistant/scripts/update-user-school-year.sh" \
  --user-id "69ce3c5f6159180001bf11e0" \
  --school-year "七年级"
```

4. 如果用户只要命令或 payload，返回对应文本，不直接执行。

### 输出规则

- 回报提交的 `userId`、`schoolYear` 和接口结果摘要。
- 失败时返回关键错误和重试命令。
