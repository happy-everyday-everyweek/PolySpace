<template>
  <div v-if="taskStore.activeTasks.length > 0 || taskStore.completedTasks.length > 0 || taskStore.failedTasks.length > 0" class="ai-task-float">
    <div
      v-for="task in visibleTasks"
      :key="task.id"
      class="task-bubble"
      :class="{ completed: task.status === 'completed', failed: task.status === 'failed' }"
      @click="showTaskDetail(task)"
    >
      <span class="task-icon">
        <svg v-if="task.status === 'running'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-dasharray="4 4" class="spin"/>
        </svg>
        <svg v-else-if="task.status === 'completed'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </span>
      <span class="task-text">{{ task.name }}</span>
      <span v-if="task.status === 'running' && task.progress !== undefined" class="task-progress">{{ task.progress }}%</span>
      <button class="task-detail-btn" @click.stop="showTaskDetail(task)" title="查看详情">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="selectedTask" class="task-detail-overlay" @click="selectedTask = null">
      <div class="task-detail-panel" @click.stop>
        <div class="detail-header">
          <h4>任务详情</h4>
          <button class="close-btn" @click="selectedTask = null">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="detail-body">
          <div class="detail-row">
            <span class="detail-label">任务名称:</span>
            <span class="detail-value">{{ selectedTask.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态:</span>
            <span class="detail-value" :class="selectedTask.status">{{ getStatusText(selectedTask.status) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">创建时间:</span>
            <span class="detail-value">{{ formatTime(selectedTask.createdAt) }}</span>
          </div>
          <div v-if="selectedTask.result" class="detail-row">
            <span class="detail-label">执行结果:</span>
            <pre class="detail-result">{{ JSON.stringify(selectedTask.result, null, 2) }}</pre>
          </div>
          <div v-if="selectedTask.error" class="detail-row">
            <span class="detail-label">错误信息:</span>
            <span class="detail-value error">{{ selectedTask.error }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTaskStore, type AITask } from '@/stores/tasks'

const taskStore = useTaskStore()
const selectedTask = ref<AITask | null>(null)

const visibleTasks = computed(() => {
  return [...taskStore.activeTasks, ...taskStore.completedTasks, ...taskStore.failedTasks]
})

function showTaskDetail(task: AITask) {
  selectedTask.value = task
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

function formatTime(date: Date) {
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.ai-task-float {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-lg) var(--spacing-sm);
  justify-content: flex-start;
}

.task-bubble {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: var(--spacing-sm) 14px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  box-shadow: var(--shadow);
  animation: slideUp 0.3s ease;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.task-bubble:hover {
  border-color: var(--text-tertiary);
  box-shadow: var(--shadow-md);
}

.task-bubble.completed {
  border-color: var(--text-secondary);
  color: var(--text-secondary);
}

.task-bubble.failed {
  border-color: var(--text-tertiary);
  color: var(--text-tertiary);
}

.task-icon {
  display: flex;
  align-items: center;
}

.task-icon .spin {
  animation: spin 1s linear infinite;
}

.task-text {
  font-weight: var(--font-weight-medium);
}

.task-progress {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.task-detail-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.task-detail-btn:hover {
  background: var(--border-color);
  color: var(--text-secondary);
}

.task-detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--overlay-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.task-detail-panel {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  width: 500px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) 20px;
  border-bottom: 1px solid var(--border-color);
}

.detail-header h4 {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.detail-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-row {
  display: flex;
  gap: var(--spacing-md);
}

.detail-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  min-width: 80px;
  flex-shrink: 0;
}

.detail-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.detail-value.running {
  color: var(--ws-success);
}

.detail-value.completed {
  color: var(--ws-success);
}

.detail-value.failed {
  color: var(--ws-danger);
}

.detail-value.error {
  color: var(--ws-danger);
}

.detail-result {
  background: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
