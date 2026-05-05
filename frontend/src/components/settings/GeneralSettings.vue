<template>
  <div class="settings-section">
    <h2 class="global-section-title">通用设置</h2>
    <div class="global-form-group">
      <label>语言</label>
      <select v-model="language" class="global-input">
        <option value="zh-CN">简体中文</option>
        <option value="en">English</option>
      </select>
    </div>
    <div class="global-form-group">
      <label>主题</label>
      <select v-model="theme" class="global-input">
        <option value="auto">跟随系统</option>
        <option value="light">浅色</option>
        <option value="dark">深色</option>
      </select>
    </div>

    <div class="global-form-group">
      <label>调试模式</label>
      <label class="global-switch">
        <input type="checkbox" v-model="debugMode" />
        <span class="slider"></span>
      </label>
      <span class="setting-hint">启用调试日志和开发模式</span>
    </div>

    <h3 class="subsection-title">数据存储</h3>
    <div class="global-form-group">
      <label>数据目录</label>
      <input type="text" v-model="envValues.DATA_DIR" class="global-input" placeholder="如: D:/PolySpace/data" />
      <span class="setting-hint">应用数据存储目录，修改后需重启</span>
    </div>
    <div class="global-form-group">
      <label>策略文件路径</label>
      <input type="text" v-model="envValues.POLICIES_PATH" class="global-input" placeholder="如: ./policies/POLICIES.yaml" />
      <span class="setting-hint">安全策略YAML文件路径</span>
    </div>

    <h3 class="subsection-title">数据库</h3>
    <div class="global-form-group">
      <label>数据库连接</label>
      <input type="text" v-model="envValues.DATABASE_URL" class="global-input" placeholder="留空使用默认SQLite" />
      <span class="setting-hint">数据库连接字符串，留空使用默认SQLite</span>
    </div>
    <div class="field-row">
      <div class="global-form-group flex-1">
        <label>连接池大小</label>
        <input type="number" v-model.number="envValues.DATABASE_POOL_SIZE" class="global-input" min="1" max="100" />
      </div>
      <div class="global-form-group flex-1">
        <label>最大溢出连接</label>
        <input type="number" v-model.number="envValues.DATABASE_MAX_OVERFLOW" class="global-input" min="0" max="100" />
      </div>
    </div>
    <div class="global-form-group">
      <label>连接回收时间 (秒)</label>
      <input type="number" v-model.number="envValues.DATABASE_POOL_RECYCLE" class="global-input" min="60" max="86400" />
    </div>

    <h3 class="subsection-title">网络配置</h3>
    <div class="field-row">
      <div class="global-form-group flex-1">
        <label>最大WS连接数</label>
        <input type="number" v-model.number="envValues.WS_MAX_CONNECTIONS" class="global-input" min="1" max="1000" />
      </div>
      <div class="global-form-group flex-1">
        <label>最大消息大小 (字节)</label>
        <input type="number" v-model.number="envValues.WS_MAX_MESSAGE_SIZE" class="global-input" min="1024" />
      </div>
    </div>
    <div class="field-row">
      <div class="global-form-group flex-1">
        <label>心跳间隔 (秒)</label>
        <input type="number" v-model.number="envValues.WS_HEARTBEAT_INTERVAL" class="global-input" min="1" max="300" step="0.5" />
      </div>
      <div class="global-form-group flex-1">
        <label>心跳超时 (秒)</label>
        <input type="number" v-model.number="envValues.WS_HEARTBEAT_TIMEOUT" class="global-input" min="1" max="600" step="0.5" />
      </div>
    </div>
    <div class="global-form-group">
      <label>CORS 允许源</label>
      <input type="text" v-model="envValues.CORS_ORIGINS" class="global-input" placeholder="逗号分隔，如: http://localhost:5173, http://localhost:3000" />
      <span class="setting-hint">允许的跨域源列表，逗号分隔</span>
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
      <span v-if="message && messageType === 'error'" class="save-error-text">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useSettings } from '@/composables/useSettings'
import api from '@/utils/api'

const { settings, updateGeneral } = useSettings()

const language = ref(settings.value.general.language)
const theme = ref(settings.value.general.theme)
const debugMode = ref(false)
const saving = ref(false)
const saved = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const envValues = reactive<Record<string, any>>({
  DATA_DIR: '',
  POLICIES_PATH: '',
  DATABASE_URL: '',
  DATABASE_POOL_SIZE: 5,
  DATABASE_MAX_OVERFLOW: 10,
  DATABASE_POOL_RECYCLE: 3600,
  WS_MAX_CONNECTIONS: 100,
  WS_MAX_MESSAGE_SIZE: 1048576,
  WS_HEARTBEAT_INTERVAL: 30,
  WS_HEARTBEAT_TIMEOUT: 60,
  CORS_ORIGINS: '',
})

async function loadEnvValues() {
  try {
    const res = await api.get('/settings/env')
    const data = res.data
    const vars = data.variables || {}
    for (const groupVars of Object.values(vars) as any[][]) {
      for (const env of groupVars) {
        if (env.key in envValues) {
          if (env.type === 'bool') {
            (envValues as any)[env.key] = env.value === true || env.value === 'true'
          } else if (env.type === 'list') {
            (envValues as any)[env.key] = Array.isArray(env.value) ? env.value.join(', ') : (env.value || '')
          } else {
            (envValues as any)[env.key] = env.value ?? ''
          }
        }
      }
    }
    if ('DEBUG' in envValues) {
      debugMode.value = envValues.DEBUG === true || envValues.DEBUG === 'true'
    }
  } catch {
    // use defaults
  }
}

async function saveAll() {
  saving.value = true
  message.value = ''
  saved.value = false
  try {
    await updateGeneral({ language: language.value, theme: theme.value })
    const updates: Record<string, any> = {}
    updates['DEBUG'] = debugMode.value
    for (const [key, value] of Object.entries(envValues)) {
      if (key === 'DEBUG') continue
      if (value === '' || value === undefined || value === null) {
        updates[key] = null
      } else {
        updates[key] = value
      }
    }
    await api.put('/settings/env', { updates })
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
  language.value = settings.value.general.language
  theme.value = settings.value.general.theme
  loadEnvValues()
}

onMounted(loadEnvValues)
</script>

<style scoped>
.settings-section {
  max-width: 640px;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.setting-hint {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin-top: 2px;
}

.field-row {
  display: flex;
  gap: 8px;
}

.flex-1 {
  flex: 1;
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

.save-error-text {
  font-size: 12px;
  color: var(--ws-danger);
  margin-left: 4px;
}
</style>
