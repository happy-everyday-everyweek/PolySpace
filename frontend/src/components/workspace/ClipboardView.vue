<template>
  <div class="clipboard-view">
    <div class="clipboard-header">
      <h2>智能剪贴板</h2>
      <div class="clipboard-actions">
        <button class="clipboard-btn" @click="pasteFromSystem">粘贴</button>
        <button class="clipboard-btn danger" @click="clearAll">清空</button>
      </div>
    </div>
    <div class="clipboard-filters">
      <button
        v-for="f in filters"
        :key="f.value"
        class="filter-btn"
        :class="{ active: activeFilter === f.value }"
        @click="activeFilter = f.value"
      >
        {{ f.label }}
      </button>
    </div>
    <div class="clipboard-list">
      <div v-for="item in filteredItems" :key="item.id" class="clipboard-item" :class="{ sensitive: item.is_sensitive }">
        <div class="item-header">
          <span class="item-type-badge" :class="'type-' + item.content_type">{{ typeLabels[item.content_type] || item.content_type }}</span>
          <span class="item-time">{{ formatTime(item.created_at) }}</span>
          <button class="item-delete-btn" @click="deleteItem(item.id)">&times;</button>
        </div>
        <div class="item-content">{{ item.content }}</div>
        <div v-if="item.is_sensitive" class="item-sensitive-warn">检测到敏感内容，已隐藏操作建议</div>
        <div v-if="item.suggestions.length && !item.is_sensitive" class="item-suggestions">
          <button
            v-for="(sug, i) in item.suggestions"
            :key="i"
            class="suggestion-btn"
            @click="executeSuggestion(sug)"
          >
            {{ sug.label }}
          </button>
        </div>
      </div>
      <div v-if="!filteredItems.length" class="clipboard-empty">
        暂无剪贴板记录
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'

interface ClipboardItem {
  id: string
  content: string
  content_type: string
  language?: string
  is_sensitive: boolean
  suggestions: { action: string; label: string; data: Record<string, string> }[]
  created_at: string
}

const items = ref<ClipboardItem[]>([])
const activeFilter = ref('all')

const filters = [
  { label: '全部', value: 'all' },
  { label: '文本', value: 'text' },
  { label: '链接', value: 'url' },
  { label: '代码', value: 'code' },
  { label: '邮箱', value: 'email' },
  { label: '电话', value: 'phone' },
]

const typeLabels: Record<string, string> = {
  text: '文本', url: '链接', email: '邮箱', phone: '电话', code: '代码', address: '地址', image: '图片',
}

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter(i => i.content_type === activeFilter.value)
})

function formatTime(iso: string) {
  try {
    const d = new Date(iso)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return ''
  }
}

async function fetchItems() {
  try {
    const { data } = await api.get('/clipboard')
    items.value = data.items || []
  } catch { /* ignore */ }
}

async function pasteFromSystem() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) {
      await api.post('/clipboard', { content: text })
      await fetchItems()
    }
  } catch { /* ignore */ }
}

async function deleteItem(id: string) {
  try {
    await api.delete(`/clipboard/${id}`)
    await fetchItems()
  } catch { /* ignore */ }
}

async function clearAll() {
  try {
    await api.delete('/clipboard')
    items.value = []
  } catch { /* ignore */ }
}

function executeSuggestion(sug: { action: string; label: string; data: Record<string, string> }) {
  switch (sug.action) {
    case 'open_url':
      window.open(sug.data.url, '_blank')
      break
    case 'create_memo':
    case 'create_todo':
    case 'translate':
    case 'summarize':
    case 'explain_code':
      console.log('Execute suggestion:', sug.action, sug.data)
      break
    default:
      break
  }
}

onMounted(fetchItems)
</script>

<style scoped>
.clipboard-view {
  padding: 20px;
  max-width: 700px;
  margin: 0 auto;
}
.clipboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.clipboard-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0;
}
.clipboard-actions {
  display: flex;
  gap: 8px;
}
.clipboard-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  cursor: pointer;
}
.clipboard-btn.danger { color: #f87171; }
.clipboard-btn:hover { opacity: 0.9; }
.clipboard-filters {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.filter-btn {
  padding: 4px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 14px;
  background: transparent;
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 12px;
  cursor: pointer;
}
.filter-btn.active {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.clipboard-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.clipboard-item {
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  padding: 12px;
  background: var(--bg-primary, var(--bg-secondary));
}
.clipboard-item.sensitive {
  border-color: #7f1d1d;
}
.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.item-type-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-secondary, var(--text-tertiary));
}
.type-url { background: #1e3a5f; color: #60a5fa; }
.type-code { background: #1e3a2f; color: #4ade80; }
.type-email { background: #3a2f1e; color: #fbbf24; }
.type-phone { background: #3a1e2f; color: #f472b6; }
.item-time {
  font-size: 11px;
  color: var(--text-secondary, var(--text-tertiary));
  flex: 1;
}
.item-delete-btn {
  background: none;
  border: none;
  color: var(--text-secondary, var(--text-tertiary));
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
}
.item-delete-btn:hover { color: #f87171; }
.item-content {
  font-size: 13px;
  color: var(--text-primary, var(--text-primary));
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 100px;
  overflow: hidden;
}
.item-sensitive-warn {
  font-size: 12px;
  color: #f87171;
  margin-top: 8px;
}
.item-suggestions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.suggestion-btn {
  padding: 3px 10px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 4px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-secondary, #ccc);
  font-size: 12px;
  cursor: pointer;
}
.suggestion-btn:hover {
  background: var(--accent-color, #6366f1);
  color: #fff;
  border-color: var(--accent-color, #6366f1);
}
.clipboard-empty {
  text-align: center;
  color: var(--text-secondary, var(--text-tertiary));
  padding: 40px;
  font-size: 14px;
}
</style>
