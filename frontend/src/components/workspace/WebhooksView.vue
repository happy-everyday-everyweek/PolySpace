<template>
  <div class="webhooks-view">
    <div class="wh-header">
      <h2>API Key 与 Webhook</h2>
      <p class="wh-desc">管理 API 访问密钥和事件推送</p>
    </div>
    <div class="wh-section">
      <h3>API 密钥</h3>
      <div class="wh-create-row">
        <input v-model="newKeyName" class="wh-input" placeholder="密钥名称" />
        <select v-model="newKeyPerm" class="wh-select">
          <option value="read">只读</option>
          <option value="write">读写</option>
          <option value="admin">管理员</option>
        </select>
        <button class="wh-btn primary" @click="createApiKey">创建密钥</button>
      </div>
      <div class="wh-list">
        <div v-for="key in apiKeys" :key="key.id" class="wh-item">
          <div class="wh-item-info">
            <span class="wh-item-name">{{ key.name }}</span>
            <span class="wh-item-key">{{ key.key_prefix }}••••••••</span>
            <span class="wh-item-perm">{{ key.permissions.join(', ') }}</span>
            <span class="wh-item-status" :class="'status-' + key.status">{{ key.status }}</span>
          </div>
          <div class="wh-item-actions">
            <button v-if="key.status === 'active'" class="wh-btn small danger" @click="revokeKey(key.id)">撤销</button>
            <button class="wh-btn small" @click="deleteKey(key.id)">删除</button>
          </div>
        </div>
        <div v-if="!apiKeys.length" class="wh-empty">尚未创建 API 密钥</div>
      </div>
    </div>
    <div class="wh-section">
      <h3>Webhook</h3>
      <div class="wh-create-row">
        <input v-model="newWhName" class="wh-input" placeholder="Webhook 名称" />
        <input v-model="newWhUrl" class="wh-input wide" placeholder="回调 URL" />
        <button class="wh-btn primary" @click="createWebhook">创建</button>
      </div>
      <div class="wh-events-config" v-if="showEventsConfig">
        <label v-for="evt in webhookEvents" :key="evt.value" class="wh-event-label">
          <input type="checkbox" v-model="newWhEvents" :value="evt.value" />
          <span>{{ evt.label }}</span>
        </label>
      </div>
      <div class="wh-list">
        <div v-for="wh in webhooks" :key="wh.id" class="wh-item">
          <div class="wh-item-info">
            <span class="wh-item-name">{{ wh.name }}</span>
            <span class="wh-item-url">{{ wh.url }}</span>
            <span class="wh-item-events">{{ wh.events.join(', ') }}</span>
            <span class="wh-item-status" :class="'status-' + wh.status">{{ wh.status }}</span>
            <span class="wh-item-count">{{ wh.trigger_count }} 次触发</span>
          </div>
          <div class="wh-item-actions">
            <button v-if="wh.status === 'active'" class="wh-btn small" @click="pauseWebhook(wh.id)">暂停</button>
            <button v-if="wh.status === 'paused'" class="wh-btn small" @click="resumeWebhook(wh.id)">恢复</button>
            <button class="wh-btn small" @click="testWebhook(wh.id)">测试</button>
            <button class="wh-btn small danger" @click="deleteWebhook(wh.id)">删除</button>
          </div>
        </div>
        <div v-if="!webhooks.length" class="wh-empty">尚未创建 Webhook</div>
      </div>
    </div>
    <div v-if="toastMsg" class="toast">{{ toastMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const toastMsg = ref('')
const toastTimer = ref<ReturnType<typeof setTimeout> | null>(null)
function showToast(msg: string) {
  toastMsg.value = msg
  if (toastTimer.value) clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => { toastMsg.value = '' }, 4000)
}

const apiKeys = ref<any[]>([])
const webhooks = ref<any[]>([])
const newKeyName = ref('')
const newKeyPerm = ref('read')
const newWhName = ref('')
const newWhUrl = ref('')
const newWhEvents = ref<string[]>([])
const showEventsConfig = ref(true)

const webhookEvents = [
  { value: 'chat.message', label: '聊天消息' },
  { value: 'chat.session', label: '会话事件' },
  { value: 'tool.call', label: '工具调用' },
  { value: 'agent.task', label: 'Agent 任务' },
  { value: 'artifact.created', label: '产出物创建' },
  { value: 'research.completed', label: '研究完成' },
  { value: 'proactive.service', label: '主动服务' },
  { value: 'device.status', label: '设备状态' },
]

async function fetchApiKeys() {
  try {
    const { data } = await api.get('/webhooks/api-keys')
    apiKeys.value = data.keys || []
  } catch { /* ignore */ }
}

async function fetchWebhooks() {
  try {
    const { data } = await api.get('/webhooks/webhooks')
    webhooks.value = data.webhooks || []
  } catch { /* ignore */ }
}

async function createApiKey() {
  if (!newKeyName.value.trim()) return
  try {
    const { data } = await api.post('/webhooks/api-keys', {
      name: newKeyName.value,
      permissions: [newKeyPerm.value],
    })
    if (data.key) {
      showToast(`API Key created: ${data.key}. Save it - it won't be shown again.`)
    }
    newKeyName.value = ''
    await fetchApiKeys()
  } catch { /* ignore */ }
}

async function revokeKey(id: string) {
  try {
    await api.post(`/webhooks/api-keys/${id}/revoke`)
    await fetchApiKeys()
  } catch { /* ignore */ }
}

async function deleteKey(id: string) {
  try {
    await api.delete(`/webhooks/api-keys/${id}`)
    await fetchApiKeys()
  } catch { /* ignore */ }
}

async function createWebhook() {
  if (!newWhName.value.trim() || !newWhUrl.value.trim()) return
  try {
    await api.post('/webhooks/webhooks', {
      name: newWhName.value,
      url: newWhUrl.value,
      events: newWhEvents.value.length ? newWhEvents.value : ['chat.message'],
    })
    newWhName.value = ''
    newWhUrl.value = ''
    newWhEvents.value = []
    await fetchWebhooks()
  } catch { /* ignore */ }
}

async function pauseWebhook(id: string) {
  try {
    await api.patch(`/webhooks/webhooks/${id}`, { status: 'paused' })
    await fetchWebhooks()
  } catch { /* ignore */ }
}

async function resumeWebhook(id: string) {
  try {
    await api.patch(`/webhooks/webhooks/${id}`, { status: 'active' })
    await fetchWebhooks()
  } catch { /* ignore */ }
}

async function testWebhook(_id: string) {
  try {
    await api.post('/webhooks/webhooks/trigger', { event: 'chat.message', payload: { test: true } })
    showToast('Test event sent')
  } catch { /* ignore */ }
}

async function deleteWebhook(id: string) {
  try {
    await api.delete(`/webhooks/webhooks/${id}`)
    await fetchWebhooks()
  } catch { /* ignore */ }
}

onMounted(() => {
  fetchApiKeys()
  fetchWebhooks()
})
</script>

<style scoped>
.webhooks-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
.wh-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 4px;
}
.wh-desc {
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 13px;
  margin: 0 0 20px;
}
.wh-section {
  margin-bottom: 24px;
}
.wh-section h3 {
  font-size: 16px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 12px;
}
.wh-create-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.wh-input {
  padding: 6px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  outline: none;
}
.wh-input.wide { flex: 1; }
.wh-select {
  padding: 6px 10px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
}
.wh-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  cursor: pointer;
}
.wh-btn.primary {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.wh-btn.small { padding: 3px 10px; font-size: 12px; }
.wh-btn.danger { color: #f87171; }
.wh-events-config {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
}
.wh-event-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary, #ccc);
  cursor: pointer;
}
.wh-event-label input { accent-color: var(--accent-color, #6366f1); }
.wh-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.wh-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-primary, var(--bg-secondary));
}
.wh-item-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.wh-item-name {
  font-size: 13px;
  color: var(--text-primary, var(--text-primary));
  font-weight: 500;
}
.wh-item-key, .wh-item-url, .wh-item-events, .wh-item-count {
  font-size: 12px;
  color: var(--text-secondary, var(--text-tertiary));
}
.wh-item-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}
.wh-item-perm {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--bg-tertiary, #1e1e3a);
  color: var(--text-secondary, var(--text-tertiary));
}
.wh-item-status {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
}
.status-active { background: #166534; color: #4ade80; }
.status-revoked, .status-failed { background: #7f1d1d; color: #f87171; }
.status-paused { background: #713f12; color: #fbbf24; }
.wh-item-actions {
  display: flex;
  gap: 4px;
}
.wh-empty {
  text-align: center;
  color: var(--text-secondary, var(--text-tertiary));
  padding: 16px;
  font-size: 13px;
}
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: var(--card-bg); color: var(--text-primary); padding: 10px 20px; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); font-size: 13px; z-index: 300; border: 1px solid var(--border-color); max-width: 500px; word-break: break-all; }
</style>
