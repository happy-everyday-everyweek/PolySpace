# PolySpace API 指南

## 概述

PolySpace 提供了丰富的 REST API 和 WebSocket 接口，用于与智能体、文件、工具等进行交互。

### 基础信息

- **API 基础路径**：`/api/v1`
- **WebSocket 路径**：`/ws`
- **认证方式**：Bearer Token（从登录接口获取）

## 身份认证

### 1. 注册用户

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password",
  "email": "your_email@example.com",
  "display_name": "Your Name",
  "role": "member"
}
```

响应示例：
```json
{
  "id": "user_id",
  "username": "your_username",
  "display_name": "Your Name",
  "role": "member"
}
```

### 2. 登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

响应示例：
```json
{
  "user": {
    "id": "user_id",
    "username": "your_username",
    "display_name": "Your Name",
    "role": "member",
    "avatar": null
  },
  "token": "your_api_token",
  "expires_at": "2024-01-01T00:00:00"
}
```

### 3. 使用认证 Token

在后续的 API 请求中，将 Token 添加到请求头：

```http
Authorization: Bearer your_api_token
```

或者直接使用 Token（为了兼容性也支持）：
```http
Authorization: your_api_token
```

## 核心 API 端点

### 聊天 API

#### 发送聊天消息

```http
POST /api/v1/chat/send
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "message": "你好，请帮我写一个 Python 脚本",
  "session_id": "optional_session_id",
  "mode": "agent"
}
```

#### 流式聊天

```http
POST /api/v1/chat/stream
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "message": "你好",
  "session_id": "optional_session_id"
}
```

响应格式：Server-Sent Events (SSE)

### 文件 API

#### 上传文件

```http
POST /api/v1/files/upload
Authorization: Bearer your_api_token
Content-Type: multipart/form-data

file: [binary data]
subdir: "optional_subdirectory"
```

#### 列出文件

```http
GET /api/v1/files/list?path=optional_path
Authorization: Bearer your_api_token
```

#### 读取文件

```http
GET /api/v1/files/read/{file_id}
Authorization: Bearer your_api_token
```

#### 下载文件

```http
GET /api/v1/files/download/{file_id}
Authorization: Bearer your_api_token
```

#### 删除文件

```http
DELETE /api/v1/files/delete/{file_id}
Authorization: Bearer your_api_token
```

#### 写入文本文件

```http
POST /api/v1/files/write
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "path": "filename.txt",
  "content": "file content here",
  "subdir": "optional_subdirectory"
}
```

### 工具 API

#### 列出可用工具

```http
GET /api/v1/tools/list?include_remote=true
Authorization: Bearer your_api_token
```

#### 获取工具定义

```http
GET /api/v1/tools/definitions?include_remote=true
Authorization: Bearer your_api_token
```

#### 调用工具

```http
POST /api/v1/tools/call/{tool_name}
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "params": {
    "param1": "value1",
    "param2": "value2"
  },
  "device_id": "optional_device_id"
}
```

#### 激活工具

```http
POST /api/v1/tools/activate/{tool_name}
Authorization: Bearer your_api_token
```

#### 休眠工具

```http
POST /api/v1/tools/hibernate/{tool_name}
Authorization: Bearer your_api_token
```

### MCP (Model Context Protocol) API

#### 列出 MCP 服务器

```http
GET /api/v1/tools/mcp/servers
Authorization: Bearer your_api_token
```

#### 注册 MCP 服务器

```http
POST /api/v1/tools/mcp/register
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "name": "server_name",
  "command": "server_command",
  "args": [],
  "env": {},
  "cwd": "optional_working_directory"
}
```

#### 连接 MCP 服务器

```http
POST /api/v1/tools/mcp/connect/{server_name}
Authorization: Bearer your_api_token
```

#### 断开 MCP 服务器

```http
POST /api/v1/tools/mcp/disconnect/{server_name}
Authorization: Bearer your_api_token
```

#### 列出 MCP 工具

```http
GET /api/v1/tools/mcp/tools
Authorization: Bearer your_api_token
```

### 技能 API

#### 列出可用技能

```http
GET /api/v1/tools/skills
Authorization: Bearer your_api_token
```

#### 执行技能

```http
POST /api/v1/tools/skills/execute/{skill_name}
Authorization: Bearer your_api_token
Content-Type: application/json

{
  "param1": "value1",
  "param2": "value2"
}
```

## 错误响应

API 错误响应格式：

```json
{
  "detail": "Error message here"
}
```

常见 HTTP 状态码：

- `200`：成功
- `400`：请求参数错误
- `401`：未认证或 Token 无效
- `403`：权限不足
- `404`：资源未找到
- `500`：服务器内部错误

## 健康检查

```http
GET /health
```

响应示例：
```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "ok",
  "services": [],
  "devices": {
    "total": 0,
    "online": 0
  }
}
```
