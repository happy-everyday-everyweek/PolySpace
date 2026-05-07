<template>
  <div class="header-search" :class="{ focused: isFocused }">
    <div class="search-input-wrap" @click="focusInput">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
      <input
        ref="inputRef"
        v-model="query"
        class="search-input"
        :placeholder="placeholderText"
        @input="onInput"
        @keydown.down.prevent="moveDown"
        @keydown.up.prevent="moveUp"
        @keydown.enter.prevent="executeSelected"
        @keydown.escape.prevent="clearSearch"
        @focus="onFocus"
        @blur="onBlur"
      />
      <button v-if="query" class="clear-btn" @click="clearSearch">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
      <kbd class="search-kbd">Ctrl+K</kbd>
    </div>

    <Teleport to="body">
      <div v-if="showResults" class="header-search-overlay" @click.self="isFocused = false">
        <div class="header-search-dropdown" :style="dropdownStyle">
          <div v-if="loading" class="search-loading">
            <svg class="spin-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <span>搜索中...</span>
          </div>

          <template v-else>
            <div v-if="groupedResults.length" class="results-list">
              <div v-for="group in groupedResults" :key="group.category" class="result-group">
                <div class="group-header">
                  <span class="group-icon" v-html="getCategoryIcon(group.category)"></span>
                  <span class="group-label">{{ getCategoryLabel(group.category) }}</span>
                  <span class="group-count">{{ group.items.length }}</span>
                </div>
                <div
                  v-for="item in group.items"
                  :key="item.id"
                  class="result-item"
                  :class="{ active: selectedIndex === getFlatIndex(group.category, item.id) }"
                  @click="execute(item)"
                  @mouseenter="selectedIndex = getFlatIndex(group.category, item.id)"
                >
                  <div class="result-info">
                    <span class="result-title">{{ item.title }}</span>
                    <span v-if="item.description" class="result-desc">{{ item.description }}</span>
                  </div>
                  <svg class="result-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 18l6-6-6-6"/>
                  </svg>
                </div>
              </div>
            </div>

            <div v-else-if="query" class="search-empty">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
              </svg>
              <span>未找到与 "{{ query }}" 相关的结果</span>
            </div>

            <div v-else class="search-hint">
              <div class="hint-scopes">
                <span class="hint-label">快速筛选:</span>
                <button
                  v-for="s in scopeOptions"
                  :key="s.value"
                  class="scope-chip"
                  :class="{ active: activeScope === s.value }"
                  @mousedown.prevent="setScope(s.value)"
                >
                  {{ s.label }}
                </button>
              </div>
              <div v-if="recentSearches.length" class="hint-recent">
                <span class="hint-label">最近搜索:</span>
                <button
                  v-for="r in recentSearches.slice(0, 5)"
                  :key="r"
                  class="recent-chip"
                  @mousedown.prevent="applyRecent(r)"
                >
                  {{ r }}
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useModeStore } from '@/stores/mode'
import api from '@/utils/api'

interface SearchResult {
  id: string
  title: string
  description: string
  category: string
  icon: string
  action: string
  action_data: Record<string, string>
  score: number
}

interface ResultGroup {
  category: string
  items: SearchResult[]
}

const emit = defineEmits<{
  (e: 'execute', result: SearchResult): void
}>()

const router = useRouter()
const modeStore = useModeStore()
const query = ref('')
const results = ref<SearchResult[]>([])
const selectedIndex = ref(0)
const loading = ref(false)
const isFocused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const activeScope = ref('all')
const recentSearches = ref<string[]>([])

const placeholderText = computed(() => {
  if (modeStore.currentMode === 'agent') {
    return '搜索对话、记忆、知识库、命令...'
  }
  return '搜索文档、知识库、待办、笔记、对话...'
})

const scopeOptions = [
  { value: 'all', label: '全部' },
  { value: 'memory', label: 'AI 记忆' },
  { value: 'chat', label: '对话记录' },
  { value: 'knowledge', label: '知识库' },
  { value: 'notes', label: '笔记' },
  { value: 'todo', label: '待办' },
  { value: 'document', label: '文档' },
  { value: 'calendar', label: '日历' },
]

const showResults = computed(() => isFocused.value && (query.value || results.value.length > 0 || recentSearches.value.length > 0))

const dropdownStyle = computed(() => {
  return {
    position: 'fixed' as const,
    top: '54px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '560px',
    maxWidth: '90vw',
  }
})

const groupedResults = computed((): ResultGroup[] => {
  const groups: Map<string, SearchResult[]> = new Map()
  const categoryOrder = ['memory', 'chat', 'knowledge', 'document', 'notes', 'todo', 'calendar', 'navigation', 'app', 'command', 'setting', 'action']
  for (const r of results.value) {
    if (!groups.has(r.category)) {
      groups.set(r.category, [])
    }
    groups.get(r.category)!.push(r)
  }
  const ordered: ResultGroup[] = []
  for (const cat of categoryOrder) {
    if (groups.has(cat)) {
      ordered.push({ category: cat, items: groups.get(cat)! })
    }
  }
  for (const [cat, items] of groups) {
    if (!categoryOrder.includes(cat)) {
      ordered.push({ category: cat, items })
    }
  }
  return ordered
})

const categoryLabels: Record<string, string> = {
  navigation: '导航',
  command: '命令',
  app: '应用',
  setting: '设置',
  action: 'AI 操作',
  knowledge: '知识库',
  notes: '笔记',
  todo: '待办',
  document: '文档',
  calendar: '日历',
  chat: '对话记录',
  memory: 'AI 记忆',
}

const categoryIcons: Record<string, string> = {
  navigation: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>',
  command: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9,11 12,14 22,4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  app: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>',
  setting: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
  action: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10"/></svg>',
  knowledge: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
  notes: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
  todo: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  document: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>',
  calendar: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  chat: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
  memory: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a7 7 0 017 7c0 3-2 5.5-4 7.5L12 22l-3-5.5C7 14.5 5 12 5 9a7 7 0 017-7z"/><circle cx="12" cy="9" r="2.5"/></svg>',
}

function getCategoryLabel(cat: string) {
  return categoryLabels[cat] || cat
}

function getCategoryIcon(cat: string) {
  return categoryIcons[cat] || categoryIcons.app
}

function getFlatIndex(category: string, id: string): number {
  let idx = 0
  for (const group of groupedResults.value) {
    for (const item of group.items) {
      if (group.category === category && item.id === id) return idx
      idx++
    }
  }
  return 0
}

function getFlatResults(): SearchResult[] {
  const flat: SearchResult[] = []
  for (const group of groupedResults.value) {
    flat.push(...group.items)
  }
  return flat
}

let searchTimer: ReturnType<typeof setTimeout> | null = null

function onInput() {
  if (searchTimer) clearTimeout(searchTimer)
  if (!query.value.trim()) {
    results.value = []
    selectedIndex.value = 0
    return
  }
  loading.value = true
  searchTimer = setTimeout(async () => {
    try {
      const params: Record<string, unknown> = { q: query.value, limit: 30 }
      if (activeScope.value !== 'all') {
        params.scope = activeScope.value
      }
      const { data } = await api.get('/search', { params })
      results.value = data.results || []
      selectedIndex.value = 0
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 200)
}

function moveDown() {
  const total = getFlatResults().length
  if (selectedIndex.value < total - 1) selectedIndex.value++
}

function moveUp() {
  if (selectedIndex.value > 0) selectedIndex.value--
}

function executeSelected() {
  const flat = getFlatResults()
  if (flat[selectedIndex.value]) {
    execute(flat[selectedIndex.value])
  }
}

function execute(result: SearchResult) {
  isFocused.value = false
  switch (result.action) {
    case 'navigate':
      if (result.action_data?.path) router.push(result.action_data.path)
      break
    case 'open_app':
      if (modeStore.currentMode === 'workspace') {
        router.push({ path: '/workspace', query: { app: result.action_data?.app } })
      } else {
        router.push({ path: '/workspace', query: { app: result.action_data?.app } })
      }
      break
    case 'open_document':
      router.push({ path: '/workspace', query: { app: result.action_data?.app || 'document' } })
      break
    case 'open_setting':
      router.push({ path: '/settings', query: { tab: result.action_data?.tab } })
      break
    case 'open_memory':
      router.push({ path: '/settings', query: { tab: 'agent' } })
      break
    case 'clear_chat':
    case 'toggle_mode':
    case 'new_session':
    case 'deep_research':
    case 'ai_action':
      emit('execute', result)
      break
    default:
      emit('execute', result)
  }
}

function clearSearch() {
  query.value = ''
  results.value = []
  selectedIndex.value = 0
  isFocused.value = false
}

function focusInput() {
  inputRef.value?.focus()
}

function onFocus() {
  isFocused.value = true
}

function onBlur() {
  setTimeout(() => {
    isFocused.value = false
  }, 200)
}

function setScope(scope: string) {
  activeScope.value = scope
  if (query.value.trim()) {
    onInput()
  }
  inputRef.value?.focus()
}

async function applyRecent(r: string) {
  query.value = r
  onInput()
  inputRef.value?.focus()
}

async function loadRecentSearches() {
  try {
    const { data } = await api.get('/search/recent', { params: { limit: 8 } })
    recentSearches.value = data.searches || []
  } catch {
    recentSearches.value = []
  }
}

function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    if (isFocused.value) {
      clearSearch()
    } else {
      isFocused.value = true
      nextTick(() => inputRef.value?.focus())
    }
  }
}

watch(isFocused, (val) => {
  if (val && recentSearches.value.length === 0) {
    loadRecentSearches()
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  loadRecentSearches()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped>
.header-search {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 480px;
  margin: 0 var(--spacing-lg);
  position: relative;
}

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  height: 32px;
  width: 100%;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  transition: all var(--transition-normal);
  cursor: text;
}

.search-input-wrap:focus-within {
  border-color: var(--primary-color);
  background: var(--bg-color);
  box-shadow: var(--focus-ring);
}

.header-search.focused .search-input-wrap {
  border-color: var(--primary-color);
  background: var(--bg-color);
}

.search-icon {
  width: 15px;
  height: 15px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  line-height: 1;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--text-quaternary);
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  background: none;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.search-kbd {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  border: 1px solid var(--border-color);
  flex-shrink: 0;
  font-family: inherit;
  line-height: 1.4;
}

.header-search-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

.header-search-dropdown {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-height: 420px;
  overflow-y: auto;
  z-index: 9999;
}

.search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: 20px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.results-list {
  padding: 6px;
}

.result-group {
  margin-bottom: 2px;
}

.result-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px 4px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.group-icon {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
}

.group-count {
  margin-left: auto;
  font-size: 10px;
  font-weight: var(--font-weight-medium);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-quaternary);
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.result-item:hover,
.result-item.active {
  background: var(--bg-secondary);
}

.result-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-desc {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-arrow {
  color: var(--text-quaternary);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.result-item:hover .result-arrow,
.result-item.active .result-arrow {
  opacity: 1;
}

.search-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 24px var(--spacing-lg);
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.search-hint {
  padding: var(--spacing-md) 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hint-scopes,
.hint-recent {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.hint-label {
  font-size: var(--font-size-xs);
  color: var(--text-quaternary);
  font-weight: var(--font-weight-medium);
  flex-shrink: 0;
}

.scope-chip {
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.scope-chip:hover {
  border-color: var(--border-color);
  color: var(--text-primary);
}

.scope-chip.active {
  background: var(--primary-color);
  color: #ffffff;
  border-color: var(--primary-color);
}

.recent-chip {
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: none;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.recent-chip:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
</style>
