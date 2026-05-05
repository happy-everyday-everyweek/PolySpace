<template>
  <div class="agent-bar">
    <div class="agents-scroll">
      <!-- 垂类智能体（固定） -->
      <div
        v-for="agent in verticalAgents"
        :key="agent.id"
        class="agent-chip"
        :class="{ active: agent.status === 'running', completed: agent.status === 'completed' }"
        @click="showAgentDetail(agent)"
      >
        <div class="agent-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
            <circle cx="8" cy="10" r="1" fill="currentColor" stroke="none" />
            <circle cx="16" cy="10" r="1" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <span class="agent-name">{{ agent.name }}</span>
        <span v-if="agent.status === 'running'" class="status-dot running"></span>
        <span v-else-if="agent.status === 'completed'" class="status-dot completed"></span>
      </div>

      <!-- 子智能体（动态创建） -->
      <div
        v-for="agent in subAgents"
        :key="agent.id"
        class="agent-chip sub"
        :class="{ active: agent.status === 'running', completed: agent.status === 'completed' }"
        @click="showAgentDetail(agent)"
      >
        <div class="agent-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
            <circle cx="8" cy="10" r="1" fill="currentColor" stroke="none" />
            <circle cx="16" cy="10" r="1" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <span class="agent-name">{{ agent.name }}</span>
        <span v-if="agent.status === 'running'" class="status-dot running"></span>
        <span v-else-if="agent.status === 'completed'" class="status-dot completed"></span>
      </div>
    </div>

    <!-- 智能体详情弹窗 -->
    <div v-if="selectedAgent" class="agent-detail-overlay" @click="selectedAgent = null">
      <div class="agent-detail-panel" @click.stop>
        <div class="detail-header">
          <div class="detail-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
              <circle cx="8" cy="10" r="1" fill="currentColor" stroke="none" />
              <circle cx="16" cy="10" r="1" fill="currentColor" stroke="none" />
            </svg>
          </div>
          <div class="detail-info">
            <h4>{{ selectedAgent.name }}</h4>
            <span class="detail-type">{{ selectedAgent.type === 'vertical' ? '垂类智能体' : '子智能体' }}</span>
          </div>
          <button class="close-btn" @click="selectedAgent = null">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="detail-body">
          <div class="detail-row">
            <span class="detail-label">状态:</span>
            <span class="detail-value" :class="selectedAgent.status">{{ getStatusText(selectedAgent.status) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">任务:</span>
            <span class="detail-value">{{ selectedAgent.task || '无' }}</span>
          </div>
          <div v-if="selectedAgent.result" class="detail-row">
            <span class="detail-label">结果:</span>
            <pre class="detail-result">{{ JSON.stringify(selectedAgent.result, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Agent {
  id: string
  name: string
  type: 'vertical' | 'sub'
  status: 'idle' | 'running' | 'completed' | 'error'
  task?: string
  result?: any
}

const verticalAgents = ref<Agent[]>([
  { id: 'coding', name: '编程', type: 'vertical', status: 'idle' },
  { id: 'writing', name: '写作', type: 'vertical', status: 'idle' },
  { id: 'data', name: '数据', type: 'vertical', status: 'idle' },
  { id: 'research', name: '研究', type: 'vertical', status: 'idle' },
  { id: 'seo', name: 'SEO', type: 'vertical', status: 'idle' },
  { id: 'education', name: '教育', type: 'vertical', status: 'idle' },
  { id: 'finance', name: '金融', type: 'vertical', status: 'idle' },
  { id: 'devops', name: '运维', type: 'vertical', status: 'idle' },
  { id: 'design', name: '设计', type: 'vertical', status: 'idle' },
])

const subAgents = ref<Agent[]>([])
const selectedAgent = ref<Agent | null>(null)

function showAgentDetail(agent: Agent) {
  selectedAgent.value = agent
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    completed: '已完成',
    error: '错误'
  }
  return statusMap[status] || status
}

// 暴露方法供外部调用
function updateAgentStatus(id: string, status: Agent['status'], task?: string, result?: any) {
  const agent = verticalAgents.value.find(a => a.id === id) || subAgents.value.find(a => a.id === id)
  if (agent) {
    agent.status = status
    if (task) agent.task = task
    if (result) agent.result = result
  }
}

function addSubAgent(name: string, task: string) {
  const id = `sub-${Date.now()}`
  subAgents.value.push({
    id,
    name,
    type: 'sub',
    status: 'running',
    task
  })
  return id
}

defineExpose({
  updateAgentStatus,
  addSubAgent
})
</script>

<style scoped>
.agent-bar {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-sm);
  box-shadow: var(--shadow-md);
  max-width: 90vw;
}

.agents-scroll {
  display: flex;
  gap: var(--spacing-sm);
  overflow-x: auto;
  padding: 4px;
  scrollbar-width: none;
}

.agents-scroll::-webkit-scrollbar {
  display: none;
}

.agent-chip {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 14px;
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-smooth);
  white-space: nowrap;
  position: relative;
}

.agent-chip:hover {
  border-color: var(--border-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.agent-chip:active {
  transform: translateY(0) scale(0.97);
  box-shadow: none;
}

.agent-chip.active {
  background: var(--primary-light);
  border-color: var(--primary-color);
}

.agent-chip.completed {
  background: var(--bg-tertiary);
  border-color: var(--text-secondary);
}

.agent-chip.sub {
  background: var(--bg-tertiary);
}

.agent-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--bg-color);
  color: var(--text-primary);
}

.agent-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: absolute;
  top: 4px;
  right: 4px;
}

.status-dot.running {
  background: var(--text-primary);
  animation: pulse 1.5s infinite;
}

.status-dot.completed {
  background: var(--text-secondary);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.agent-detail-overlay {
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

.agent-detail-panel {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  width: 480px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
  animation: micro-bounce-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) 20px;
  border-bottom: 1px solid var(--border-color);
}

.detail-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.detail-info {
  flex: 1;
}

.detail-info h4 {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.detail-type {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
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
  min-width: 60px;
}

.detail-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.detail-value.running {
  color: var(--text-primary);
}

.detail-value.completed {
  color: var(--text-secondary);
}

.detail-value.error {
  color: var(--text-tertiary);
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

.close-btn:active {
  transform: scale(0.95);
}
</style>
