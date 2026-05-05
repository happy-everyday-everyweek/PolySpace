# AGENT_Chinese.md - PolySpace 项目智能体指南

## 项目概述

**PolySpace 聚境工作台** 是一个 AI 驱动的个人生产力平台，整合了智能体系统、工作台工具和跨设备协同能力。采用三层架构：Python 后端 (FastAPI) + Vue 3 前端 + 多平台连接器 (Android/Windows/Web)。

## 系统架构

```
用户界面层
  ├── 前端 (Vue 3 + Vite + Pinia)          -- Web 单页应用
  ├── Android (Kotlin + Jetpack Compose)    -- 原生 + WebView
  └── 桌面端 (Electron)                     -- Windows 自动化

后端层 (Python 3.11+ / FastAPI)
  ├── API 路由 (REST + WebSocket)
  ├── 核心模块
  │   ├── agent/       -- ReAct 推理、多智能体编排、MATE 模式
  │   ├── memory/      -- 双记忆系统、向量存储、做梦巩固
  │   ├── llm/         -- 分级模型调度、LiteLLM 网关
  │   ├── tool/        -- 工具状态机、注册表、10 个内置工具
  │   ├── skills/      -- 技能加载器、适配器、动画引擎
  │   ├── personality/ -- HeartFlow 情感流、PFC 决策、表达学习
  │   ├── safety/      -- 策略引擎、运行时监控、确认系统
  │   ├── connector/   -- 设备管理器、桥接工具 (Android/Windows/Web)
  │   ├── mcp/         -- MCP 协议适配器与客户端
  │   └── inference/   -- 本地推理引擎
  └── 服务层           -- 18 个业务服务

数据层
  ├── SQLite (aiosqlite)    -- 主数据库
  ├── ChromaDB              -- 记忆向量存储
  └── 文件系统              -- 文档、策略、技能
```

## 关键目录

| 路径 | 用途 |
|------|------|
| `backend/app/core/agent/` | 智能体系统：ReAct 引擎、多智能体、MATE 协调器、中间件链 |
| `backend/app/core/memory/` | 记忆系统：双记忆、向量存储、整合器、做梦 |
| `backend/app/core/llm/` | LLM 层：网关 (LiteLLM)、分级调度器、模型配置 |
| `backend/app/core/tool/` | 工具系统：带状态机的基类、注册表、10 个内置工具 |
| `backend/app/core/skills/` | 技能系统：YAML 加载器、工具适配器、SVG 动画引擎 |
| `backend/app/core/personality/` | 拟人化：HeartFlow 情感、PFC 决策、问候、表达 |
| `backend/app/core/safety/` | 安全：策略引擎、运行时监控、确认机制 |
| `backend/app/core/connector/` | 连接器：设备管理器、桥接工具、通信协议 |
| `backend/app/api/v1/` | REST API 路由（14 个路由组） |
| `backend/app/services/` | 业务逻辑服务（18 个服务） |
| `frontend/src/` | Vue 3 前端：组件、组合函数、状态、视图 |
| `android/app/src/main/` | Android：Kotlin/Compose UI、Linux 管理器、服务 |
| `desktop/` | Electron 桌面端：robotjs 自动化、截图、WebSocket |
| `mobile/` | 移动端构建脚本：Android rootfs 构建器 |

## 核心数据流

```
1. 用户请求 → FastAPI → 中间件链（10 个中间件）
2. 中间件链 → ReAct 智能体（思考-行动-观察循环）
3. ReAct 智能体 → 模型调度器 → LLM 网关 (LiteLLM)
4. LLM 响应 → 工具调用 → 工具注册表
5. 工具注册表 → 本地工具 或 设备桥接（远程工具）
6. 执行结果 → 记忆系统（工作记忆 + 交互记忆）
7. 多智能体模式：规划器 → 调度器 → 子/垂类智能体 → 监督器
8. 周期性：做梦系统巩固记忆，进化引擎从反馈中学习
```

## 智能体系统详解

### 单智能体模式 (ReAct)
- `ReActAgent` 执行 Think-Act-Observe 循环，可配置最大迭代次数
- 工具结果缓存（LRU + TTL）和循环检测防止重复调用
- 中间件链处理请求：记忆注入、文件上传、沙箱执行、摘要等

### 多智能体模式
- `PlanningAgent`：将复杂任务分解为可执行计划
- `DispatchAgent`：按计划分发执行，支持依赖解析和并行执行
- `SubAgent`：为特定子任务动态创建
- `VerticalAgent`：垂类领域智能体（SEO、教育、金融）
- `SupervisorAgent`：质量监督，0-1 评分（低于 0.6 拒绝）
- `MultiAgentOrchestrator`：顶层编排器，支持单/多模式切换

### MATE 模式
- `MateCoordinator`：基于 LLM 的智能体选择与委派
- `AgentRegistry`：按标签/能力查找，工厂模式懒加载

### 自我进化
- `SelfEvolutionEngine`：观察执行结果、从用户反馈学习、进化提示词
- 进化数据持久化到 JSON 文件

## 记忆系统

### 双记忆
- **工作记忆 (WorkingMemory)**：任务、文件操作、日程、决策、知识
- **交互记忆 (InteractionMemory)**：对话、情感、偏好、沟通风格、反馈
- 两个独立存储，支持统一搜索和摘要

### 做梦（记忆巩固）
- **浅层做梦 (Light Dream)**：去重、提取洞察
- **深层做梦 (Deep Dream)**：模式发现、长期意义分析
- **REM 做梦**：创造性模式合成、发现隐藏关联

## 工具系统

### 状态机
每个工具遵循生命周期：`inactive → activating → active → calling → hibernate → active`

### 10 个内置工具
邮件、日历、待办、知识库、备忘录、看板、记忆、协调、PDF 解析、Markitdown

### 设备桥接
当工具在本地不可用时，注册表通过 WebSocket 将调用路由到已连接的远程设备。

## LLM 配置

环境变量（前缀：`POLYSPACE_`）：
- `LLM_BASE_MODEL`（必填）：日常任务默认模型
- `LLM_STRONG_MODEL`：复杂推理任务
- `LLM_PERFORMANCE_MODEL`：高性能任务
- `LLM_COST_EFFECTIVE_MODEL`：成本敏感任务
- `LLM_MULTIMODAL_MODEL`：视觉/多模态任务
- `LLM_SCREEN_MODEL`：屏幕操作任务

任务类别自动路由到合适的模型层级：规划、日常、意图、记忆、浏览器、屏幕、多模态、自定义。

## API 端点

| 前缀 | 用途 |
|------|------|
| `/api/v1/chat` | 聊天消息、历史、会话管理 |
| `/api/v1/workspace` | 工作台管理 |
| `/api/v1/tools` | 工具列表与调用 |
| `/api/v1/models` | LLM 模型配置 |
| `/api/v1/settings` | 系统设置 |
| `/api/v1/files` | 文件管理 |
| `/api/v1/sync` | 数据同步 |
| `/api/v1/dashboard` | 仪表盘与智能体追踪 |
| `/api/v1/email` | 邮件管理 |
| `/api/v1/kanban` | 看板管理 |
| `/api/v1/ai/workspace` | AI 工作台（视频/文档/PPT/Excel/日历） |
| `/api/v1/ai/coordination` | 核心协调（智能体、记忆、做梦、进化、技能） |
| `/api/v1/devices` | 设备管理 |
| `/ws` | WebSocket 聊天（消息、设备命令） |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+, FastAPI, uvicorn, pydantic, SQLAlchemy, aiosqlite, litellm |
| 前端 | Vue 3.5, TypeScript 5.7, Vite 5.4, Pinia 2.3, Vue Router 4.5, Axios |
| Android | Kotlin 2.1, Jetpack Compose, Material3, OkHttp, Commons Compress |
| 桌面端 | Electron 33.2, robotjs, screenshot-desktop, ws |
| 向量数据库 | ChromaDB（可选） |
| 构建 | uv (Python), npm/pnpm (Node), Gradle (Android) |

## 开发命令

```bash
# 后端
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm run dev

# Android（在 android/ 目录下）
./gradlew assembleDebug

# 代码检查（后端）
cd backend && uv run ruff check .

# 测试（后端）
cd backend && uv run pytest
```

## 安全策略

定义在 `backend/policies/POLICIES.yaml`：
- **高风险**（文件删除、系统修改、凭据访问）：需要用户确认
- **中风险**（网络访问、代码执行、数据库修改）：通知用户
- **低风险**（安全操作）：自动允许

## 重要约定

- 环境变量前缀：`POLYSPACE_`
- 数据库：SQLite + aiosqlite 异步驱动
- 所有工具类继承 `BaseTool`，遵循状态机生命周期
- 智能体类继承 `BaseAgent`，实现 `run()` 和 `think()` 接口
- 中间件遵循责任链模式，通过 `MiddlewareChain` 执行
- API 响应遵循统一的 JSON 结构
- 前端仅使用 SVG 图标（不使用图标字体）
- Android 使用原生 Kotlin（不使用跨端框架）
- 所有图标必须使用 SVG 绘制
- 依赖安装目录和缓存目录必须放置在 D 盘

## 核心模块连接关系

```
用户请求
  │
  ▼
FastAPI (main.py) ──→ API 路由 ──→ ai_coordination.py（核心入口）
  │                                      │
  │         ┌──────────┬───────────┬──────────────┐
  │         │          │           │              │
  ▼         ▼          ▼           ▼              ▼
ReActAgent  MultiAgent  MemoryManager  CronService  EvolutionEngine
  │         Orchestrator  │            │              │
  │         │            │            │              │
  ▼         ▼            ▼            ▼              ▼
ModelDispatcher  PlanningAgent  DualMemorySystem  CronJob  PromptEvolution
  │         DispatchAgent   │            │
  │         SupervisorAgent │            ▼
  ▼         SubAgent        ▼         DreamStore
LLMGateway  VerticalAgent  VectorStore
  │                        │
  ▼                        ▼
litellm                  ChromaDB

ToolRegistry ◀── internal_tools（10 个内置工具）
  │
  ├── DeviceBridgeTool ──→ DeviceManager ──→ WebSocket 设备
  │
  └── SkillToolAdapter ──→ SkillLoader ──→ YAML 技能文件

MiddlewareChain: ThreadData → MemoryInjection → Uploads → Sandbox →
                 Summarization → Title → TodoList → Clarification →
                 LoopDetection → TokenUsage

HeartFlow（情感）───→ 影响 LLM 回复风格
RuntimeMonitor（安全）───→ 速率限制 / 抖动检测
```
