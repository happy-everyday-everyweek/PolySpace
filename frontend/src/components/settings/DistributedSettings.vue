<template>
  <div class="settings-section">
    <h2 class="global-section-title">分布式同步</h2>

    <div class="global-form-group lab-row">
      <label>启用分布式同步</label>
      <label class="global-switch">
        <input type="checkbox" v-model="enabled" />
        <span class="slider"></span>
      </label>
    </div>

    <template v-if="enabled">
      <div class="global-form-group lab-row">
        <label>自动同步</label>
        <label class="global-switch">
          <input type="checkbox" v-model="autoSync" />
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="autoSync" class="global-form-group">
        <label>自动同步间隔 (秒)</label>
        <input
          type="number"
          v-model.number="autoSyncIntervalSec"
          class="global-input"
          min="30"
          max="3600"
        />
      </div>

      <div class="global-form-group lab-row">
        <label>启动时同步</label>
        <label class="global-switch">
          <input type="checkbox" v-model="syncOnStartup" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="global-form-group lab-row">
        <label>设备切换时同步</label>
        <label class="global-switch">
          <input type="checkbox" v-model="syncOnHandoff" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="global-form-group lab-row">
        <label>本地优先</label>
        <label class="global-switch">
          <input type="checkbox" v-model="localFirst" />
          <span class="slider"></span>
        </label>
        <span class="setting-hint">敏感数据优先在本地处理</span>
      </div>

      <div class="global-form-group lab-row">
        <label>传输加密</label>
        <label class="global-switch">
          <input type="checkbox" v-model="encryptTransit" />
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="encryptTransit" class="global-form-group">
        <label>加密密钥</label>
        <input
          type="password"
          v-model="encryptionKey"
          class="global-input"
          placeholder="输入加密密钥，用于同步数据加密"
        />
        <span class="setting-hint">用于 GitHub 同步时的数据加密，请妥善保管</span>
      </div>

      <div class="global-form-group">
        <label>冲突解决策略</label>
        <select v-model="conflictStrategy" class="global-input">
          <option value="latest">最新优先</option>
          <option value="local">本地优先</option>
          <option value="remote">远程优先</option>
          <option value="merge">合并</option>
        </select>
      </div>

      <div class="global-form-group">
        <label>同步范围</label>
        <div class="scope-checkboxes">
          <label v-for="scope in allScopes" :key="scope" class="scope-checkbox">
            <input type="checkbox" :value="scope" v-model="syncScopes" />
            <span>{{ scopeLabels[scope] || scope }}</span>
          </label>
        </div>
      </div>

      <h3 class="subsection-title">GitHub 同步</h3>
      <p class="subsection-desc">通过 GitHub 仓库实现端云同步，将数据加密后推送至远端仓库，实现多设备间的数据同步与备份</p>
      <div class="global-form-group">
        <label>GitHub Token</label>
        <input
          type="password"
          v-model="githubToken"
          class="global-input"
          placeholder="输入 GitHub Personal Access Token"
        />
        <span class="setting-hint">用于加密同步到 GitHub 仓库</span>
      </div>
      <div class="global-form-group">
        <label>GitHub 仓库</label>
        <input
          type="text"
          v-model="githubRepo"
          class="global-input"
          placeholder="如: username/polyspace-sync"
        />
        <span class="setting-hint">同步目标仓库，格式: owner/repo</span>
      </div>

      <h3 class="subsection-title">设备信息</h3>
      <div class="global-form-group">
        <label>设备名称</label>
        <input
          type="text"
          v-model="deviceName"
          class="global-input"
          placeholder="如: 我的笔记本"
        />
        <span class="setting-hint">在多设备列表中显示的名称</span>
      </div>
      <div class="global-form-group">
        <label>设备 ID</label>
        <input type="text" v-model="deviceId" class="global-input" disabled />
      </div>

      <div class="save-bar">
        <button class="save-btn" :class="{ saved: saved, 'save-error': messageType === 'error' && message }" @click="saveAll" :disabled="saving">
          <svg v-if="saved" class="check-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-if="saving">保存中...</span>
          <span v-else-if="saved">已保存</span>
          <span v-else>保存设置</span>
        </button>
        <button class="cancel-btn" @click="resetAll">重置</button>
        <button class="sync-btn" @click="triggerSync" :disabled="syncing">
          {{ syncing ? '同步中...' : '立即同步' }}
        </button>
        <span v-if="message && messageType === 'error'" class="save-error-text">{{ message }}</span>
      </div>
    </template>

    <div v-if="syncStatus" class="sync-status-panel">
      <h4 class="status-title">同步状态</h4>
      <div class="status-row">
        <span>注册设备数</span>
        <span>{{ syncStatus.registered_devices }}</span>
      </div>
      <div class="status-row">
        <span>本地变更</span>
        <span>{{ syncStatus.local_changes }}</span>
      </div>
      <div class="status-row">
        <span>待拉取变更</span>
        <span>{{ syncStatus.remote_pending }}</span>
      </div>
      <div class="status-row">
        <span>上次同步</span>
        <span>{{ syncStatus.last_sync || '从未同步' }}</span>
      </div>
    </div>

    <div v-if="devices.length > 0" class="devices-panel">
      <h4 class="status-title">已注册设备</h4>
      <div v-for="dev in devices" :key="dev.id" class="device-row">
        <div class="device-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          <span class="device-name">{{ dev.name || dev.id?.slice(0, 8) || '未知设备' }}</span>
          <span v-if="dev.id === deviceId" class="device-badge current">当前</span>
        </div>
        <span class="device-last-sync">{{ dev.last_sync || '未同步' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettings } from '@/composables/useSettings'
import { useCloudSync } from '@/composables/useCloudSync'
import { SYNC_SCOPES } from '@/types/settings'
import type { SyncScope, ConflictStrategy } from '@/types/settings'
import api from '@/utils/api'

const { settings, updateDistributed } = useSettings()
const { fetchStatus, initSync, startAutoSync, stopAutoSync, sync } = useCloudSync()

const enabled = ref(settings.value.distributed.enabled)
const autoSync = ref(settings.value.distributed.autoSync)
const autoSyncIntervalSec = ref(settings.value.distributed.autoSyncIntervalSec)
const syncOnStartup = ref(settings.value.distributed.syncOnStartup)
const syncOnHandoff = ref(settings.value.distributed.syncOnHandoff)
const conflictStrategy = ref<ConflictStrategy>(settings.value.distributed.conflictStrategy)
const githubToken = ref(settings.value.distributed.githubToken)
const githubRepo = ref('')
const encryptionKey = ref('')
const deviceName = ref('')
const deviceId = ref(settings.value.distributed.deviceId || crypto.randomUUID())
const syncScopes = ref<SyncScope[]>([...settings.value.distributed.syncScopes])
const localFirst = ref(settings.value.distributed.localFirst)
const encryptTransit = ref(settings.value.distributed.encryptTransit)

const saving = ref(false)
const syncing = ref(false)
const saved = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const allScopes: SyncScope[] = [...SYNC_SCOPES]

const scopeLabels: Record<string, string> = {
  settings: '设置',
  persona: '人格',
  mode: '模式',
  workspace: '工作区',
  memory: '记忆',
}

const syncStatus = ref<any>(null)
const devices = ref<any[]>([])

async function saveAll() {
  saving.value = true
  message.value = ''
  saved.value = false
  try {
    await updateDistributed({
      enabled: enabled.value,
      autoSync: autoSync.value,
      autoSyncIntervalSec: autoSyncIntervalSec.value,
      syncOnStartup: syncOnStartup.value,
      syncOnHandoff: syncOnHandoff.value,
      conflictStrategy: conflictStrategy.value,
      githubToken: githubToken.value,
      deviceId: deviceId.value,
      syncScopes: syncScopes.value,
      localFirst: localFirst.value,
      encryptTransit: encryptTransit.value,
    })

    if (enabled.value && autoSync.value) {
      startAutoSync(autoSyncIntervalSec.value)
    } else {
      stopAutoSync()
    }

    saved.value = true
    messageType.value = 'success'
    setTimeout(() => { saved.value = false }, 1500)
  } catch (e: any) {
    message.value = e.message || '保存失败'
    messageType.value = 'error'
    setTimeout(() => { message.value = '' }, 3000)
  } finally {
    saving.value = false
  }
}

function resetAll() {
  enabled.value = settings.value.distributed.enabled
  autoSync.value = settings.value.distributed.autoSync
  autoSyncIntervalSec.value = settings.value.distributed.autoSyncIntervalSec
  syncOnStartup.value = settings.value.distributed.syncOnStartup
  syncOnHandoff.value = settings.value.distributed.syncOnHandoff
  conflictStrategy.value = settings.value.distributed.conflictStrategy
  githubToken.value = settings.value.distributed.githubToken
  syncScopes.value = [...settings.value.distributed.syncScopes]
  localFirst.value = settings.value.distributed.localFirst
  encryptTransit.value = settings.value.distributed.encryptTransit
}

async function triggerSync() {
  syncing.value = true
  message.value = ''
  try {
    await sync(syncScopes.value)
    message.value = '同步完成'
    messageType.value = 'success'
    syncStatus.value = await fetchStatus()
  } catch (e: any) {
    message.value = e.message || '同步失败'
    messageType.value = 'error'
  } finally {
    syncing.value = false
    setTimeout(() => { message.value = '' }, 3000)
  }
}

async function loadDevices() {
  try {
    const res = await api.get('/sync/devices')
    devices.value = res.data?.devices || res.data || []
  } catch {
    devices.value = []
  }
}

onMounted(async () => {
  syncStatus.value = await fetchStatus()
  if (enabled.value) {
    initSync()
  }
  loadDevices()
})
</script>

<style scoped>
.settings-section {
  max-width: 600px;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.subsection-desc {
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin: -8px 0 12px;
  line-height: 1.5;
}

.setting-hint {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin-top: 2px;
}

.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lab-row label:first-child {
  font-size: 14px;
  color: var(--text-color);
}

.global-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
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

.global-switch input:checked + .slider {
  background: var(--primary-color);
}

.global-switch input:checked + .slider::before {
  transform: translateX(18px);
}

.scope-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}

.scope-checkbox {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  cursor: pointer;
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
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.save-btn:hover {
  opacity: 0.9;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn.saved {
  background: var(--text-secondary);
  animation: save-pop 0.35s ease;
}

.save-btn.save-error {
  background: var(--text-primary);
  animation: save-shake 0.4s ease;
}

.check-icon {
  width: 14px;
  height: 14px;
}

@keyframes save-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.08); }
  100% { transform: scale(1); }
}

@keyframes save-shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-3px); }
  40% { transform: translateX(3px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
}

.cancel-btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
}

.cancel-btn:hover {
  background: var(--border-color);
}

.sync-btn {
  padding: 6px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: none;
  border: 1px solid var(--primary-color);
  color: var(--primary-color);
  cursor: pointer;
  transition: opacity 0.2s;
  margin-left: auto;
}

.sync-btn:hover {
  background: var(--primary-color);
  color: white;
}

.sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-error-text {
  font-size: 12px;
  color: var(--text-primary);
  margin-left: 4px;
}

.sync-status-panel,
.devices-panel {
  margin-top: 16px;
  padding: 12px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  background: var(--bg-secondary, #f5f5f5);
}

.status-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 8px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.device-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color);
}

.device-row:last-child {
  border-bottom: none;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.device-name {
  font-size: 13px;
  color: var(--text-primary);
}

.device-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.device-badge.current {
  background: var(--primary-light);
  color: var(--text-primary);
}

.device-last-sync {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
