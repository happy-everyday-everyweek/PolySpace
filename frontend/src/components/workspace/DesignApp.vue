<template>
  <div class="design-app">
    <div v-if="loading" class="design-loading">
      <div class="loading-spinner"></div>
      <p>正在启动设计引擎...</p>
    </div>
    <div v-else-if="error" class="design-error">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="startDaemon">重试</button>
    </div>
    <iframe
      v-else
      ref="designFrame"
      :src="designUrl"
      class="design-frame"
      allow="clipboard-read; clipboard-write"
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
      @load="onFrameLoad"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const designUrl = ref('')
const loading = ref(true)
const error = ref('')
const designFrame = ref<HTMLIFrameElement>()

const DESIGN_PORT = 3838
const DESIGN_HOST = '127.0.0.1'
const API_BASE = '/api/v1'

let pollTimer: ReturnType<typeof setInterval> | null = null

async function startDaemon() {
  loading.value = true
  error.value = ''
  try {
    const resp = await axios.post(`${API_BASE}/tools/invoke`, {
      tool_name: 'open_design',
      parameters: { action: 'ensure_running' },
    })
    const result = resp.data?.result || resp.data
    if (result?.status === 'running' || result?.status === 'already_running') {
      designUrl.value = `http://${DESIGN_HOST}:${DESIGN_PORT}`
      loading.value = false
      startHealthPoll()
    } else {
      error.value = result?.error || '启动失败'
      loading.value = false
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '无法连接到后端服务'
    loading.value = false
  }
}

function startHealthPoll() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      await axios.post(`${API_BASE}/tools/invoke`, {
        tool_name: 'open_design',
        parameters: { action: 'health' },
      })
    } catch {
      error.value = '设计引擎连接中断'
      loading.value = false
      designUrl.value = ''
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
  if (designFrame.value) {
    try {
      designFrame.value.contentWindow?.postMessage(
        { type: 'polyspace-context', source: 'polyspace-design-app' },
        '*',
      )
    } catch {}
  }
}

function handleMessage(event: MessageEvent) {
  if (event.data?.type === 'design-export-request') {
    handleDesignExport(event.data)
  } else if (event.data?.type === 'design-ready') {
    if (designFrame.value?.contentDocument) {
      try {
        const doc = designFrame.value.contentDocument
        const style = doc.createElement('style')
        style.id = 'polyspace-theme-override'
        style.textContent = `
          :root {
            --bg: #ffffff !important;
            --bg-app: #ffffff !important;
            --bg-panel: #ffffff !important;
            --bg-subtle: #f8f8f8 !important;
            --bg-muted: #f0f0f0 !important;
            --border: #dddddd !important;
            --text: #1a1a1a !important;
            --text-muted: #555555 !important;
            --accent: #000000 !important;
            --accent-hover: #333333 !important;
          }
          [data-theme="dark"] {
            --bg: #121212 !important;
            --bg-app: #121212 !important;
            --bg-panel: #1e1e1e !important;
            --bg-subtle: #2a2a2a !important;
            --bg-muted: #333333 !important;
            --border: #333333 !important;
            --text: #e0e0e0 !important;
            --text-muted: #aaaaaa !important;
            --accent: #e0e0e0 !important;
            --accent-hover: #ffffff !important;
          }
        `
        const existing = doc.getElementById('polyspace-theme-override')
        if (existing) existing.remove()
        doc.head.appendChild(style)
      } catch {}
    }
  }
}

async function handleDesignExport(data: any) {
  try {
    const resp = await axios.post('/api/v1/ai/workspace/design/export', {
      project_id: data.project_id,
      export_format: data.export_format || 'html',
      target_app: data.target_app,
    })
    designFrame.value?.contentWindow?.postMessage(
      { type: 'design-export-response', request_id: data.request_id, result: resp.data },
      '*',
    )
  } catch (e: any) {
    designFrame.value?.contentWindow?.postMessage(
      { type: 'design-export-response', request_id: data.request_id, error: e?.message || 'Export failed' },
      '*',
    )
  }
}

onMounted(() => {
  window.addEventListener('message', handleMessage)
  startDaemon()
})

onUnmounted(() => {
  window.removeEventListener('message', handleMessage)
  stopHealthPoll()
})
</script>

<style scoped>
.design-app {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.design-frame {
  width: 100%;
  height: 100%;
  border: none;
  flex: 1;
}

.design-loading,
.design-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-tertiary);
}

.design-loading p,
.design-error p {
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
