<template>
  <Teleport to="body">
    <div v-if="visible" class="command-palette-overlay" @click.self="close">
      <div class="command-palette">
        <div class="command-palette-input-wrap">
          <svg class="command-palette-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input
            ref="inputRef"
            v-model="query"
            class="command-palette-input"
            placeholder="搜索应用、命令、设置..."
            @keydown.down.prevent="moveDown"
            @keydown.up.prevent="moveUp"
            @keydown.enter.prevent="executeSelected"
            @keydown.escape.prevent="close"
          />
          <kbd class="command-palette-kbd">ESC</kbd>
        </div>
        <div v-if="results.length" class="command-palette-results">
          <div
            v-for="(result, index) in results"
            :key="result.id"
            class="command-palette-result"
            :class="{ active: index === selectedIndex }"
            @click="execute(result)"
            @mouseenter="selectedIndex = index"
          >
            <span class="command-palette-result-icon">{{ getIconSvg(result.icon) }}</span>
            <div class="command-palette-result-info">
              <span class="command-palette-result-title">{{ result.title }}</span>
              <span class="command-palette-result-desc">{{ result.description }}</span>
            </div>
            <span class="command-palette-result-category">{{ categoryLabel(result.category) }}</span>
          </div>
        </div>
        <div v-else-if="query" class="command-palette-empty">
          未找到匹配结果
        </div>
        <div v-else class="command-palette-hint">
          输入关键词搜索应用、命令和设置
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
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

const emit = defineEmits<{
  (e: 'execute', result: SearchResult): void
}>()

const router = useRouter()
const visible = ref(false)
const query = ref('')
const results = ref<SearchResult[]>([])
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

const categoryLabels: Record<string, string> = {
  navigation: '导航',
  command: '命令',
  app: '应用',
  setting: '设置',
  action: 'AI 操作',
}

function categoryLabel(cat: string) {
  return categoryLabels[cat] || cat
}

const iconCache: Record<string, string> = {
  'message-circle': '💬', layout: '📐', settings: '⚙', trash: '🗑', repeat: '🔄',
  plus: '➕', 'file-text': '📄', presentation: '📊', table: '📋', calendar: '📅',
  'check-square': '☑', 'book-open': '📖', 'sticky-note': '📝', mail: '📧',
  columns: '📋', 'git-branch': '🌳', edit: '✏', code: '💻', 'trending-up': '📈',
  cloud: '☁', clock: '⏱', users: '👥', book: '📕', music: '🎵', image: '🖼',
  film: '🎬', calculator: '🧮', monitor: '🖥', 'bar-chart': '📊', search: '🔍',
  clipboard: '📋', workflow: '🔗', sliders: '🎛', cpu: '🤖', 'share-2': '🔗',
  'flask-conical': '🧪', microscope: '🔬', languages: '🌐', 'help-circle': '❓',
  package: '📦', graduation: '🎓', pen: '✍',
}

function getIconSvg(icon: string): string {
  return iconCache[icon] || '📦'
}

let searchTimer: ReturnType<typeof setTimeout> | null = null

watch(query, (val) => {
  if (searchTimer) clearTimeout(searchTimer)
  if (!val.trim()) {
    results.value = []
    selectedIndex.value = 0
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/search', { params: { q: val, limit: 15 } })
      results.value = data.results || []
      selectedIndex.value = 0
    } catch {
      results.value = []
    }
  }, 150)
})

function moveDown() {
  if (selectedIndex.value < results.value.length - 1) selectedIndex.value++
}

function moveUp() {
  if (selectedIndex.value > 0) selectedIndex.value--
}

function executeSelected() {
  if (results.value[selectedIndex.value]) {
    execute(results.value[selectedIndex.value])
  }
}

function execute(result: SearchResult) {
  close()
  switch (result.action) {
    case 'navigate':
      if (result.action_data?.path) router.push(result.action_data.path)
      break
    case 'open_app':
      router.push({ path: '/workspace', query: { app: result.action_data?.app } })
      break
    case 'open_setting':
      router.push({ path: '/settings', query: { tab: result.action_data?.tab } })
      break
    case 'clear_chat':
      emit('execute', result)
      break
    case 'toggle_mode':
      emit('execute', result)
      break
    case 'new_session':
      emit('execute', result)
      break
    case 'deep_research':
      router.push({ path: '/workspace', query: { app: 'research' } })
      break
    case 'ai_action':
      emit('execute', result)
      break
    default:
      emit('execute', result)
  }
}

function open() {
  visible.value = true
  query.value = ''
  results.value = []
  selectedIndex.value = 0
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  query.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    if (visible.value) close()
    else open()
  }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

defineExpose({ open, close })
</script>

<style scoped>
.command-palette-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  padding-top: 15vh;
}
.command-palette {
  width: 560px;
  max-height: 420px;
  background: var(--bg-primary, #1a1a2e);
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.command-palette-input-wrap {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #2a2a4a);
  gap: 10px;
}
.command-palette-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary, #888);
  flex-shrink: 0;
}
.command-palette-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary, #e0e0e0);
  font-size: 15px;
}
.command-palette-input::placeholder {
  color: var(--text-secondary, #666);
}
.command-palette-kbd {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-secondary, #2a2a4a);
  color: var(--text-secondary, #888);
  border: 1px solid var(--border-color, #3a3a5a);
}
.command-palette-results {
  overflow-y: auto;
  flex: 1;
  padding: 4px;
}
.command-palette-result {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  gap: 12px;
  transition: background 0.15s;
}
.command-palette-result.active {
  background: var(--bg-secondary, #2a2a4a);
}
.command-palette-result-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}
.command-palette-result-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.command-palette-result-title {
  font-size: 14px;
  color: var(--text-primary, #e0e0e0);
}
.command-palette-result-desc {
  font-size: 12px;
  color: var(--text-secondary, #888);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.command-palette-result-category {
  font-size: 11px;
  color: var(--text-secondary, #666);
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-tertiary, #1e1e3a);
  flex-shrink: 0;
}
.command-palette-empty,
.command-palette-hint {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary, #666);
  font-size: 14px;
}
</style>
