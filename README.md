# PolySpace 聚境工作台 - 项目文档

## 1. 项目概述

**PolySpace 聚境工作台** 是一个 AI 驱动的个人生产力平台，整合了智能体系统、工作台工具和跨设备协同能力。项目采用三层架构设计，将 AI Agent 能力与生产力工具深度融合，支持多端协同工作。

### 核心理念

- **交互与执行分离**：聊天模块负责拟人化交互，执行模块负责任务处理，两者通过"执行"工具异步桥接
- **分级模型调度**：根据任务复杂度自动路由到不同能力的 LLM 模型，优化成本与质量
- **统一工具接口**：所有工具（内置、MCP、Skills、设备桥接）遵循统一的状态机生命周期
- **跨设备协同**：类 Git 分支模型的分布式架构，支持端云同步
- **主动服务**：基于上下文感知的主动服务系统，从被动响应转向主动关怀
- **全链路审计**：每次操作留痕，支持链路追踪和完整性校验

## 2. 系统架构

```
+------------------------------------------------------------------+
|                        用户界面层                                  |
|  +------------------+  +------------------+  +------------------+ |
|  |  Web 前端        |  |  Android 客户端   |  |  Windows 桌面端  | |
|  |  Vue 3 + Vite    |  |  Kotlin/Compose  |  |  Electron        | |
|  |  + Pinia         |  |  + WebView       |  |  + robotjs       | |
|  |  21个工作台应用   |  |  19个原生工具     |  |  设备桥接        | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                     |                      |           |
+-----------+---------------------+----------------------+-----------+
            |                     |                      |
            v                     v                      v
+------------------------------------------------------------------+
|                     后端层 (Python 3.11+ / FastAPI)                |
|                                                                    |
|  +-------------------+  +-------------------+  +----------------+ |
|  | API 路由层         |  | 核心模块层         |  | 服务层          | |
|  | REST + WebSocket  |  |                   |  | 20 个业务服务   | |
|  | 15 个路由组       |  | agent/   智能体    |  +----------------+ |
|  +-------------------+  | memory/  记忆      |                     |
|                         | llm/     模型调度  |                     |
|                         | tool/    工具系统  |                     |
|                         | skills/  技能系统  |                     |
|                         | personality/ 拟人  |                     |
|                         | safety/  安全治理  |                     |
|                         | connector/ 连接器  |                     |
|                         | mcp/     MCP协议   |                     |
|                         | coordination/ 统筹 |                     |
|                         | audit/   审计      |                     |
|                         | inference/ 推理    |                     |
|                         | vertical/ 垂类     |                     |
|                         +-------------------+                     |
+------------------------------------------------------------------+
            |                     |                      |
            v                     v                      v
+------------------------------------------------------------------+
|                          数据层                                    |
|  +------------------+  +------------------+  +------------------+ |
|  | SQLite           |  | ChromaDB         |  | 文件系统         | |
|  | (aiosqlite)      |  | (向量存储)        |  | 文档/策略/技能   | |
|  | + 审计数据库      |  |                  |  |                  | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

## 3. 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **后端框架** | FastAPI | >=0.115.0 | 异步 Web 框架 |
| **后端运行时** | uvicorn | >=0.30.0 | ASGI 服务器 |
| **数据验证** | pydantic | >=2.0 | 数据模型与校验 |
| **配置管理** | pydantic-settings | >=2.0 | 环境变量配置 |
| **ORM** | SQLAlchemy | >=2.0 | 异步数据库操作 |
| **数据库迁移** | Alembic | >=1.13 | 数据库版本管理 |
| **数据库** | SQLite + aiosqlite | >=0.20 | 异步 SQLite 驱动 |
| **LLM 网关** | LiteLLM | >=1.50 | 多供应商模型统一接入 |
| **HTTP 客户端** | httpx | >=0.27 | 异步 HTTP 请求 |
| **WebSocket** | websockets | >=12.0 | 实时通信 |
| **前端框架** | Vue | ^3.5.13 | 渐进式 JavaScript 框架 |
| **前端构建** | Vite | ^5.4.0 | 下一代前端构建工具 |
| **状态管理** | Pinia | ^2.3.0 | Vue 官方状态管理 |
| **路由** | Vue Router | ^4.5.0 | Vue 官方路由 |
| **TypeScript** | TypeScript | ~5.7.0 | 类型安全 |
| **HTTP 库** | Axios | ^1.7.9 | HTTP 请求 |
| **Markdown** | markdown-it | ^14.1.0 | Markdown 渲染 |
| **代码高亮** | highlight.js | ^11.11.0 | 代码语法高亮 |
| **Android 语言** | Kotlin | 2.1.0 | Android 原生开发 |
| **Android UI** | Jetpack Compose | BOM 2024.12.01 | 声明式 UI |
| **Android 设计** | Material3 | - | Material Design 3 |
| **Android 网络** | OkHttp | 4.12.0 | HTTP 客户端 |
| **桌面端** | Electron | ^33.2.0 | 跨平台桌面应用 |
| **桌面自动化** | robotjs | ^0.6.0 | 键鼠模拟 |
| **桌面截图** | screenshot-desktop | ^1.15.0 | 屏幕截图 |
| **向量数据库** | ChromaDB | >=0.4.0 (可选) | 记忆向量存储 |
| **Python 包管理** | uv | - | 快速 Python 包管理器 |
| **Node 包管理** | npm | - | Node.js 包管理 |
| **Android 构建** | Gradle | 8.7.3 | Android 构建系统 |

## 4. 目录结构

```
PolySpace/
├── backend/                          # Python 后端
│   ├── app/
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理 (pydantic-settings)
│   │   ├── dependencies.py           # 依赖注入
│   │   ├── api/
│   │   │   └── v1/                   # REST API v1 路由
│   │   │       ├── chat.py           # 聊天消息、历史、会话
│   │   │       ├── workspace.py      # 工作台管理
│   │   │       ├── tools.py          # 工具列表与调用
│   │   │       ├── models.py         # LLM 模型配置
│   │   │       ├── settings.py       # 系统设置
│   │   │       ├── files.py          # 文件管理
│   │   │       ├── sync.py           # 数据同步
│   │   │       ├── dashboard.py      # 仪表盘与智能体追踪
│   │   │       ├── email.py          # 邮件管理
│   │   │       ├── kanban.py         # 看板管理
│   │   │       ├── ai_workspace.py   # AI 工作台 (21个应用辅助)
│   │   │       ├── ai_coordination.py # 核心协调 (智能体/记忆/做梦/进化/技能/统筹)
│   │   │       ├── audit.py          # 审计日志查询与校验
│   │   │       └── devices.py        # 设备管理
│   │   ├── core/
│   │   │   ├── agent/                # 智能体系统
│   │   │   │   ├── base.py           # BaseAgent 抽象基类
│   │   │   │   ├── react.py          # ReActAgent (思考-行动-观察循环)
│   │   │   │   ├── planner.py        # PlannerAgent (任务分解)
│   │   │   │   ├── subagent.py       # SubAgentExecutor (子任务委派)
│   │   │   │   ├── multi_agent.py    # MultiAgentOrchestrator (多智能体编排)
│   │   │   │   ├── vertical_agents.py # 9个垂类智能体 (编码/写作/数据/研究/SEO/教育/金融/DevOps/设计)
│   │   │   │   ├── evolution.py      # SelfEvolutionEngine (自我进化)
│   │   │   │   ├── session.py        # SessionRouter (会话路由)
│   │   │   │   ├── cron.py           # CronService (定时任务)
│   │   │   │   ├── dashboard.py      # DashboardManager (运行追踪)
│   │   │   │   ├── middleware.py      # MiddlewareChain (10个中间件)
│   │   │   │   ├── thread_state.py   # ThreadState (线程状态管理)
│   │   │   │   ├── prompts.py        # 深度人格化提示词模板
│   │   │   │   ├── sandbox.py        # 沙箱执行环境
│   │   │   │   └── mate/             # MATE 多智能体模式
│   │   │   │       ├── coordinator.py # MateCoordinator (LLM智能体选择)
│   │   │   │       └── registry.py   # AgentRegistry (标签/能力查找)
│   │   │   ├── memory/               # 记忆系统
│   │   │   │   ├── manager.py        # MemoryManager (统一记忆管理)
│   │   │   │   ├── dual_memory.py    # DualMemorySystem (工作+交互双记忆)
│   │   │   │   ├── dreaming.py       # MemoryDreamer (做梦巩固)
│   │   │   │   ├── consolidator.py   # MemoryConsolidator (记忆整合)
│   │   │   │   └── vector_store.py   # VectorStore (向量存储)
│   │   │   ├── llm/                  # LLM 层
│   │   │   │   ├── gateway.py        # LLMGateway (LiteLLM 封装)
│   │   │   │   ├── dispatcher.py     # ModelDispatcher (分级模型调度)
│   │   │   │   ├── models.py         # 模型配置数据类
│   │   │   │   └── providers/        # LLM 供应商适配
│   │   │   ├── tool/                 # 工具系统
│   │   │   │   ├── base.py           # BaseTool (状态机基类)
│   │   │   │   ├── registry.py       # ToolRegistry (工具注册表)
│   │   │   │   ├── internal_tools.py # 10个内置工具实现
│   │   │   │   └── unified_spec.py   # UnifiedToolSpec (统一工具规格)
│   │   │   ├── tools/                # 扩展工具实现
│   │   │   │   ├── file_tool.py      # 文件工具
│   │   │   │   ├── pdf_tool.py       # PDF 解析工具
│   │   │   │   ├── browser_tool.py   # 浏览器自动化工具
│   │   │   │   ├── desktop_tool.py   # 桌面自动化工具
│   │   │   │   ├── scheduler_tool.py # 调度工具
│   │   │   │   ├── search_tool.py    # 搜索工具
│   │   │   │   └── shell_tool.py     # Shell 执行工具
│   │   │   ├── skills/               # 技能系统
│   │   │   │   ├── loader.py         # SkillLoader (YAML 技能加载)
│   │   │   │   ├── adapter.py        # SkillToolAdapter (技能-工具适配)
│   │   │   │   └── animation.py      # SVG 动画引擎
│   │   │   ├── personality/          # 拟人化系统
│   │   │   │   ├── persona_core.py   # PersonaCore (人格内核)
│   │   │   │   ├── inner_voice.py    # InnerVoice (内心独白系统)
│   │   │   │   ├── heartflow.py      # HeartFlow (VAD连续情绪空间)
│   │   │   │   ├── expression.py     # ExpressionLearner (表达学习系统)
│   │   │   │   ├── greeting.py       # GreetingManager (情境感知主动交互)
│   │   │   │   ├── pfc.py            # PFCManager (前额叶皮层决策)
│   │   │   │   └── person_info.py    # PersonInfoManager (关系同步)
│   │   │   ├── safety/               # 安全治理
│   │   │   │   ├── policies.py       # PolicyEngine (策略引擎)
│   │   │   │   ├── monitor.py        # RuntimeMonitor (运行时监控)
│   │   │   │   └── confirmation.py   # ConfirmationManager (确认系统)
│   │   │   ├── connector/            # 连接器
│   │   │   │   ├── base.py           # BaseConnector (连接器抽象)
│   │   │   │   ├── web.py            # WebConnector
│   │   │   │   ├── android.py        # AndroidConnector
│   │   │   │   ├── windows.py        # WindowsConnector
│   │   │   │   ├── bridge_tool.py    # DeviceBridgeTool (设备桥接工具)
│   │   │   │   ├── device_manager.py # DeviceManager (设备管理器)
│   │   │   │   └── protocol.py       # 通信协议定义
│   │   │   ├── mcp/                  # MCP 协议
│   │   │   │   ├── client.py         # MCPClient (MCP 客户端)
│   │   │   │   └── adapter.py        # MCP 工具适配器
│   │   │   ├── coordination/         # 统筹模块 (主动服务)
│   │   │   │   ├── context/          # 上下文感知引擎
│   │   │   │   │   ├── aggregator.py # ContextAggregator (10种ContextSource)
│   │   │   │   │   ├── user_profile.py # DynamicUserProfile (动态用户画像)
│   │   │   │   │   ├── context_window.py # SlidingContextWindow (滑动窗口)
│   │   │   │   │   ├── trigger.py    # ProactiveTrigger (主动触发器)
│   │   │   │   │   ├── screen_handler.py # ScreenContextHandler (屏幕感知)
│   │   │   │   │   ├── notification_handler.py # NotificationHandler (通知感知)
│   │   │   │   │   ├── habit_learner.py # HabitLearner (习惯学习)
│   │   │   │   │   ├── predictor.py  # BehaviorPredictor (行为预测)
│   │   │   │   │   └── multimodal.py # SceneDetector (场景检测+多模态理解)
│   │   │   │   ├── proactive/        # 主动服务核心
│   │   │   │   │   ├── scheduler.py  # ProactiveScheduler (主动调度器)
│   │   │   │   │   ├── service_registry.py # ProactiveServiceRegistry (20个内置服务)
│   │   │   │   │   ├── channel_router.py # ChannelRouter (渠道路由)
│   │   │   │   │   ├── content_generator.py # ProactiveContentGenerator (内容生成)
│   │   │   │   │   ├── conversational.py # ConversationalProactiveService (对话式服务)
│   │   │   │   │   └── services.py   # 20个内置ProactiveServiceBase实现
│   │   │   │   ├── channels/         # 多渠道路由
│   │   │   │   │   ├── email_channel.py # EmailChannel (邮件渠道)
│   │   │   │   │   ├── voice_channel.py # VoiceChannel (语音渠道)
│   │   │   │   │   └── calendar_channel.py # CalendarChannel (日历注入)
│   │   │   │   ├── workflow/         # 工作流编排
│   │   │   │   │   └── workflow_engine.py # WorkflowEngine (5个内置模板)
│   │   │   │   ├── agent_team/       # 代理协作
│   │   │   │   │   └── coordinator.py # AgentCoordinator (7个内置专家)
│   │   │   │   ├── automation/       # 环境自动化
│   │   │   │   │   └── environment_rules.py # EnvironmentRulesEngine (8个内置规则)
│   │   │   │   ├── handoff/          # 跨设备流转
│   │   │   │   │   └── activity_handoff.py # ActivityHandoff + ContextSync
│   │   │   │   └── privacy/          # 隐私安全
│   │   │   │       └── privacy_guard.py # PrivacyGuard + ConsentManager
│   │   │   ├── audit/                # 审计系统
│   │   │   │   ├── models.py         # 审计数据模型 (28种分类, SHA-256校验)
│   │   │   │   ├── service.py        # AuditService (缓冲写入, 链路追踪)
│   │   │   │   └── middleware.py     # AuditMiddleware + WebSocketAuditHook
│   │   │   ├── inference/            # 本地推理
│   │   │   │   └── local_engine.py   # LocalInferenceEngine
│   │   │   ├── vertical/             # 垂类领域
│   │   │   │   └── finance.py        # 金融领域模块
│   │   │   ├── hub/                  # Hub 市场
│   │   │   │   └── client.py         # ClawHub 客户端
│   │   │   └── offline/              # 离线功能
│   │   │       └── manager.py        # 离线内容管理
│   │   ├── db/
│   │   │   └── database.py           # 数据库连接与初始化
│   │   ├── models/                   # SQLAlchemy 数据模型
│   │   │   ├── chat.py               # 聊天模型
│   │   │   ├── llm.py                # LLM 配置模型
│   │   │   ├── settings.py           # 设置模型 (含PersonaSettings)
│   │   │   ├── sync.py               # 同步模型
│   │   │   ├── tool.py               # 工具模型
│   │   │   ├── user.py               # 用户模型
│   │   │   └── workspace.py          # 工作台模型
│   │   └── services/                 # 业务逻辑服务
│   │       ├── chat_service.py       # 聊天服务 (拟人化管线)
│   │       ├── coordination_service.py # 统筹服务 (整合所有统筹子模块)
│   │       ├── ai_workspace_service.py # AI工作台服务 (21个应用辅助)
│   │       ├── ai_email_service.py   # AI邮件服务
│   │       ├── workspace_service.py  # 工作台服务 (智能鼓励)
│   │       ├── email_service.py      # 邮件服务
│   │       ├── calendar_service.py   # 日历服务
│   │       ├── todo_service.py       # 待办服务
│   │       ├── kanban_service.py     # 看板服务
│   │       ├── knowledge_service.py  # 知识库服务
│   │       ├── memo_service.py       # 备忘录服务
│   │       ├── pdf_service.py        # PDF 解析服务
│   │       ├── video_service.py      # 视频服务
│   │       ├── voice_service.py      # 语音服务
│   │       ├── weather_service.py    # 天气数据服务 (Open-Meteo)
│   │       ├── browser_service.py    # 浏览器服务
│   │       ├── desktop_service.py    # 桌面服务
│   │       ├── execution_service.py  # 执行服务
│   │       └── sync_service.py       # 同步服务
│   ├── data/                         # 运行时数据目录
│   │   └── .email_key                # 邮件加密密钥
│   ├── policies/
│   │   └── POLICIES.yaml             # 安全策略定义
│   ├── tests/                        # 测试目录
│   ├── Dockerfile                    # Docker 构建文件
│   ├── pyproject.toml                # Python 项目配置
│   └── alembic.ini                   # 数据库迁移配置
│
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                   # 根组件 (双模式布局 + 侧边栏)
│   │   ├── main.ts                   # 应用入口
│   │   ├── style.css                 # 全局样式 (含情绪主题CSS变量)
│   │   ├── router/
│   │   │   └── index.ts              # 路由配置 (Agent/Workspace/Settings)
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   ├── index.ts              # Store 入口
│   │   │   ├── chat.ts               # 聊天状态 (含情绪/内心独白)
│   │   │   ├── mode.ts               # 模式切换状态
│   │   │   ├── settings.ts           # 设置状态 (含人格设置)
│   │   │   ├── workspace.ts          # 工作台状态 (21个应用)
│   │   │   └── activity.ts           # 操作路径追踪状态
│   │   ├── composables/
│   │   │   ├── useChat.ts            # 聊天组合函数 (拟人化+打字节奏+上下文)
│   │   │   ├── useCloudSync.ts       # 云同步 (端云协同/推送/拉取/冲突/GitHub)
│   │   │   └── useCrossDevice.ts     # 跨设备 (设备发现/远程工具调用/能力查询)
│   │   ├── types/                    # TypeScript 类型定义
│   │   │   ├── chat.ts               # 聊天类型 (含EmotionState/InnerVoice)
│   │   │   ├── settings.ts           # 设置类型 (含PersonaSettings)
│   │   │   ├── tool.ts               # 工具类型
│   │   │   └── workspace.ts          # 工作台类型 (21个应用类型)
│   │   ├── utils/
│   │   │   ├── api.ts                # Axios 实例与拦截器
│   │   │   └── constants.ts          # 常量定义 (API/WS/斜杠命令/模型层级)
│   │   └── views/
│   │       ├── AgentView.vue         # AI Agent 视图
│   │       ├── WorkspaceView.vue     # 工作台视图
│   │       └── SettingsView.vue      # 设置视图
│   │   └── components/
│   │       ├── chat/                 # 聊天组件
│   │       │   ├── ChatPanel.vue     # 聊天面板 (含思考动画)
│   │       │   ├── ChatMessage.vue   # 消息气泡 (SVG头像+内心独白)
│   │       │   ├── ChatInput.vue     # 输入框
│   │       │   └── ToolResult.vue    # 工具结果展示
│   │       ├── common/               # 通用组件
│   │       │   ├── AppHeader.vue     # 应用头部
│   │       │   ├── AppSidebar.vue    # 应用侧边栏
│   │       │   └── SvgIcon.vue       # SVG图标组件
│   │       ├── settings/             # 设置组件
│   │       │   ├── SettingsDialog.vue # 设置对话框 (含审计日志标签页)
│   │       │   ├── GeneralSettings.vue # 通用设置
│   │       │   ├── AgentSettings.vue # Agent设置 (含人格设置面板)
│   │       │   ├── AppSettings.vue   # 应用设置
│   │       │   ├── DistributedSettings.vue # 分布式设置
│   │       │   ├── LabSettings.vue   # 实验室设置
│   │       │   └── AuditSettings.vue # 审计日志查看
│   │       └── workspace/            # 工作台组件 (21个应用)
│   │           ├── WorkspaceView.vue # 工作台主视图
│   │           ├── DocumentEditor.vue # Word文档编辑器
│   │           ├── PptEditor.vue     # PPT编辑器
│   │           ├── ExcelEditor.vue   # Excel编辑器
│   │           ├── CalendarView.vue  # 日历
│   │           ├── VideoEditor.vue   # 视频编辑器
│   │           ├── EmailClient.vue   # 邮件客户端
│   │           ├── KanbanBoard.vue   # 看板
│   │           ├── KnowledgeBase.vue # 知识库
│   │           ├── TodoList.vue      # 待办列表
│   │           ├── MemoList.vue      # 备忘录
│   │           ├── ScreenRecorder.vue # 屏幕录制 (含AI辅助)
│   │           ├── WeatherView.vue   # 天气 (城市搜索/7天预报/AI建议)
│   │           ├── MindMapView.vue   # 思维导图 (AI生成/转任务)
│   │           ├── NotesEditor.vue   # 笔记 (Markdown/AI摘要)
│   │           ├── ContactsView.vue  # 联系人 (AI会议准备)
│   │           ├── FocusTimer.vue    # 专注计时 (番茄钟/AI推荐)
│   │           ├── ImageEditor.vue   # 图片编辑 (CSS滤镜/AI描述)
│   │           ├── ReaderView.vue    # 阅读器 (AI摘要/日报)
│   │           ├── CodeEditor.vue    # 代码编辑 (AI审查/重构)
│   │           ├── FinanceView.vue   # 财务管理 (AI预算/预测)
│   │           ├── CalculatorView.vue # 计算器 (AI自然语言计算)
│   │           ├── MusicPlayer.vue   # 音乐播放 (白噪音/AI推荐)
│   │           ├── EncourageCard.vue # AI鼓励卡片 (上下文感知)
│   │           └── RecommendCard.vue # AI推荐卡片
│   ├── public/
│   │   └── favicon.svg               # SVG 图标
│   ├── index.html                    # HTML 入口
│   ├── package.json                  # Node.js 依赖
│   ├── tsconfig.json                 # TypeScript 配置
│   └── vite.config.ts                # Vite 构建配置
│
├── android/                          # Android 原生客户端
│   ├── app/
│   │   ├── build.gradle.kts          # 应用级 Gradle 配置
│   │   └── src/main/java/com/polyspace/mobile/
│   │       ├── MainActivity.kt       # 主 Activity
│   │       ├── PolySpaceApplication.kt # 应用类 (含ToolInitializer)
│   │       ├── ui/
│   │       │   ├── navigation/PolySpaceNavGraph.kt  # 导航图
│   │       │   ├── screens/
│   │       │   │   ├── home/         # 首页 (HomeScreen + ViewModel)
│   │       │   │   ├── webview/      # WebView 页面
│   │       │   │   ├── config/       # 配置页面
│   │       │   │   │   ├── BackendConfigScreen.kt   # 后端配置
│   │       │   │   │   ├── FullSettingsScreen.kt    # 完整设置 (100+项)
│   │       │   │   │   └── SettingsManager.kt       # 设置管理器
│   │       │   │   └── onboarding/   # 引导页
│   │       │   └── theme/            # Material3 主题
│   │       ├── service/
│   │       │   ├── BackendService.kt       # 后端服务管理
│   │       │   ├── MessageBridge.kt        # 消息桥接
│   │       │   ├── MessageListenerService.kt # 消息监听
│   │       │   ├── NotificationStore.kt    # 通知存储
│   │       │   ├── CalendarSyncService.kt  # 日历同步
│   │       │   ├── PolySpaceAccessibilityService.kt # 无障碍服务
│   │       │   └── CrossDeviceBridge.kt    # 跨设备执行桥接
│   │       ├── linux/
│   │       │   └── LinuxManager.kt   # Linux 环境管理 (proot)
│   │       ├── tool/                 # 原生工具系统
│   │       │   ├── NativeTool.kt     # 工具接口 + ToolRegistry
│   │       │   ├── NativeTools.kt    # 18个原生工具实现
│   │       │   └── ScreenOperationTool.kt # 屏幕操作 (多模态截图)
│   │       ├── accessibility/
│   │       │   └── AccessibilityBridge.kt # 无障碍桥接
│   │       └── receiver/
│   │           └── BootReceiver.kt   # 开机自启
│   ├── build.gradle.kts              # 项目级 Gradle 配置
│   ├── settings.gradle.kts           # Gradle 设置
│   └── gradle.properties             # Gradle 属性
│
├── desktop/                          # Electron 桌面端
│   ├── src/
│   │   ├── main/
│   │   │   └── index.js              # Electron 主进程
│   │   ├── preload/
│   │   │   └── index.js              # 预加载脚本
│   │   └── automation/
│   │       ├── manager.js            # 自动化管理器
│   │       └── tool.js               # 自动化工具
│   └── package.json                  # Electron 依赖
│
├── mobile/                           # 移动端构建脚本
│   ├── build_rootfs.py               # Linux rootfs 构建器 (Windows原生)
│   ├── build_rootfs.sh               # Shell 构建脚本
│   ├── quick_start.sh                # 快速启动脚本
│   └── start_termux.sh               # Termux 启动脚本
│
└── .trae/                            # Trae IDE 配置
    ├── memory/                       # 任务记忆文档
    └── specs/                        # 项目规格文档
```

## 5. 核心模块详解

### 5.1 智能体系统 (backend/app/core/agent/)

智能体系统是 PolySpace 的核心，支持单智能体、多智能体和 MATE 三种运行模式。

#### 5.1.1 BaseAgent 抽象基类

所有智能体的基类，定义了统一接口：

```python
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, message: str, **kwargs) -> str: ...

    @abstractmethod
    async def think(self, message: str, **kwargs) -> dict: ...
```

- `run()`: 执行完整任务，返回最终结果
- `think()`: 单步推理，返回思考结果和工具调用
- 内置消息历史管理 (`add_message`, `get_history`, `clear_history`)

#### 5.1.2 ReActAgent (单智能体模式)

实现 Think-Act-Observe 推理循环：

```
用户输入 → Think (LLM 推理) → Act (工具调用) → Observe (结果观察) → 循环或返回
```

**关键特性**：
- **循环检测** (`LoopDetector`): 检测重复工具调用，防止死循环
  - 警告阈值: 3 次重复
  - 硬限制: 5 次重复（强制切换策略）
- **结果缓存** (`ToolResultCache`): LRU + TTL 缓存，避免重复计算
  - 最大缓存: 100 条
  - TTL: 300 秒
- **执行超时**: 默认 120 秒
- **最大迭代**: 默认 10 轮
- **流式输出**: 支持 `run_stream()` 异步迭代器

#### 5.1.3 PlannerAgent (规划智能体)

负责任务分解，将复杂任务拆解为可执行步骤：
- 使用强能力模型 (TaskCategory.PLANNING) 进行规划
- 考虑步骤间的依赖关系
- 建议最优执行顺序

#### 5.1.4 SubAgentExecutor (子智能体执行器)

支持子任务的委派和后台执行：
- `delegate()`: 同步委派子任务
- `delegate_background()`: 异步后台委派，支持回调
- `wait_for_task()`: 等待后台任务完成
- `cancel_task()`: 取消后台任务
- 所有执行记录到 DashboardManager 进行追踪

#### 5.1.5 MultiAgentOrchestrator (多智能体编排器)

顶层编排器，支持单/多模式切换：
- `PlanningAgent`: 将复杂任务分解为可执行计划
- `DispatchAgent`: 按计划分发执行，支持依赖解析和并行执行
- `SubAgent`: 为特定子任务动态创建
- `VerticalAgent`: 垂类领域智能体
- `SupervisorAgent`: 质量监督，0-1 评分（低于 0.6 拒绝）

#### 5.1.6 垂类智能体 (vertical_agents.py)

9 个内置垂类智能体，每个有专属系统提示词和工具集：

| 智能体 | 领域 | 说明 |
|--------|------|------|
| `coding` | 编码 | 全栈编码，代码生成/审查/重构/调试 |
| `writing` | 写作 | 专业写作，文案/报告/创意 |
| `data` | 数据 | 数据分析，可视化/统计/洞察 |
| `research` | 研究 | 学术研究，文献/综述/假设 |
| `seo` | SEO | 搜索优化，关键词/内容/技术 |
| `education` | 教育 | 教学辅导，个性化/自适应 |
| `finance` | 金融 | 金融分析，投资/风控/合规 |
| `devops` | DevOps | 运维自动化，部署/监控/排障 |
| `design` | 设计 | UI/UX设计，原型/规范/评审 |

#### 5.1.7 MATE 模式 (mate/)

基于 LLM 的智能体选择与委派：
- `MateCoordinator`: 使用 LLM 分析用户意图，自动选择最合适的智能体
- `AgentRegistry`: 按标签/能力查找智能体，工厂模式懒加载
- 支持动态注册和发现新智能体

#### 5.1.8 中间件链 (middleware.py)

责任链模式，10 个中间件按序处理请求：

```
ThreadData → MemoryInjection → Uploads → Sandbox →
Summarization → Title → TodoList → Clarification →
LoopDetection → TokenUsage
```

| 中间件 | 功能 |
|--------|------|
| ThreadData | 线程状态初始化 |
| MemoryInjection | 注入相关记忆到上下文 |
| Uploads | 处理文件上传 |
| Sandbox | 沙箱执行环境 |
| Summarization | 长对话摘要 |
| Title | 自动生成会话标题 |
| TodoList | 待办事项提取 |
| Clarification | 澄清问询 |
| LoopDetection | 循环检测与干预 |
| TokenUsage | Token 用量统计 |

#### 5.1.9 SelfEvolutionEngine (自我进化引擎)

观察执行结果并从反馈中学习：

- **执行观察**: 记录失败或慢速执行（>5s）的任务
- **反馈学习**: 分析用户反馈，生成行为变更建议
- **提示词进化**: 基于性能指标优化系统提示词
- **持久化**: 进化数据保存到 `data/evolution/evolution_state.json`

#### 5.1.10 SessionRouter (会话路由)

管理多会话的生命周期：
- 会话创建、查找、关闭
- 空闲会话自动淘汰（TTL: 86400 秒）
- 最大会话数: 5000
- 支持按 agent/channel 路由

#### 5.1.11 CronService (定时任务)

支持三种调度模式：
- **AT**: 一次性定时执行
- **EVERY**: 固定间隔执行
- **CRON**: Cron 表达式调度（5 段式）

任务持久化到 `data/cron_jobs.json`。

### 5.2 记忆系统 (backend/app/core/memory/)

#### 5.2.1 双记忆架构 (dual_memory.py)

| 记忆类型 | 用途 | 存储 |
|----------|------|------|
| **工作记忆 (WorkingMemory)** | 任务、文件操作、日程、决策、知识 | 内存 + 持久化 |
| **交互记忆 (InteractionMemory)** | 对话、情感、偏好、沟通风格、反馈 | 内存 + 持久化 |

两个独立存储，支持统一搜索和摘要。

#### 5.2.2 MemoryManager (统一接口)

- `store()`: 存储新记忆（同时写入向量存储）
- `retrieve()`: 语义检索 + 关键词匹配
- `consolidate()`: 触发记忆巩固
- `add_fact()`: 添加事实知识
- `update_user_context()`: 更新用户画像
- `update_history_context()`: 更新历史上下文

#### 5.2.3 结构化记忆

记忆以 JSON 格式持久化，包含以下结构：

```json
{
  "version": "1.0",
  "user": {
    "workContext": { "summary": "", "updatedAt": "" },
    "personalContext": { "summary": "", "updatedAt": "" },
    "topOfMind": { "summary": "", "updatedAt": "" }
  },
  "history": {
    "recentMonths": { "summary": "", "updatedAt": "" },
    "earlierContext": { "summary": "", "updatedAt": "" },
    "longTermBackground": { "summary": "", "updatedAt": "" }
  },
  "facts": [{ "id": "", "content": "", "confidence": 0.0-1.0, "createdAt": "" }]
}
```

#### 5.2.4 做梦系统 (MemoryDreamer)

模拟人类睡眠的记忆巩固机制：

| 阶段 | 频率 | 功能 | 置信度 |
|------|------|------|--------|
| **浅层做梦 (Light)** | 每 6 小时 | 去重、提取洞察 | 0.7 |
| **深层做梦 (Deep)** | 每天凌晨 3 点 | 模式发现、长期意义分析 | 0.9 |
| **REM 做梦** | 每周日凌晨 5 点 | 创造性模式合成、隐藏关联发现 | 0.6 |

深层做梦还包含**恢复机制**：检查低置信度事实，决定恢复或剪枝。

做梦结果保存到 `data/dreams/` 目录。

#### 5.2.5 记忆整合器 (consolidator.py)

负责记忆的整合与压缩：
- 短期记忆到长期记忆的迁移
- 重复记忆的合并
- 记忆重要性的重新评估

#### 5.2.6 向量存储 (vector_store.py)

基于 ChromaDB 的语义检索：
- 文本向量化与存储
- 语义相似度搜索
- 支持元数据过滤

### 5.3 LLM 模型调度 (backend/app/core/llm/)

#### 5.3.1 LLMGateway

对 LiteLLM 的异步封装，提供统一接口：
- `acompletion()`: 异步补全
- `acompletion_stream()`: 异步流式补全
- `aembedding()`: 异步向量化
- 模型 ID 格式: `provider/model_id`（如 `openai/gpt-4o`）

#### 5.3.2 ModelDispatcher (分级模型调度)

根据任务类别自动路由到合适的模型：

| 任务类别 | 路由模型 | 典型场景 |
|----------|----------|----------|
| `planning` | 强能力模型 → 基础模型 | 复杂规划、任务分解 |
| `daily` | 高性能模型 → 基础模型 | 日常对话、工具调用 |
| `intent` | 性价比模型 → 高性能模型 → 基础模型 | 意图判断 |
| `memory` | 性价比模型 → 高性能模型 → 基础模型 | 记忆整理 |
| `browser` | 性价比模型 → 高性能模型 → 基础模型 | 浏览器操作 |
| `screen_operation` | 屏幕操作模型 → 高性能模型 → 基础模型 | 屏幕自动化 |
| `multimodal` | 多模态模型 → 基础模型 | 图片/视频/音频处理 |
| `custom` | 自定义垂类模型 → 性价比模型 → 基础模型 | 用户定义场景 |

**多模态降级策略**：当当前模型不支持视觉但输入包含多模态内容时：
1. 多模态模型先处理模态内容，生成描述
2. 描述作为上下文传给主模型
3. 为主模型增加 `ask_multimodal_model` 工具

**自定义垂类模型判断**：由性价比模型根据场景描述决定是否调用。

### 5.4 工具系统 (backend/app/core/tool/)

#### 5.4.1 工具状态机

每个工具遵循严格的状态机生命周期：

```
inactive → activating → active → calling → active
                         ↓          ↓
                    hibernating  hibernating
                         ↓          ↓
                      inactive    error
```

**状态转换规则**：
- `INACTIVE` → `ACTIVATING`: 工具被激活
- `ACTIVATING` → `ACTIVE`: 激活成功
- `ACTIVATING` → `ERROR`: 激活失败
- `ACTIVE` → `CALLING`: 工具被调用
- `CALLING` → `ACTIVE`: 调用完成
- `ACTIVE/CALLING` → `HIBERNATING`: 工具休眠
- `HIBERNATING` → `INACTIVE`: 休眠完成
- 任何状态 → `ERROR`: 发生错误

#### 5.4.2 BaseTool 抽象基类

```python
class BaseTool(ABC):
    async def activate(self) -> None: ...    # 激活工具
    async def call(self, **kwargs) -> Any: ...  # 调用工具
    async def hibernate(self) -> None: ...   # 休眠工具

    @abstractmethod
    async def _on_activate(self) -> None: ...   # 子类实现：激活逻辑
    @abstractmethod
    async def _on_call(self, **kwargs) -> Any: ...  # 子类实现：调用逻辑
    @abstractmethod
    async def _on_hibernate(self) -> None: ...  # 子类实现：休眠逻辑
```

#### 5.4.3 ToolRegistry (工具注册表)

统一管理所有工具的注册、调用和生命周期：
- `register()`: 注册工具
- `call_tool()`: 调用工具（本地优先，自动路由到远程设备）
- `activate_tool()` / `hibernate_tool()`: 工具生命周期管理
- `register_device_tools()`: 注册设备桥接工具
- `get_definitions()`: 获取 OpenAI Function Calling 格式的工具定义

**10 个内置工具**：邮件、日历、待办、知识库、备忘录、看板、记忆、协调、PDF 解析、Markitdown

#### 5.4.4 扩展工具 (tools/)

| 工具 | 文件 | 功能 |
|------|------|------|
| 文件工具 | `file_tool.py` | 文件读写、目录操作 |
| PDF 工具 | `pdf_tool.py` | PDF 解析与文本提取 |
| 浏览器工具 | `browser_tool.py` | 浏览器自动化操作 |
| 桌面工具 | `desktop_tool.py` | 桌面端键鼠模拟 |
| 调度工具 | `scheduler_tool.py` | 定时任务管理 |
| 搜索工具 | `search_tool.py` | 网络搜索 |
| Shell 工具 | `shell_tool.py` | 命令行执行 |

#### 5.4.5 统一工具规格 (unified_spec.py)

`UnifiedToolSpec` 定义统一的工具描述格式，兼容 OpenAI Function Calling 和 MCP 协议。

### 5.5 拟人化系统 (backend/app/core/personality/)

拟人化系统模拟人类认知过程，遵循"感知→思考→感受→表达"管线。

#### 5.5.1 PersonaCore (人格内核)

统一人格内核，所有子系统通过它获取人格参数：
- 人格特质定义（开放性/尽责性/外向性/宜人性/神经质）
- 说话风格配置
- 兴趣爱好与知识领域
- 人格参数的持久化与加载

#### 5.5.2 HeartFlow (VAD 连续情绪空间)

替代离散情绪分类，使用 VAD (Valence-Arousal-Dominance) 三维连续空间：
- **Valence (效价)**: 愉快-不愉快 [-1, 1]
- **Arousal (唤醒)**: 平静-激动 [-1, 1]
- **Dominance (支配)**: 被动-主动 [-1, 1]
- 支持复合情绪和连续过渡
- `process_input()`: 分析用户输入的情绪
- `get_emotion_prompt_modifier()`: 获取情绪修饰符影响 LLM 回复风格

#### 5.5.3 InnerVoice (内心独白系统)

模拟人类内心独白，支持三级可见性：
- **private**: 仅系统内部可见，不展示给用户
- **thinkable**: 可在思考过程中展示
- **visible**: 可直接展示给用户

内心独白影响回复的深度和风格。

#### 5.5.4 PFCManager (前额叶皮层决策管理器)

模拟人类前额叶皮层的决策过程：

- **目标分析** (`GoalAnalyzer`): 分析对话目标，决定继续/修改/新建/完成
- **冷场检测**: 60 秒无交互判定为冷场
- **行动规划**: 根据对话状态决定下一步行动
  - `DIRECT_REPLY`: 直接回复
  - `SEND_NEW_MESSAGE`: 主动发消息
  - `FETCH_KNOWLEDGE`: 获取知识
  - `FOLLOW_UP`: 跟进
  - `SAY_GOODBYE`: 告别
  - `END_CONVERSATION`: 结束对话
- **告别决策**: 判断是否需要告别语

#### 5.5.5 ExpressionLearner (表达学习系统)

从用户交互中学习表达风格：
- 学习用户的语言习惯和偏好
- `configure_from_persona()`: 根据人格参数调整表达
- 动态调整回复的语气、长度和措辞

#### 5.5.6 GreetingManager (情境感知主动交互)

基于时间和情境的主动问候：
- 时段感知（早上/中午/下午/晚上/深夜）
- 工作状态感知
- 个性化问候语生成

#### 5.5.7 PersonInfoManager (关系同步)

管理与用户的关系信息：
- 用户偏好和习惯记录
- 关系亲密度追踪
- `sync_relationship_to_persona()`: 将关系信息同步到 PersonaCore

### 5.6 安全治理 (backend/app/core/safety/)

#### 5.6.1 PolicyEngine (策略引擎)

基于 `POLICIES.yaml` 的规则引擎，支持三级风险分类：

| 风险级别 | 操作类型 | 处理方式 |
|----------|----------|----------|
| **high_risk** | 文件删除、系统修改、凭据访问 | 需要用户确认 (confirm) |
| **medium_risk** | 网络访问、代码执行、数据库修改 | 通知用户 (notify) |
| **low_risk** | 文件读取、搜索、列表 | 自动允许 (allow) |

策略通过正则表达式匹配操作名称。

#### 5.6.2 RuntimeMonitor (运行时监控)

- **工具抖动检测**: 30 秒内使用 5 个以上不同工具视为抖动
- **速率限制**: 每分钟最多 30 次工具调用
- **确定性验证**: 比较预期输出与实际输出

#### 5.6.3 ConfirmationManager (确认系统)

管理高风险操作的用户确认流程：
- 确认请求的创建与等待
- 超时自动拒绝
- 确认结果回调

### 5.7 连接器系统 (backend/app/core/connector/)

#### 5.7.1 BaseConnector 抽象基类

支持四种连接器类型：
- `ANDROID`: Android 设备连接器
- `WINDOWS`: Windows 桌面连接器
- `WEB`: Web 浏览器连接器

连接器遵循与工具相同的 `activate() → execute() → hibernate()` 生命周期。

#### 5.7.2 平台连接器

| 连接器 | 文件 | 功能 |
|--------|------|------|
| AndroidConnector | `android.py` | Android 设备通信 |
| WindowsConnector | `windows.py` | Windows 桌面通信 |
| WebConnector | `web.py` | Web 浏览器通信 |

#### 5.7.3 DeviceManager (设备管理器)

管理已连接设备：
- 设备注册与发现
- 心跳监控
- 工具能力声明
- 远程工具执行
- 设备状态同步

#### 5.7.4 DeviceBridgeTool (设备桥接工具)

当工具在本地不可用时，通过 WebSocket 将调用路由到已连接的远程设备。

#### 5.7.5 通信协议 (protocol.py)

定义设备间通信的消息格式和协议规范。

### 5.8 MCP 协议 (backend/app/core/mcp/)

#### MCPClient

实现 Model Context Protocol 客户端：
- 通过子进程启动 MCP 服务器
- JSON-RPC 2.0 通信
- 支持 `initialize`、`tools/list`、`tools/call` 方法
- 自动发现和注册 MCP 工具

### 5.9 技能系统 (backend/app/core/skills/)

#### 5.9.1 SkillLoader

从 YAML 文件加载技能定义：
- 自动扫描 `skills/` 目录下的 `.yaml`/`.yml` 文件
- 支持两种入口点格式：
  - 文件路径: `entry_point: "handler.py"` (查找 `execute` 或 `run` 函数)
  - 模块路径: `entry_point: "mymodule:handler_func"`
- 动态加载和缓存技能模块

#### 5.9.2 SVG 动画引擎 (animation.py)

支持 SVG 图形的动画渲染：
- 动画序列编排
- 关键帧插值
- 缓动函数支持

### 5.10 统筹模块 (backend/app/core/coordination/)

统筹模块是 PolySpace 的主动服务核心，将 AI 从被动响应转向主动关怀。包含 8 个子模块。

#### 5.10.1 上下文感知引擎 (context/)

| 组件 | 功能 |
|------|------|
| ContextAggregator | 10 种 ContextSource 聚合，事件缓冲，订阅机制，LLM 上下文生成 |
| DynamicUserProfile | 动态用户画像，7 种 ActivityState，6 种 AttentionFocus，5 种 MoodState |
| SlidingContextWindow | 4 级滑动窗口 (precise/compressed/trend/long_term)，自动压缩 |
| ProactiveTrigger | 5 种 ConditionType，AND/OR/NOT 逻辑，冷却/日限/优先级 |
| ScreenContextHandler | 屏幕感知，敏感内容检测/脱敏，LLM 分析 |
| NotificationHandler | 6 种 Category，4 级 Urgency，动作提取，时间敏感检测 |
| HabitLearner | 4 类模式 (时间/应用/通信/工作节奏)，异常检测，置信度衰减 |
| BehaviorPredictor | 行为预测，最佳时机推断，A/B 分组，准确率追踪 |
| SceneDetector | 13 种 Scene 检测，场景-服务映射，多模态理解 |

#### 5.10.2 主动服务核心 (proactive/)

| 组件 | 功能 |
|------|------|
| ProactiveScheduler | 触发评估，冷却控制，投递决策，WebSocket 推送 |
| ProactiveServiceRegistry | 20 个内置服务，5 大分类，反馈追踪，自动优化 |
| ChannelRouter | 10 种 ChannelPriority，紧急度映射，活动过滤，情绪适配 |
| ProactiveContentGenerator | 模板系统，LLM 生成，语气适配，长度控制 |
| ConversationalProactiveService | 对话式服务，目标追踪，LLM 开场/回复 |

**20 个内置主动服务**：

| 分类 | 服务 |
|------|------|
| 日程管理 | daily_briefing, meeting_prep, deadline_guard |
| 专注保护 | focus_protector, break_reminder |
| 信息推送 | news_digest, weather_alert, email_summary |
| 生活助手 | health_reminder, commute_advice |
| 工作辅助 | task_prioritizer, follow_up_reminder, learning_suggestion |

#### 5.10.3 多渠道路由 (channels/)

| 渠道 | 功能 |
|------|------|
| EmailChannel | 邮件渠道，模板渲染，日限控制，发送历史 |
| VoiceChannel | 语音渠道，耳机检测，通话中过滤，队列管理 |
| CalendarChannel | 日历注入，4 种模板，接受/拒绝，持久化 |

#### 5.10.4 工作流编排 (workflow/)

- `WorkflowEngine`: 5 个内置模板，步骤执行/重试，暂停/恢复

#### 5.10.5 代理协作 (agent_team/)

- `AgentCoordinator`: 7 个内置专家代理，域匹配，冲突解决

#### 5.10.6 环境自动化 (automation/)

- `EnvironmentRulesEngine`: 8 个内置规则，条件匹配，执行日志

#### 5.10.7 跨设备流转 (handoff/)

- `ActivityHandoff`: 设备注册，活动切换检测
- `ContextSync`: 上下文同步，冲突解决

#### 5.10.8 隐私安全 (privacy/)

| 组件 | 功能 |
|------|------|
| PrivacyGuard | 数据分级，敏感检测，脱敏处理 |
| ConsentManager | 同意管理，权限追踪 |
| LocalFirstStrategy | 本地优先策略，数据最小化 |

### 5.11 审计系统 (backend/app/core/audit/)

全链路可审计体系，确保每次操作留痕。

#### 5.11.1 审计数据模型 (models.py)

- **AuditCategory**: 28 种审计分类，覆盖 API/设备/同步/工具/策略/记忆/文件/WebSocket
- **AuditLevel**: info/warn/error/critical 四级
- **audit_logs 表**: 23 个字段，含 trace_id/span_id/parent_span_id 实现链路追踪
- **audit_integrity 表**: 完整性校验记录
- 10 个索引优化查询性能

#### 5.11.2 AuditService (审计核心服务)

- **缓冲写入**: 200 条/2 秒自动刷盘，支持高并发
- `record()`: 记录审计日志，自动计算 SHA-256 校验和
- `query()`: 多维度查询（分类/级别/操作者/设备/时间范围/trace_id）
- `get_trace_chain()`: 获取完整链路追踪
- `verify_integrity()`: 完整性校验，验证每条记录的 checksum
- `get_stats()`: 统计信息（按分类/级别/状态/设备分组）
- `AuditSpan`: 异步上下文管理器，自动记录操作耗时和异常
- **ContextVar**: 实现 trace_id/span_id 跨协程传播

#### 5.11.3 审计中间件 (middleware.py)

- `AuditMiddleware`: 自动审计所有 HTTP 请求，脱敏敏感头和字段
- `WebSocketAuditHook`: WebSocket 事件审计钩子（连接/断开/消息）

#### 5.11.4 审计集成

审计已集成到以下模块：
- **DeviceManager**: 设备注册/断开/远程执行/广播
- **Sync API**: 同步注册/推送/拉取/冲突解决
- **ToolRegistry**: 工具调用/注册/注销
- **PolicyEngine**: 策略评估/阻断/确认
- **MemoryManager**: 记忆写入/读取/巩固

#### 5.11.5 关键设计决策

- **独立审计数据库**: `polyspace_audit.db` 与主库分离，避免影响业务性能
- **使用 aiosqlite**: 避免 greenlet DLL 在 Windows 上的兼容性问题
- **SHA-256 校验和**: 每条记录自动计算 checksum，支持完整性验证
- **脱敏处理**: 自动遮蔽 authorization/cookie/password/token 等敏感字段

### 5.12 本地推理 (backend/app/core/inference/)

- `LocalInferenceEngine`: 本地模型推理引擎，支持离线场景下的模型调用

### 5.13 垂类领域 (backend/app/core/vertical/)

- `finance.py`: 金融领域专用模块，提供金融分析工具和数据模型

## 6. API 接口

### 6.1 REST API

所有 API 路径前缀为 `/api/v1`。

| 路径前缀 | 方法 | 功能 |
|----------|------|------|
| `/chat/send` | POST | 发送聊天消息 |
| `/chat/history/{session_id}` | GET | 获取聊天历史 |
| `/chat/session/{session_id}` | DELETE | 删除会话 |
| `/workspace` | - | 工作台管理 |
| `/workspace/encouragement` | GET | 获取AI鼓励话语 |
| `/workspace/encouragement/smart` | POST | 上下文感知智能鼓励 |
| `/tools` | - | 工具列表与调用 |
| `/models` | - | LLM 模型配置 |
| `/settings` | - | 系统设置 (含人格设置) |
| `/files` | - | 文件管理 |
| `/dashboard` | - | 仪表盘与追踪 |
| `/email` | - | 邮件管理 |
| `/kanban` | - | 看板管理 |
| `/ai/workspace` | - | AI 工作台 (21个应用辅助) |
| `/ai/workspace/{app}/assist` | POST | 各应用AI辅助端点 |
| `/ai/workspace/weather/*` | GET | 天气数据 (搜索/预报/当前/空气质量) |
| `/ai/coordination` | - | 核心协调 (智能体/记忆/做梦/进化/技能/统筹) |
| `/ai/coordination/proactive/*` | - | 主动服务 (列表/开关/触发/反馈/历史/统计) |
| `/ai/coordination/context/*` | - | 上下文 (摄入/获取/屏幕/通知) |
| `/ai/coordination/workflow/*` | - | 工作流 (模板/创建/执行) |
| `/ai/coordination/automation/*` | - | 自动化 (规则/评估) |
| `/ai/coordination/privacy/*` | - | 隐私 (状态/偏好/同意) |
| `/sync/register` | POST | 设备注册到同步服务 |
| `/sync/push` | POST | 推送本地变更到云端 |
| `/sync/pull` | POST | 从云端拉取变更 |
| `/sync/status/{device_id}` | GET | 查询同步状态 |
| `/sync/conflicts/{device_id}` | GET | 检测同步冲突 |
| `/sync/resolve-conflict` | POST | 解决同步冲突 |
| `/sync/github` | POST | 加密同步到 GitHub 仓库 |
| `/devices` | - | 设备管理 (WebSocket连接/工具调用/能力查询) |
| `/audit/logs` | GET | 审计日志查询 |
| `/audit/trace/{trace_id}` | GET | 链路追踪 |
| `/audit/verify` | POST | 完整性校验 |
| `/audit/stats` | GET | 审计统计 |
| `/audit/categories` | GET | 审计分类列表 |
| `/health` | GET | 健康检查 |

### 6.2 WebSocket

路径: `/ws`

支持：
- 聊天消息实时通信
- 设备命令下发
- 流式响应
- 主动服务推送

### 6.3 请求/响应格式

聊天请求：
```json
{
  "message": "用户消息",
  "session_id": "可选，会话ID",
  "mode": "agent",
  "operation_path": "可选，操作路径上下文"
}
```

聊天响应：
```json
{
  "session_id": "会话ID",
  "reply": "AI 回复",
  "tool_calls": [],
  "emotion": { "valence": 0.5, "arousal": 0.3, "dominance": 0.2 },
  "inner_voice": { "content": "...", "visibility": "thinkable" },
  "action_type": "DIRECT_REPLY",
  "reflection": "..."
}
```

健康检查响应：
```json
{
  "status": "ok",
  "version": "0.1.0",
  "devices": {
    "total": 0,
    "online": 0
  }
}
```

## 7. 前端架构

### 7.1 路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | AgentView | AI Agent 聊天界面 |
| `/workspace` | WorkspaceView | 工作台模式 |
| `/settings` | SettingsView | 设置页面 |

### 7.2 状态管理 (Pinia Stores)

| Store | 功能 | 持久化字段 | 持久化 Key |
|-------|------|-----------|-----------|
| `useChatStore` | 聊天状态 | currentSessionId, messages | `polyspace-chat` |
| `useModeStore` | 模式切换 | currentMode (agent/workspace) | `polyspace-mode` |
| `useSettingsStore` | 设置管理 | settings, persona | `polyspace-settings` |
| `useWorkspaceStore` | 工作台状态 | activeTab, activeDocument, activeDocumentType, completedTasksCount | `polyspace-workspace` |
| `useActivityStore` | 操作路径追踪 | history | `polyspace-activity` |

所有 Store 均通过 `pinia-plugin-persistedstate` 持久化到 `localStorage`，页面刷新后状态自动恢复。

### 7.3 云同步 (useCloudSync)

前端提供 `useCloudSync` 组合函数，支持端云协同：

| 功能 | 说明 |
|------|------|
| `register()` | 注册设备到同步服务 |
| `push()` | 推送本地设置/模式/工作台状态到云端 |
| `pull()` | 从云端拉取变更并应用到本地 |
| `sync()` | 完整同步流程（注册→推送→拉取） |
| `fetchConflicts()` | 获取同步冲突列表 |
| `resolveConflict()` | 解决同步冲突 |
| `syncToGitHub()` | 加密同步到 GitHub 仓库 |

### 7.4 跨设备调用 (useCrossDevice)

前端提供 `useCrossDevice` 组合函数，支持跨设备工具发现与调用：

| 功能 | 说明 |
|------|------|
| `fetchDevices()` | 获取所有已连接设备列表 |
| `getDeviceCapabilities()` | 获取指定设备的能力清单 |
| `executeOnDevice()` | 在远程设备上执行工具 |
| `findDeviceForTool()` | 根据工具名查找可用设备 |
| `findDevicesByCapability()` | 按能力名查找设备 |
| `disconnectDevice()` | 断开指定设备连接 |

### 7.5 工作台应用 (21个)

| 类别 | 应用 | AI 辅助能力 |
|------|------|------------|
| 文档编辑 | Word, PPT, Excel, PDF | 写作/摘要/翻译/排版/审查 |
| 多媒体 | Video, Image, Music | 剪辑建议/描述/编辑/推荐 |
| 信息管理 | Calendar, Knowledge, Todo, Memo, Email, Kanban, Contacts, Reader | 日程优化/摘要/分类/会议准备 |
| 可视化思考 | MindMap, Notes | 生成/扩展/转任务/摘要/标签 |
| 时间管理 | Focus Timer | 时长推荐/周报/休息建议 |
| 开发工具 | Code Editor, Calculator | 解释/重构/审查/生成/自然语言计算 |
| 生活管理 | Finance, Weather | 预算/报告/预测/穿搭/出行建议 |
| 系统工具 | Screen Recorder | 总结/亮点/标题/章节 |

### 7.6 设置结构

```typescript
interface Settings {
  general: {
    language: string       // 语言: 'zh-CN'
    theme: 'light' | 'dark' | 'auto'  // 主题
  }
  agent: {
    baseModel: ModelConfig | null          // 基础模型
    strongModel: ModelConfig | null        // 强能力模型
    performanceModel: ModelConfig | null   // 高性能模型
    costEffectiveModel: ModelConfig | null // 性价比模型
    verticalModels: ModelConfig[]          // 垂类模型列表
    mateModeEnabled: boolean               // Mate 多智能体模式开关
  }
  persona: {
    traits: { openness: number, conscientiousness: number, extraversion: number, agreeableness: number, neuroticism: number }
    speakingStyle: string
    interests: string[]
  }
  app: {
    defaultMode: 'agent' | 'workspace'     // 默认模式
  }
  distributed: {
    enabled: boolean        // 分布式同步开关
    githubToken: string     // GitHub 令牌
    deviceId: string        // 设备标识
    isMainBranch: boolean   // 是否为主分支
  }
  lab: {
    localInferenceEnabled: boolean  // 本地推理
    offlineMapEnabled: boolean      // 离线地图
    offlineWikiEnabled: boolean     // 离线百科
  }
}
```

### 7.7 斜杠命令

在输入框输入 `/` 触发命令菜单：

| 命令 | 说明 |
|------|------|
| `/settings` | 打开设置页面 |
| `/clear` | 清空当前对话记录 |
| `/mode` | 在 Agent 和工作台模式间切换 |

### 7.8 模型层级配置

| 层级 Key | 标签 | 说明 |
|----------|------|------|
| `base` | 基础模型 | 未配置分级模型时的默认模型 |
| `strong` | 强能力模型 | 负责规划，如 GLM-5.1、GPT-5.4 |
| `performance` | 高性能模型 | 负责日常任务，如 qwen3.5-35b-a3b |
| `cost_effective` | 性价比模型 | 负责意图判断、记忆整理等简单任务 |
| `vertical_multimodal` | 多模态模型 | 处理图片、视频、音频等模态 |
| `vertical_screen` | 屏幕操作模型 | 推荐 AutoGLM-Phone-9B |
| `vertical_custom` | 自定义垂类模型 | 用户自定义的垂类模型 |

### 7.9 侧边栏

工作台侧边栏包含：
- **推荐卡片 (RecommendCard)**: AI 推荐相关工具和操作
- **鼓励卡片 (EncourageCard)**: 上下文感知的 AI 鼓励话语，点击可展开为聊天界面
- **操作路径上下文**: 自动追踪用户最近 30 分钟的操作，作为 AI 辅助的上下文

### 7.10 开发代理配置

Vite 开发服务器配置了代理：
- `/api` → `http://localhost:8000` (后端 API)
- `/ws` → `ws://localhost:8000` (WebSocket)

## 8. Android 客户端

### 8.1 架构

Android 客户端采用原生 Kotlin + Jetpack Compose 开发（不使用跨端框架），包含以下核心模块：

- **原生配置页面**: 后端配置、100+ 设置项
- **WebView 页面**: 承载 Web 前端界面
- **后端服务**: 通过 Linux 环境运行 Python 后端
- **无障碍服务**: 屏幕操作自动化
- **原生工具系统**: 19 个原生工具
- **跨设备桥接**: 设备注册与远程命令执行

### 8.2 关键组件

| 组件 | 说明 |
|------|------|
| `MainActivity` | 主入口 Activity |
| `PolySpaceApplication` | Application 类 (含 ToolInitializer) |
| `PolySpaceNavGraph` | Compose Navigation 导航图 |
| `HomeScreen` | 首页 |
| `WebViewScreen` | WebView 承载页 |
| `BackendConfigScreen` | 后端配置页 |
| `FullSettingsScreen` | 完整设置页 (100+ 可视化设置项) |
| `SettingsManager` | 统一设置管理器 (7大类) |
| `BackendService` | 后端服务管理 |
| `LinuxManager` | Linux 环境管理 (proot) |
| `MessageBridge` | 消息桥接 |
| `MessageListenerService` | 消息监听服务 |
| `CalendarSyncService` | 日历同步服务 |
| `PolySpaceAccessibilityService` | 无障碍服务 |
| `AccessibilityBridge` | 无障碍桥接 |
| `CrossDeviceBridge` | 跨设备执行桥接 |
| `BootReceiver` | 开机自启广播接收器 |

### 8.3 原生工具系统

#### 8.3.1 工具框架

- `NativeTool`: 工具接口，定义 `name`、`description`、`parameters`、`execute()`
- `ToolRegistry`: 工具注册表，管理工具注册与执行
- `ToolResult`: 工具执行结果封装
- `ToolInitializer`: 应用启动时自动注册所有工具

#### 8.3.2 18 个原生工具

| 工具 | 功能 |
|------|------|
| AudioRecordTool | 录音 |
| AlarmTool | 闹钟设置 |
| AppLauncherTool | 应用启动 |
| ClipboardTool | 剪贴板读写 |
| ContactTool | 联系人查询 |
| PhoneCallTool | 拨打电话 |
| SmsTool | 发送短信 |
| WifiTool | WiFi 管理 |
| BatteryTool | 电池信息 |
| LocationTool | 位置获取 |
| StorageTool | 存储信息 |
| ScreenTool | 屏幕信息 |
| FlashlightTool | 手电筒控制 |
| NotificationTool | 通知发送 |
| ShareTool | 内容分享 |
| VibrationTool | 振动控制 |
| TtsTool | 文字转语音 |
| NetworkTool | 网络信息 |

#### 8.3.3 ScreenOperationTool (屏幕操作)

多模态屏幕操作工具：
- 通过 AccessibilityService 截屏，转为 Base64 JPEG
- 截屏缩放至最大 1920px
- 同时发送 UI 层级和截图给模型进行多模态分析
- 支持扩展操作：click, long_press, swipe, input_text, scroll_up/down, back, home, recents, notifications, quick_settings, lock_screen, take_screenshot

### 8.4 设置系统 (100+ 项)

| 分类 | 数量 | 包含项 |
|------|------|--------|
| GENERAL | 7 | auto_start, language, theme_mode, onboarding, crash_report, analytics |
| AI | 22 | model, temperature, max_tokens, top_p, penalties, streaming, memory, dreaming, evolution, multi-agent, vertical agents |
| NETWORK | 11 | host, port, timeouts, retry, health_check, cross_device, HTTPS, API key |
| UI | 14 | linux, font_scale, animation, status_bar, icons, webview settings |
| SYNC | 11 | calendar, messages, files, state sync intervals and directions |
| SECURITY | 9 | accessibility, screen_operation, screenshot quality, confirmations, remote commands |
| ADVANCED | 16 | logging, debug, proot, crash handling, TTS, audio recording |

### 8.5 跨设备桥接 (CrossDeviceBridge)

- WebSocket 长连接实现实时双向通信（与 Desktop 端一致）
- 自动心跳保活（15 秒间隔）
- 指数退避自动重连（最多 10 次）
- 设备注册与能力清单（19 个原生工具能力声明）
- 远程工具调用（通过 WebSocket 接收 tool_call，本地执行后返回 tool_result）
- 状态同步（后端状态/消息监听/无障碍/工具数量）
- 动态能力更新（运行时发送 capability_update）

### 8.6 Linux 环境 (LinuxManager)

通过 proot 在 Android 上运行完整 Linux 环境：
- 首次启动解压 rootfs (Alpine Linux + Python 3.11 + 后端依赖)
- 首次运行自动 pip install 预打包的 wheels
- 后续启动直接运行 uvicorn

**Rootfs 大小**：
- aarch64: 67.28 MB (arm64-v8a 设备)
- x86_64: 59.47 MB (x86_64 模拟器)

### 8.7 构建配置

- `compileSdk`: 35
- `minSdk`: 26 (Android 8.0)
- `targetSdk`: 35
- `applicationId`: `com.polyspace.mobile`
- `jvmTarget`: 17

## 9. Windows 桌面端

### 9.1 架构

基于 Electron 的桌面客户端，核心功能：
- 加载 Web 前端界面
- 键鼠模拟自动化 (robotjs)
- 屏幕截图 (screenshot-desktop)
- 设备桥接 (WebSocket 连接后端)

### 9.2 IPC 接口

| 频道 | 功能 |
|------|------|
| `config:get` / `config:set` | 配置读写 |
| `automation:click` | 鼠标点击 |
| `automation:doubleClick` | 双击 |
| `automation:rightClick` | 右键点击 |
| `automation:type` | 输入文本 |
| `automation:keyTap` | 按键 |
| `automation:keyCombo` | 组合键 |
| `automation:scroll` | 滚动 |
| `automation:moveMouse` | 移动鼠标 |
| `automation:getMousePos` | 获取鼠标位置 |
| `automation:screenshot` | 截屏 |
| `automation:getScreenSize` | 获取屏幕尺寸 |
| `bridge:status` / `bridge:reconnect` | 设备桥接状态 |

### 9.3 构建配置

- `appId`: `com.polyspace.desktop`
- `productName`: `PolySpace`
- Windows 安装包格式: NSIS (支持自定义安装目录)

## 10. 环境配置

### 10.1 环境变量

所有环境变量以 `POLYSPACE_` 为前缀：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `POLYSPACE_LLM_BASE_MODEL` | 是 | 基础模型（未配置分级模型时所有调用使用此模型） |
| `POLYSPACE_LLM_STRONG_MODEL` | 否 | 强能力模型（规划任务） |
| `POLYSPACE_LLM_PERFORMANCE_MODEL` | 否 | 高性能模型（日常任务） |
| `POLYSPACE_LLM_COST_EFFECTIVE_MODEL` | 否 | 性价比模型（简单任务） |
| `POLYSPACE_LLM_MULTIMODAL_MODEL` | 否 | 多模态模型 |
| `POLYSPACE_LLM_SCREEN_MODEL` | 否 | 屏幕操作模型 |
| `POLYSPACE_GITHUB_TOKEN` | 否 | GitHub 令牌（云端同步） |
| `POLYSPACE_DATABASE_URL` | 否 | 数据库 URL（默认 SQLite） |
| `POLYSPACE_POLICIES_PATH` | 否 | 安全策略文件路径 |
| `POLYSPACE_MATE_MODE_ENABLED` | 否 | Mate 多智能体模式开关 |
| `POLYSPACE_DEBUG` | 否 | 调试模式 |

### 10.2 安全策略配置

安全策略定义在 `backend/policies/POLICIES.yaml`，包含以下预定义策略：

- **file_deletion** (高风险): 文件删除操作需确认
- **system_modification** (高风险): 系统修改操作需确认
- **credential_access** (高风险): 凭据访问需确认
- **network_access** (中风险): 网络访问通知用户
- **code_execution** (中风险): 代码执行通知用户
- **database_modification** (中风险): 数据库修改需确认
- **safe_operations** (低风险): 安全操作自动允许

## 11. 开发指南

### 11.1 环境准备

```bash
# 后端
cd backend
uv sync                    # 安装 Python 依赖

# 前端
cd frontend
npm install                # 安装 Node.js 依赖

# Android
# 需要 Android SDK 35 和 JDK 17

# 桌面端
cd desktop
npm install                # 安装 Electron 依赖
```

### 11.2 启动开发服务器

```bash
# 后端 (端口 8000)
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 前端 (端口 3000，自动代理到后端)
cd frontend
npm run dev

# 桌面端
cd desktop
npm run dev
```

### 11.3 构建生产版本

```bash
# 前端
cd frontend
npm run build              # 输出到 frontend/dist/

# Android
cd android
./gradlew assembleDebug    # Debug APK
./gradlew assembleRelease  # Release APK (需要签名配置)

# 桌面端
cd desktop
npm run build:win          # Windows 安装包

# 后端 Docker
cd backend
docker build -t polyspace-backend .
```

### 11.4 代码检查与测试

```bash
# 后端代码检查
cd backend
uv run ruff check .

# 后端测试
cd backend
uv run pytest

# 前端类型检查
cd frontend
npm run type-check
```

### 11.5 数据库迁移

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
```

## 12. 数据流

### 12.1 用户请求处理流程

```
1. 用户输入 → 前端 (Vue 3)
   ├── REST: POST /api/v1/chat/send
   └── WebSocket: /ws/chat/main

2. FastAPI → API 路由 → 中间件链
   ThreadData → MemoryInjection → Uploads → Sandbox →
   Summarization → Title → TodoList → Clarification →
   LoopDetection → TokenUsage

3. 中间件链 → ReActAgent / MultiAgentOrchestrator / MATE
   ├── 单智能体: Think → Act → Observe 循环
   ├── 多智能体: Planner → Dispatcher → SubAgents → Supervisor
   └── MATE: LLM选择 → 垂类Agent → 结果

4. Agent → ModelDispatcher → LLMGateway → LiteLLM → LLM 供应商

5. LLM 响应 → 工具调用 → ToolRegistry
   ├── 本地工具: BaseTool.call()
   ├── 扩展工具: browser/desktop/search/shell
   └── 远程工具: DeviceBridgeTool → DeviceManager → WebSocket 设备

6. 执行结果 → MemoryManager
   ├── 工作记忆: 任务/文件/日程/决策/知识
   ├── 交互记忆: 对话/情感/偏好/风格/反馈
   └── 结构化记忆: 用户画像、历史上下文、事实

7. 拟人化管线: 感知 → 思考 → 感受 → 表达
   ├── HeartFlow: VAD情绪分析
   ├── PFC: 行动决策
   ├── InnerVoice: 内心独白
   └── PersonaCore + ExpressionLearner: 表达调制

8. 周期性任务:
   ├── CronService: 定时任务执行
   ├── MemoryDreamer: 记忆巩固 (浅层/深层/REM)
   ├── SelfEvolutionEngine: 自我进化
   └── ProactiveScheduler: 主动服务调度

9. 审计追踪:
   ├── AuditMiddleware: HTTP请求自动审计
   ├── AuditSpan: 操作链路追踪
   └── SHA-256: 完整性校验
```

### 12.2 模块依赖关系

```
FastAPI (main.py)
  ├── API 路由 → ai_coordination.py (核心入口)
  │     ├── ReActAgent / MultiAgentOrchestrator / MATE
  │     ├── MemoryManager → DualMemorySystem → VectorStore → ChromaDB
  │     ├── CronService → CronJob → DreamStore
  │     ├── SelfEvolutionEngine → PromptEvolution
  │     └── CoordinationService → 8个子模块
  │
  ├── ModelDispatcher → PlanningAgent / DispatchAgent / ...
  │     └── LLMGateway → litellm
  │
  ├── ToolRegistry
  │     ├── 内置工具 (10 个)
  │     ├── 扩展工具 (browser/desktop/search/shell/scheduler)
  │     ├── DeviceBridgeTool → DeviceManager → WebSocket 设备
  │     ├── SkillToolAdapter → SkillLoader → YAML 技能文件
  │     └── MCPAdapter → MCPClient → MCP 服务器进程
  │
  ├── MiddlewareChain
  │     └── ThreadData → MemoryInjection → Uploads → ...
  │
  ├── Personality Pipeline
  │     ├── PersonaCore (人格内核)
  │     ├── HeartFlow (VAD情绪) → 影响 LLM 回复风格
  │     ├── InnerVoice (内心独白)
  │     ├── PFCManager (决策)
  │     ├── ExpressionLearner (表达学习)
  │     ├── GreetingManager (主动交互)
  │     └── PersonInfoManager (关系同步)
  │
  ├── AuditSystem
  │     ├── AuditMiddleware (HTTP审计)
  │     ├── AuditService (缓冲写入 + SHA-256)
  │     └── AuditSpan (链路追踪)
  │
  └── PolicyEngine + RuntimeMonitor + ConfirmationManager (安全治理)
```

## 13. 扩展开发

### 13.1 添加新工具

1. 在 `backend/app/core/tools/` 下创建新文件
2. 继承 `BaseTool`，实现 `_on_activate`、`_on_call`、`_on_hibernate`
3. 在工具注册表中注册

```python
from app.core.tool.base import BaseTool

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="工具描述",
            parameters={"type": "object", "properties": {...}}
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        return "result"

    async def _on_hibernate(self) -> None:
        pass
```

### 13.2 添加新智能体

1. 继承 `BaseAgent`，实现 `run()` 和 `think()`
2. 注册到 `AgentRegistry`（MATE 模式）
3. 可添加到 `vertical_agents.py` 作为垂类智能体

### 13.3 添加 MCP 服务器

1. 配置 `MCPServerConfig`
2. 通过 `MCPClient.register_server()` 注册
3. 调用 `MCPClient.connect()` 连接

### 13.4 添加技能

1. 在 `skills/` 目录下创建 YAML 文件
2. 定义 `name`、`description`、`entry_point`、`parameters`
3. 创建对应的 Python 入口文件，实现 `execute()` 或 `run()` 函数

### 13.5 添加安全策略

在 `backend/policies/POLICIES.yaml` 中添加新策略：

```yaml
- name: my_policy
  level: medium_risk
  patterns:
    - "pattern.*regex"
  action: notify
  message: "策略描述"
```

### 13.6 添加主动服务

1. 继承 `ProactiveServiceBase`，实现 `check()` 和 `generate()`
2. 注册到 `ProactiveServiceRegistry`
3. 配置触发条件和渠道路由

### 13.7 添加 Android 原生工具

1. 在 `android/.../tool/NativeTools.kt` 中添加新工具类
2. 实现 `NativeTool` 接口
3. 在 `ToolInitializer` 中注册

## 14. 项目约定

- **环境变量前缀**: `POLYSPACE_`
- **数据库**: SQLite + aiosqlite 异步驱动 + 独立审计数据库
- **工具生命周期**: 所有工具继承 `BaseTool`，遵循状态机生命周期
- **智能体接口**: 所有智能体继承 `BaseAgent`，实现 `run()` 和 `think()`
- **中间件模式**: 责任链模式，通过 `MiddlewareChain` 执行
- **API 响应**: 统一 JSON 结构
- **图标**: 仅使用 SVG 绘制（不使用图标字体）
- **Android**: 原生 Kotlin 开发（不使用跨端框架）
- **依赖安装**: 所有依赖安装在 D 盘，缓存和构建目录放置在 D 盘
- **代码风格**: Python 使用 Ruff (line-length=120, target=py311)
- **测试**: pytest + asyncio 自动模式
- **审计**: 所有操作自动审计，SHA-256 校验和保证完整性
- **拟人化管线**: 感知→思考→感受→表达 四阶段处理
