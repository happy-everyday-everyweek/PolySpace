<template>
  <div class="email-client">
    <div class="email-sidebar">
      <div class="email-mode-switch">
        <button :class="['mode-btn', { active: mode === 'human' }]" @click="mode = 'human'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          我的邮件
        </button>
        <button :class="['mode-btn', { active: mode === 'ai' }]" @click="mode = 'ai'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          AI 邮件
        </button>
      </div>

      <template v-if="mode === 'human'">
        <button class="compose-btn" @click="openCompose()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          写邮件
        </button>
        <div class="email-folders">
          <div v-for="folder in folders" :key="folder.name" :class="['folder-item', { active: currentFolder === folder.name }]" @click="switchFolder(folder.name)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path :d="folder.icon"/></svg>
            <span>{{ folder.label }}</span>
            <span v-if="folder.count" class="folder-count">{{ folder.count }}</span>
          </div>
        </div>
        <div class="sidebar-section">
          <div class="sidebar-label">账户</div>
          <div v-if="accounts.length === 0" class="no-account-hint">暂无账户</div>
          <div v-for="acc in accounts" :key="acc.id" :class="['account-item', { active: currentAccountId === acc.id }]" @click="switchAccount(acc.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            <span class="account-name">{{ acc.name || acc.email_address }}</span>
            <button class="icon-btn-sm" @click.stop="confirmDeleteAccount(acc.id)" title="删除账户">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
            </button>
          </div>
          <button class="add-account-btn" @click="showAccountDialog = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            添加账户
          </button>
        </div>
      </template>

      <template v-if="mode === 'ai'">
        <div class="ai-sidebar-section">
          <div class="sidebar-label">AI 邮件控制</div>
          <div class="ai-status-row">
            <span class="status-label">监控</span>
            <button :class="['toggle-btn', { on: aiMonitoring }]" @click="toggleMonitoring">
              {{ aiMonitoring ? '开' : '关' }}
            </button>
          </div>
          <div class="ai-config-info">
            <span class="config-hint">自动回复、任务提取、通知等设置</span>
            <button class="goto-settings-btn" @click="$emit('openSettings')">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
              前往设置
            </button>
          </div>
        </div>
        <div class="ai-sidebar-section">
          <div class="sidebar-label">AI 统计</div>
          <div class="stat-row"><span class="stat-label">已处理</span><span class="stat-value">{{ aiStats.total_processed }}</span></div>
          <div class="stat-row"><span class="stat-label">自动回复</span><span class="stat-value">{{ aiStats.auto_replied }}</span></div>
          <div class="stat-row"><span class="stat-label">任务提取</span><span class="stat-value">{{ aiStats.tasks_extracted }}</span></div>
          <div class="stat-row"><span class="stat-label">用户通知</span><span class="stat-value">{{ aiStats.user_notified }}</span></div>
        </div>
        <button class="check-now-btn" @click="checkNewEmails">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
          立即检查
        </button>
      </template>

      <div class="sidebar-bottom">
        <button class="coord-btn" @click="showCoordPanel = !showCoordPanel">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          协调
        </button>
      </div>
    </div>

    <div class="email-main">
      <template v-if="mode === 'human'">
        <div class="email-list">
          <div class="email-list-header">
            <input v-model="searchQuery" placeholder="搜索邮件..." class="search-input" @input="onSearch" />
          </div>
          <div v-if="loading" class="loading-state"><div class="spinner"></div><span>加载中...</span></div>
          <template v-else>
            <div v-if="accounts.length === 0" class="empty-state">
              <div class="empty-hint">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                <p>请先添加邮件账户</p>
                <button class="primary-btn-sm" @click="showAccountDialog = true">添加账户</button>
              </div>
            </div>
            <template v-else>
              <div v-for="em in filteredEmails" :key="em.id" :class="['email-item', { unread: !toBool(em.is_read), selected: selectedEmail?.id === em.id }]" @click="selectEmail(em)">
                <div class="email-item-row">
                  <span class="email-item-sender">{{ getSender(em) }}</span>
                  <span class="email-item-date">{{ formatDate(em.date_received) }}</span>
                </div>
                <div class="email-item-subject">{{ em.subject || '(无主题)' }}</div>
                <div class="email-item-preview">{{ getPreview(em) }}</div>
                <div class="email-item-tags">
                  <span v-if="em.category" :class="['category-tag', em.category]">{{ categoryLabel(em.category) }}</span>
                  <span v-if="em.priority && em.priority !== 'normal'" :class="['priority-tag', em.priority]">{{ priorityLabel(em.priority) }}</span>
                  <span v-if="getAttachments(em).length" class="attachment-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
                    {{ getAttachments(em).length }}
                  </span>
                </div>
              </div>
              <div v-if="filteredEmails.length === 0" class="empty-state">暂无邮件</div>
            </template>
          </template>
        </div>
        <div class="email-detail" v-if="selectedEmail">
          <div class="email-detail-header">
            <h3>{{ selectedEmail.subject || '(无主题)' }}</h3>
            <div class="email-detail-meta">
              <span>发件人: {{ getSender(selectedEmail) }}</span>
              <span>收件人: {{ getRecipients(selectedEmail) }}</span>
              <span>{{ formatDate(selectedEmail.date_received) }}</span>
            </div>
          </div>
          <div class="email-detail-participants" v-if="getCCList(selectedEmail).length">
            <span class="cc-label">抄送:</span>
            <span>{{ getCCList(selectedEmail).join(', ') }}</span>
          </div>
          <div class="email-detail-body" v-html="selectedEmail.html || selectedEmail.text"></div>
          <div class="email-detail-attachments" v-if="getAttachments(selectedEmail).length">
            <div v-for="att in getAttachments(selectedEmail)" :key="att.filename" class="attachment-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
              <span class="att-name">{{ att.filename }}</span>
              <span class="att-size">{{ formatSize(att.size) }}</span>
            </div>
          </div>
          <div class="email-thread-section" v-if="threadEmails.length > 1">
            <div class="sidebar-label">会话 ({{ threadEmails.length }} 条)</div>
            <div v-for="te in threadEmails" :key="te.id" :class="['thread-msg', { current: te.id === selectedEmail.id }]">
              <div class="thread-msg-header">
                <span class="thread-msg-sender">{{ getSender(te) }}</span>
                <span class="thread-msg-date">{{ formatDate(te.date_received) }}</span>
              </div>
              <div class="thread-msg-body" v-html="te.html || te.text"></div>
            </div>
          </div>
          <div class="email-ai-actions">
            <button class="email-ai-btn" @click="aiSummarizeEmail">AI 摘要</button>
            <button class="email-ai-btn" @click="openReply">回复</button>
            <button class="email-ai-btn" @click="aiReplyEmail">AI 回复</button>
            <button class="email-ai-btn" @click="aiCategorizeOne">AI 分类</button>
            <button :class="['email-action-btn', { starred: toBool(selectedEmail.is_starred) }]" @click="toggleStar">
              <svg width="14" height="14" viewBox="0 0 24 24" :fill="toBool(selectedEmail.is_starred) ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            </button>
            <button class="email-action-btn" @click="deleteSelectedEmail">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
            </button>
          </div>
        </div>
        <div class="email-detail empty-state" v-else>选择一封邮件查看</div>
      </template>

      <template v-if="mode === 'ai'">
        <div class="ai-email-content">
          <div class="ai-email-records">
            <div class="section-title">AI 处理记录</div>
            <div v-for="record in aiRecords" :key="record.email_id" :class="['ai-record-card', record.decision?.priority]">
              <div class="record-header">
                <span class="record-subject">{{ record.subject }}</span>
                <span :class="['action-badge', record.decision?.action]">{{ actionLabel(record.decision?.action) }}</span>
              </div>
              <div class="record-meta">
                <span class="record-sender">{{ record.sender }}</span>
                <span v-if="record.processed_at" class="record-time">{{ formatTimestamp(record.processed_at) }}</span>
              </div>
              <div v-if="record.decision" class="record-decision">
                <div class="decision-row">
                  <span class="decision-label">分类:</span>
                  <span class="decision-value">{{ categoryLabel(record.decision.category) }}</span>
                </div>
                <div class="decision-row">
                  <span class="decision-label">优先级:</span>
                  <span :class="['priority-tag', record.decision.priority]">{{ priorityLabel(record.decision.priority) }}</span>
                </div>
                <div class="decision-row">
                  <span class="decision-label">原因:</span>
                  <span class="decision-value">{{ record.decision.reason }}</span>
                </div>
              </div>
              <div class="record-status">
                <span v-if="record.auto_replied" class="status-tag replied">已自动回复</span>
                <span v-if="record.user_notified" class="status-tag notified">已通知用户</span>
                <span v-if="record.tasks_created?.length" class="status-tag tasks">{{ record.tasks_created.length }} 个任务</span>
              </div>
            </div>
            <div v-if="aiRecords.length === 0" class="empty-state">暂无 AI 处理记录</div>
          </div>
        </div>
      </template>
    </div>

    <div v-if="showCompose" class="compose-overlay" @click.self="showCompose = false">
      <div class="compose-modal">
        <h3>{{ composeData.in_reply_to ? '回复邮件' : '写邮件' }}</h3>
        <input v-model="composeData.to" placeholder="收件人" class="compose-input" />
        <input v-model="composeData.cc" placeholder="抄送" class="compose-input" />
        <input v-model="composeData.subject" placeholder="主题" class="compose-input" />
        <textarea v-model="composeData.body" placeholder="正文" class="compose-body"></textarea>
        <div class="compose-actions">
          <button class="btn-ai" @click="aiComposeEmail">AI 撰写</button>
          <button class="btn-primary" @click="sendEmail">发送</button>
          <button class="btn-secondary" @click="saveAsDraft">存草稿</button>
          <button class="btn-secondary" @click="showCompose = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showAccountDialog" class="compose-overlay" @click.self="showAccountDialog = false">
      <div class="compose-modal">
        <h3>添加邮件账户</h3>
        <input v-model="accountForm.name" placeholder="账户名称" class="compose-input" />
        <input v-model="accountForm.email_address" placeholder="邮箱地址" class="compose-input" />
        <input v-model="accountForm.username" placeholder="用户名" class="compose-input" />
        <input v-model="accountForm.password" type="password" placeholder="密码/授权码" class="compose-input" />
        <input v-model="accountForm.imap_host" placeholder="IMAP 服务器" class="compose-input" />
        <input v-model.number="accountForm.imap_port" placeholder="IMAP 端口" type="number" class="compose-input" />
        <input v-model="accountForm.smtp_host" placeholder="SMTP 服务器" class="compose-input" />
        <input v-model.number="accountForm.smtp_port" placeholder="SMTP 端口" type="number" class="compose-input" />
        <label class="config-row" style="margin-top:4px">
          <input type="checkbox" v-model="accountForm.use_ssl" />
          <span>使用 SSL</span>
        </label>
        <div v-if="accountError" class="account-error">{{ accountError }}</div>
        <div class="compose-actions">
          <button class="btn-primary" @click="addAccount" :disabled="!accountForm.email_address || !accountForm.imap_host || !accountForm.password">添加</button>
          <button class="btn-secondary" @click="showAccountDialog = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header">
        <h4>AI 邮件助手</h4>
        <button class="close-btn" @click="showAIPanel = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI 处理中...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.summary" class="ai-section"><div class="sidebar-label">摘要</div><p class="summary-text">{{ aiResult.summary }}</p></div>
          <div v-if="aiResult.body" class="ai-section"><div class="sidebar-label">撰写内容</div><div class="composed-body">{{ aiResult.body }}</div><button class="apply-btn" @click="applyComposedEmail">应用</button></div>
          <div v-if="aiResult.category" class="ai-section"><div class="sidebar-label">分类</div><span class="category-badge">{{ categoryLabel(aiResult.category) }}</span><span v-if="aiResult.urgency" :class="['urgency-badge', aiResult.urgency]">{{ priorityLabel(aiResult.urgency) }}</span></div>
          <div v-if="aiResult.result && !aiResult.summary && !aiResult.body" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>

    <div v-if="showCoordPanel" class="coord-panel">
      <div class="coord-header">
        <h4>AI 协调</h4>
        <button class="close-btn" @click="showCoordPanel = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="coord-tabs">
        <button :class="['coord-tab', { active: coordTab === 'notifications' }]" @click="coordTab = 'notifications'">通知</button>
        <button :class="['coord-tab', { active: coordTab === 'plan' }]" @click="coordTab = 'plan'">每日计划</button>
        <button :class="['coord-tab', { active: coordTab === 'status' }]" @click="coordTab = 'status'">状态</button>
      </div>
      <div class="coord-content">
        <div v-if="coordTab === 'notifications'" class="coord-notifications">
          <button class="refresh-btn" @click="loadNotifications">刷新</button>
          <div v-for="notif in notifications" :key="notif.id" :class="['notif-card', notif.priority, { read: notif.read }]">
            <div class="notif-header">
              <span :class="['notif-type', notif.type]">{{ notif.type?.replace('_', ' ') }}</span>
              <span class="notif-time">{{ formatTimestamp(notif.created_at) }}</span>
            </div>
            <div class="notif-title">{{ notif.title }}</div>
            <p class="notif-content">{{ notif.content }}</p>
            <div class="notif-actions" v-if="!notif.read">
              <button class="notif-btn read-btn" @click="markNotifRead(notif.id)">已读</button>
              <button class="notif-btn dismiss-btn" @click="dismissNotif(notif.id)">忽略</button>
            </div>
          </div>
          <div v-if="notifications.length === 0" class="empty-state">暂无通知</div>
        </div>
        <div v-if="coordTab === 'plan'" class="coord-plan">
          <button class="refresh-btn" @click="generatePlan">生成计划</button>
          <div v-if="dailyPlan" class="plan-content">
            <p class="plan-summary">{{ dailyPlan.summary }}</p>
            <div v-if="dailyPlan.email_checks?.length" class="plan-section">
              <div class="sidebar-label">邮件检查</div>
              <div v-for="(ec, i) in dailyPlan.email_checks" :key="i" class="plan-item">
                <span class="plan-time">{{ ec.time }}</span>
                <span class="plan-desc">{{ ec.reason }}</span>
              </div>
            </div>
            <div v-if="dailyPlan.scheduled_reminders?.length" class="plan-section">
              <div class="sidebar-label">提醒</div>
              <div v-for="(r, i) in dailyPlan.scheduled_reminders" :key="i" class="plan-item">
                <span class="plan-time">{{ r.time }}</span>
                <span class="plan-desc">{{ r.title }}: {{ r.content }}</span>
              </div>
            </div>
            <div v-if="dailyPlan.proactive_actions?.length" class="plan-section">
              <div class="sidebar-label">主动行动</div>
              <div v-for="(a, i) in dailyPlan.proactive_actions" :key="i" class="plan-item">
                <span class="plan-time">{{ a.time }}</span>
                <span class="plan-desc">{{ a.action }}: {{ a.content }}</span>
              </div>
            </div>
            <div v-if="dailyPlan.pending_tasks?.length" class="plan-section">
              <div class="sidebar-label">待办任务</div>
              <div v-for="(t, i) in dailyPlan.pending_tasks" :key="i" class="plan-item">
                <span :class="['plan-priority', t.priority]">{{ priorityLabel(t.priority) }}</span>
                <span class="plan-desc">{{ t.title }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">尚未生成每日计划</div>
        </div>
        <div v-if="coordTab === 'status'" class="coord-status">
          <button class="refresh-btn" @click="loadCoordStatus">刷新</button>
          <div v-if="coordStatus" class="status-grid">
            <div class="status-item"><span class="status-label">运行中</span><span :class="['status-val', { on: coordStatus.running }]">{{ coordStatus.running ? '是' : '否' }}</span></div>
            <div class="status-item"><span class="status-label">用户在线</span><span :class="['status-val', { on: coordStatus.user_online }]">{{ coordStatus.user_online ? '是' : '否' }}</span></div>
            <div class="status-item"><span class="status-label">未读通知</span><span class="status-val">{{ coordStatus.unread_notifications }}</span></div>
            <div class="status-item"><span class="status-label">紧急</span><span class="status-val urgent">{{ coordStatus.urgent_notifications }}</span></div>
            <div class="status-item"><span class="status-label">邮件监控</span><span :class="['status-val', { on: coordStatus.email_monitoring }]">{{ coordStatus.email_monitoring ? '活跃' : '未启动' }}</span></div>
            <div v-if="coordStatus.email_stats" class="status-item"><span class="status-label">已处理</span><span class="status-val">{{ coordStatus.email_stats.total_processed }}</span></div>
          </div>
          <div class="coord-controls">
            <button v-if="!coordStatus?.running" class="start-btn" @click="startCoordination">启动协调</button>
            <button v-else class="stop-btn" @click="stopCoordination">停止协调</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../../utils/api'
import { useAppSettings } from '@/composables/useAppSettings'
import { useSettings } from '@/composables/useSettings'

const { settings: emailSettings } = useAppSettings('email')
const { updateApp } = useSettings()

defineEmits<{ openSettings: [] }>()

interface EmailParticipant { role: string; address: string; display_name: string }
interface EmailAttachment { filename: string; content_type: string; size: number }
interface EmailItem {
  id: number; message_id: string; thread_id: string; subject: string
  text: string; html: string; direction: string
  participants: EmailParticipant[] | string; attachments: EmailAttachment[] | string
  is_read: boolean | number; is_starred: boolean | number; is_deleted: boolean | number
  folder: string; date_received: string; category: string; priority: string
  sender?: string; recipients?: string; cc?: string
}

function toBool(val: boolean | number | undefined): boolean {
  if (typeof val === 'boolean') return val
  if (typeof val === 'number') return val !== 0
  return !!val
}

function parseParticipants(em: EmailItem): EmailParticipant[] {
  const p = em.participants
  if (Array.isArray(p)) return p
  if (typeof p === 'string') { try { return JSON.parse(p) } catch { return [] } }
  return []
}

function getAttachments(em: EmailItem): EmailAttachment[] {
  const a = em.attachments
  if (Array.isArray(a)) return a
  if (typeof a === 'string') { try { return JSON.parse(a) } catch { return [] } }
  return []
}

const categoryMap: Record<string, string> = {
  work: '工作', personal: '个人', promotional: '推广', social: '社交',
  financial: '财务', travel: '出行', shopping: '购物', notification: '通知',
  system: '系统', unknown: '未知', work_task: '工作任务', meeting_invite: '会议邀请',
  marketing: '营销',
}
function categoryLabel(cat: string): string { return categoryMap[cat] || cat || '' }

const priorityMap: Record<string, string> = { urgent: '紧急', high: '高', normal: '普通', low: '低' }
function priorityLabel(p: string): string { return priorityMap[p] || p || '' }

const actionMap: Record<string, string> = {
  auto_reply: '自动回复', extract_task: '提取任务', notify_user: '通知用户',
  schedule_event: '日程安排', forward_to_user: '转发用户', archive: '归档', ignore: '忽略',
}
function actionLabel(a: string | undefined): string { return actionMap[a || ''] || a || '待处理' }

const mode = ref<'human' | 'ai'>('human')
const emails = ref<EmailItem[]>([])
const selectedEmail = ref<EmailItem | null>(null)
const threadEmails = ref<EmailItem[]>([])
const currentFolder = ref('INBOX')
const searchQuery = ref('')
const loading = ref(false)
const showCompose = ref(false)
const composeData = ref({ to: '', cc: '', subject: '', body: '', in_reply_to: '', thread_id: '' })
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiMonitoring = ref(emailSettings.value.monitoring)
const aiStats = ref<any>({ total_processed: 0, auto_replied: 0, tasks_extracted: 0, user_notified: 0, monitoring: false, categories: {} })
const aiRecords = ref<any[]>([])
const showCoordPanel = ref(false)
const coordTab = ref('notifications')
const notifications = ref<any[]>([])
const dailyPlan = ref<any>(null)
const coordStatus = ref<any>(null)
const accounts = ref<any[]>([])
const currentAccountId = ref<number | null>(null)
const showAccountDialog = ref(false)
const accountForm = ref({ name: '', email_address: '', username: '', password: '', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587, use_ssl: true, provider: 'imap_smtp' })
const accountError = ref('')
let ws: WebSocket | null = null
let notifPollTimer: ReturnType<typeof setInterval> | null = null
let searchTimer: ReturnType<typeof setTimeout> | null = null

const folders = computed(() => [
  { name: 'INBOX', label: '收件箱', icon: 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z', count: emails.value.filter(e => !toBool(e.is_read) && e.folder === 'INBOX').length },
  { name: 'SENT', label: '已发送', icon: 'M2.01 21L23 12 2.01 3 2 10l15 2-15 2z', count: 0 },
  { name: 'DRAFTS', label: '草稿箱', icon: 'M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7', count: 0 },
  { name: 'TRASH', label: '已删除', icon: 'M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2', count: 0 },
])

const filteredEmails = computed(() => {
  let result = emails.value.filter(e => e.folder === currentFolder.value && !toBool(e.is_deleted))
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e => (e.subject || '').toLowerCase().includes(q) || (e.text || '').toLowerCase().includes(q))
  }
  return result
})

function getSender(em: EmailItem): string {
  const participants = parseParticipants(em)
  if (participants.length) {
    const from = participants.find((p: EmailParticipant) => p.role === 'from')
    if (from) return from.display_name || from.address
  }
  if (em.sender) return em.sender
  return ''
}

function getRecipients(em: EmailItem): string {
  const participants = parseParticipants(em)
  if (participants.length) {
    return participants.filter((p: EmailParticipant) => p.role === 'to').map((p: EmailParticipant) => p.address).join(', ')
  }
  if (em.recipients) return em.recipients
  return ''
}

function getCCList(em: EmailItem): string[] {
  const participants = parseParticipants(em)
  if (participants.length) {
    return participants.filter((p: EmailParticipant) => p.role === 'cc').map((p: EmailParticipant) => p.address)
  }
  return []
}

function getPreview(em: EmailItem): string {
  const text = em.text || em.html || ''
  const clean = text.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
  return clean.length > 120 ? clean.substring(0, 120) + '...' : clean
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function switchFolder(folder: string) {
  currentFolder.value = folder
  selectedEmail.value = null
  threadEmails.value = []
}

function switchAccount(accountId: number) {
  currentAccountId.value = accountId
  selectedEmail.value = null
  threadEmails.value = []
  loadEmails()
}

function selectEmail(em: EmailItem) {
  selectedEmail.value = em
  if (!toBool(em.is_read)) {
    em.is_read = true
    api.put(`/email/emails/${em.id}/read`, { is_read: true })
  }
  if (em.thread_id) {
    loadThread(em.thread_id)
  } else {
    threadEmails.value = [em]
  }
}

async function loadThread(threadId: string) {
  try {
    const res = await api.get(`/email/threads/${encodeURIComponent(threadId)}`)
    threadEmails.value = res.data.emails || []
  } catch { threadEmails.value = [] }
}

function openCompose(replyTo?: EmailItem) {
  if (replyTo) {
    composeData.value = {
      to: parseParticipants(replyTo).find((p: EmailParticipant) => p.role === 'from')?.address || '',
      cc: '',
      subject: replyTo.subject?.startsWith('Re: ') ? replyTo.subject : `Re: ${replyTo.subject || ''}`,
      body: '',
      in_reply_to: replyTo.message_id || '',
      thread_id: replyTo.thread_id || '',
    }
  } else {
    composeData.value = { to: '', cc: '', subject: '', body: '', in_reply_to: '', thread_id: '' }
  }
  showCompose.value = true
}

function openReply() {
  if (selectedEmail.value) openCompose(selectedEmail.value)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 86400000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (diff < 604800000) return d.toLocaleDateString([], { weekday: 'short' })
    return d.toLocaleDateString()
  } catch { return dateStr }
}

function formatTimestamp(ts: number): string {
  if (!ts) return ''
  try { return new Date(ts * 1000).toLocaleString() } catch { return '' }
}

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { loadEmails() }, 300)
}

async function addAccount() {
  accountError.value = ''
  try {
    await api.post('/email/accounts', accountForm.value)
    showAccountDialog.value = false
    accountForm.value = { name: '', email_address: '', username: '', password: '', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587, use_ssl: true, provider: 'imap_smtp' }
    await loadAccounts()
  } catch (e: any) {
    accountError.value = e?.response?.data?.detail || '添加账户失败'
  }
}

async function confirmDeleteAccount(accountId: number) {
  if (!confirm('确定要删除此邮件账户吗？相关邮件也将被删除。')) return
  try {
    await api.delete(`/email/accounts/${accountId}`)
    if (currentAccountId.value === accountId) {
      currentAccountId.value = null
      emails.value = []
      selectedEmail.value = null
    }
    await loadAccounts()
  } catch (e) { console.error('删除账户失败:', e) }
}

async function sendEmail() {
  try {
    await api.post('/email/send', { account_id: currentAccountId.value, ...composeData.value })
    showCompose.value = false
    composeData.value = { to: '', cc: '', subject: '', body: '', in_reply_to: '', thread_id: '' }
    loadEmails()
  } catch (e) { console.error('发送失败:', e) }
}

async function saveAsDraft() {
  try {
    await api.post('/email/drafts', { account_id: currentAccountId.value, ...composeData.value })
    showCompose.value = false
  } catch (e) { console.error('保存草稿失败:', e) }
}

async function loadAccounts() {
  try {
    const res = await api.get('/email/accounts')
    accounts.value = res.data.accounts || []
    if (accounts.value.length > 0 && !currentAccountId.value) {
      currentAccountId.value = accounts.value[0].id
    }
  } catch (e) { console.error('加载账户失败:', e) }
}

async function loadEmails() {
  loading.value = true
  try {
    if (!currentAccountId.value) {
      await loadAccounts()
    }
    if (currentAccountId.value) {
      const emailRes = await api.get(`/email/accounts/${currentAccountId.value}/emails`, {
        params: { folder: currentFolder.value, search: searchQuery.value }
      })
      emails.value = emailRes.data.emails || []
    }
  } catch (e) { console.error('加载邮件失败:', e) }
  finally { loading.value = false }
}

async function toggleStar() {
  if (!selectedEmail.value) return
  const newVal = !toBool(selectedEmail.value.is_starred)
  selectedEmail.value.is_starred = newVal
  await api.put(`/email/emails/${selectedEmail.value.id}/star`, { is_starred: newVal })
}

async function deleteSelectedEmail() {
  if (!selectedEmail.value) return
  await api.delete(`/email/emails/${selectedEmail.value.id}`)
  selectedEmail.value = null
  threadEmails.value = []
  loadEmails()
}

async function toggleMonitoring() {
  try {
    if (aiMonitoring.value) { await api.post('/ai/coordination/ai-email/monitor/stop'); aiMonitoring.value = false }
    else { await api.post('/ai/coordination/ai-email/monitor/start', { poll_interval: 60 }); aiMonitoring.value = true }
    updateApp({ email: { autoReply: emailSettings.value.autoReply, taskExtraction: emailSettings.value.taskExtraction, notification: emailSettings.value.notification, monitoring: aiMonitoring.value } })
  } catch (e) { console.error('切换监控失败:', e) }
}

async function loadAIStats() {
  try { const res = await api.get('/ai/coordination/ai-email/stats'); aiStats.value = res.data } catch (e) { console.error('统计加载失败:', e) }
}

async function loadAIRecords() {
  try { const res = await api.get('/ai/coordination/ai-email/records'); aiRecords.value = res.data.records || [] } catch (e) { console.error('记录加载失败:', e) }
}

async function checkNewEmails() {
  try { await api.post('/ai/coordination/ai-email/check-new'); await loadAIRecords(); await loadAIStats(); await loadEmails() } catch (e) { console.error('检查失败:', e) }
}

async function aiComposeEmail() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/email/assist', { action: 'compose', params: { context: composeData.value.body || composeData.value.subject, to: composeData.value.to, subject: composeData.value.subject } })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: '撰写失败。' } }
  finally { aiLoading.value = false }
}

async function aiReplyEmail() {
  if (!selectedEmail.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/email/assist', { action: 'reply', params: { original_subject: selectedEmail.value.subject, original_body: selectedEmail.value.text, sender: getSender(selectedEmail.value) } })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: '回复失败。' } }
  finally { aiLoading.value = false }
}

async function aiSummarizeEmail() {
  if (!selectedEmail.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/email/assist', { action: 'summarize', params: { subject: selectedEmail.value.subject, body: selectedEmail.value.text } })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: '摘要失败。' } }
  finally { aiLoading.value = false }
}

async function aiCategorizeOne() {
  if (!selectedEmail.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/email/assist', { action: 'categorize', params: { subject: selectedEmail.value.subject, body: selectedEmail.value.text, sender: getSender(selectedEmail.value) } })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: '分类失败。' } }
  finally { aiLoading.value = false }
}

function applyComposedEmail() {
  if (aiResult.value?.subject) composeData.value.subject = aiResult.value.subject
  if (aiResult.value?.body) composeData.value.body = aiResult.value.body
  showAIPanel.value = false
}

async function loadNotifications() {
  try { const res = await api.get('/ai/coordination/notifications'); notifications.value = res.data.notifications || [] } catch (e) { console.error('通知加载失败:', e) }
}

async function markNotifRead(id: string) {
  try { await api.post(`/ai/coordination/notifications/${id}/read`); await loadNotifications() } catch (e) { console.error('标记已读失败:', e) }
}

async function dismissNotif(id: string) {
  try { await api.post(`/ai/coordination/notifications/${id}/dismiss`); await loadNotifications() } catch (e) { console.error('忽略失败:', e) }
}

async function generatePlan() {
  try { const res = await api.post('/ai/coordination/plan/generate'); dailyPlan.value = res.data } catch (e) { console.error('计划生成失败:', e) }
}

async function loadCoordStatus() {
  try { const res = await api.get('/ai/coordination/status'); coordStatus.value = res.data; aiMonitoring.value = res.data.email_monitoring } catch (e) { console.error('状态加载失败:', e) }
}

async function startCoordination() {
  try { await api.post('/ai/coordination/start'); await loadCoordStatus() } catch (e) { console.error('启动失败:', e) }
}

async function stopCoordination() {
  try { await api.post('/ai/coordination/stop'); await loadCoordStatus() } catch (e) { console.error('停止失败:', e) }
}

function connectWS() {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'notification') {
          notifications.value.unshift(data.data)
          if (notifications.value.length > 100) notifications.value = notifications.value.slice(0, 100)
        }
      } catch {}
    }
    ws.onclose = () => { setTimeout(connectWS, 5000) }
  } catch (e) { console.error('WS 连接失败:', e) }
}

onMounted(() => {
  loadAccounts().then(() => { loadEmails() })
  loadAIStats(); loadAIRecords(); loadCoordStatus(); loadNotifications()
  connectWS()
  api.post('/ai/coordination/user-status', { online: true }).catch(() => {})
  notifPollTimer = setInterval(() => { loadNotifications(); loadAIStats() }, 30000)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (notifPollTimer) clearInterval(notifPollTimer)
  if (searchTimer) clearTimeout(searchTimer)
  api.post('/ai/coordination/user-status', { online: false }).catch(() => {})
})
</script>

<style scoped>
.email-client { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); font-size: var(--font-size-base); }
.email-sidebar { width: 220px; border-right: 1px solid var(--border-color); padding: var(--spacing-md); background: var(--bg-primary); display: flex; flex-direction: column; gap: var(--spacing-sm); }
.email-mode-switch { display: flex; gap: 4px; background: var(--bg-secondary); border-radius: var(--radius-md); padding: 3px; }
.mode-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 5px; padding: 7px 8px; border-radius: var(--radius-sm); font-size: var(--font-size-sm); color: var(--text-tertiary); background: transparent; border: none; cursor: pointer; transition: all var(--transition-fast); }
.mode-btn.active { background: var(--ws-accent); color: #fff; }
.compose-btn { display: flex; align-items: center; gap: var(--spacing-sm); width: 100%; padding: 10px var(--spacing-lg); background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-md); cursor: pointer; font-size: var(--font-size-base); transition: background var(--transition-fast); }
.compose-btn:hover { background: var(--ws-accent-hover); }
.email-folders { display: flex; flex-direction: column; gap: 2px; }
.folder-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: 8px var(--spacing-md); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); color: var(--text-secondary); transition: all var(--transition-fast); }
.folder-item:hover { background: var(--bg-secondary); }
.folder-item.active { background: var(--ws-accent-light); color: var(--ws-accent-soft); }
.folder-count { margin-left: auto; background: var(--ws-accent); color: #fff; border-radius: var(--radius-full); padding: 1px 6px; font-size: var(--font-size-xs); }
.sidebar-section { display: flex; flex-direction: column; gap: 4px; margin-top: var(--spacing-sm); padding-top: var(--spacing-sm); border-top: 1px solid var(--border-color); }
.sidebar-label { font-size: var(--font-size-xs); color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; font-weight: var(--font-weight-medium); }
.no-account-hint { font-size: var(--font-size-sm); color: var(--text-tertiary); padding: 4px 0; }
.account-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: 6px var(--spacing-md); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); color: var(--text-secondary); transition: all var(--transition-fast); }
.account-item:hover { background: var(--bg-secondary); }
.account-item.active { background: var(--ws-accent-light); color: var(--ws-accent-soft); }
.account-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.icon-btn-sm { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 2px; border-radius: var(--radius-sm); display: flex; align-items: center; }
.icon-btn-sm:hover { color: var(--ws-danger); }
.add-account-btn { display: flex; align-items: center; gap: 6px; width: 100%; padding: 6px var(--spacing-md); background: none; color: var(--ws-accent-soft); border: 1px dashed var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.add-account-btn:hover { border-color: var(--ws-accent); background: var(--ws-accent-light); }
.ai-sidebar-section { padding: var(--spacing-md); background: var(--bg-secondary); border-radius: var(--radius-md); }
.ai-status-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing-sm); }
.status-label { font-size: var(--font-size-sm); color: var(--text-secondary); }
.toggle-btn { padding: 3px 12px; border-radius: var(--radius-full); font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); border: none; cursor: pointer; background: var(--border-color); color: var(--text-tertiary); transition: all var(--transition-fast); }
.toggle-btn.on { background: var(--ws-success); color: #fff; }
.ai-config-info { display: flex; flex-direction: column; gap: 6px; margin-top: 6px; }
.config-hint { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.goto-settings-btn { display: flex; align-items: center; gap: 4px; padding: 5px 10px; background: var(--bg-primary); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-xs); transition: all var(--transition-fast); }
.goto-settings-btn:hover { border-color: var(--ws-accent); }
.stat-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: var(--font-size-sm); }
.stat-value { color: var(--ws-accent-soft); font-weight: var(--font-weight-semibold); }
.check-now-btn { display: flex; align-items: center; gap: 6px; width: 100%; padding: 8px var(--spacing-md); background: var(--bg-secondary); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.check-now-btn:hover { border-color: var(--ws-accent); }
.sidebar-bottom { margin-top: auto; padding-top: var(--spacing-sm); border-top: 1px solid var(--border-color); }
.coord-btn { display: flex; align-items: center; gap: 6px; width: 100%; padding: 8px var(--spacing-md); background: var(--bg-secondary); color: var(--ws-accent); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.coord-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.email-main { flex: 1; display: flex; overflow: hidden; }
.email-list { width: 320px; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; overflow-y: auto; }
.email-list-header { padding: var(--spacing-md); }
.search-input { width: 100%; padding: 8px var(--spacing-md); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: var(--font-size-sm); box-sizing: border-box; background: var(--bg-secondary); color: var(--text-primary); outline: none; transition: border-color var(--transition-fast); }
.search-input:focus { border-color: var(--ws-accent); }
.loading-state { display: flex; align-items: center; justify-content: center; gap: var(--spacing-sm); padding: var(--spacing-xl); color: var(--text-tertiary); }
.spinner { width: 20px; height: 20px; border: 2px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.email-item { padding: 10px var(--spacing-lg); border-bottom: 1px solid var(--bg-secondary); cursor: pointer; transition: background var(--transition-fast); }
.email-item:hover { background: var(--bg-secondary); }
.email-item.selected { background: var(--ws-accent-light); }
.email-item.unread .email-item-sender { font-weight: var(--font-weight-semibold); }
.email-item.unread .email-item-subject { font-weight: var(--font-weight-semibold); }
.email-item-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.email-item-sender { font-size: var(--font-size-sm); }
.email-item-date { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.email-item-subject { font-size: var(--font-size-sm); color: var(--text-primary); margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.email-item-preview { font-size: var(--font-size-xs); color: var(--text-tertiary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.email-item-tags { display: flex; gap: 4px; margin-top: 4px; }
.category-tag { padding: 1px 6px; border-radius: 3px; font-size: 10px; }
.category-tag.work, .category-tag.work_task { background: var(--ws-accent); color: #fff; }
.category-tag.personal { background: #2196f3; color: #fff; }
.category-tag.promotional, .category-tag.marketing { background: #ff9800; color: #fff; }
.category-tag.financial { background: #4caf50; color: #fff; }
.category-tag.notification { background: #9c27b0; color: #fff; }
.priority-tag { padding: 1px 6px; border-radius: 3px; font-size: 10px; }
.priority-tag.urgent { background: var(--ws-danger); color: #fff; }
.priority-tag.high { background: var(--ws-warning); color: #000; }
.priority-tag.normal { background: var(--ws-success); color: #fff; }
.priority-tag.low { background: var(--text-tertiary); color: #fff; }
.attachment-tag { display: flex; align-items: center; gap: 2px; font-size: 10px; color: var(--text-tertiary); }
.email-detail { flex: 1; padding: var(--spacing-xl); overflow-y: auto; }
.email-detail-header { margin-bottom: var(--spacing-lg); }
.email-detail-header h3 { margin: 0 0 var(--spacing-sm); font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
.email-detail-meta { display: flex; gap: var(--spacing-lg); font-size: var(--font-size-sm); color: var(--text-tertiary); flex-wrap: wrap; }
.email-detail-participants { font-size: var(--font-size-sm); color: var(--text-tertiary); margin-bottom: var(--spacing-md); }
.cc-label { margin-right: 4px; }
.email-detail-body { font-size: var(--font-size-base); line-height: 1.6; color: var(--text-secondary); }
.email-detail-attachments { margin-top: var(--spacing-md); padding: var(--spacing-sm); background: var(--bg-secondary); border-radius: var(--radius-sm); }
.attachment-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: 4px 0; font-size: var(--font-size-sm); color: var(--text-secondary); }
.att-name { flex: 1; }
.att-size { color: var(--text-tertiary); }
.email-thread-section { margin-top: var(--spacing-lg); padding-top: var(--spacing-md); border-top: 1px solid var(--border-color); }
.thread-msg { padding: var(--spacing-sm); margin-bottom: var(--spacing-sm); border-radius: var(--radius-sm); background: var(--bg-secondary); }
.thread-msg.current { border-left: 3px solid var(--ws-accent); }
.thread-msg-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.thread-msg-sender { font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); }
.thread-msg-date { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.thread-msg-body { font-size: var(--font-size-sm); line-height: 1.5; color: var(--text-secondary); }
.email-ai-actions { display: flex; gap: 6px; margin-top: var(--spacing-lg); padding-top: var(--spacing-md); border-top: 1px solid var(--border-color); flex-wrap: wrap; }
.email-ai-btn { padding: 6px 14px; background: var(--bg-secondary); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.email-ai-btn:hover { border-color: var(--ws-accent); }
.email-action-btn { padding: 6px 10px; background: var(--bg-secondary); color: var(--text-tertiary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition-fast); }
.email-action-btn:hover { color: var(--text-primary); border-color: var(--ws-accent); }
.email-action-btn.starred { color: var(--ws-warning); }
.empty-state { display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); font-size: var(--font-size-base); flex: 1; }
.empty-hint { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md); padding: var(--spacing-2xl); }
.empty-hint p { color: var(--text-tertiary); }
.primary-btn-sm { padding: 6px 16px; background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); }
.primary-btn-sm:hover { background: var(--ws-accent-hover); }
.ai-email-content { flex: 1; padding: var(--spacing-lg); overflow-y: auto; }
.section-title { font-size: var(--font-size-base); color: var(--ws-accent-soft); margin: 0 0 var(--spacing-md); font-weight: var(--font-weight-semibold); }
.ai-record-card { padding: var(--spacing-md); background: var(--bg-secondary); border-radius: var(--radius-md); margin-bottom: var(--spacing-sm); border-left: 3px solid var(--ws-accent); }
.ai-record-card.urgent { border-left-color: var(--ws-danger); }
.ai-record-card.high { border-left-color: var(--ws-warning); }
.record-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.record-subject { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); color: var(--text-primary); }
.action-badge { padding: 2px 8px; border-radius: var(--radius-full); font-size: 10px; }
.action-badge.auto_reply { background: var(--ws-success); color: #fff; }
.action-badge.extract_task { background: var(--ws-accent); color: #fff; }
.action-badge.notify_user { background: var(--ws-warning); color: #000; }
.action-badge.forward_to_user { background: #2196f3; color: #fff; }
.action-badge.schedule_event { background: #00bcd4; color: #000; }
.action-badge.archive { background: var(--text-tertiary); color: #fff; }
.action-badge.ignore { background: #333; color: var(--text-tertiary); }
.record-meta { display: flex; justify-content: space-between; font-size: var(--font-size-xs); color: var(--text-tertiary); margin-bottom: 6px; }
.record-decision { padding: var(--spacing-sm); background: var(--bg-primary); border-radius: 4px; margin-bottom: 6px; }
.decision-row { display: flex; gap: var(--spacing-sm); font-size: var(--font-size-sm); margin-bottom: 2px; }
.decision-label { color: var(--text-tertiary); min-width: 50px; }
.decision-value { color: var(--text-secondary); }
.record-status { display: flex; gap: 6px; }
.status-tag { padding: 2px 8px; border-radius: var(--radius-full); font-size: 10px; }
.status-tag.replied { background: var(--ws-success); color: #fff; }
.status-tag.notified { background: var(--ws-warning); color: #000; }
.status-tag.tasks { background: var(--ws-accent); color: #fff; }
.compose-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.compose-modal { background: var(--bg-primary); border-radius: var(--radius-lg); padding: var(--spacing-xl); width: 560px; max-height: 80vh; display: flex; flex-direction: column; gap: var(--spacing-md); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg); }
.compose-modal h3 { margin: 0; color: var(--text-primary); font-size: var(--font-size-md); }
.compose-input { width: 100%; padding: 8px var(--spacing-md); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: var(--font-size-sm); box-sizing: border-box; background: var(--bg-secondary); color: var(--text-primary); outline: none; transition: border-color var(--transition-fast); }
.compose-input:focus { border-color: var(--ws-accent); }
.compose-body { width: 100%; min-height: 200px; padding: 8px var(--spacing-md); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: var(--font-size-sm); resize: vertical; box-sizing: border-box; background: var(--bg-secondary); color: var(--text-primary); outline: none; font-family: inherit; transition: border-color var(--transition-fast); }
.compose-body:focus { border-color: var(--ws-accent); }
.compose-actions { display: flex; gap: var(--spacing-sm); justify-content: flex-end; }
.btn-ai { padding: 8px var(--spacing-lg); background: var(--bg-secondary); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.btn-ai:hover { border-color: var(--ws-accent); }
.btn-primary { padding: 8px 20px; background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: background var(--transition-fast); }
.btn-primary:hover { background: var(--ws-accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 8px 20px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; color: var(--text-tertiary); font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.btn-secondary:hover { color: var(--text-primary); }
.account-error { color: var(--ws-danger); font-size: var(--font-size-sm); padding: 4px 0; }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: var(--font-size-base); color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 2px; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: var(--spacing-md); }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md); padding: var(--spacing-xl); color: var(--text-tertiary); }
.ai-section { margin-bottom: var(--spacing-lg); }
.ai-result { color: var(--text-primary); }
.summary-text { font-size: var(--font-size-sm); line-height: 1.6; color: var(--text-secondary); padding: var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); }
.composed-body { font-size: var(--font-size-sm); line-height: 1.6; color: var(--text-secondary); padding: 10px; background: var(--bg-primary); border-radius: var(--radius-sm); white-space: pre-wrap; }
.apply-btn { width: 100%; padding: 8px; background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); margin-top: var(--spacing-sm); transition: background var(--transition-fast); }
.apply-btn:hover { background: var(--ws-accent-hover); }
.category-badge { padding: 3px 10px; background: var(--border-color); border-radius: var(--radius-full); font-size: var(--font-size-sm); color: var(--ws-accent-soft); }
.urgency-badge { padding: 2px 8px; border-radius: var(--radius-full); font-size: var(--font-size-xs); margin-left: 6px; }
.urgency-badge.high { background: var(--ws-danger); color: #fff; }
.urgency-badge.medium { background: var(--ws-warning); color: #000; }
.urgency-badge.low { background: #44aa44; color: #fff; }
.coord-panel { width: 380px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.coord-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.coord-header h4 { margin: 0; font-size: var(--font-size-base); color: var(--ws-accent-soft); }
.coord-tabs { display: flex; border-bottom: 1px solid var(--border-color); }
.coord-tab { flex: 1; padding: 8px; text-align: center; font-size: var(--font-size-sm); color: var(--text-tertiary); background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; transition: all var(--transition-fast); }
.coord-tab.active { color: var(--ws-accent-soft); border-bottom-color: var(--ws-accent); }
.coord-content { flex: 1; overflow-y: auto; padding: var(--spacing-md); }
.refresh-btn { width: 100%; padding: 6px; background: var(--bg-primary); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-xs); margin-bottom: 10px; transition: all var(--transition-fast); }
.refresh-btn:hover { border-color: var(--ws-accent); }
.notif-card { padding: 10px; background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: 6px; border-left: 3px solid var(--ws-accent); }
.notif-card.urgent { border-left-color: var(--ws-danger); }
.notif-card.high { border-left-color: var(--ws-warning); }
.notif-card.read { opacity: 0.6; }
.notif-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.notif-type { font-size: 10px; text-transform: uppercase; padding: 1px 6px; border-radius: 3px; background: var(--border-color); color: var(--ws-accent-soft); }
.notif-time { font-size: 10px; color: var(--text-tertiary); }
.notif-title { font-size: var(--font-size-sm); color: var(--text-primary); margin: 0 0 4px; }
.notif-content { font-size: var(--font-size-sm); color: var(--text-tertiary); margin-bottom: 6px; }
.notif-actions { display: flex; gap: 6px; }
.notif-btn { padding: 3px 10px; border-radius: 4px; font-size: var(--font-size-xs); border: none; cursor: pointer; }
.read-btn { background: var(--border-color); color: var(--ws-accent-soft); }
.dismiss-btn { background: var(--bg-tertiary); color: var(--text-tertiary); }
.plan-content { color: var(--text-primary); }
.plan-summary { font-size: var(--font-size-sm); line-height: 1.6; color: var(--text-secondary); padding: var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: var(--spacing-md); }
.plan-section { margin-bottom: var(--spacing-md); }
.plan-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: 4px var(--spacing-sm); background: var(--bg-primary); border-radius: 4px; margin-bottom: 3px; font-size: var(--font-size-sm); }
.plan-time { color: var(--ws-accent); min-width: 50px; }
.plan-desc { color: var(--text-secondary); flex: 1; }
.plan-priority { padding: 1px 6px; border-radius: 3px; font-size: 10px; }
.plan-priority.high { background: var(--ws-danger); color: #fff; }
.plan-priority.medium { background: var(--ws-warning); color: #000; }
.plan-priority.low { background: var(--ws-success); color: #fff; }
.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm); margin-bottom: var(--spacing-md); }
.status-item { display: flex; justify-content: space-between; padding: var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); }
.status-item .status-label { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.status-val { font-size: var(--font-size-sm); color: var(--ws-accent-soft); font-weight: var(--font-weight-semibold); }
.status-val.on { color: var(--ws-success); }
.status-val.urgent { color: var(--ws-danger); }
.coord-controls { display: flex; gap: var(--spacing-sm); }
.start-btn { flex: 1; padding: 8px; background: var(--ws-success); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: opacity var(--transition-fast); }
.start-btn:hover { opacity: 0.9; }
.stop-btn { flex: 1; padding: 8px; background: var(--ws-danger); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); transition: opacity var(--transition-fast); }
.stop-btn:hover { opacity: 0.9; }
</style>
