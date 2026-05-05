<template>
  <div class="proactive-settings">
    <h3 class="global-section-title">主动式交互</h3>
    <p class="proactive-desc">配置 AI 助手的主动服务、消息渠道、隐私偏好和自动化规则，让 AI 在合适的时机以合适的方式主动帮助你</p>

    <div class="global-form-group lab-row">
      <label>启用主动服务</label>
      <label class="global-switch">
        <input type="checkbox" v-model="proactiveEnabled" @change="toggleProactive" />
        <span class="slider"></span>
      </label>
    </div>

    <div v-if="proactiveEnabled">
      <h4 class="subsection-title">主动服务</h4>
      <p class="section-hint">管理 20 个内置主动服务的启用状态。AI 会根据上下文和触发条件自动调度已启用的服务。</p>

      <div class="service-categories">
        <div v-for="cat in serviceCategories" :key="cat.key" class="service-category">
          <div class="category-header" @click="cat.expanded = !cat.expanded">
            <div class="category-left">
              <span class="category-icon" v-html="cat.icon"></span>
              <span class="category-name">{{ cat.label }}</span>
              <span class="category-count">{{ getEnabledCount(cat.key) }}/{{ getCategoryServices(cat.key).length }}</span>
            </div>
            <svg class="expand-arrow" :class="{ expanded: cat.expanded }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <div v-if="cat.expanded" class="category-services">
            <div v-for="svc in getCategoryServices(cat.key)" :key="svc.name" class="service-card">
              <div class="service-info">
                <span class="service-name">{{ svc.display_name }}</span>
                <span class="service-desc">{{ svc.description }}</span>
              </div>
              <div class="service-right">
                <span class="priority-badge" :class="svc.priority">{{ priorityLabels[svc.priority] || svc.priority }}</span>
                <label class="global-switch small">
                  <input type="checkbox" :checked="svc.enabled" @change="toggleService(svc.name, $event)" />
                  <span class="slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <h4 class="subsection-title">调度设置</h4>
      <div class="config-block">
        <div class="field-row">
          <div class="global-form-group flex-1">
            <label>检查间隔 (秒)</label>
            <input type="number" v-model.number="schedulerConfig.checkInterval" class="global-input" min="10" max="600" step="10" />
          </div>
          <div class="global-form-group flex-1">
            <label>默认冷却时间 (秒)</label>
            <input type="number" v-model.number="schedulerConfig.defaultCooldown" class="global-input" min="30" max="86400" step="30" />
          </div>
        </div>
        <div class="field-row">
          <div class="global-form-group flex-1">
            <label>记忆构建间隔 (秒)</label>
            <input type="number" v-model.number="schedulerConfig.memoryBuildInterval" class="global-input" min="30" max="600" step="10" />
          </div>
          <div class="global-form-group flex-1">
            <label>自动优化间隔 (秒)</label>
            <input type="number" v-model.number="schedulerConfig.optimizeInterval" class="global-input" min="600" max="86400" step="600" />
          </div>
        </div>
      </div>

      <h4 class="subsection-title">消息渠道</h4>
      <p class="section-hint">配置 AI 主动触达你的消息渠道。不同紧急度的服务会自动选择合适的渠道。</p>

      <div class="channel-section">
        <div class="channel-sub-header">IM 渠道</div>
        <div class="channel-list">
          <div v-for="channel in imChannels" :key="channel.channel_type" class="channel-card">
            <div class="channel-info">
              <span class="channel-icon">
                <ChannelSvgIcon :type="channel.channel_type" />
              </span>
              <div class="channel-details">
                <span class="channel-name">{{ channelNames[channel.channel_type] || channel.channel_type }}</span>
                <span class="channel-status" :class="{ connected: channel.connected && channel.enabled }">
                  {{ channel.connected && channel.enabled ? '已启用' : channel.enabled ? '未连接' : '未启用' }}
                </span>
              </div>
            </div>
            <div class="channel-actions">
              <button v-if="!channel.enabled" class="ch-btn" @click="configureChannel(channel.channel_type)">配置</button>
              <button v-if="channel.enabled" class="ch-btn" @click="configureChannel(channel.channel_type)">设置</button>
              <button v-if="channel.enabled" class="ch-btn toggle" @click="toggleChannel(channel.channel_type, false)">禁用</button>
            </div>
          </div>
        </div>
      </div>

      <div class="channel-section">
        <div class="channel-sub-header">内置渠道</div>
        <div class="channel-card">
          <div class="channel-info">
            <span class="channel-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,6 12,13 2,6"/></svg>
            </span>
            <div class="channel-details">
              <span class="channel-name">AI 邮箱</span>
              <span class="channel-status connected">内置渠道</span>
            </div>
          </div>
        </div>
        <div class="channel-card">
          <div class="channel-info">
            <span class="channel-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 010 14.14"/><path d="M15.54 8.46a5 5 0 010 7.07"/></svg>
            </span>
            <div class="channel-details">
              <span class="channel-name">语音播报</span>
              <span class="channel-status">需连接耳机</span>
            </div>
          </div>
        </div>
        <div class="channel-card">
          <div class="channel-info">
            <span class="channel-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            </span>
            <div class="channel-details">
              <span class="channel-name">日历注入</span>
              <span class="channel-status">AI 可建议日程</span>
            </div>
          </div>
        </div>
      </div>

      <h4 class="subsection-title">渠道路由</h4>
      <p class="section-hint">不同紧急度的主动服务会通过不同渠道投递。你可以在下方调整各紧急度对应的投递渠道。</p>

      <div class="routing-block">
        <div v-for="route in urgencyRoutes" :key="route.level" class="route-row">
          <span class="route-level" :class="route.level">{{ route.label }}</span>
          <div class="route-channels">
            <span v-for="ch in route.channels" :key="ch" class="route-channel-tag">{{ channelLabelMap[ch] || ch }}</span>
          </div>
        </div>
      </div>

      <h4 class="subsection-title">自动化规则</h4>
      <p class="section-hint">基于环境条件自动触发操作。AI 会根据位置、设备状态、日历等条件自动执行规则。</p>

      <div class="automation-list">
        <div v-for="rule in automationRules" :key="rule.name" class="automation-card">
          <div class="automation-info">
            <span class="automation-name">{{ rule.display_name || rule.name }}</span>
            <span class="automation-desc">{{ rule.description }}</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" :checked="rule.enabled" @change="toggleAutomationRule(rule.name, $event)" />
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <h4 class="subsection-title">隐私偏好</h4>
      <p class="section-hint">控制 AI 主动服务可以访问的数据类型。敏感数据始终在本地处理。</p>

      <div class="privacy-block">
        <div class="privacy-row">
          <div class="privacy-info">
            <span class="privacy-label">屏幕分析</span>
            <span class="privacy-desc">允许 AI 分析屏幕内容以提供上下文感知服务</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="privacyPrefs.allow_screen_analysis" @change="savePrivacyPref('allow_screen_analysis', $event)" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="privacy-row">
          <div class="privacy-info">
            <span class="privacy-label">通知分析</span>
            <span class="privacy-desc">允许 AI 读取通知内容以判断紧急度和提取行动项</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="privacyPrefs.allow_notification_analysis" @change="savePrivacyPref('allow_notification_analysis', $event)" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="privacy-row">
          <div class="privacy-info">
            <span class="privacy-label">位置追踪</span>
            <span class="privacy-desc">允许 AI 使用位置信息提供通勤助手和场景检测</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="privacyPrefs.allow_location_tracking" @change="savePrivacyPref('allow_location_tracking', $event)" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="privacy-row">
          <div class="privacy-info">
            <span class="privacy-label">剪贴板分析</span>
            <span class="privacy-desc">允许 AI 分析剪贴板内容以提供洞察和建议</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="privacyPrefs.allow_clipboard_analysis" @change="savePrivacyPref('allow_clipboard_analysis', $event)" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="privacy-row">
          <div class="privacy-info">
            <span class="privacy-label">数据保留天数</span>
            <span class="privacy-desc">主动服务相关数据的保留时长</span>
          </div>
          <div class="privacy-input">
            <input type="number" v-model.number="privacyPrefs.data_retention_days" class="global-input small" min="1" max="365" step="1" @change="savePrivacyPref('data_retention_days', $event)" />
            <span class="privacy-unit">天</span>
          </div>
        </div>
      </div>

      <h4 class="subsection-title">投递偏好</h4>
      <p class="section-hint">控制 AI 在不同用户状态下的投递行为。</p>

      <div class="delivery-block">
        <div class="delivery-row">
          <div class="delivery-info">
            <span class="delivery-label">会议中仅投递紧急消息</span>
            <span class="delivery-desc">在检测到你处于会议中时，仅投递 urgent 及以上优先级的主动服务</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="deliveryPrefs.meetingQuietMode" @change="saveDeliveryPrefs" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="delivery-row">
          <div class="delivery-info">
            <span class="delivery-label">专注模式过滤</span>
            <span class="delivery-desc">在检测到深度专注时，不投递 suggested 和 chitchat 级别的服务</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="deliveryPrefs.focusFilter" @change="saveDeliveryPrefs" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="delivery-row">
          <div class="delivery-info">
            <span class="delivery-label">情绪感知降级</span>
            <span class="delivery-desc">检测到压力情绪时，自动降低低优先级服务的投递频率</span>
          </div>
          <label class="global-switch small">
            <input type="checkbox" v-model="deliveryPrefs.moodAware" @change="saveDeliveryPrefs" />
            <span class="slider"></span>
          </label>
        </div>
      </div>

      <div class="save-bar">
        <button class="save-btn" @click="saveAll" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
        <button class="cancel-btn" @click="loadAll">重置</button>
      </div>

      <div v-if="message" class="save-message" :class="messageType">{{ message }}</div>
    </div>

    <div v-if="showConfig" class="config-modal" @click.self="showConfig = false">
      <div class="config-panel">
        <h3>{{ channelNames[configType] }} 配置</h3>
        <div class="config-fields">
          <div v-for="field in configFields[configType]" :key="field.key" class="config-field">
            <label>{{ field.label }}</label>
            <input v-model="configData[field.key]" :type="field.type || 'text'" :placeholder="field.placeholder || ''" class="global-input" />
          </div>
        </div>
        <div class="config-actions">
          <button class="config-btn cancel" @click="showConfig = false">取消</button>
          <button class="config-btn save" @click="saveConfig">保存并启用</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import ChannelSvgIcon from './ChannelSvgIcon.vue'

interface ChannelStatus {
  channel_type: string
  enabled: boolean
  connected: boolean
  daily_count: number
}

interface ProactiveService {
  name: string
  display_name: string
  description: string
  category: string
  enabled: boolean
  priority: string
  cooldown_seconds: number
  max_fires_per_day: number
  fire_count: number
  accept_count: number
  ignore_count: number
  negative_count: number
}

interface AutomationRule {
  name: string
  display_name: string
  description: string
  enabled: boolean
  condition: Record<string, any>
  action: Record<string, any>
}

const proactiveEnabled = ref(true)
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const services = ref<ProactiveService[]>([])
const imChannels = ref<ChannelStatus[]>([])
const automationRules = ref<AutomationRule[]>([])

const showConfig = ref(false)
const configType = ref('')
const configData = ref<Record<string, string>>({})

const schedulerConfig = reactive({
  checkInterval: 60,
  defaultCooldown: 300,
  memoryBuildInterval: 120,
  optimizeInterval: 3600,
})

const privacyPrefs = reactive({
  allow_screen_analysis: true,
  allow_notification_analysis: true,
  allow_location_tracking: false,
  allow_clipboard_analysis: true,
  data_retention_days: 30,
})

const deliveryPrefs = reactive({
  meetingQuietMode: true,
  focusFilter: true,
  moodAware: true,
})

const channelNames: Record<string, string> = {
  wechat: '微信', telegram: 'Telegram', discord: 'Discord',
  slack: 'Slack', feishu: '飞书', wecom: '企业微信', dingtalk: '钉钉',
}

const configFields: Record<string, { key: string; label: string; type?: string; placeholder?: string }[]> = {
  wechat: [{ key: 'app_id', label: 'App ID' }, { key: 'app_secret', label: 'App Secret', type: 'password' }],
  telegram: [{ key: 'bot_token', label: 'Bot Token', type: 'password' }],
  discord: [{ key: 'bot_token', label: 'Bot Token', type: 'password' }],
  slack: [{ key: 'bot_token', label: 'Bot Token (xoxb-...)', type: 'password' }],
  feishu: [{ key: 'app_id', label: 'App ID' }, { key: 'app_secret', label: 'App Secret', type: 'password' }],
  wecom: [{ key: 'corp_id', label: 'Corp ID' }, { key: 'agent_id', label: 'Agent ID' }, { key: 'secret', label: 'Secret', type: 'password' }],
  dingtalk: [{ key: 'app_key', label: 'App Key' }, { key: 'app_secret', label: 'App Secret', type: 'password' }],
}

const priorityLabels: Record<string, string> = {
  urgent: '紧急',
  important: '重要',
  suggested: '建议',
  chitchat: '闲聊',
}

const channelLabelMap: Record<string, string> = {
  system_notification: '系统通知',
  popup: '弹窗',
  widget: '小组件',
  email: '邮件',
  chat_message: '聊天消息',
  websocket: 'WebSocket',
  voice: '语音',
  calendar_inject: '日历注入',
  low_priority_notification: '低优先级通知',
  toast: '轻提示',
}

const urgencyRoutes = [
  { level: 'critical', label: '紧急', channels: ['system_notification', 'popup', 'websocket'] },
  { level: 'urgent', label: '急迫', channels: ['system_notification', 'websocket'] },
  { level: 'important', label: '重要', channels: ['widget', 'email', 'websocket'] },
  { level: 'normal', label: '普通', channels: ['chat_message', 'websocket'] },
  { level: 'suggested', label: '建议', channels: ['chat_message', 'low_priority_notification'] },
  { level: 'chitchat', label: '闲聊', channels: ['low_priority_notification', 'toast'] },
]

const serviceCategories = reactive([
  { key: 'work', label: '工作', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>', expanded: true },
  { key: 'info', label: '信息', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>', expanded: false },
  { key: 'life', label: '生活', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>', expanded: false },
  { key: 'env', label: '环境', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/><circle cx="12" cy="12" r="5"/></svg>', expanded: false },
  { key: 'creative', label: '创意', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>', expanded: false },
  { key: 'social', label: '社交', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>', expanded: false },
])

function getCategoryServices(category: string): ProactiveService[] {
  return services.value.filter(s => s.category === category)
}

function getEnabledCount(category: string): number {
  return getCategoryServices(category).filter(s => s.enabled).length
}

async function fetchServices() {
  try {
    const { data } = await api.get('/ai/coordination/proactive/services')
    services.value = data.services || []
  } catch { /* ignore */ }
}

async function fetchChannels() {
  try {
    const { data } = await api.get('/im/channels')
    imChannels.value = data.channels || []
  } catch { /* ignore */ }
}

async function fetchAutomationRules() {
  try {
    const { data } = await api.get('/ai/coordination/automation/rules')
    automationRules.value = (data.rules || []).map((r: any) => ({
      name: r.name,
      display_name: r.display_name || r.name,
      description: r.description || '',
      enabled: r.enabled !== false,
      condition: r.condition || {},
      action: r.action || {},
    }))
  } catch { /* ignore */ }
}

async function fetchPrivacyStatus() {
  try {
    const { data } = await api.get('/ai/coordination/privacy/status')
    const prefs = data.preferences || {}
    if (prefs.allow_screen_analysis !== undefined) privacyPrefs.allow_screen_analysis = prefs.allow_screen_analysis
    if (prefs.allow_notification_analysis !== undefined) privacyPrefs.allow_notification_analysis = prefs.allow_notification_analysis
    if (prefs.allow_location_tracking !== undefined) privacyPrefs.allow_location_tracking = prefs.allow_location_tracking
    if (prefs.allow_clipboard_analysis !== undefined) privacyPrefs.allow_clipboard_analysis = prefs.allow_clipboard_analysis
    if (prefs.data_retention_days !== undefined) privacyPrefs.data_retention_days = prefs.data_retention_days
  } catch { /* ignore */ }
}

async function fetchProactiveConfig() {
  try {
    const { data } = await api.get('/ai/coordination/proactive/config')
    if (data.scheduler) {
      schedulerConfig.checkInterval = data.scheduler.check_interval ?? 60
      schedulerConfig.defaultCooldown = data.scheduler.default_cooldown ?? 300
      schedulerConfig.memoryBuildInterval = data.scheduler.memory_build_interval ?? 120
      schedulerConfig.optimizeInterval = data.scheduler.optimize_interval ?? 3600
    }
    if (data.delivery) {
      deliveryPrefs.meetingQuietMode = data.delivery.meeting_quiet_mode ?? true
      deliveryPrefs.focusFilter = data.delivery.focus_filter ?? true
      deliveryPrefs.moodAware = data.delivery.mood_aware ?? true
    }
    if (data.enabled !== undefined) {
      proactiveEnabled.value = data.enabled
    }
  } catch { /* ignore */ }
}

async function toggleService(name: string, event: Event) {
  const enabled = (event.target as HTMLInputElement).checked
  try {
    await api.post('/ai/coordination/proactive/services/toggle', { service_name: name, enabled })
    const svc = services.value.find(s => s.name === name)
    if (svc) svc.enabled = enabled
  } catch { /* ignore */ }
}

async function toggleAutomationRule(name: string, event: Event) {
  const enabled = (event.target as HTMLInputElement).checked
  try {
    await api.post('/ai/coordination/automation/rules/toggle', { rule_name: name, enabled })
    const rule = automationRules.value.find(r => r.name === name)
    if (rule) rule.enabled = enabled
  } catch { /* ignore */ }
}

async function toggleProactive() {
  try {
    await api.post('/ai/coordination/proactive/config', { enabled: proactiveEnabled.value })
  } catch { /* ignore */ }
}

async function savePrivacyPref(key: string, event: Event) {
  const value = key === 'data_retention_days'
    ? parseInt((event.target as HTMLInputElement).value, 10)
    : (event.target as HTMLInputElement).checked
  try {
    await api.post('/ai/coordination/privacy/preference', { key, value })
  } catch { /* ignore */ }
}

async function saveDeliveryPrefs() {
  try {
    await api.post('/ai/coordination/proactive/config', {
      delivery: {
        meeting_quiet_mode: deliveryPrefs.meetingQuietMode,
        focus_filter: deliveryPrefs.focusFilter,
        mood_aware: deliveryPrefs.moodAware,
      }
    })
  } catch { /* ignore */ }
}

function configureChannel(type: string) {
  configType.value = type
  configData.value = {}
  showConfig.value = true
}

async function saveConfig() {
  try {
    await api.post('/im/channels/configure', {
      channel_type: configType.value,
      config: configData.value,
      enabled: true,
    })
    showConfig.value = false
    await fetchChannels()
  } catch { /* ignore */ }
}

async function toggleChannel(type: string, enabled: boolean) {
  try {
    await api.post('/im/channels/configure', {
      channel_type: type,
      config: {},
      enabled,
    })
    await fetchChannels()
  } catch { /* ignore */ }
}

async function saveAll() {
  saving.value = true
  message.value = ''
  try {
    await api.post('/ai/coordination/proactive/config', {
      enabled: proactiveEnabled.value,
      scheduler: {
        check_interval: schedulerConfig.checkInterval,
        default_cooldown: schedulerConfig.defaultCooldown,
        memory_build_interval: schedulerConfig.memoryBuildInterval,
        optimize_interval: schedulerConfig.optimizeInterval,
      },
      delivery: {
        meeting_quiet_mode: deliveryPrefs.meetingQuietMode,
        focus_filter: deliveryPrefs.focusFilter,
        mood_aware: deliveryPrefs.moodAware,
      }
    })
    message.value = '设置已保存'
    messageType.value = 'success'
  } catch (e: any) {
    message.value = e.message || '保存失败'
    messageType.value = 'error'
  } finally {
    saving.value = false
    setTimeout(() => { message.value = '' }, 3000)
  }
}

function loadAll() {
  fetchServices()
  fetchChannels()
  fetchAutomationRules()
  fetchPrivacyStatus()
  fetchProactiveConfig()
}

onMounted(loadAll)
</script>

<style scoped>
.proactive-settings {
  max-width: 640px;
}
.proactive-desc {
  color: var(--text-secondary, #888);
  font-size: 13px;
  margin: 0 0 20px;
}
.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 8px;
  background: var(--bg-secondary);
  margin-bottom: 16px;
}
.lab-row.global-form-group {
  margin-bottom: 16px;
}
.lab-row label:first-child {
  font-size: 14px;
  color: var(--text-color);
  display: inline;
  margin-bottom: 0;
}
.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}
.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 12px;
}
.global-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
  margin-bottom: 0;
}
.global-switch.small {
  width: 34px;
  height: 18px;
}
.global-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.global-switch .slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--border-color);
  border-radius: 22px;
  transition: 0.2s;
}
.global-switch .slider::before {
  content: '';
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.2s;
}
.global-switch.small .slider::before {
  height: 12px;
  width: 12px;
}
.global-switch input:checked + .slider {
  background: var(--primary-color);
}
.global-switch input:checked + .slider::before {
  transform: translateX(18px);
}
.global-switch.small input:checked + .slider::before {
  transform: translateX(16px);
}
.service-categories {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.service-category {
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 8px;
  overflow: hidden;
}
.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  background: var(--bg-secondary);
  transition: background 0.15s;
}
.category-header:hover {
  background: var(--border-color);
}
.category-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.category-icon {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
}
.category-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #e0e0e0);
}
.category-count {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-primary);
  padding: 1px 6px;
  border-radius: 8px;
}
.expand-arrow {
  color: var(--text-tertiary);
  transition: transform 0.2s;
}
.expand-arrow.expanded {
  transform: rotate(180deg);
}
.category-services {
  padding: 4px 0;
}
.service-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-top: 1px solid var(--border-color, #2a2a4a);
}
.service-card:first-child {
  border-top: none;
}
.service-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
.service-name {
  font-size: 13px;
  color: var(--text-primary, #e0e0e0);
  font-weight: 500;
}
.service-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.service-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 12px;
}
.priority-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
}
.priority-badge.urgent { background: var(--primary-light); color: var(--text-primary); }
.priority-badge.important { background: var(--bg-tertiary); color: var(--text-secondary); }
.priority-badge.suggested { background: var(--bg-tertiary); color: var(--text-secondary); }
.priority-badge.chitchat { background: var(--bg-tertiary); color: var(--text-tertiary); }
.config-block {
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
  background: var(--bg-secondary);
}
.config-block .global-form-group {
  margin-bottom: 0;
}
.field-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.field-row:last-child {
  margin-bottom: 0;
}
.flex-1 {
  flex: 1;
}
.channel-section {
  margin-bottom: 12px;
}
.channel-sub-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.channel-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.channel-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 8px;
  background: var(--bg-primary, #1a1a2e);
  margin-bottom: 6px;
}
.channel-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.channel-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text-secondary, #888);
}
.channel-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.channel-name {
  font-size: 13px;
  color: var(--text-primary, #e0e0e0);
  font-weight: 500;
}
.channel-status {
  font-size: 12px;
  color: var(--text-secondary, #666);
}
.channel-status.connected { color: var(--text-secondary); }
.channel-actions {
  display: flex;
  gap: 6px;
}
.ch-btn {
  padding: 4px 12px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 4px;
  background: var(--bg-secondary, #2a2a4a);
  color: var(--text-primary, #e0e0e0);
  font-size: 12px;
  cursor: pointer;
}
.ch-btn.toggle { color: var(--text-secondary); }
.routing-block {
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 16px;
  background: var(--bg-secondary);
}
.route-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}
.route-row:not(:last-child) {
  border-bottom: 1px solid var(--border-color, #2a2a4a);
  padding-bottom: 8px;
  margin-bottom: 4px;
}
.route-level {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  min-width: 48px;
  text-align: center;
  white-space: nowrap;
}
.route-level.critical { background: var(--primary-light); color: var(--text-primary); }
.route-level.urgent { background: var(--bg-tertiary); color: var(--text-secondary); }
.route-level.important { background: var(--bg-tertiary); color: var(--text-secondary); }
.route-level.normal { background: var(--bg-tertiary); color: var(--text-secondary); }
.route-level.suggested { background: var(--bg-tertiary); color: var(--text-tertiary); }
.route-level.chitchat { background: var(--bg-tertiary); color: var(--text-tertiary); }
.route-channels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.route-channel-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--bg-primary);
  color: var(--text-secondary);
}
.automation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.automation-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 8px;
  background: var(--bg-primary);
}
.automation-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
.automation-name {
  font-size: 13px;
  color: var(--text-primary, #e0e0e0);
  font-weight: 500;
}
.automation-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}
.privacy-block {
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 10px;
  padding: 4px 0;
  margin-bottom: 16px;
  background: var(--bg-secondary);
}
.privacy-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
}
.privacy-row:not(:last-child) {
  border-bottom: 1px solid var(--border-color, #2a2a4a);
}
.privacy-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.privacy-label {
  font-size: 13px;
  color: var(--text-primary, #e0e0e0);
  font-weight: 500;
}
.privacy-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}
.privacy-input {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.global-input.small {
  width: 70px;
  text-align: center;
}
.privacy-unit {
  font-size: 12px;
  color: var(--text-tertiary);
}
.delivery-block {
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 10px;
  padding: 4px 0;
  margin-bottom: 16px;
  background: var(--bg-secondary);
}
.delivery-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
}
.delivery-row:not(:last-child) {
  border-bottom: 1px solid var(--border-color, #2a2a4a);
}
.delivery-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.delivery-label {
  font-size: 13px;
  color: var(--text-primary, #e0e0e0);
  font-weight: 500;
}
.delivery-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}
.save-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
.save-btn {
  padding: 6px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.save-btn:hover { opacity: 0.9; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
}
.cancel-btn:hover { background: var(--border-color); }
.save-message {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
}
.save-message.success { background: var(--bg-tertiary); color: var(--text-secondary); }
.save-message.error { background: var(--bg-tertiary); color: var(--text-primary); }
.config-modal {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.config-panel {
  width: 400px;
  padding: 24px;
  background: var(--bg-primary, #1a1a2e);
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 12px;
}
.config-panel h3 {
  margin: 0 0 16px;
  color: var(--text-primary, #e0e0e0);
}
.config-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.config-field label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin-bottom: 4px;
}
.config-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
.config-btn {
  padding: 8px 20px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}
.config-btn.cancel { background: var(--bg-secondary, #2a2a4a); color: var(--text-primary, #e0e0e0); }
.config-btn.save { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }
</style>
