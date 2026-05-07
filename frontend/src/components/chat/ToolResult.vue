<template>
  <div class="tool-call-item" :class="{ 'tool-error': hasError, 'tool-pending': isPending }">
    <div class="tool-header" @click="expanded = !expanded">
      <div class="tool-icon-row">
        <svg v-if="isPending" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
        <svg v-else-if="hasError" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <span class="tool-name">{{ displayName }}</span>
      </div>
      <span class="tool-status" :class="statusClass">{{ statusLabel }}</span>
    </div>
    <div v-if="expanded" class="tool-detail">
      <div v-if="displayArgs" class="tool-args">
        <span class="detail-label">参数</span>
        <pre>{{ displayArgs }}</pre>
      </div>
      <div v-if="displayResult" class="tool-result-content">
        <span class="detail-label">{{ hasError ? '错误' : '结果' }}</span>
        <pre>{{ displayResult }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ToolCall, ToolResult } from '@/types/chat'

const props = defineProps<{
  toolCall: ToolCall
  toolResult?: ToolResult
}>()

const expanded = ref(false)

const TOOL_NAME_MAP: Record<string, string> = {
  execute_task: '执行任务',
  search: '搜索',
  read_file: '读取文件',
  email: '邮件',
  calendar: '日历',
  todo: '待办',
  knowledge: '知识库',
  notes: '笔记',
  kanban: '看板',
  memory: '记忆',
  coordination: '协调',
  pdf: 'PDF',
  markitdown: '文档转换',
}

const displayName = computed(() => TOOL_NAME_MAP[props.toolCall.name] || props.toolCall.name)

const isPending = computed(() => !props.toolResult)

const hasError = computed(() => !!props.toolResult?.error)

const statusClass = computed(() => {
  if (isPending.value) return 'status-pending'
  if (hasError.value) return 'status-error'
  return 'status-done'
})

const statusLabel = computed(() => {
  if (isPending.value) return '执行中'
  if (hasError.value) return '失败'
  return '完成'
})

const displayArgs = computed(() => {
  const args = props.toolCall.arguments
  if (!args || Object.keys(args).length === 0) return ''
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
})

const displayResult = computed(() => {
  if (!props.toolResult) return ''
  const result = props.toolResult.result
  if (!result) return ''
  try {
    const str = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
    return str.length > 500 ? str.slice(0, 500) + '...' : str
  } catch {
    return String(result).slice(0, 500)
  }
})
</script>

<style scoped>
.tool-call-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  background: var(--bg-secondary);
  font-size: 13px;
  margin: 4px 0;
  transition: all var(--transition-fast);
}

.tool-call-item:hover {
  border-color: var(--text-tertiary);
}

.tool-call-item.tool-pending {
  border-left: 3px solid var(--text-primary);
}

.tool-call-item.tool-error {
  border-left: 3px solid var(--status-danger, #EF4444);
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.tool-icon-row {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.tool-name {
  font-weight: 500;
  color: var(--text-color);
}

.tool-status {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  letter-spacing: 0.3px;
}

.status-pending {
  color: var(--text-primary);
  background: var(--primary-light);
}

.status-done {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.status-error {
  color: var(--status-danger, #EF4444);
  background: var(--bg-tertiary);
}

.tool-detail {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

.detail-label {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-args pre,
.tool-result-content pre {
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-code);
  max-height: 150px;
  overflow-y: auto;
  margin: 0;
  padding: 6px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
