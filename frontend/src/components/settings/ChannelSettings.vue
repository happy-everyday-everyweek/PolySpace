<template>
  <div class="channel-settings">
    <h3>消息渠道</h3>
    <p class="channel-desc">配置 AI 助手主动触达你的消息渠道，包括 IM、邮件、语音、日历</p>

    <div class="channel-section">
      <h4>IM 渠道</h4>
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
      <h4>邮件渠道</h4>
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
        <div class="channel-actions">
          <button class="ch-btn" @click="$emit('openApp', 'email')">管理</button>
        </div>
      </div>
    </div>

    <div class="channel-section">
      <h4>语音渠道</h4>
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
    </div>

    <div class="channel-section">
      <h4>日历渠道</h4>
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
          <button class="config-btn save" :class="{ saved: saved }" @click="saveConfig" :disabled="saving">
            <svg v-if="saved" class="check-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span v-if="saving">保存中...</span>
            <span v-else-if="saved">已保存</span>
            <span v-else>保存并启用</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import ChannelSvgIcon from './ChannelSvgIcon.vue'

defineEmits<{ (e: 'openApp', app: string): void }>()

interface ChannelStatus {
  channel_type: string
  enabled: boolean
  connected: boolean
  daily_count: number
}

const imChannels = ref<ChannelStatus[]>([])
const showConfig = ref(false)
const configType = ref('')
const configData = ref<Record<string, string>>({})
const saving = ref(false)
const saved = ref(false)

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

async function fetchChannels() {
  try {
    const { data } = await api.get('/im/channels')
    imChannels.value = data.channels || []
  } catch { /* ignore */ }
}

function configureChannel(type: string) {
  configType.value = type
  configData.value = {}
  showConfig.value = true
}

async function saveConfig() {
  saving.value = true
  saved.value = false
  try {
    await api.post('/im/channels/configure', {
      channel_type: configType.value,
      config: configData.value,
      enabled: true,
    })
    saved.value = true
    await fetchChannels()
    setTimeout(() => {
      showConfig.value = false
      saved.value = false
    }, 800)
  } catch {
    saving.value = false
  }
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

onMounted(fetchChannels)
</script>

<style scoped>
.channel-settings {
  max-width: 600px;
}
.channel-settings h3 {
  font-size: 18px;
  color: var(--text-primary, #e0e0e0);
  margin: 0 0 4px;
}
.channel-desc {
  color: var(--text-secondary, #888);
  font-size: 13px;
  margin: 0 0 20px;
}
.channel-section {
  margin-bottom: 20px;
}
.channel-section h4 {
  font-size: 14px;
  color: var(--text-primary, #e0e0e0);
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color, #2a2a4a);
}
.channel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.channel-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 8px;
  background: var(--bg-primary, #1a1a2e);
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
.channel-status.connected { color: #4ade80; }
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
.ch-btn.toggle { color: #f87171; }
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
.config-btn.save { background: var(--primary-color); color: #fff; border-color: var(--primary-color); transition: all 0.25s ease; display: inline-flex; align-items: center; gap: 4px; }
.config-btn.save.saved { background: var(--text-secondary); border-color: var(--text-secondary); animation: save-pop 0.35s ease; }
.config-btn.save:disabled { opacity: 0.5; cursor: not-allowed; }
.check-icon { width: 14px; height: 14px; }
@keyframes save-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.08); }
  100% { transform: scale(1); }
}
</style>
