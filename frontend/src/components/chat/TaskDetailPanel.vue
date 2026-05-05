<template>
  <Teleport to="body">
    <Transition name="task-detail-fade">
      <div v-if="visible" class="task-detail-overlay" @click.self="$emit('close')">
        <div class="task-detail-panel">
          <div class="detail-header">
            <div class="header-left">
              <span class="task-icon" :class="statusIconClass">
                <svg v-if="taskData.status === 'running'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="spin"/>
                </svg>
                <svg v-else-if="taskData.status === 'completed'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else-if="taskData.status === 'failed'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                <svg v-else-if="taskData.status === 'pending' || taskData.status === 'planning'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="spin"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10"/>
                </svg>
              </span>
              <h3 class="task-title">{{ taskData.description || '任务详情' }}</h3>
            </div>
            <div class="header-right">
              <span class="status-badge" :class="'status-' + taskData.status">{{ statusText }}</span>
              <button class="close-btn" @click="$emit('close')" title="关闭">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="detail-body">
            <div class="detail-left">
              <section class="info-section" v-if="taskData.goal">
                <h4>目标</h4>
                <p>{{ taskData.goal }}</p>
              </section>

              <section class="info-section" v-if="taskData.progress_message">
                <h4>当前进度</h4>
                <div class="progress-bar-container">
                  <div class="progress-bar-track">
                    <div
                      class="progress-bar-fill"
                      :style="{ width: (taskData.progress * 100) + '%' }"
                    ></div>
                  </div>
                  <span class="progress-text">{{ Math.round(taskData.progress * 100) }}%</span>
                </div>
                <p class="progress-message">{{ taskData.progress_message }}</p>
              </section>

              <section class="info-section" v-if="taskData.steps && taskData.steps.length > 0">
                <h4>执行步骤</h4>
                <ul class="steps-list">
                  <li
                    v-for="(step, idx) in taskData.steps"
                    :key="idx"
                    class="step-item"
                  >
                    <span class="step-icon">
                      <svg v-if="step.action || step.thought" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      </span>
                    <div class="step-content">
                      <span class="step-action">{{ step.action || step.thought || `步骤 ${idx + 1}` }}</span>
                      <span v-if="step.observation" class="step-observation">{{ step.observation }}</span>
                    </div>
                  </li>
                </ul>
              </section>

              <section class="info-section" v-if="taskData.supplements && taskData.supplements.length > 0">
                <h4>补充信息</h4>
                <ul class="supplements-list">
                  <li v-for="(sup, idx) in taskData.supplements" :key="idx" class="supplement-item">
                    <span class="supplement-source">[{{ sup.source }}]</span>
                    {{ sup.info }}
                  </li>
                </ul>
              </section>

              <section class="info-section" v-if="taskData.error">
                <h4>错误信息</h4>
                <p class="error-text">{{ taskData.error }}</p>
              </section>

              <section class="info-section" v-if="taskData.result && typeof taskData.result === 'object'">
                <h4>执行结果</h4>
                <pre class="result-preview">{{ formatResult(taskData.result) }}</pre>
              </section>

              <section class="actions-section">
                <button
                  v-if="canSupplement"
                  class="action-btn supplement-btn"
                  @click="showSupplementInput = !showSupplementInput"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  补充要求
                </button>
                <button
                  v-if="canCancel"
                  class="action-btn cancel-btn"
                  @click="handleCancel"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  </svg>
                  取消任务
                </button>
                <div v-if="showSupplementInput" class="supplement-input-wrap">
                  <textarea
                    v-model="supplementText"
                    placeholder="输入补充要求..."
                    rows="3"
                    @keydown.ctrl.enter="handleSupplement"
                  ></textarea>
                  <button class="submit-supplement-btn" @click="handleSupplement" :disabled="!supplementText.trim()">
                    发送
                  </button>
                </div>
              </section>
            </div>

            <div class="detail-right">
              <div class="preview-area">
                <div class="preview-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/>
                  </svg>
                  <span>执行预览</span>
                </div>
                <div class="preview-content">
                  <div v-if="!hasResultContent" class="preview-empty">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                      <line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/>
                    </svg>
                    <p>等待执行结果...</p>
                  </div>
                  <pre v-else class="result-full">{{ fullResultText }}</pre>
                </div>
              </div>

              <div v-if="taskData.steps && taskData.steps.length > 0" class="steps-timeline">
                <div
                  v-for="(_, idx) in displaySteps"
                  :key="idx"
                  class="timeline-step"
                  :class="{ active: idx <= currentStepIndex }"
                >
                  <div class="timeline-dot"></div>
                  <span class="timeline-label">0{{ idx + 1 }}</span>
                  <span class="timeline-status">{{ getStepStatus(idx) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { API_BASE } from '@/utils/constants'

const props = defineProps<{
  visible: boolean
  taskId: string | null
}>()

defineEmits<{
  close: []
}>()

const taskData = ref<any>({})
const loading = ref(false)
const showSupplementInput = ref(false)
const supplementText = ref('')

const statusText = computed(() => {
  const map: Record<string, string> = {
    pending: '规划中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[taskData.value?.status] || '未知'
})

const statusIconClass = computed(() => {
  const s = taskData.value?.status
  if (s === 'completed') return 'icon-success'
  if (s === 'failed') return 'icon-error'
  if (s === 'running') return 'icon-running'
  return 'icon-pending'
})

const canSupplement = computed(() => {
  const s = taskData.value?.status
  return s === 'pending' || s === 'running'
})

const canCancel = computed(() => {
  const s = taskData.value?.status
  return s === 'pending' || s === 'running'
})

const hasResultContent = computed(() => {
  return taskData.value?.result && (
    typeof taskData.value.result === 'string' ||
    Object.keys(taskData.value.result).length > 0
  )
})

const fullResultText = computed(() => {
  const r = taskData.value?.result
  if (!r) return ''
  if (typeof r === 'string') return r
  return JSON.stringify(r, null, 2)
})

const currentStepIndex = computed(() => {
  const steps = taskData.value?.steps || []
  let idx = -1
  for (let i = 0; i < steps.length; i++) {
    if (steps[i].action || steps[i].observation) {
      idx = i
    }
  }
  return idx
})

const displaySteps = computed(() => {
  const steps = taskData.value?.steps || []
  if (steps.length <= 8) return steps
  return steps.slice(0, 8)
})

function getStepStatus(idx: number): string {
  if (idx < currentStepIndex.value) return 'Completed'
  if (idx === currentStepIndex.value) {
    const step = (taskData.value?.steps || [])[idx]
    if (step?.observation) return 'Completed'
    if (step?.action) return 'Running'
    return 'Pending'
  }
  return 'Pending'
}

function formatResult(result: any): string {
  if (!result) return ''
  try {
    return JSON.stringify(result, null, 2)
  } catch {
    return String(result)
  }
}

async function fetchTaskDetail() {
  if (!props.taskId) return
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/tasks/${props.taskId}`)
    if (res.ok) {
      taskData.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch task detail:', e)
  } finally {
    loading.value = false
  }
}

async function handleSupplement() {
  if (!supplementText.value.trim() || !props.taskId) return
  try {
    const res = await fetch(`${API_BASE}/tasks/${props.taskId}/supplement`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ info: supplementText.value.trim(), source: 'user' }),
    })
    if (res.ok) {
      supplementText.value = ''
      showSupplementInput.value = false
      await fetchTaskDetail()
    }
  } catch (e) {
    console.error('Failed to supplement task:', e)
  }
}

async function handleCancel() {
  if (!props.taskId) return
  try {
    const res = await fetch(`${API_BASE}/tasks/${props.taskId}/cancel`, { method: 'POST' })
    if (res.ok) {
      await fetchTaskDetail()
    }
  } catch (e) {
    console.error('Failed to cancel task:', e)
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null

watch(() => props.visible, async (val) => {
  if (val && props.taskId) {
    await fetchTaskDetail()
    startPolling()
  } else {
    stopPolling()
  }
})

watch(() => props.taskId, async () => {
  if (props.visible && props.taskId) {
    await fetchTaskDetail()
  }
})

onMounted(() => {
  if (props.visible && props.taskId) {
    fetchTaskDetail()
  }
})

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (taskData.value?.status === 'running' || taskData.value?.status === 'pending') {
      await fetchTaskDetail()
    } else {
      stopPolling()
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}
</script>

<style scoped>
.task-detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--overlay-bg);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.task-detail-panel {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  width: 900px;
  max-width: 95vw;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.task-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.icon-success { color: var(--text-secondary); background: var(--bg-tertiary); }
.icon-error { color: var(--text-tertiary); background: var(--bg-tertiary); }
.icon-running { color: var(--text-primary); background: var(--primary-light); }
.icon-pending { color: var(--text-tertiary); background: var(--bg-tertiary); }

.task-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-pending,
.status-planning {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}
.status-running {
  color: var(--text-primary);
  background: var(--primary-light);
}
.status-completed {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}
.status-failed {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}
.status-cancelled {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.detail-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.detail-left {
  width: 340px;
  min-width: 280px;
  border-right: 1px solid var(--border-color);
  padding: 16px 20px;
  overflow-y: auto;
  flex-shrink: 0;
}

.detail-right {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.info-section {
  margin-bottom: 18px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-section h4 {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.info-section p {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-primary);
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.progress-bar-track {
  flex: 1;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--text-primary);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 36px;
  text-align: right;
}

.progress-message {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.steps-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--bg-secondary);
}

.step-item:last-child {
  border-bottom: none;
}

.step-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
  margin-top: 2px;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.step-action {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.step-observation {
  font-size: 12px;
  color: var(--text-tertiary);
}

.supplements-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.supplement-item {
  font-size: 12px;
  padding: 6px 10px;
  background: var(--bg-secondary);
  border-radius: 6px;
  margin-bottom: 4px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.supplement-source {
  font-weight: 600;
  color: var(--text-tertiary);
  margin-right: 4px;
}

.error-text {
  color: var(--text-tertiary);
  font-size: 13px;
}

.result-preview {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-secondary);
}

.actions-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  border-color: var(--text-tertiary);
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.cancel-btn:hover {
  border-color: var(--text-tertiary);
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.supplement-input-wrap {
  width: 100%;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.supplement-input-wrap textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text-primary);
  font-size: 13px;
  resize: vertical;
  outline: none;
  font-family: inherit;
}

.supplement-input-wrap textarea:focus {
  border-color: var(--primary-color);
}

.submit-supplement-btn {
  align-self: flex-end;
  padding: 6px 16px;
  border-radius: 6px;
  border: none;
  background: var(--primary-color);
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}

.submit-supplement-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-supplement-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 250px;
  background: var(--bg-secondary);
  margin: 12px;
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.preview-content {
  flex: 1;
  padding: 12px 14px;
  overflow-y: auto;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: var(--text-tertiary);
  gap: 10px;
}

.preview-empty p {
  font-size: 13px;
  margin: 0;
}

.result-full {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.steps-timeline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  gap: 4px;
  overflow-x: auto;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 48px;
  opacity: 0.35;
  transition: opacity 0.2s ease;
}

.timeline-step.active {
  opacity: 1;
}

.timeline-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.timeline-step.active .timeline-dot {
  border-color: var(--text-primary);
  background: var(--primary-light);
}

.timeline-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-tertiary);
}

.timeline-status {
  font-size: 9px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-detail-fade-enter-active,
.task-detail-fade-leave-active {
  transition: all 0.25s ease;
}

.task-detail-fade-enter-from,
.task-detail-fade-leave-to {
  opacity: 0;
}

.task-detail-fade-enter-from .task-detail-panel,
.task-detail-fade-leave-to .task-detail-panel {
  transform: scale(0.96) translateY(10px);
}
</style>
