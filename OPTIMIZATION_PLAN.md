# PolySpace 聚境工作台 - 深度优化方案

> 分析日期: 2026-04-18
> 分析范围: 后端核心模块、前端架构、桌面端、Android端、部署与运维
> 目标: 提升系统稳定性、性能、安全性和可维护性

---

## 一、后端核心模块优化

### 1.1 全局单例模式缺乏生命周期管理

**现状**: `get_memory_manager()`, `get_memory_dreamer()`, `get_cron_service()`, `get_evolution_engine()`, `get_session_router()` 等函数使用模块级全局变量 + 懒加载模式，缺少显式初始化和关闭流程。

**问题**:
- 全局变量在测试中难以替换和重置
- 没有统一的启动/关闭生命周期
- 多处硬编码路径 (`d:/PolySpace/backend/data/...`)，跨平台部署困难
- `CronService` 和 `MemoryDreamer` 未在 `lifespan` 中启动/停止

**优化方案**:
- 引入应用级 `ServiceContainer`，统一管理所有核心服务的生命周期
- 将硬编码路径统一由 `config.py` 的 `Settings` 管理，通过 `POLYSPACE_DATA_DIR` 环境变量配置
- 在 `lifespan` 中按依赖顺序启动所有服务，关闭时逆序停止
- 为测试提供 `override_dependency` 机制

**优先级**: 高
**涉及文件**: `config.py`, `main.py`, `core/memory/manager.py`, `core/memory/dreaming.py`, `core/agent/cron.py`, `core/agent/evolution.py`, `core/agent/session.py`

---

### 1.2 数据库层严重不足

**现状**: `db/database.py` 仅有 15 行代码，`init_db()` 函数体为空，SQLAlchemy 模型定义在 `models/` 目录但未与数据库初始化关联，Alembic 配置存在但无迁移脚本。

**问题**:
- 数据库表未自动创建，应用启动后无法持久化数据
- 聊天历史 API (`/chat/history/{session_id}`) 返回空列表
- 无数据库连接池配置
- 无数据库健康检查
- 缺少索引策略

**优化方案**:
- 完善 `init_db()`，使用 `create_all()` 或 Alembic 迁移创建表
- 配置 SQLAlchemy 连接池 (`pool_size`, `max_overflow`, `pool_recycle`)
- 添加数据库连接健康检查端点
- 为高频查询字段添加索引 (session_id, created_at 等)
- 实现聊天历史的真实持久化存储

**优先级**: 极高
**涉及文件**: `db/database.py`, `models/`, `alembic/`

---

### 1.3 API 层服务注入方式脆弱

**现状**: `chat.py` 使用模块级全局变量 `_chat_service` + `set_chat_service()` 函数注入服务实例，直接访问 `_chat_service._heartflow` 和 `_chat_service._persona` 等私有属性。

**问题**:
- 破坏封装性，API 层直接访问服务内部实现
- 全局可变状态，线程安全隐患
- 难以进行单元测试
- 服务未注入时返回硬编码默认值而非明确错误

**优化方案**:
- 使用 FastAPI 的 `Depends()` 依赖注入系统
- 定义服务接口 (Protocol/ABC)，API 层只依赖接口
- 移除对私有属性的直接访问，通过公共方法获取数据
- 未初始化时抛出 503 Service Unavailable 而非返回假数据

**优先级**: 高
**涉及文件**: `api/v1/chat.py`, 以及其他 API 路由文件

---

### 1.4 错误处理不一致

**现状**: 部分模块用 try/except 吞掉异常 (`except: pass` 或 `except: # ignore`)，部分直接暴露内部错误信息。

**问题**:
- `settings.ts` 中 `updatePersona` 的 catch 块为空，静默失败
- `chat.py` 的 `send_message` 在异常时返回包含内部错误信息的回复
- `ToolRegistry.call_tool` 捕获所有异常后重新抛出，但丢失原始堆栈
- `MemoryManager` 的 `store` 和 `retrieve` 方法中 audit 记录失败不影响主流程，但无告警

**优化方案**:
- 定义统一的异常层级: `PolySpaceError` -> `ToolError`, `LLMError`, `MemoryError` 等
- 实现全局异常处理中间件，统一错误响应格式
- 区分面向用户的错误消息和内部日志
- 对关键路径添加结构化错误日志

**优先级**: 高
**涉及文件**: 新建 `core/exceptions.py`, 修改 `main.py` 添加异常中间件

---

### 1.5 记忆系统性能瓶颈

**现状**: `MemoryManager` 的短期记忆使用 Python 列表，检索使用线性扫描 (`query.lower() in item.content.lower()`)；长期记忆依赖可选的 ChromaDB；结构化记忆每次读写都进行 JSON 文件 I/O。

**问题**:
- 短期记忆检索 O(n) 复杂度，随消息量增长性能下降
- `add_fact()` 每次调用都触发完整的 JSON 文件读写（load -> modify -> save）
- 文件 I/O 无异步化处理（同步 `read_text`/`write_text` 在 async 函数中）
- 向量存储未配置时，记忆检索退化为纯关键词匹配
- `MemoryItem` 无过期机制，短期记忆可能无限增长

**优化方案**:
- 短期记忆检索改用倒排索引或至少预计算 lowercase 版本
- `add_fact` / `update_user_context` 改为批量写入，引入写缓冲
- 文件 I/O 使用 `aiofiles` 或 `asyncio.to_thread()` 包装
- 为 MemoryItem 添加 TTL，自动过期清理
- 无向量存储时，使用 TF-IDF 或 BM25 作为降级检索方案

**优先级**: 中
**涉及文件**: `core/memory/manager.py`, `core/memory/dreaming.py`

---

### 1.6 LLM 调用缺乏重试和熔断机制

**现状**: `LLMGateway` 直接调用 `litellm.acompletion`，无重试、无超时、无熔断、无降级。

**问题**:
- LLM 供应商 API 不稳定时，整个请求链路直接失败
- 无请求超时控制，可能无限等待
- 无调用频率限制，可能触发供应商限流
- 多模态降级策略中，连续两次 LLM 调用（多模态模型 + 主模型）无中间缓存
- `should_use_vertical_model` 每次都调用 LLM 判断，成本高

**优化方案**:
- 为 LLM 调用添加指数退避重试 (最多 3 次)
- 添加每请求超时 (默认 60s)
- 实现简单的熔断器: 连续 N 次失败后暂停调用，一段时间后半开试探
- `should_use_vertical_model` 的判断结果缓存 (TTL 5 分钟)
- 添加 LLM 调用统计和成本追踪

**优先级**: 高
**涉及文件**: `core/llm/gateway.py`, `core/llm/dispatcher.py`

---

### 1.7 安全策略引擎正则编译性能

**现状**: `PolicyEngine.evaluate()` 每次调用都 `import re` 并执行 `re.search()`，未预编译正则。

**问题**:
- 每次策略评估都重新编译正则表达式，浪费 CPU
- `import re` 在函数内部，违反 PEP 8 且有微小的导入开销
- `_schedule_audit` 使用 `loop.create_task()` 发射即忘，任务异常无法捕获

**优化方案**:
- 在 `load_policies()` 时预编译所有正则 (`re.compile()`)
- 将 `import re` 移至模块顶部
- `_schedule_audit` 改用 `asyncio.create_task()` + 异常回调

**优先级**: 低
**涉及文件**: `core/safety/policies.py`

---

### 1.8 运行时监控器内存泄漏风险

**现状**: `RuntimeMonitor._tool_call_history` 是一个只增不减的列表，虽然有 `_cleanup_old_records()` 但仅在 `record_tool_call()` 时触发。

**问题**:
- 如果工具调用频率低但运行时间长，历史记录可能持续增长
- `get_stats()` 每次调用都遍历整个列表做过滤
- `detect_jitter()` 和 `check_rate_limit()` 也各自遍历列表

**优化方案**:
- 改用 `collections.deque` 配合 maxlen 自动淘汰
- `get_stats()` 缓存计算结果，仅在数据变化时重新计算
- 合并 `detect_jitter()` 和 `check_rate_limit()` 的遍历为一次

**优先级**: 低
**涉及文件**: `core/safety/monitor.py`

---

### 1.9 Cron 服务调度精度和可靠性

**现状**: `CronService` 使用 5 秒轮询间隔，Cron 表达式解析通过暴力遍历分钟实现。

**问题**:
- 5 秒轮询间隔导致最大 5 秒的调度延迟
- `_compute_cron_next` 最多搜索 7 天，超过 7 天的调度返回 None
- 每次执行完任务后立即持久化，高频任务时 I/O 压力大
- 任务执行异常后无指数退避重试
- `_callback` 字段无法序列化，持久化后丢失

**优化方案**:
- 使用 `asyncio.sleep()` 精确计算下次唤醒时间，而非固定 5 秒轮询
- 改进 Cron 表达式解析算法，使用标准库或 `croniter` 库
- 批量持久化: 改为定时持久化 (如每 30 秒) 而非每次执行后
- 添加任务执行失败的重试策略 (指数退避，最大 3 次)
- 将回调注册机制与持久化分离

**优先级**: 中
**涉及文件**: `core/agent/cron.py`

---

### 1.10 做梦系统缺乏并发控制和资源限制

**现状**: `MemoryDreamer` 的三个阶段 (light/deep/rem) 可以通过 `run_all_phases()` 顺序执行，但无并发保护。

**问题**:
- 多个触发源可能同时启动做梦，导致重复执行
- 做梦过程中的 LLM 调用无并发限制，可能耗尽 API 配额
- `light_dream` 的去重逻辑使用前 200 字符作为 key，可能误判
- 做梦结果写入记忆后无法回滚

**优化方案**:
- 添加 `asyncio.Lock` 防止并发做梦
- 为做梦过程的 LLM 调用设置独立的速率限制
- 改进去重逻辑: 使用 simhash 或编辑距离而非前缀匹配
- 做梦结果先标记为 "pending"，经用户确认或质量评估后再正式写入

**优先级**: 中
**涉及文件**: `core/memory/dreaming.py`

---

## 二、前端架构优化

### 2.1 前端组件缺乏代码分割

**现状**: `router/index.ts` 已使用动态 `import()` 实现路由级懒加载，但 `App.vue` 中直接导入了 `RecommendCard`, `EncourageCard`, `ChatPanel` 等组件。

**问题**:
- 工作台侧边栏组件在 Agent 模式下也会被加载
- 38 个 Vue 组件全部打包到主 bundle，首屏加载慢
- `markdown-it` 和 `highlight.js` 体积较大，但未按需加载

**优化方案**:
- `App.vue` 中的工作台侧边栏组件使用 `defineAsyncComponent()` 懒加载
- `markdown-it` 和 `highlight.js` 改为动态导入，仅在消息包含代码块时加载
- 配置 Vite 的 `manualChunks` 将第三方库分离
- 添加 `vite-plugin-compression` 启用 gzip/brotli 压缩

**优先级**: 中
**涉及文件**: `App.vue`, `vite.config.ts`, `package.json`

---

### 2.2 状态管理缺乏持久化和同步

**现状**: Pinia stores 全部使用内存状态，无持久化；`useSettingsStore` 的 `updateGeneral` 等方法只更新本地状态，不同步到后端。

**问题**:
- 页面刷新后所有状态丢失（聊天记录、设置等）
- 设置修改未持久化到后端，多设备无法同步
- `useChatStore` 的消息列表无上限，长时间聊天可能内存溢出
- 缺少离线状态管理和网络恢复机制

**优化方案**:
- 使用 `pinia-plugin-persistedstate` 持久化关键 store
- 设置修改时同步调用后端 API
- 聊天消息列表添加上限 (如 200 条)，超出时自动摘要压缩
- 添加网络状态检测 (`navigator.onLine`) 和离线队列

**优先级**: 高
**涉及文件**: 所有 stores, `main.ts`

---

### 2.3 API 层缺乏请求取消和防抖

**现状**: `useChat.ts` 的 `sendMessage` 每次都创建新请求，无取消机制；打字机效果使用 `setTimeout` 递归实现。

**问题**:
- 快速连续发送消息时，前一个请求的响应可能覆盖后一个
- 打字机效果的 `setTimeout` 在组件卸载时可能未清理
- 无请求防抖，用户快速输入时可能触发多次请求
- API 超时 30 秒过长，用户体验差

**优化方案**:
- 使用 `AbortController` 实现请求取消
- 打字机效果改用 `requestAnimationFrame` 或 `CSS animation`
- 搜索/输入类操作添加防抖 (300ms)
- 缩短 API 超时至 15 秒，流式响应使用更短超时

**优先级**: 中
**涉及文件**: `composables/useChat.ts`, `utils/api.ts`

---

### 2.4 CSS 变量体系冗余

**现状**: `style.css` 中定义了两组语义重复的变量:
- `--primary-color` / `--primary`
- `--bg-color` / `--bg-primary`
- `--text-color` / `--text-primary`

**问题**:
- 两套变量容易混淆，不同组件可能使用不同变量
- 暗色模式需要同时维护两套变量的覆盖
- 缺少设计 Token 体系，颜色/间距/字号无统一规范

**优化方案**:
- 统一为一套 CSS 变量，移除重复定义
- 建立完整的设计 Token 体系: 颜色、间距、字号、圆角、阴影
- 使用 CSS 变量实现主题切换，而非 class 切换
- 考虑引入 Tailwind CSS 或 UnoCSS 统一工具类

**优先级**: 低
**涉及文件**: `style.css`, 所有 `.vue` 文件

---

### 2.5 TypeScript 类型安全不足

**现状**: `api.ts` 的响应拦截器返回 `error.response?.data?.detail`，但 API 响应类型全部依赖运行时推断；`useChat.ts` 中 `response.data` 无类型约束。

**问题**:
- API 响应无编译时类型检查，容易因后端接口变更导致前端运行时错误
- `ChatMessage` 等类型定义与后端 Pydantic 模型不同步
- 缺少 API 错误码的枚举定义

**优化方案**:
- 为每个 API 端点定义请求/响应的 TypeScript 类型
- 使用 `openapi-typescript` 从后端 OpenAPI schema 自动生成类型
- 创建类型化的 API 客户端封装
- 添加 API 响应的运行时校验 (zod)

**优先级**: 中
**涉及文件**: `utils/api.ts`, `types/`, `composables/`

---

### 2.6 前端缺少国际化基础设施

**现状**: 虽然设置中有 `language: 'zh-CN'` 配置，但所有 UI 文本硬编码在组件中。

**问题**:
- 无法切换语言
- 新增语言需要修改所有组件
- 与 Android 端已中文化的努力不一致

**优化方案**:
- 引入 `vue-i18n` 国际化框架
- 提取所有硬编码文本到 locale 文件
- 支持中英文切换

**优先级**: 低
**涉及文件**: 所有 `.vue` 文件, 新建 `locales/` 目录

---

## 三、桌面端优化

### 3.1 Electron 安全配置不足

**现状**: `desktop/src/main/index.js` 中 `sandbox: false`，`contextIsolation: true` 但 preload 脚本暴露了大量 IPC 接口。

**问题**:
- `sandbox: false` 降低了渲染进程的安全性
- IPC 接口无权限校验，恶意网页可能调用自动化接口
- `electron-store` 在每个 IPC handler 中重复 `require` 和实例化
- 无 CSP (Content Security Policy) 配置

**优化方案**:
- 启用 `sandbox: true`，将 Node.js 操作全部移到主进程
- 为 IPC 接口添加来源验证和权限控制
- `electron-store` 实例化移到模块顶层，避免重复创建
- 配置严格的 CSP 头

**优先级**: 高
**涉及文件**: `desktop/src/main/index.js`, `desktop/src/preload/index.js`

---

### 3.2 桌面端缺乏错误处理和日志

**现状**: 桌面端代码几乎没有 try/catch，异常直接崩溃。

**问题**:
- `robotjs` 调用失败时无友好提示
- WebSocket 断连后无自动重连
- 无日志系统，问题排查困难

**优化方案**:
- 为所有 IPC handler 添加 try/catch
- 实现 WebSocket 自动重连 (指数退避)
- 添加 `electron-log` 日志系统
- 实现崩溃报告收集

**优先级**: 中
**涉及文件**: `desktop/src/main/index.js`, `desktop/src/bridge/`

---

## 四、Android 端优化

### 4.1 日历同步缺乏冲突处理

**现状**: `CalendarSyncService` 实现了双向同步，但无冲突检测和解决机制。

**问题**:
- 同一事件在两端同时修改时，后写入覆盖先写入
- 无增量同步，每次全量比对
- 同步操作在主线程执行，可能 ANR

**优化方案**:
- 实现基于时间戳的冲突检测
- 采用增量同步: 仅同步上次同步后变更的事件
- 同步操作移到 `WorkManager` 后台执行
- 添加同步状态 UI 反馈

**优先级**: 中
**涉及文件**: `CalendarSyncService.kt`

---

### 4.2 Android 缺少暗色模式

**现状**: 记忆文档中提到 "可增加暗色模式支持"，目前未实现。

**问题**:
- 系统暗色模式下应用仍为亮色，体验割裂
- Material3 本身支持动态颜色，但未启用

**优化方案**:
- 启用 Material3 的 `dynamicColor`
- 为 WebView 注入暗色模式 CSS
- 创建 `res/values-night/` 资源

**优先级**: 低
**涉及文件**: `ui/theme/`, `res/values/`

---

## 五、架构与部署优化

### 5.1 Docker 镜像优化

**现状**: `Dockerfile` 使用 `python:3.11-slim`，但安装方式混乱 (先尝试 uv，失败后 fallback 到 pip)。

**问题**:
- 镜像层未优化，每次代码变更都重新安装依赖
- 无 `.dockerignore`，可能将 `.venv/` 等大目录拷入镜像
- 生产环境使用 `--reload` 不合适
- 无健康检查配置
- 无非 root 用户运行

**优化方案**:
- 分离依赖安装层和代码拷贝层，利用 Docker 缓存
- 添加 `.dockerignore`: 排除 `.venv/`, `__pycache__/`, `.git/`, `data/`
- 生产 CMD 不使用 `--reload`
- 添加 `HEALTHCHECK` 指令
- 创建非 root 用户运行应用

**优先级**: 中
**涉及文件**: `Dockerfile`, 新建 `.dockerignore`

---

### 5.2 缺乏可观测性

**现状**: 无结构化日志、无指标收集、无分布式追踪。

**问题**:
- 生产环境问题排查困难
- 无法监控系统健康状态和性能趋势
- LLM 调用成本无法追踪

**优化方案**:
- 配置 Python `logging` 的结构化 JSON 输出
- 添加 Prometheus 指标暴露端点 (`/metrics`)
- 关键路径添加 OpenTelemetry 追踪
- LLM 调用添加 token 用量和成本追踪

**优先级**: 中
**涉及文件**: `main.py`, `core/llm/gateway.py`, 新建 `core/observability/`

---

### 5.3 测试覆盖率极低

**现状**: `tests/` 目录仅有 `conftest.py` 和空的 `__init__.py`，无实际测试用例。

**问题**:
- 核心模块无测试保护，重构风险高
- CI/CD 无法有效验证代码质量
- 回归问题无法及时发现

**优化方案**:
- 优先为核心模块添加单元测试:
  - `ToolStateMachine` 状态转换
  - `LoopDetector` 循环检测
  - `ToolResultCache` 缓存行为
  - `ModelDispatcher` 模型路由
  - `PolicyEngine` 策略评估
  - `SessionRouter` 会话管理
- 添加 API 集成测试
- 配置 pytest-cov 覆盖率报告
- 目标: 核心模块覆盖率 > 80%

**优先级**: 高
**涉及文件**: `tests/`

---

### 5.4 配置管理不完善

**现状**: `config.py` 仅定义了基本的环境变量配置，缺少验证、默认值文档和配置分层。

**问题**:
- `LLM_BASE_MODEL` 为空字符串时，应用启动不报错但运行时崩溃
- 无配置验证 (如 API Key 格式、URL 格式)
- 无开发/测试/生产环境配置区分
- 敏感信息 (API Key) 可能被日志泄露

**优化方案**:
- 添加 `@model_validator` 验证必要配置
- 实现配置分层: 环境变量 > 配置文件 > 默认值
- 敏感字段标记为 `SecretStr`，防止日志泄露
- 添加配置文档生成端点 (`/api/v1/config/schema`)

**优先级**: 中
**涉及文件**: `config.py`

---

### 5.5 WebSocket 连接管理不足

**现状**: WebSocket 路由在 `api/websocket/chat_ws.py`，但缺乏连接数限制、心跳、重连机制。

**问题**:
- 无最大连接数限制，可能被恶意连接耗尽资源
- 客户端断连后服务端可能未及时清理
- 无 WebSocket 消息大小限制
- 缺少 WebSocket 认证

**优化方案**:
- 添加最大连接数限制 (如 100)
- 实现服务端心跳检测
- 限制单条消息大小 (如 1MB)
- 添加 WebSocket 连接认证 (JWT/Token)

**优先级**: 高
**涉及文件**: `api/websocket/chat_ws.py`, `main.py`

---

## 六、优化优先级总览

| 优先级 | 编号 | 优化项 | 影响范围 | 预估工作量 |
|--------|------|--------|----------|-----------|
| 极高 | 1.2 | 数据库层完善 | 后端 | 中 |
| 高 | 1.1 | 全局单例生命周期管理 | 后端 | 中 |
| 高 | 1.3 | API 层依赖注入重构 | 后端 | 中 |
| 高 | 1.4 | 统一错误处理 | 后端 | 小 |
| 高 | 1.6 | LLM 调用重试和熔断 | 后端 | 中 |
| 高 | 2.2 | 状态持久化和同步 | 前端 | 中 |
| 高 | 3.1 | Electron 安全加固 | 桌面端 | 中 |
| 高 | 5.3 | 测试覆盖率提升 | 全项目 | 大 |
| 高 | 5.5 | WebSocket 连接管理 | 后端 | 小 |
| 中 | 1.5 | 记忆系统性能优化 | 后端 | 中 |
| 中 | 1.9 | Cron 服务调度优化 | 后端 | 中 |
| 中 | 1.10 | 做梦系统并发控制 | 后端 | 小 |
| 中 | 2.1 | 前端代码分割 | 前端 | 小 |
| 中 | 2.3 | API 请求取消和防抖 | 前端 | 小 |
| 中 | 2.5 | TypeScript 类型安全 | 前端 | 中 |
| 中 | 3.2 | 桌面端错误处理 | 桌面端 | 小 |
| 中 | 4.1 | 日历同步冲突处理 | Android | 中 |
| 中 | 5.1 | Docker 镜像优化 | 部署 | 小 |
| 中 | 5.2 | 可观测性建设 | 全项目 | 中 |
| 中 | 5.4 | 配置管理完善 | 后端 | 小 |
| 低 | 1.7 | 策略引擎正则预编译 | 后端 | 极小 |
| 低 | 1.8 | 运行时监控内存优化 | 后端 | 极小 |
| 低 | 2.4 | CSS 变量体系统一 | 前端 | 小 |
| 低 | 2.6 | 国际化基础设施 | 前端 | 中 |
| 低 | 4.2 | Android 暗色模式 | Android | 小 |

---

## 七、实施路线建议

### Phase 1: 基础加固 (1-2 周)

1. **数据库层完善** (1.2) - 让数据真正持久化
2. **统一错误处理** (1.4) - 建立异常体系
3. **配置管理完善** (5.4) - 防止启动时静默失败
4. **WebSocket 连接管理** (5.5) - 防止资源耗尽
5. **策略引擎正则预编译** (1.7) - 快速修复

### Phase 2: 核心重构 (2-3 周)

6. **全局单例生命周期管理** (1.1) - 统一服务管理
7. **API 层依赖注入重构** (1.3) - 提升可测试性
8. **LLM 调用重试和熔断** (1.6) - 提升稳定性
9. **状态持久化和同步** (2.2) - 前端数据不丢失
10. **Electron 安全加固** (3.1) - 安全基线

### Phase 3: 性能和体验 (2-3 周)

11. **记忆系统性能优化** (1.5) - 检索加速
12. **Cron 服务调度优化** (1.9) - 调度精度
13. **前端代码分割** (2.1) - 首屏加速
14. **TypeScript 类型安全** (2.5) - 开发体验
15. **Docker 镜像优化** (5.1) - 部署效率

### Phase 4: 质量和运维 (2-3 周)

16. **测试覆盖率提升** (5.3) - 质量保障
17. **可观测性建设** (5.2) - 运维能力
18. **做梦系统并发控制** (1.10) - 稳定性
19. **桌面端错误处理** (3.2) - 用户体验
20. **日历同步冲突处理** (4.1) - 数据一致性

### Phase 5: 打磨和扩展 (1-2 周)

21. **API 请求取消和防抖** (2.3)
22. **CSS 变量体系统一** (2.4)
23. **国际化基础设施** (2.6)
24. **Android 暗色模式** (4.2)
25. **运行时监控内存优化** (1.8)

---

## 八、关键指标目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 后端测试覆盖率 | ~0% | > 80% (核心模块) |
| API 响应错误格式统一率 | ~30% | 100% |
| LLM 调用成功率 (含重试) | 未知 | > 99% |
| 前端首屏加载时间 | 未知 | < 2s |
| 前端状态持久化 | 0% | 100% (关键状态) |
| Docker 镜像大小 | 未知 | < 500MB |
| 数据库表自动创建 | 否 | 是 |
| WebSocket 最大连接数限制 | 无 | 100 |
| 配置验证覆盖率 | ~10% | 100% |

---

> 本方案基于 2026-04-18 的代码状态分析，建议按优先级和依赖关系分阶段实施，每个 Phase 完成后进行验证和回顾。
