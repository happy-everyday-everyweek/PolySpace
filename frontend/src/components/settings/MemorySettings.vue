<template>
  <div class="memory-settings">
    <h3 class="subsection-title">AI 记忆管理</h3>
    <p class="section-hint">查看和管理 AI 的记忆内容，包括工作记忆和交互记忆。</p>

    <div class="memory-summary-bar">
      <div class="summary-stat">
        <span class="stat-value">{{ workingCount }}</span>
        <span class="stat-label">工作记忆</span>
      </div>
      <div class="summary-stat">
        <span class="stat-value">{{ interactionCount }}</span>
        <span class="stat-label">交互记忆</span>
      </div>
      <div class="summary-stat">
        <span class="stat-value">{{ factCount }}</span>
        <span class="stat-label">事实记录</span>
      </div>
    </div>

    <div class="memory-toolbar">
      <div class="memory-tabs">
        <button
          v-for="tab in memoryTabs"
          :key="tab.key"
          class="memory-tab-btn"
          :class="{ active: activeMemoryTab === tab.key }"
          @click="switchMemoryTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="memory-actions">
        <input
          type="text"
          v-model="memoryFilter"
          class="global-input memory-filter"
          placeholder="搜索记忆..."
        />
        <button class="inference-btn sm" @click="refreshMemory" :disabled="memoryLoading">刷新</button>
      </div>
    </div>

    <div v-if="memoryLoading" class="memory-loading">加载中...</div>

    <template v-else>
      <div v-if="activeMemoryTab === 'working'" class="memory-list">
        <div v-if="filteredWorkingMemory.length === 0" class="memory-empty">暂无工作记忆</div>
        <div v-for="entry in filteredWorkingMemory" :key="entry.id" class="memory-item">
          <div class="memory-item-header">
            <span class="memory-category-badge" :class="'cat-' + entry.category">{{ categoryLabel(entry.category) }}</span>
            <span class="memory-time">{{ formatTime(entry.created_at) }}</span>
            <button class="memory-delete-btn" @click="deleteMemory('working', entry.id)" title="删除">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="memory-item-content">{{ entry.content }}</div>
          <div v-if="entry.tags && entry.tags.length" class="memory-tags">
            <span v-for="tag in entry.tags" :key="tag" class="memory-tag">{{ tag }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeMemoryTab === 'interaction'" class="memory-list">
        <div v-if="filteredInteractionMemory.length === 0" class="memory-empty">暂无交互记忆</div>
        <div v-for="entry in filteredInteractionMemory" :key="entry.id" class="memory-item">
          <div class="memory-item-header">
            <span class="memory-category-badge" :class="'cat-' + entry.category">{{ categoryLabel(entry.category) }}</span>
            <span class="memory-time">{{ formatTime(entry.created_at) }}</span>
            <button class="memory-delete-btn" @click="deleteMemory('interaction', entry.id)" title="删除">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="memory-item-content">{{ entry.content }}</div>
          <div v-if="entry.tags && entry.tags.length" class="memory-tags">
            <span v-for="tag in entry.tags" :key="tag" class="memory-tag">{{ tag }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeMemoryTab === 'facts'" class="memory-list">
        <div v-if="filteredFacts.length === 0" class="memory-empty">暂无事实记录</div>
        <div v-for="fact in filteredFacts" :key="fact.id" class="memory-item">
          <div class="memory-item-header">
            <span class="memory-category-badge cat-fact">事实</span>
            <span class="memory-confidence">置信度: {{ Math.round(fact.confidence * 100) }}%</span>
            <button class="memory-delete-btn" @click="deleteFact(fact.id)" title="删除">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="memory-item-content">{{ fact.content }}</div>
        </div>
      </div>

      <div v-if="activeMemoryTab === 'dream'" class="memory-list">
        <div v-if="dreamResults.length === 0" class="memory-empty">暂无梦境整合记录</div>
        <div v-for="dream in dreamResults" :key="dream.phase + dream.timestamp" class="memory-item dream-item">
          <div class="memory-item-header">
            <span class="memory-category-badge" :class="'dream-' + dream.phase">{{ dreamLabel(dream.phase) }}</span>
            <span class="memory-time">{{ formatTime(dream.timestamp) }}</span>
          </div>
          <div v-if="dream.insights && dream.insights.length" class="dream-section">
            <span class="dream-section-label">洞察:</span>
            <ul class="dream-list">
              <li v-for="insight in dream.insights" :key="insight">{{ insight }}</li>
            </ul>
          </div>
          <div v-if="dream.patterns && dream.patterns.length" class="dream-section">
            <span class="dream-section-label">模式:</span>
            <ul class="dream-list">
              <li v-for="pattern in dream.patterns" :key="String(pattern)">{{ pattern }}</li>
            </ul>
          </div>
          <div v-if="dream.report" class="dream-section">
            <span class="dream-section-label">报告:</span>
            <p class="dream-report">{{ dream.report }}</p>
          </div>
        </div>
      </div>
    </template>

    <h3 class="subsection-title">记忆配置</h3>
    <div class="memory-config-block">
      <div class="global-form-group lab-row">
        <label>启用梦境整合</label>
        <label class="global-switch">
          <input type="checkbox" v-model="dreamEnabled" @change="saveMemoryConfig" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="global-form-group lab-row">
        <label>自动记忆对话</label>
        <label class="global-switch">
          <input type="checkbox" v-model="autoRecordChat" @change="saveMemoryConfig" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="global-form-group lab-row">
        <label>记忆搜索范围</label>
        <select v-model="searchDepth" class="global-input" @change="saveMemoryConfig">
          <option value="shallow">浅层 (仅标题和关键词)</option>
          <option value="medium">中层 (标题+内容摘要)</option>
          <option value="deep">深层 (全量语义搜索)</option>
        </select>
      </div>

      <div class="global-form-group lab-row">
        <label>短期记忆上限</label>
        <input type="number" v-model.number="shortTermLimit" class="global-input small-input" min="10" max="500" @change="saveMemoryConfig" />
      </div>

      <div class="global-form-group lab-row">
        <label>长期记忆保留天数</label>
        <input type="number" v-model.number="longTermRetentionDays" class="global-input small-input" min="7" max="365" @change="saveMemoryConfig" />
      </div>
    </div>

    <div class="memory-danger-zone">
      <h3 class="subsection-title danger">危险操作</h3>
      <div class="danger-actions">
        <button class="inference-btn danger" @click="clearAllMemory" :disabled="clearingMemory">
          {{ clearingMemory ? '清除中...' : '清除所有记忆' }}
        </button>
        <button class="inference-btn danger" @click="triggerDream('light')">触发轻度梦境</button>
        <button class="inference-btn danger" @click="triggerDream('deep')">触发深度梦境</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

const memoryLoading = ref(false)
const clearingMemory = ref(false)
const activeMemoryTab = ref('working')
const memoryFilter = ref('')

const workingMemory = ref<any[]>([])
const interactionMemory = ref<any[]>([])
const facts = ref<any[]>([])
const dreamResults = ref<any[]>([])

const workingCount = ref(0)
const interactionCount = ref(0)
const factCount = ref(0)

const dreamEnabled = ref(true)
const autoRecordChat = ref(true)
const searchDepth = ref('medium')
const shortTermLimit = ref(100)
const longTermRetentionDays = ref(90)

const memoryTabs = [
  { key: 'working', label: '工作记忆' },
  { key: 'interaction', label: '交互记忆' },
  { key: 'facts', label: '事实记录' },
  { key: 'dream', label: '梦境记录' },
]

const filteredWorkingMemory = computed(() => {
  if (!memoryFilter.value) return workingMemory.value
  const kw = memoryFilter.value.toLowerCase()
  return workingMemory.value.filter(e =>
    e.content?.toLowerCase().includes(kw) ||
    e.category?.toLowerCase().includes(kw) ||
    (e.tags || []).some((t: string) => t.toLowerCase().includes(kw))
  )
})

const filteredInteractionMemory = computed(() => {
  if (!memoryFilter.value) return interactionMemory.value
  const kw = memoryFilter.value.toLowerCase()
  return interactionMemory.value.filter(e =>
    e.content?.toLowerCase().includes(kw) ||
    e.category?.toLowerCase().includes(kw) ||
    (e.tags || []).some((t: string) => t.toLowerCase().includes(kw))
  )
})

const filteredFacts = computed(() => {
  if (!memoryFilter.value) return facts.value
  const kw = memoryFilter.value.toLowerCase()
  return facts.value.filter(f => f.content?.toLowerCase().includes(kw))
})

const _CATEGORY_LABELS: Record<string, string> = {
  task: '任务',
  file_operation: '文件操作',
  schedule: '日程',
  decision: '决策',
  knowledge: '知识',
  conversation: '对话',
  emotion: '情绪',
  preference: '偏好',
  communication_style: '交流风格',
  feedback: '反馈',
  fact: '事实',
}

function categoryLabel(cat: string): string {
  return _CATEGORY_LABELS[cat] || cat
}

function dreamLabel(phase: string): string {
  const map: Record<string, string> = { light: '轻度梦境', deep: '深度梦境', rem: 'REM 梦境' }
  return map[phase] || phase
}

function formatTime(ts: string): string {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

function switchMemoryTab(key: string) {
  activeMemoryTab.value = key
  if (key === 'dream' && dreamResults.value.length === 0) {
    loadDreamResults()
  }
}

async function refreshMemory() {
  memoryLoading.value = true
  try {
    await Promise.all([
      loadMemorySummary(),
      loadWorkingMemory(),
      loadInteractionMemory(),
      loadFacts(),
    ])
    if (activeMemoryTab.value === 'dream') {
      await loadDreamResults()
    }
  } finally {
    memoryLoading.value = false
  }
}

async function loadMemorySummary() {
  try {
    const { data } = await api.get('/ai/coordination/memory/summary')
    workingCount.value = data.working?.total_entries || 0
    interactionCount.value = data.interaction?.total_entries || 0
    factCount.value = data.working?.facts_count || data.interaction?.facts_count || 0
  } catch {
    workingCount.value = 0
    interactionCount.value = 0
    factCount.value = 0
  }
}

async function loadWorkingMemory() {
  try {
    const { data } = await api.get('/ai/coordination/memory/search', { params: { query: '*', limit: 50 } })
    workingMemory.value = (data.working || []).map((e: any) => ({
      id: e.id || '',
      content: e.content || '',
      category: e.category || 'task',
      tags: e.tags || [],
      created_at: e.created_at || '',
      confidence: e.confidence || 0,
    }))
  } catch {
    workingMemory.value = []
  }
}

async function loadInteractionMemory() {
  try {
    const { data } = await api.get('/ai/coordination/memory/search', { params: { query: '*', limit: 50 } })
    interactionMemory.value = (data.interaction || []).map((e: any) => ({
      id: e.id || '',
      content: e.content || '',
      category: e.category || 'conversation',
      tags: e.tags || [],
      created_at: e.created_at || '',
      confidence: e.confidence || 0,
    }))
  } catch {
    interactionMemory.value = []
  }
}

async function loadFacts() {
  try {
    const { data } = await api.get('/ai/coordination/memories/latest')
    if (data && data.content) {
      facts.value = [{ id: data.id || '1', content: data.content, confidence: data.confidence || 1.0, created_at: data.created_at || '' }]
    } else {
      facts.value = []
    }
  } catch {
    facts.value = []
  }
}

async function loadDreamResults() {
  try {
    const { data } = await api.get('/ai/coordination/memory/dream/results', { params: { limit: 10 } })
    dreamResults.value = data.results || []
  } catch {
    dreamResults.value = []
  }
}

async function deleteMemory(type: string, id: string) {
  try {
    await api.delete(`/ai/coordination/memory/${type}/${id}`)
    if (type === 'working') {
      workingMemory.value = workingMemory.value.filter(e => e.id !== id)
    } else {
      interactionMemory.value = interactionMemory.value.filter(e => e.id !== id)
    }
  } catch {
    // ignore
  }
}

async function deleteFact(id: string) {
  try {
    await api.delete(`/ai/coordination/memories/${id}`)
    facts.value = facts.value.filter(f => f.id !== id)
  } catch {
    // ignore
  }
}

async function clearAllMemory() {
  if (!confirm('确定要清除所有 AI 记忆吗？此操作不可恢复。')) return
  clearingMemory.value = true
  try {
    await api.post('/ai/coordination/memory/clear')
    workingMemory.value = []
    interactionMemory.value = []
    facts.value = []
    dreamResults.value = []
    workingCount.value = 0
    interactionCount.value = 0
    factCount.value = 0
  } catch {
    // ignore
  } finally {
    clearingMemory.value = false
  }
}

async function triggerDream(phase: string) {
  try {
    await api.post(`/ai/coordination/memory/dream/${phase}`)
    await loadDreamResults()
  } catch {
    // ignore
  }
}

async function saveMemoryConfig() {
  try {
    await api.put('/settings/memory', {
      dream_enabled: dreamEnabled.value,
      auto_record_chat: autoRecordChat.value,
      search_depth: searchDepth.value,
      short_term_limit: shortTermLimit.value,
      long_term_retention_days: longTermRetentionDays.value,
    })
  } catch {
    // ignore
  }
}

async function loadMemoryConfig() {
  try {
    const { data } = await api.get('/settings/memory')
    if (data) {
      dreamEnabled.value = data.dream_enabled ?? true
      autoRecordChat.value = data.auto_record_chat ?? true
      searchDepth.value = data.search_depth ?? 'medium'
      shortTermLimit.value = data.short_term_limit ?? 100
      longTermRetentionDays.value = data.long_term_retention_days ?? 90
    }
  } catch {
    // use defaults
  }
}

onMounted(async () => {
  memoryLoading.value = true
  try {
    await Promise.all([
      loadMemorySummary(),
      loadWorkingMemory(),
      loadFacts(),
      loadMemoryConfig(),
    ])
  } finally {
    memoryLoading.value = false
  }
})
</script>

<style scoped>
.memory-settings {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.subsection-title.danger {
  color: var(--text-primary);
}

.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.memory-summary-bar {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  margin-bottom: 16px;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 60px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-label {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.memory-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.memory-tabs {
  display: flex;
  gap: 2px;
  background: var(--bg-secondary);
  padding: 3px;
  border-radius: 8px;
}

.memory-tab-btn {
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.memory-tab-btn:hover {
  color: var(--text-primary);
}

.memory-tab-btn.active {
  background: var(--bg-color);
  color: var(--text-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.memory-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.memory-filter {
  width: 160px;
  font-size: 12px;
  padding: 5px 10px;
}

.memory-loading {
  text-align: center;
  padding: 32px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.memory-empty {
  text-align: center;
  padding: 24px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.memory-item {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
}

.memory-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.memory-category-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--primary-light);
  color: var(--primary-color);
}

.memory-category-badge.cat-task { background: var(--primary-light); color: var(--text-primary); }
.memory-category-badge.cat-file_operation { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-schedule { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-decision { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-knowledge { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-conversation { background: var(--primary-light); color: var(--text-primary); }
.memory-category-badge.cat-emotion { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-preference { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-communication_style { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-feedback { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.cat-fact { background: var(--bg-tertiary); color: var(--text-secondary); }

.memory-category-badge.dream-light { background: var(--bg-tertiary); color: var(--text-secondary); }
.memory-category-badge.dream-deep { background: var(--primary-light); color: var(--text-primary); }
.memory-category-badge.dream-rem { background: var(--bg-tertiary); color: var(--text-secondary); }

.memory-time {
  font-size: 10px;
  color: var(--text-quaternary);
  margin-left: auto;
}

.memory-confidence {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.memory-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  color: var(--text-quaternary);
  background: none;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
  border: none;
}

.memory-delete-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.memory-item-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.memory-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.memory-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--bg-tertiary, #eee);
  color: var(--text-tertiary);
}

.dream-section {
  margin-top: 6px;
}

.dream-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 4px;
}

.dream-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.dream-report {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
}

.memory-config-block {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lab-row label:first-child {
  font-size: 13px;
  color: var(--text-primary);
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

.small-input {
  width: 80px;
  text-align: center;
}

.memory-danger-zone {
  margin-top: 8px;
}

.danger-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.inference-btn.sm {
  padding: 3px 10px;
  font-size: 11px;
}

.inference-btn.danger {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.inference-btn.danger:hover {
  background: var(--primary-light);
}

.inference-btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: opacity 0.15s;
  border: none;
}

.inference-btn:hover {
  opacity: 0.9;
}

.inference-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
