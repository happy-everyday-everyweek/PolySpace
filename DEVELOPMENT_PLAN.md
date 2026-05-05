# PolySpace 激进开发计划 -- "超维跃迁"

> 制定日期: 2026-04-17
> 执行周期: 2026-04-17 ~ 2026-04-18 (48小时极限冲刺)
> 任务密度: 极高 -- 常规需6-8周的工作量压缩至48小时
> 愿景: 取代所有现有生产力工具，实现功能全面覆盖与超越，深度融合AI，构建前所未有的主动式智能服务系统

---

## 一、总纲: 超越生产力工具的定义

PolySpace 不再是一个"工具"，而是一个**始终在线的智能协作者**。它不是被动等待指令，而是像一位顶级助理一样，在你开口之前就已经准备好了一切。它看得到你的屏幕，听得见你的消息，理解你的习惯，预判你的需求，在你还没意识到的时候就已经把事情办好了。

### 核心哲学

1. **零等待原则**: 用户永远不应该等待AI响应，系统应在需求出现前就预判并准备
2. **全知上下文**: 结合屏幕内容、聊天记录、通知流、日历、邮件、文件操作、地理位置、设备状态，构建完整的用户上下文
3. **主动触达**: 不只是被动回答，而是通过小组件、通知、语音、弹窗、邮件、日程插入等一切渠道主动服务
4. **无感渗透**: 服务触达应当自然、不打扰，像呼吸一样融入用户的工作流
5. **越用越懂**: 每一次交互都在加深系统对用户的理解，主动服务的精准度持续提升

---

## 二、48小时冲刺时间表

### Phase 1: 主动感知引擎 (04-17 00:00 - 04-17 06:00)

#### 1.1 全局上下文聚合器 [后端] (00:00-01:30)

**目标**: 构建统一的多源上下文聚合引擎，将所有感知数据融合为实时用户画像

- [ ] `backend/app/core/context/` 新模块
  - [ ] `aggregator.py` -- ContextAggregator: 实时聚合所有上下文源
    - 屏幕内容流 (OCR/截图分析结果)
    - 聊天消息流 (最近N条对话摘要)
    - 通知流 (所有应用通知聚合)
    - 日历事件流 (即将到来的事件)
    - 邮件流 (最新邮件摘要)
    - 文件操作流 (最近打开/编辑的文件)
    - 位置信息流 (当前/最近位置)
    - 设备状态流 (电量/网络/静音模式等)
  - [ ] `user_profile.py` -- DynamicUserProfile: 实时用户画像
    - 当前活动推断 (工作/休息/通勤/会议中)
    - 注意力焦点 (当前关注的应用/文档/话题)
    - 情绪状态推断 (基于消息语气/工作节奏)
    - 紧急度评估 (是否有待处理的紧急事项)
    - 效率曲线 (一天中不同时段的效率模式)
  - [ ] `context_window.py` -- SlidingContextWindow: 滑动窗口上下文
    - 最近5分钟: 精确上下文 (逐条记录)
    - 最近1小时: 压缩上下文 (关键事件摘要)
    - 最近1天: 趋势上下文 (模式/趋势/统计)
    - 最近1周: 长期上下文 (习惯/偏好/周期)
  - [ ] `trigger.py` -- ProactiveTrigger: 主动触发器
    - 条件组合触发 (AND/OR/NOT 条件组合)
    - 时间窗口触发 (在特定时间范围内满足条件)
    - 频率控制 (同一触发器最短间隔/每日最大次数)
    - 优先级排序 (多个触发同时满足时的优先级)

#### 1.2 屏幕感知系统 [Android + 后端] (01:30-03:00)

**目标**: Android端实时屏幕内容理解，为主动服务提供视觉上下文

- [ ] `android/app/src/main/java/com/polyspace/mobile/screen/` 新模块
  - [ ] `ScreenCaptureService.kt` -- 屏幕捕获服务
    - MediaProjection API 截屏 (可配置间隔: 5s/10s/30s)
    - 智能截图: 仅在屏幕内容变化超过阈值时捕获
    - 隐私过滤: 自动检测并模糊密码/支付等敏感界面
    - 当前前台应用识别 (UsageStatsManager)
  - [ ] `ScreenAnalyzer.kt` -- 本地屏幕分析
    - OCR文字提取 (ML Kit / Tesseract)
    - UI元素识别 (无障碍节点树解析)
    - 当前Activity/Fragment识别
    - 屏幕内容哈希 (快速判断内容是否变化)
  - [ ] `ScreenContextBridge.kt` -- 屏幕上下文桥接
    - 将屏幕分析结果通过WebSocket推送至后端
    - 增量传输: 仅发送变化部分
    - 隐私模式: 用户可暂停/排除特定应用

- [ ] 后端屏幕上下文处理
  - [ ] `backend/app/core/context/screen_handler.py` -- ScreenContextHandler
    - 接收并存储屏幕上下文流
    - 调用LLM进行高级理解 (当前任务推断/下一步建议)
    - 屏幕内容与用户画像的关联分析

#### 1.3 通知感知增强 [Android + 桌面 + 后端] (03:00-04:30)

**目标**: 全平台通知聚合与智能分析，从通知中提取用户需求

- [ ] Android通知感知增强
  - [ ] `SmartNotificationProcessor.kt` -- 智能通知处理器
    - 通知分类 (社交/工作/购物/出行/金融/系统)
    - 紧急度评估 (基于发送者/内容关键词/时间)
    - 行动项提取 (从通知中提取待办事项)
    - 通知摘要 (批量通知的压缩摘要)
    - 通知关联 (将相关通知串联成上下文)
  - [ ] `NotificationAIAnalyzer.kt` -- 通知AI分析器
    - 将通知内容发送至后端LLM分析
    - 生成建议行动 (回复/忽略/稍后处理/创建待办)
    - 检测通知中的时间敏感信息 (会议变更/航班延误等)

- [ ] Windows桌面通知感知
  - [ ] `desktop/src/main/notification/` 新模块
    - `WindowsNotificationListener.js` -- Windows通知监听
      - 通过Windows API监听系统通知
      - 支持Toast通知和Action Center通知
    - `DesktopNotificationBridge.js` -- 通知桥接至后端

- [ ] 后端通知智能处理
  - [ ] `backend/app/core/context/notification_handler.py`
    - 通知流聚合 (多设备通知去重/排序)
    - 通知驱动的主动触发 (如: 检测到航班延误通知 -> 主动建议改签)
    - 通知疲劳管理 (防止过多主动推送)

#### 1.4 习惯学习引擎 [后端] (04:30-06:00)

**目标**: 从用户行为中学习习惯模式，为主动服务提供预测基础

- [ ] `backend/app/core/context/habit_learner.py` -- HabitLearner
  - 时间模式学习 (每天固定时间的行为模式)
  - 应用使用模式 (哪些应用在什么场景下使用)
  - 通信模式 (与谁在什么时间沟通什么内容)
  - 工作节奏模式 (深度工作/会议/休息的周期)
  - 异常检测 (偏离习惯的行为 -> 可能需要帮助)
- [ ] `backend/app/core/context/predictor.py` -- BehaviorPredictor
  - 基于历史模式预测用户下一步行为
  - 预测用户可能需要的工具/信息/服务
  - 预测最佳主动服务时机 (何时推送最不打扰)
  - A/B测试框架 (不同主动策略的效果对比)

---

### Phase 2: 主动服务核心 (04-17 06:00 - 04-17 14:00)

#### 2.1 主动服务调度器 [后端] (06:00-08:00)

**目标**: 构建主动服务的"大脑"，决定何时、以何种方式、推送什么内容

- [ ] `backend/app/core/proactive/` 新模块
  - [ ] `scheduler.py` -- ProactiveScheduler: 主动服务调度器
    - 基于ContextAggregator的实时上下文评估
    - 基于HabitLearner的习惯模式匹配
    - 基于BehaviorPredictor的时机预测
    - 服务优先级队列 (紧急/重要/建议/闲聊)
    - 冷静期管理 (同类服务的最小间隔)
    - 用户状态适配 (会议中不推送闲聊，深度工作时仅推送紧急)
  - [ ] `service_registry.py` -- ProactiveServiceRegistry: 主动服务注册中心
    - 服务声明式注册 (名称/触发条件/优先级/渠道/冷静期)
    - 服务动态启用/禁用
    - 服务效果追踪 (用户接受率/忽略率/负面反馈率)
    - 服务自优化 (根据反馈自动调整触发条件和推送方式)
  - [ ] `channel_router.py` -- ChannelRouter: 渠道路由器
    - 根据内容紧急度和用户状态选择最佳触达渠道
    - 渠道优先级: 紧急 -> 系统通知/弹窗; 重要 -> 小组件/邮件; 建议 -> 聊天消息; 闲聊 -> 低优先级通知
    - 渠道降级: 首选渠道不可用时自动降级到次选
    - 渠道组合: 重要事项多渠道同时触达
  - [ ] `content_generator.py` -- ProactiveContentGenerator: 主动内容生成器
    - 基于上下文生成个性化推送内容
    - 语气适配 (正式/轻松/紧急/关怀)
    - 长度适配 (通知: 1句; 小组件: 3-5句; 邮件: 完整段落)
    - 行动按钮生成 (一键执行/一键忽略/稍后提醒)

#### 2.2 内置主动服务集 [后端] (08:00-11:00)

**目标**: 实现第一批20+个主动服务，覆盖工作生活的方方面面

**工作类主动服务**:
- [ ] `daily_briefing.py` -- 每日简报服务
  - 早间简报: 今日日程/待办/重要邮件/天气/新闻摘要
  - 午间回顾: 上午完成情况/下午重点/需要关注的事项
  - 晚间总结: 今日成就/未完成项/明日预览
- [ ] `meeting_prep.py` -- 会议准备服务
  - 会议前15分钟推送: 参会人信息/相关文档/上次会面记录/议题摘要
  - 自动从邮件/聊天中提取与会议相关的内容
  - 生成会议议程建议
- [ ] `deadline_guard.py` -- 截止日期守护者
  - 截止日期临近时主动提醒 (3天前/1天前/当天)
  - 检测可能无法按时完成的风险
  - 主动建议: 拆分任务/请求延期/重新排优先级
- [ ] `focus_protector.py` -- 专注守护者
  - 检测深度工作状态 (连续编辑文档/写代码)
  - 自动过滤非紧急通知
  - 专注结束后推送被屏蔽的通知摘要
- [ ] `smart_followup.py` -- 智能跟进服务
  - 检测聊天中承诺但未执行的事项
  - 检测发送后未收到回复的重要消息
  - 主动建议跟进时机和内容

**信息类主动服务**:
- [ ] `context_news.py` -- 上下文新闻服务
  - 根据当前工作内容推荐相关新闻/文章
  - 根据聊天话题推荐深度阅读
  - 行业动态监控 (基于用户职业/兴趣)
- [ ] `doc_suggestion.py` -- 文档建议服务
  - 根据当前编辑内容推荐相关文档
  - 根据聊天讨论推荐知识库条目
  - 根据邮件内容推荐模板/历史文档
- [ ] `learning_path.py` -- 学习路径服务
  - 检测知识盲区 (聊天中频繁查询的话题)
  - 推荐系统化学习资源
  - 追踪学习进度

**生活类主动服务**:
- [ ] `wellness_guard.py` -- 健康守护者
  - 久坐提醒 (连续工作超过1小时)
  - 用眼休息提醒 (20-20-20法则)
  - 饮水提醒
  - 作息规律检测 (加班/熬夜预警)
- [ ] `commute_assistant.py` -- 通勤助手
  - 基于日历和位置预测通勤时间
  - 实时路况/天气提醒
  - 通勤时间推荐 (播客/文章/待办)
- [ ] `expense_tracker.py` -- 消费追踪服务
  - 从通知中识别支付/消费信息
  - 月度消费趋势分析
  - 异常消费预警
- [ ] `social_reminder.py` -- 社交提醒服务
  - 亲友生日/纪念日提醒
  - 长时间未联系的重要人脉提醒
  - 社交消息优先级排序

**环境类主动服务**:
- [ ] `weather_advisor.py` -- 天气顾问
  - 恶劣天气预警 (影响出行的天气)
  - 根据天气建议日程调整
  - 天气相关的健康提醒 (过敏/紫外线)
- [ ] `device_health.py` -- 设备健康服务
  - 电量低时建议省电/充电
  - 存储空间不足时建议清理
  - 网络异常时自动切换离线模式
- [ ] `security_guard.py` -- 安全守护者
  - 异常登录检测
  - 可疑链接/附件预警
  - 隐私泄露风险检测

**创意类主动服务**:
- [ ] `idea_spark.py` -- 灵感火花服务
  - 基于当前工作内容生成创意建议
  - 跨领域联想 (将不相关领域的概念与当前工作结合)
  - 定期推送思维拓展内容
- [ ] `writing_coach.py` -- 写作教练服务
  - 检测文档编辑中的常见问题
  - 主动建议改进措辞/结构
  - 写作风格一致性检查
- [ ] `data_insight.py` -- 数据洞察服务
  - 检测Excel/表格中的异常数据
  - 主动发现数据趋势和模式
  - 建议可视化方案

#### 2.3 主动服务API层 [后端] (11:00-12:00)

- [ ] `backend/app/api/v1/proactive.py` -- 主动服务API
  - `GET /api/v1/proactive/services` -- 列出所有主动服务及状态
  - `POST /api/v1/proactive/services/{id}/toggle` -- 启用/禁用服务
  - `GET /api/v1/proactive/history` -- 主动服务推送历史
  - `POST /api/v1/proactive/feedback` -- 用户反馈 (接受/忽略/负面)
  - `GET /api/v1/proactive/context` -- 当前用户上下文快照
  - `POST /api/v1/proactive/trigger` -- 手动触发服务 (调试用)
  - `GET /api/v1/proactive/stats` -- 主动服务效果统计
  - `WS /ws/proactive` -- 主动服务实时推送WebSocket

#### 2.4 主动服务前端管理 [前端] (12:00-14:00)

- [ ] `frontend/src/components/proactive/` 新组件目录
  - [ ] `ProactiveDashboard.vue` -- 主动服务仪表盘
    - 今日主动服务统计 (推送数/接受率/忽略率)
    - 各服务状态和效果图表
    - 用户上下文实时预览
  - [ ] `ProactiveServiceList.vue` -- 服务列表
    - 分类展示所有主动服务
    - 开关切换/参数调整
    - 服务效果追踪
  - [ ] `ProactiveHistory.vue` -- 推送历史
    - 时间线展示所有主动推送
    - 反馈标注 (有用/无用/打扰)
  - [ ] `ProactiveBubble.vue` -- 主动服务气泡
    - 非侵入式的主动服务展示
    - 可展开/折叠/忽略/一键执行
    - 渐入渐出动画
  - [ ] `ContextPreview.vue` -- 上下文预览卡片
    - 展示系统当前理解的上下文
    - 用户可修正/补充

---

### Phase 3: 多渠道触达系统 (04-17 14:00 - 04-17 22:00)

#### 3.1 Android小组件系统 [Android] (14:00-17:30)

**目标**: 实现4种Android桌面小组件，让主动服务常驻用户视野

- [ ] `android/app/src/main/java/com/polyspace/mobile/widget/` 新模块
  - [ ] `DailyBriefingWidget.kt` -- 每日简报小组件 (4x2)
    - 显示今日日程概要/待办数量/重要提醒
    - 点击展开完整简报
    - 自动刷新 (可配置间隔)
    - 深色/浅色主题适配
    - SVG矢量图标渲染
  - [ ] `SmartTodoWidget.kt` -- 智能待办小组件 (4x1)
    - 显示当前最高优先级待办
    - 一键完成/推迟
    - AI建议的下一步行动
    - 进度环形图
  - [ ] `AIInsightWidget.kt` -- AI洞察小组件 (4x2)
    - 上下文相关的AI建议/洞察
    - 主动服务推送展示
    - 一键执行建议操作
    - 滑动切换多条洞察
  - [ ] `QuickActionWidget.kt` -- 快捷操作小组件 (4x1)
    - 基于当前上下文的快捷操作
    - 语音输入按钮
    - 一键创建待办/备忘/邮件
    - 最近使用的工具快捷入口
  - [ ] `WidgetDataProvider.kt` -- 小组件数据提供者
    - 从后端获取小组件数据
    - 本地缓存 + 增量更新
    - 离线降级展示
  - [ ] `WidgetConfigActivity.kt` -- 小组件配置界面
    - 选择小组件类型和尺寸
    - 配置刷新频率
    - 配置展示内容过滤

- [ ] AndroidManifest.xml 更新
  - 注册 AppWidgetProvider
  - 声明 widget 相关权限

- [ ] `res/xml/` 小组件配置XML
  - `daily_briefing_widget_info.xml`
  - `smart_todo_widget_info.xml`
  - `ai_insight_widget_info.xml`
  - `quick_action_widget_info.xml`

- [ ] `res/layout/` 小组件布局 (使用RemoteViews兼容)
  - 各尺寸小组件的布局文件
  - SVG图标资源

#### 3.2 Android通知系统增强 [Android] (17:30-19:30)

**目标**: 构建丰富的通知渠道，支持行动按钮、智能分组、渐进式通知

- [ ] `android/app/src/main/java/com/polyspace/mobile/notification/` 新模块
  - [ ] `ProactiveNotificationManager.kt` -- 主动通知管理器
    - 通知渠道管理 (紧急/重要/建议/闲聊 4个渠道)
    - 通知分组 (同类通知聚合)
    - 通知优先级排序
    - 通知冷静期 (防止通知轰炸)
    - 免打扰模式适配 (检测系统DND状态)
  - [ ] `NotificationActionHandler.kt` -- 通知行动处理器
    - 直接在通知上执行操作 (回复/完成/推迟/确认)
    - NotificationCompat.Action 按钮
    - RemoteInput 直接回复
    - 行动结果反馈 (成功/失败toast)
  - [ ] `SmartNotificationBuilder.kt` -- 智能通知构建器
    - 根据内容类型自动选择通知样式
    - 大文本/大图/收件箱/进度条样式
    - 通知模板系统 (会议提醒/待办/邮件/洞察)
    - 通知声音/振动/灯光策略
  - [ ] `NotificationSummaryService.kt` -- 通知摘要服务
    - 定期将积压通知生成摘要
    - 摘要推送 (如: "你有5条未处理通知，其中2条紧急")
    - 一键处理所有通知

#### 3.3 桌面端通知系统 [桌面] (19:30-21:30)

**目标**: Windows桌面端系统级通知与主动服务展示

- [ ] `desktop/src/main/proactive/` 新模块
  - [ ] `DesktopNotificationManager.js` -- 桌面通知管理器
    - Windows Toast通知 (electron-windows-notifications)
    - 通知渠道分类 (紧急/重要/建议)
    - 通知行动按钮
    - 通知历史记录
  - [ ] `ProactiveOverlay.js` -- 主动服务悬浮窗
    - 屏幕右下角非侵入式悬浮卡片
    - 渐入渐出动画
    - 可拖拽/可关闭/可固定
    - 展示AI洞察/建议/提醒
    - 一键执行/忽略
  - [ ] `DailyBriefingWindow.js` -- 每日简报窗口
    - 首次解锁电脑时自动弹出
    - 今日概览/待办/日程/邮件摘要
    - 一键开始工作 (打开相关应用/文档)
  - [ ] `FocusModeManager.js` -- 专注模式管理器
    - 检测深度工作状态 (键盘/鼠标活动模式)
    - 自动进入专注模式 (屏蔽非紧急通知)
    - 专注统计 (今日专注时长/次数)
    - 专注结束后的通知摘要
  - [ ] `SystemTrayProactive.js` -- 系统托盘主动服务
    - 托盘图标状态变化 (正常/有通知/专注模式)
    - 托盘右键菜单快速操作
    - 托盘气泡通知

#### 3.4 Web端推送 [前端] (21:30-22:00)

- [ ] Web Push Notification 支持
  - [ ] Service Worker 注册和推送订阅
  - [ ] `frontend/src/composables/usePushNotification.ts`
  - [ ] `frontend/src/components/proactive/ProactiveToast.vue` -- 页面内推送
    - 右下角Toast通知
    - 行动按钮
    - 自动消失/手动关闭
    - 堆叠展示

#### 3.5 邮件主动触达 [后端] (22:00-22:30)

- [ ] `backend/app/core/proactive/channels/email_channel.py` -- 邮件触达渠道
  - 重要的主动服务通过邮件推送 (如: 每日简报/周报)
  - 邮件模板系统 (HTML邮件)
  - 邮件发送频率控制
  - 用户邮件偏好设置

#### 3.6 语音主动触达 [后端 + Android] (22:30-23:30)

- [ ] `backend/app/core/proactive/channels/voice_channel.py` -- 语音触达渠道
  - 紧急事项通过TTS语音播报
  - 语音播报内容精简 (1-2句话)
  - 语音播报时机 (耳机连接时/独处时)
- [ ] Android端语音播报
  - [ ] `VoiceAnnouncementService.kt` -- 语音播报服务
    - 检测耳机/蓝牙设备连接状态
    - 检测用户是否在通话中
    - TextToSpeech引擎管理
    - 语音播报队列

#### 3.7 日程注入触达 [后端] (23:30-00:00)

- [ ] `backend/app/core/proactive/channels/calendar_channel.py` -- 日程注入渠道
  - 将AI建议的时间块直接注入用户日历
  - 如: "专注工作时间"/"休息时间"/"学习时间"
  - 日历事件附带AI建议和上下文
  - 用户可一键接受/拒绝/调整

---

### Phase 4: 深度AI融合 (04-18 00:00 - 04-18 08:00)

#### 4.1 多模态上下文理解 [后端] (00:00-02:00)

**目标**: 让AI真正"看懂"用户的整个数字生活

- [ ] `backend/app/core/context/multimodal.py` -- 多模态上下文理解
  - 屏幕截图 + OCR文字 + UI结构 -> 当前任务理解
  - 聊天记录 + 通知流 + 邮件 -> 通信意图理解
  - 日历 + 待办 + 文件操作 -> 工作进度理解
  - 位置 + 时间 + 习惯 -> 生活场景理解
  - 多模态融合推理 (将所有信号融合为统一理解)
- [ ] `backend/app/core/context/scene_detector.py` -- 场景检测器
  - 工作场景 (深度编码/文档撰写/会议/邮件处理)
  - 学习场景 (阅读/笔记/搜索)
  - 生活场景 (购物/社交/娱乐/通勤)
  - 过渡场景 (场景切换时的平滑处理)
  - 场景切换触发服务策略变更

#### 4.2 对话式主动服务 [后端 + 前端] (02:00-04:00)

**目标**: 主动服务不只是通知，而是自然的对话

- [ ] `backend/app/core/proactive/conversational.py` -- 对话式主动服务
  - 主动发起对话 (非侵入式，像朋友一样自然)
  - 对话上下文延续 (主动服务引发的对话有独立上下文)
  - 对话目标导向 (每次主动对话有明确目标)
  - 对话结果追踪 (用户是否采纳建议)
- [ ] 前端对话式主动服务组件
  - [ ] `ProactiveChatBubble.vue` -- 主动聊天气泡
    - 在聊天界面顶部展示主动发起的对话
    - 区分用户主动对话和AI主动对话
    - 可展开/折叠/忽略
  - [ ] `ProactiveSuggestionBar.vue` -- 主动建议栏
    - 输入框上方的建议条
    - 基于上下文的输入建议
    - 一键采纳建议

#### 4.3 AI工作流自动编排 [后端] (04:00-06:00)

**目标**: AI不只是辅助，而是自动编排完整工作流

- [ ] `backend/app/core/proactive/workflow/` 新模块
  - [ ] `workflow_engine.py` -- 主动工作流引擎
    - 工作流模板 (常见工作流的预设模板)
    - 工作流自动编排 (根据上下文自动组合工具)
    - 工作流执行监控 (实时追踪工作流进度)
    - 工作流异常恢复 (出错时自动重试/降级/通知)
  - [ ] `workflow_templates.py` -- 内置工作流模板
    - 邮件处理工作流 (收件 -> 分类 -> 草拟回复 -> 提醒确认)
    - 会议工作流 (准备 -> 提醒 -> 记录 -> 待办提取 -> 跟进)
    - 文档工作流 (大纲 -> 撰写 -> 审阅 -> 修订 -> 定稿)
    - 数据分析工作流 (数据获取 -> 清洗 -> 分析 -> 可视化 -> 报告)
    - 项目管理工作流 (需求 -> 拆分 -> 分配 -> 追踪 -> 回顾)
  - [ ] `workflow_learner.py` -- 工作流学习器
    - 从用户操作序列中学习新工作流
    - 工作流变体识别 (同一目标的不同执行路径)
    - 工作流优化建议 (减少步骤/并行化/自动化)

#### 4.4 智能代理协作网络 [后端] (06:00-08:00)

**目标**: 多个AI代理协同工作，形成主动服务的"团队"

- [ ] `backend/app/core/proactive/agent_team/` 新模块
  - [ ] `proactive_agent.py` -- 主动服务代理
    - 常驻后台的轻量级代理
    - 持续监控上下文变化
    - 触发条件满足时唤醒完整Agent
    - 代理间通信 (代理之间可以协作)
  - [ ] `specialist_agents.py` -- 专家代理集
    - 邮件专家: 专注邮件处理和回复建议
    - 日程专家: 专注时间管理和日程优化
    - 文档专家: 专注文档撰写和编辑
    - 数据专家: 专注数据分析和可视化
    - 通信专家: 专注消息处理和社交管理
  - [ ] `agent_coordinator.py` -- 代理协调器
    - 多代理任务分配
    - 代理间上下文共享
    - 冲突解决 (多个代理想同时推送时)
    - 协作结果合并

---

### Phase 5: 超越与极致体验 (04-18 08:00 - 04-18 16:00)

#### 5.1 全局搜索与命令面板 [前端 + 后端] (08:00-09:30)

**目标**: 一个搜索框搞定一切，超越Spotlight/Alfred/Raycast

- [ ] `frontend/src/components/common/CommandPalette.vue` -- 全局命令面板
  - Ctrl+K / Cmd+K 快捷键唤起
  - 模糊搜索: 应用/文件/联系人/命令/设置/知识库
  - AI增强搜索: 自然语言查询 -> 智能结果
  - 最近使用/推荐命令
  - 命令分类: 导航/操作/搜索/AI
  - 内联预览 (选中结果时显示预览)
- [ ] `backend/app/api/v1/search.py` -- 统一搜索API
  - 跨所有数据源的统一搜索
  - 搜索结果排序 (相关度/时效性/重要性)
  - 搜索建议和自动补全
  - 搜索历史

#### 5.2 智能剪贴板 [Android + 桌面 + 后端] (09:30-11:00)

**目标**: 剪贴板不再是临时存储，而是AI理解用户意图的窗口

- [ ] Android智能剪贴板
  - [ ] `SmartClipboardService.kt` -- 智能剪贴板服务
    - 监听剪贴板变化
    - 内容分类 (文本/链接/图片/电话/地址/代码)
    - 智能操作建议 (链接->打开; 电话->拨打; 地址->导航; 代码->格式化)
    - 剪贴板历史 (加密存储)
- [ ] 桌面端智能剪贴板
  - [ ] `SmartClipboardManager.js` -- 智能剪贴板
    - 监听系统剪贴板
    - 内容理解和操作建议
    - 跨设备剪贴板同步
- [ ] 后端剪贴板AI处理
  - [ ] `backend/app/core/proactive/clipboard_handler.py`
    - 剪贴板内容深度分析
    - 从剪贴板内容推断用户意图
    - 生成上下文相关的操作建议

#### 5.3 环境感知自动化 [后端 + 多端] (11:00-13:00)

**目标**: 基于环境变化自动执行操作，无需用户指令

- [ ] `backend/app/core/proactive/automation/` 新模块
  - [ ] `environment_rules.py` -- 环境规则引擎
    - IF-THEN规则: 位置变化/时间变化/网络变化/设备变化 -> 自动操作
    - 规则模板库 (常见自动化场景)
    - 规则冲突检测和解决
    - 规则效果追踪
  - [ ] `automation_templates.py` -- 自动化模板
    - 到达公司 -> 静音手机 + 打开工作文档 + 查看今日待办
    - 离开公司 -> 发送今日工作总结 + 开启通勤模式
    - 连接耳机 -> 询问是否播放音乐/播客
    - 电量低于20% -> 开启省电模式 + 暂停非紧急同步
    - 检测到会议开始 -> 自动静音 + 开始会议记录
    - 检测到航班延误 -> 自动搜索替代航班 + 通知接机人
    - 检测到快递到达 -> 提醒取件 + 更新待办状态
    - 检测到账单 -> 自动分类 + 提醒缴费
  - [ ] `scene_automation.py` -- 场景自动化
    - 工作场景: 专注模式 + 工作文档 + 消息过滤
    - 会议场景: 静音 + 会议记录 + 议程展示
    - 通勤场景: 播客推荐 + 路况信息 + 邮件摘要
    - 休息场景: 社交消息 + 娱乐推荐 + 健康提醒
    - 学习场景: 笔记工具 + 知识库 + 专注模式

#### 5.4 跨设备无缝流转 [全端] (13:00-15:00)

**目标**: 在任何设备上开始的工作，都能在其他设备上无缝继续

- [ ] `backend/app/core/proactive/handoff/` 新模块
  - [ ] `activity_handoff.py` -- 活动流转
    - 检测用户切换设备
    - 自动将当前活动上下文推送到新设备
    - 如: 手机上阅读的文章 -> 电脑上继续阅读
    - 如: 电脑上编辑的文档 -> 手机上查看
    - 如: 手机上的通话 -> 电脑上记录要点
  - [ ] `context_sync.py` -- 上下文同步
    - 实时同步用户上下文到所有设备
    - 增量同步 (仅传输变化部分)
    - 冲突解决 (多设备同时修改)
    - 离线缓存 + 恢复
  - [ ] `device_orchestrator.py` -- 设备编排器
    - 多设备协同任务分配
    - 如: 电脑处理数据 + 手机展示结果
    - 如: 手机拍照 + 电脑编辑
    - 如: 平板演示 + 手机遥控
    - 设备能力感知和最优分配

#### 5.5 隐私与安全增强 [全端] (15:00-16:00)

**目标**: 主动服务的前提是绝对的安全和隐私保护

- [ ] `backend/app/core/proactive/privacy/` 新模块
  - [ ] `privacy_guard.py` -- 隐私守护者
    - 上下文数据分级 (公开/内部/机密/绝密)
    - 敏感信息自动脱敏 (密码/支付/身份信息)
    - 上下文数据生命周期管理 (自动过期/删除)
    - 用户隐私偏好设置 (哪些数据可以被分析)
    - 隐私审计日志 (所有上下文访问记录)
  - [ ] `consent_manager.py` -- 授权管理器
    - 每个主动服务需要用户明确授权
    - 授权粒度: 服务级别/数据级别/渠道级别
    - 授权有效期和自动过期
    - 一键撤销所有授权
  - [ ] `local_first.py` -- 本地优先策略
    - 尽可能在本地处理上下文 (不发送到云端)
    - 本地小模型处理简单上下文分析
    - 仅在必要时才调用云端LLM
    - 端到端加密传输

---

### Phase 6: 极致打磨与集成测试 (04-18 16:00 - 04-18 24:00)

#### 6.1 前后端全面集成 [全端] (16:00-18:00)

- [ ] 前端所有组件与后端API对接
  - [ ] 工作台组件: 文档/PPT/Excel/视频/日历/知识库/待办/备忘/邮件/看板
  - [ ] 主动服务组件: 仪表盘/服务列表/推送历史/气泡/建议栏
  - [ ] 设置组件: 主动服务设置/隐私设置/渠道设置
  - [ ] 通用组件: 命令面板/上下文预览
- [ ] Android端与后端全面集成
  - [ ] 小组件数据绑定
  - [ ] 通知系统对接
  - [ ] 屏幕感知对接
  - [ ] 语音播报对接
- [ ] 桌面端与后端全面集成
  - [ ] 通知系统对接
  - [ ] 悬浮窗对接
  - [ ] 专注模式对接
  - [ ] 剪贴板对接

#### 6.2 性能优化 [全端] (18:00-20:00)

- [ ] 后端性能优化
  - [ ] 上下文聚合器缓存策略
  - [ ] 主动服务调度器异步执行
  - [ ] WebSocket消息批处理
  - [ ] 数据库查询优化
- [ ] 前端性能优化
  - [ ] 组件懒加载
  - [ ] 虚拟列表 (长列表场景)
  - [ ] WebSocket消息节流
  - [ ] 主动服务气泡动画性能
- [ ] Android性能优化
  - [ ] 屏幕捕获CPU/内存优化
  - [ ] 小组件刷新频率优化
  - [ ] 通知处理后台任务优化
  - [ ] 电池消耗优化

#### 6.3 端到端测试 [全端] (20:00-22:00)

- [ ] 主动服务集成测试
  - [ ] 上下文聚合 -> 触发器 -> 调度器 -> 渠道路由 -> 通知展示 完整链路
  - [ ] 多设备场景测试
  - [ ] 离线/弱网场景测试
  - [ ] 隐私模式测试
- [ ] 压力测试
  - [ ] 高频上下文更新场景
  - [ ] 大量通知并发场景
  - [ ] 长时间运行稳定性
- [ ] 用户体验测试
  - [ ] 通知频率是否合理
  - [ ] 主动建议是否相关
  - [ ] 渠道选择是否恰当
  - [ ] 隐私保护是否充分

#### 6.4 文档与收尾 [全端] (22:00-24:00)

- [ ] API文档更新
- [ ] 主动服务配置指南
- [ ] 隐私政策文档
- [ ] 最终构建与部署验证

---

## 三、主动服务触达渠道总览

| 渠道 | 平台 | 紧急度 | 侵入性 | 适用场景 |
|------|------|--------|--------|----------|
| Android系统通知 | Android | 高-中 | 中 | 所有主动提醒 |
| Android桌面小组件 | Android | 低 | 低 | 常驻信息展示 |
| Android语音播报 | Android | 高 | 高 | 紧急事项(耳机模式) |
| Android弹窗 | Android | 高 | 高 | 极紧急事项 |
| Windows Toast通知 | Desktop | 高-中 | 中 | 所有主动提醒 |
| 桌面悬浮窗 | Desktop | 中-低 | 低 | AI洞察/建议 |
| 系统托盘 | Desktop | 低 | 极低 | 状态/快捷操作 |
| Web Push | Web | 中 | 中 | 浏览器内提醒 |
| 页面内Toast | Web | 低 | 低 | 非侵入式建议 |
| 聊天消息 | 全平台 | 中 | 低 | 对话式主动服务 |
| 邮件 | 全平台 | 低 | 极低 | 每日简报/周报 |
| 日程注入 | 全平台 | 中 | 低 | 时间块建议 |
| 命令面板建议 | 前端 | 低 | 极低 | 操作建议 |

---

## 四、技术架构新增模块总览

```
backend/app/core/
  context/                    # 上下文感知引擎
    aggregator.py             # 多源上下文聚合器
    user_profile.py           # 动态用户画像
    context_window.py         # 滑动窗口上下文
    trigger.py                # 主动触发器
    screen_handler.py         # 屏幕上下文处理
    notification_handler.py   # 通知上下文处理
    habit_learner.py          # 习惯学习引擎
    predictor.py              # 行为预测器
    multimodal.py             # 多模态上下文理解
    scene_detector.py         # 场景检测器
  proactive/                  # 主动服务系统
    scheduler.py              # 主动服务调度器
    service_registry.py       # 服务注册中心
    channel_router.py         # 渠道路由器
    content_generator.py      # 主动内容生成器
    conversational.py         # 对话式主动服务
    privacy/                  # 隐私保护
      privacy_guard.py        # 隐私守护者
      consent_manager.py      # 授权管理器
      local_first.py          # 本地优先策略
    channels/                 # 触达渠道
      email_channel.py        # 邮件渠道
      voice_channel.py        # 语音渠道
      calendar_channel.py     # 日程注入渠道
    workflow/                 # 工作流编排
      workflow_engine.py      # 工作流引擎
      workflow_templates.py   # 工作流模板
      workflow_learner.py     # 工作流学习器
    agent_team/               # 代理协作
      proactive_agent.py      # 主动服务代理
      specialist_agents.py    # 专家代理集
      agent_coordinator.py    # 代理协调器
    automation/               # 环境自动化
      environment_rules.py    # 环境规则引擎
      automation_templates.py # 自动化模板
      scene_automation.py     # 场景自动化
    handoff/                  # 跨设备流转
      activity_handoff.py     # 活动流转
      context_sync.py         # 上下文同步
      device_orchestrator.py  # 设备编排器
    services/                 # 内置主动服务
      daily_briefing.py       # 每日简报
      meeting_prep.py         # 会议准备
      deadline_guard.py       # 截止日期守护
      focus_protector.py      # 专注守护
      smart_followup.py       # 智能跟进
      context_news.py         # 上下文新闻
      doc_suggestion.py       # 文档建议
      learning_path.py        # 学习路径
      wellness_guard.py       # 健康守护
      commute_assistant.py    # 通勤助手
      expense_tracker.py      # 消费追踪
      social_reminder.py      # 社交提醒
      weather_advisor.py      # 天气顾问
      device_health.py        # 设备健康
      security_guard.py       # 安全守护
      idea_spark.py           # 灵感火花
      writing_coach.py        # 写作教练
      data_insight.py         # 数据洞察
    clipboard_handler.py      # 剪贴板AI处理

android/app/src/main/java/com/polyspace/mobile/
  screen/                     # 屏幕感知
    ScreenCaptureService.kt
    ScreenAnalyzer.kt
    ScreenContextBridge.kt
  widget/                     # 小组件
    DailyBriefingWidget.kt
    SmartTodoWidget.kt
    AIInsightWidget.kt
    QuickActionWidget.kt
    WidgetDataProvider.kt
    WidgetConfigActivity.kt
  notification/               # 通知系统
    ProactiveNotificationManager.kt
    NotificationActionHandler.kt
    SmartNotificationBuilder.kt
    NotificationSummaryService.kt
  voice/                      # 语音播报
    VoiceAnnouncementService.kt
  clipboard/                  # 智能剪贴板
    SmartClipboardService.kt

desktop/src/main/
  proactive/                  # 主动服务
    DesktopNotificationManager.js
    ProactiveOverlay.js
    DailyBriefingWindow.js
    FocusModeManager.js
    SystemTrayProactive.js
  notification/               # 通知监听
    WindowsNotificationListener.js
    DesktopNotificationBridge.js
  clipboard/                  # 智能剪贴板
    SmartClipboardManager.js

frontend/src/
  components/proactive/       # 主动服务组件
    ProactiveDashboard.vue
    ProactiveServiceList.vue
    ProactiveHistory.vue
    ProactiveBubble.vue
    ProactiveChatBubble.vue
    ProactiveSuggestionBar.vue
    ProactiveToast.vue
    ContextPreview.vue
  components/common/
    CommandPalette.vue         # 全局命令面板
  composables/
    usePushNotification.ts    # Web推送
    useContextSync.ts          # 上下文同步
```

---

## 五、关键指标与验收标准

### 5.1 主动服务指标

| 指标 | 目标值 |
|------|--------|
| 主动服务数量 | >= 20个 |
| 触达渠道数量 | >= 13个 |
| 上下文源数量 | >= 8个 |
| 主动建议接受率 | >= 40% |
| 通知打扰评分 (用户反馈) | <= 2/5 |
| 上下文理解准确率 | >= 75% |
| 场景检测准确率 | >= 80% |
| 习惯学习收敛周期 | <= 7天 |

### 5.2 性能指标

| 指标 | 目标值 |
|------|--------|
| 上下文聚合延迟 | <= 500ms |
| 主动触发响应时间 | <= 2s |
| 通知展示延迟 | <= 1s |
| 小组件刷新延迟 | <= 3s |
| Android屏幕捕获CPU占用 | <= 5% |
| 后端内存增量 | <= 200MB |
| WebSocket消息吞吐 | >= 1000 msg/s |

### 5.3 隐私指标

| 指标 | 目标值 |
|------|--------|
| 敏感信息脱敏率 | 100% |
| 本地处理比例 | >= 60% |
| 用户授权覆盖率 | 100% |
| 隐私审计完整性 | 100% |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 通知轰炸导致用户反感 | 高 | 严格冷静期 + 用户反馈学习 + 免打扰适配 |
| 上下文数据隐私泄露 | 极高 | 本地优先 + 端到端加密 + 敏感信息脱敏 + 审计日志 |
| 屏幕捕获耗电 | 中 | 智能截图 + 变化检测 + 可配置间隔 |
| LLM调用成本过高 | 中 | 分级模型 + 本地小模型 + 缓存 + 批处理 |
| 多设备同步冲突 | 中 | CRDT + 最后写入胜出 + 用户手动解决 |
| 习惯学习冷启动 | 低 | 预设模板 + 渐进式学习 + 用户引导 |

---

## 七、里程碑检查点

| 时间 | 里程碑 | 验收标准 |
|------|--------|----------|
| 04-17 06:00 | 主动感知引擎就绪 | 上下文聚合器运行 + 屏幕感知可用 + 通知感知可用 |
| 04-17 14:00 | 主动服务核心就绪 | 调度器运行 + 10+主动服务可用 + API就绪 |
| 04-17 22:00 | 多渠道触达就绪 | Android小组件 + 通知 + 桌面通知 + Web推送 |
| 04-18 08:00 | 深度AI融合就绪 | 多模态理解 + 对话式服务 + 工作流编排 + 代理协作 |
| 04-18 16:00 | 极致体验就绪 | 命令面板 + 智能剪贴板 + 环境自动化 + 跨设备流转 |
| 04-18 24:00 | 集成测试通过 | 全链路测试通过 + 性能达标 + 隐私合规 |

---

> "最好的服务是你还没开口就已经办好了的服务。"
> -- PolySpace 超维跃迁计划
