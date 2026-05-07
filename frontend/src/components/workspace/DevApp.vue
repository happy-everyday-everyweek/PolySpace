<template>
  <div class="dev-app">
    <div v-if="loading" class="dev-loading">
      <div class="loading-spinner"></div>
      <p>正在启动开发平台...</p>
    </div>
    <div v-else-if="error" class="dev-error">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="startNocoBase">重试</button>
    </div>
    <iframe
      v-else
      ref="devFrame"
      :src="devUrl"
      class="dev-frame"
      allow="clipboard-read; clipboard-write"
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
      @load="onFrameLoad"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const devUrl = ref('')
const loading = ref(true)
const error = ref('')
const devFrame = ref<HTMLIFrameElement>()

const NOCOBASE_DEFAULT_PORT = 13000
const NOCOBASE_DEFAULT_HOST = '127.0.0.1'
const API_BASE = '/api/v1'

let pollTimer: ReturnType<typeof setInterval> | null = null

async function startNocoBase() {
  loading.value = true
  error.value = ''
  try {
    const resp = await axios.post(`${API_BASE}/tools/invoke`, {
      tool_name: 'nocobase',
      parameters: { action: 'ensure_running' },
    })
    const result = resp.data?.result || resp.data
    if (result?.status === 'running' || result?.status === 'already_running') {
      devUrl.value = result.base_url || `http://${NOCOBASE_DEFAULT_HOST}:${NOCOBASE_DEFAULT_PORT}`
      loading.value = false
      startHealthPoll()
    } else {
      devUrl.value = `http://${NOCOBASE_DEFAULT_HOST}:${NOCOBASE_DEFAULT_PORT}`
      loading.value = false
      startHealthPoll()
    }
  } catch (e: any) {
    devUrl.value = `http://${NOCOBASE_DEFAULT_HOST}:${NOCOBASE_DEFAULT_PORT}`
    loading.value = false
    startHealthPoll()
  }
}

function startHealthPoll() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      await axios.post(`${API_BASE}/tools/invoke`, {
        tool_name: 'nocobase',
        parameters: { action: 'app_info' },
      })
    } catch {
      error.value = '开发平台连接中断'
      loading.value = false
      devUrl.value = ''
      stopHealthPoll()
    }
  }, 30000)
}

function stopHealthPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function onFrameLoad() {
  if (devFrame.value) {
    try {
      devFrame.value.contentWindow?.postMessage(
        { type: 'polyspace-context', source: 'polyspace-dev-app' },
        '*',
      )
      injectPolySpaceStyle()
    } catch {}
  }
}

function injectPolySpaceStyle() {
  if (!devFrame.value?.contentDocument) return
  try {
    const doc = devFrame.value.contentDocument
    const style = doc.createElement('style')
    style.id = 'polyspace-theme-override'
    style.textContent = `
      :root {
        --color-bg: #ffffff !important;
        --color-bg-secondary: #f8f8f8 !important;
        --color-bg-tertiary: #f0f0f0 !important;
        --color-border: #dddddd !important;
        --color-text: #1a1a1a !important;
        --color-text-secondary: #555555 !important;
        --color-primary: #000000 !important;
        --color-primary-hover: #333333 !important;
        --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        --border-radius: 8px !important;
      }
      [data-theme="dark"], .dark {
        --color-bg: #121212 !important;
        --color-bg-secondary: #1e1e1e !important;
        --color-bg-tertiary: #2a2a2a !important;
        --color-border: #333333 !important;
        --color-text: #e0e0e0 !important;
        --color-text-secondary: #aaaaaa !important;
        --color-primary: #e0e0e0 !important;
        --color-primary-hover: #ffffff !important;
      }
      body {
        font-family: var(--font-family) !important;
        font-size: 14px !important;
      }
      .ant-btn-primary {
        background: #000000 !important;
        border-color: #000000 !important;
      }
      .ant-btn-primary:hover {
        background: #333333 !important;
        border-color: #333333 !important;
      }
    `
    const existing = doc.getElementById('polyspace-theme-override')
    if (existing) existing.remove()
    doc.head.appendChild(style)
  } catch {}
}

onMounted(() => {
  startNocoBase()
})

onUnmounted(() => {
  stopHealthPoll()
})
</script>

<style scoped>
.dev-app {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.dev-frame {
  width: 100%;
  height: 100%;
  border: none;
  flex: 1;
}

.dev-loading,
.dev-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-tertiary);
}

.dev-loading p,
.dev-error p {
  font-size: 14px;
  margin: 0;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  padding: 6px 16px;
  border-radius: 6px;
  background: var(--primary-color);
  color: #fff;
  border: none;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.retry-btn:hover {
  opacity: 0.9;
}

.retry-btn:active {
  transform: scale(0.97);
}
</style>
