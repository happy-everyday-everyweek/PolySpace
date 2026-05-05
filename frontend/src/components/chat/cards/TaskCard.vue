<template>
  <div class="card task-card" :class="statusClass" @click="emit('click', props.data)">
    <div class="card-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <template v-if="status === 'planning' || status === 'pending'">
          <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="spin"/>
        </template>
        <template v-else-if="status === 'running'">
          <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="spin"/>
        </template>
        <template v-else-if="status === 'completed'">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </template>
        <template v-else-if="status === 'failed'">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </template>
        <template v-else-if="status === 'cancelled'">
          <circle cx="12" cy="12" r="10"/>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
        </template>
        <template v-else>
          <circle cx="12" cy="12" r="10"/>
        </template>
      </svg>
      <span class="card-type-label">任务</span>
      <span class="task-status-badge" :class="'badge-' + status">{{ statusLabel }}</span>
    </div>
    <div class="card-body">
      <h4 class="task-title">{{ description || '未命名任务' }}</h4>
      <div v-if="taskId" class="task-id-row">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
        <span class="task-id-text">{{ taskId }}</span>
      </div>
      <div v-if="status === 'running' && hasProgress" class="task-progress">
        <div class="progress-bar-track">
          <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span class="progress-percent">{{ progressPercent }}%</span>
      </div>
      <div v-if="progressMessage && (status === 'running' || status === 'planning')" class="task-progress-msg">
        {{ progressMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CardData } from '@/utils/contentRenderer'

const props = defineProps<{
  data: CardData
}>()

const emit = defineEmits<{
  click: [data: CardData]
}>()

const taskId = computed(() => String(props.data.task_id || ''))
const description = computed(() => String(props.data.description || ''))
const progressMessage = computed(() => String(props.data.progress_message || ''))

const status = computed(() => {
  const s = String(props.data.status || '')
  if (!s) return 'pending'
  if (s === 'pending') return 'planning'
  return s
})

const statusLabel = computed(() => {
  const s = status.value
  if (s === 'planning') return '规划中'
  if (s === 'running') return '执行中'
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  if (s === 'cancelled') return '已取消'
  return '规划中'
})

const statusClass = computed(() => `status-${status.value}`)

const hasProgress = computed(() => {
  const p = Number(props.data.progress)
  return !isNaN(p) && p > 0
})

const progressPercent = computed(() => {
  const p = Number(props.data.progress)
  if (isNaN(p)) return 0
  return Math.round(p * 100)
})
</script>

<style scoped>
.task-card {
  border-left: 3px solid var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.card-type-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-status-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  margin-left: auto;
  letter-spacing: 0.3px;
}

.badge-planning {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.badge-running {
  color: var(--text-primary);
  background: var(--primary-light);
}

.badge-completed {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.badge-failed {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.badge-cancelled {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.status-completed {
  border-left-color: var(--text-secondary);
}

.status-completed .card-header {
  color: var(--text-secondary);
}

.status-failed {
  border-left-color: var(--text-tertiary);
}

.status-failed .card-header {
  color: var(--text-tertiary);
}

.status-running {
  border-left-color: var(--text-primary);
}

.status-running .card-header {
  color: var(--text-primary);
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: var(--text-color);
}

.task-id-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.task-id-row svg {
  flex-shrink: 0;
  opacity: 0.6;
}

.task-id-text {
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 11px;
  letter-spacing: 0.3px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.progress-bar-track {
  flex: 1;
  height: 4px;
  background: var(--bg-secondary, #e8e8e8);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--text-primary);
  border-radius: 2px;
  transition: width 0.4s ease;
}

.progress-percent {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 32px;
  text-align: right;
}

.task-progress-msg {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
