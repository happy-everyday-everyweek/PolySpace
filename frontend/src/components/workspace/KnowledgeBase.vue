<template>
  <div class="knowledge-base">
    <div class="kb-header">
      <div class="search-bar">
        <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="6.5" cy="6.5" r="5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 10l4 4" stroke="currentColor" stroke-width="1.5"/></svg>
        <input v-model="searchQuery" placeholder="Search or ask AI..." @keyup.enter="onSearch" />
        <button class="ai-search-btn" @click="aiSemanticSearch" title="AI Semantic Search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </button>
      </div>
      <button class="add-btn" @click="addEntry">+ Add</button>
    </div>
    <div class="kb-content">
      <div class="kb-sidebar">
        <div class="sidebar-section">
          <h5 class="sidebar-title">Tags</h5>
          <div
            v-for="tag in tags"
            :key="tag"
            :class="['tag-item', { active: selectedTag === tag }]"
            @click="selectTag(tag)"
          >
            {{ tag }}
          </div>
        </div>
        <div class="sidebar-section">
          <h5 class="sidebar-title">AI Tools</h5>
          <button class="ai-tool-btn" @click="aiQA">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
            <span>Ask AI</span>
          </button>
          <button class="ai-tool-btn" @click="aiAutoTagAll">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82zM7 7h.01"/></svg>
            <span>Auto Tag All</span>
          </button>
          <button class="ai-tool-btn" @click="aiExtractEntities">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
            <span>Extract Entities</span>
          </button>
        </div>
      </div>
      <div class="kb-entries">
        <div v-for="entry in filteredEntries" :key="entry.entry_id" class="entry-card" @click="openEntry(entry)">
          <div class="entry-card-header">
            <h4 class="entry-title">{{ entry.title }}</h4>
            <div class="entry-ai-actions">
              <button class="mini-ai-btn" @click.stop="aiSummarizeDoc(entry)" title="AI Summarize">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="2" width="14" height="2" rx="1"/><rect x="1" y="6" width="10" height="2" rx="1"/><rect x="1" y="10" width="12" height="2" rx="1"/></svg>
              </button>
              <button class="mini-ai-btn" @click.stop="aiAutoTagEntry(entry)" title="AI Auto Tag">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82zM7 7h.01"/></svg>
              </button>
            </div>
          </div>
          <p class="entry-preview">{{ entry.content.substring(0, 150) }}...</p>
          <div class="entry-meta">
            <span class="entry-source">{{ entry.source }}</span>
            <span class="entry-date">{{ entry.updated_at }}</span>
          </div>
          <div class="entry-tags">
            <span v-for="tag in entry.tags" :key="tag" class="tag-badge">{{ tag }}</span>
          </div>
        </div>
        <div v-if="!filteredEntries.length" class="empty-state">
          <svg width="48" height="48" viewBox="0 0 48 48"><path d="M8 6h24l8 8v28a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zm4 12h20v2H12v-2zm0 8h20v2H12v-2zm0 8h12v2H12v-2z" fill="currentColor" opacity="0.3"/></svg>
          <p>No entries found</p>
        </div>
      </div>

      <div v-if="showAIPanel" class="ai-panel">
        <div class="ai-panel-header">
          <h4>AI Knowledge Assistant</h4>
          <button class="close-btn" @click="showAIPanel = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="ai-panel-content">
          <div v-if="aiLoading" class="ai-loading">
            <div class="spinner"></div>
            <span>AI is thinking...</span>
          </div>
          <div v-else-if="aiResult" class="ai-result">
            <div v-if="aiResult.results?.length" class="ai-section">
              <h5>Semantic Search Results</h5>
              <div v-for="(r, i) in aiResult.results" :key="i" class="search-result-item">
                <strong>{{ r.title }}</strong>
                <span class="relevance">{{ Math.round(r.relevance * 100) }}% match</span>
                <p class="snippet">{{ r.snippet }}</p>
              </div>
            </div>
            <div v-if="aiResult.answer" class="ai-section">
              <h5>Answer</h5>
              <p class="answer-text">{{ aiResult.answer }}</p>
              <div v-if="aiResult.sources?.length" class="answer-sources">
                <span class="sources-label">Sources:</span>
                <span v-for="(s, i) in aiResult.sources" :key="i" class="source-badge">{{ s }}</span>
              </div>
              <span v-if="aiResult.confidence" class="confidence-badge">Confidence: {{ Math.round(aiResult.confidence * 100) }}%</span>
            </div>
            <div v-if="aiResult.summary" class="ai-section">
              <h5>Summary</h5>
              <p class="summary-text">{{ aiResult.summary }}</p>
              <div v-if="aiResult.key_points?.length" class="key-points">
                <strong>Key Points:</strong>
                <ul><li v-for="(p, i) in aiResult.key_points" :key="i">{{ p }}</li></ul>
              </div>
              <div v-if="aiResult.entities?.length" class="entities">
                <strong>Entities:</strong>
                <span v-for="(e, i) in aiResult.entities" :key="i" class="entity-badge">{{ e }}</span>
              </div>
              <div v-if="aiResult.topics?.length" class="topics">
                <strong>Topics:</strong>
                <span v-for="(t, i) in aiResult.topics" :key="i" class="topic-badge">{{ t }}</span>
              </div>
            </div>
            <div v-if="aiResult.tags?.length" class="ai-section">
              <h5>Suggested Tags</h5>
              <div class="suggested-tags">
                <div v-for="(t, i) in aiResult.tags" :key="i" class="suggested-tag">
                  <span class="tag-name">{{ t.name }}</span>
                  <span class="tag-confidence">{{ Math.round(t.confidence * 100) }}%</span>
                  <span class="tag-category">{{ t.category }}</span>
                </div>
              </div>
              <button class="apply-btn" @click="applyTags">Apply Tags</button>
            </div>
            <div v-if="aiResult.entities_list?.length" class="ai-section">
              <h5>Extracted Entities</h5>
              <div v-for="(e, i) in aiResult.entities_list" :key="i" class="entity-item">
                <span class="entity-name">{{ e.name }}</span>
                <span class="entity-type">{{ e.type }}</span>
                <span class="entity-count">x{{ e.count }}</span>
              </div>
            </div>
            <div v-if="aiResult.result && !aiResult.results && !aiResult.answer && !aiResult.summary && !aiResult.tags" class="ai-section">
              <p>{{ aiResult.result }}</p>
            </div>
          </div>
          <div v-else class="ai-empty">
            <p>Search semantically, ask questions, or use AI tools to explore your knowledge base</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showEntryDetail" class="entry-detail-overlay" @click.self="showEntryDetail = false">
      <div class="entry-detail-modal">
        <div class="detail-header">
          <h3>{{ detailEntry?.title }}</h3>
          <button class="close-btn" @click="showEntryDetail = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="detail-meta">
          <span>{{ detailEntry?.source }}</span>
          <span>{{ detailEntry?.updated_at }}</span>
        </div>
        <div class="detail-content">{{ detailEntry?.content }}</div>
        <div class="detail-tags">
          <span v-for="tag in detailEntry?.tags" :key="tag" class="tag-badge">{{ tag }}</span>
        </div>
        <div class="detail-ai-actions">
          <button class="detail-ai-btn" @click="aiSummarizeDoc(detailEntry!)">Summarize</button>
          <button class="detail-ai-btn" @click="aiAutoTagEntry(detailEntry!)">Auto Tag</button>
          <button class="detail-ai-btn" @click="aiQAAboutEntry(detailEntry!)">Ask About This</button>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>{{ dialogLabel }}</h4>
        <input ref="dialogInput" v-model="dialogValue" class="dialog-input" :placeholder="dialogLabel" @keydown.enter="confirmDialog" @keydown.escape="dialogVisible = false" />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmDialog" :disabled="!dialogValue.trim()">OK</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import api from '../../utils/api'

interface KnowledgeEntry {
  entry_id: string
  title: string
  content: string
  source: string
  tags: string[]
  updated_at: string
}

const searchQuery = ref('')
const selectedTag = ref<string | null>(null)
const entries = ref<KnowledgeEntry[]>([])
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const showEntryDetail = ref(false)
const detailEntry = ref<KnowledgeEntry | null>(null)
const aiTargetEntry = ref<KnowledgeEntry | null>(null)

const tags = computed(() => {
  const tagSet = new Set<string>()
  entries.value.forEach(e => e.tags.forEach(t => tagSet.add(t)))
  return Array.from(tagSet)
})

const filteredEntries = computed(() => {
  let result = entries.value
  if (selectedTag.value) {
    result = result.filter(e => e.tags.includes(selectedTag.value!))
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e =>
      e.title.toLowerCase().includes(q) || e.content.toLowerCase().includes(q)
    )
  }
  return result
})

function onSearch() {}
function selectTag(tag: string) {
  selectedTag.value = selectedTag.value === tag ? null : tag
}

const dialogVisible = ref(false)
const dialogValue = ref('')
const dialogLabel = ref('')
const dialogCallback = ref<((val: string) => void) | null>(null)
const dialogInput = ref<HTMLInputElement | null>(null)

function showDialog(label: string, callback: (val: string) => void) {
  dialogLabel.value = label
  dialogValue.value = ''
  dialogCallback.value = callback
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function confirmDialog() {
  if (dialogCallback.value && dialogValue.value.trim()) {
    dialogCallback.value(dialogValue.value.trim())
  }
  dialogVisible.value = false
}

function addEntry() {
  showDialog('Entry title:', (title) => {
    showDialog('Entry content:', (content) => {
      entries.value.push({
        entry_id: Date.now().toString(),
        title,
        content,
        source: 'manual',
        tags: [],
        updated_at: new Date().toISOString().split('T')[0],
      })
    })
  })
}

function openEntry(entry: KnowledgeEntry) {
  detailEntry.value = entry
  showEntryDetail.value = true
}

async function aiSemanticSearch() {
  if (!searchQuery.value.trim()) return
  aiLoading.value = true
  showAIPanel.value = true
  aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/knowledge/assist', {
      action: 'semantic_search',
      params: { query: searchQuery.value, entries: entries.value.map(e => ({ id: e.entry_id, title: e.title, content: e.content })) },
    })
    aiResult.value = res.data
  } catch (e) {
    aiResult.value = { result: 'Semantic search failed.' }
  } finally {
    aiLoading.value = false
  }
}

async function aiQA() {
  showDialog('Ask a question about your knowledge base:', async (question) => {
    aiLoading.value = true
    showAIPanel.value = true
    aiResult.value = null
    try {
      const res = await api.post('/ai/workspace/knowledge/assist', {
        action: 'qa',
        params: { question, entries: entries.value.map(e => ({ id: e.entry_id, title: e.title, content: e.content })) },
      })
      aiResult.value = res.data
    } catch (e) {
      aiResult.value = { result: 'QA failed.' }
    } finally {
      aiLoading.value = false
    }
  })
}

async function aiQAAboutEntry(entry: KnowledgeEntry) {
  showDialog(`Ask about "${entry.title}":`, async (question) => {
    aiLoading.value = true
    showAIPanel.value = true
    aiResult.value = null
    try {
      const res = await api.post('/ai/workspace/knowledge/assist', {
        action: 'qa',
        params: { question, entries: [{ id: entry.entry_id, title: entry.title, content: entry.content }] },
      })
      aiResult.value = res.data
  } catch (e) {
      aiResult.value = { result: 'QA failed.' }
    } finally {
      aiLoading.value = false
    }
  })
}

async function aiSummarizeDoc(entry: KnowledgeEntry) {
  aiTargetEntry.value = entry
  aiLoading.value = true
  showAIPanel.value = true
  aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/knowledge/assist', {
      action: 'summarize_doc',
      params: { title: entry.title, content: entry.content },
    })
    aiResult.value = res.data
  } catch (e) {
    aiResult.value = { result: 'Summarization failed.' }
  } finally {
    aiLoading.value = false
  }
}

async function aiAutoTagEntry(entry: KnowledgeEntry) {
  aiTargetEntry.value = entry
  aiLoading.value = true
  showAIPanel.value = true
  aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/knowledge/assist', {
      action: 'auto_tag',
      params: { title: entry.title, content: entry.content, existing_tags: tags.value },
    })
    aiResult.value = res.data
  } catch (e) {
    aiResult.value = { result: 'Auto-tagging failed.' }
  } finally {
    aiLoading.value = false
  }
}

async function aiAutoTagAll() {
  if (!entries.value.length) return
  aiLoading.value = true
  showAIPanel.value = true
  aiResult.value = null
  try {
    const allContent = entries.value.map(e => ({ id: e.entry_id, title: e.title, content: e.content.substring(0, 200) }))
    const res = await api.post('/ai/workspace/knowledge/assist', {
      action: 'auto_tag',
      params: { entries: allContent, existing_tags: tags.value },
    })
    aiResult.value = res.data
  } catch (e) {
    aiResult.value = { result: 'Auto-tagging failed.' }
  } finally {
    aiLoading.value = false
  }
}

async function aiExtractEntities() {
  if (!entries.value.length) return
  aiLoading.value = true
  showAIPanel.value = true
  aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/knowledge/assist', {
      action: 'extract_entities',
      params: { entries: entries.value.map(e => ({ id: e.entry_id, title: e.title, content: e.content.substring(0, 300) })) },
    })
    aiResult.value = res.data
  } catch (e) {
    aiResult.value = { result: 'Entity extraction failed.' }
  } finally {
    aiLoading.value = false
  }
}

function applyTags() {
  if (!aiResult.value?.tags || !aiTargetEntry.value) return
  const newTags = aiResult.value.tags
    .filter((t: any) => t.confidence > 0.5)
    .map((t: any) => t.name)
  const existing = new Set(aiTargetEntry.value.tags)
  newTags.forEach((t: string) => existing.add(t))
  aiTargetEntry.value.tags = Array.from(existing)
  showAIPanel.value = false
}
</script>

<style scoped>
.knowledge-base { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.kb-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.search-bar { flex: 1; display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 8px; background: var(--bg-secondary); color: var(--text-tertiary); border: 1px solid var(--border-color); }
.search-bar input { flex: 1; border: none; outline: none; background: transparent; color: var(--text-primary); font-size: 14px; }
.search-bar input::placeholder { color: var(--text-tertiary); }
.ai-search-btn { background: none; border: none; color: var(--ws-accent); cursor: pointer; padding: 2px; display: flex; }
.ai-search-btn:hover { color: var(--ws-accent-soft); }
.add-btn { padding: 6px 12px; border-radius: var(--radius-sm); background: var(--ws-accent); color: var(--bg-primary); font-size: var(--font-size-sm); border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.kb-content { flex: 1; display: flex; overflow: hidden; }
.kb-sidebar { width: 180px; padding: 12px; border-right: 1px solid var(--border-color); overflow-y: auto; background: var(--bg-primary); }
.sidebar-section { margin-bottom: 16px; }
.sidebar-title { font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 8px; }
.tag-item { padding: 6px 10px; border-radius: 4px; font-size: 13px; color: var(--text-secondary); cursor: pointer; margin-bottom: 2px; }
.tag-item:hover { background: var(--bg-secondary); }
.tag-item.active { background: var(--ws-accent); color: var(--bg-primary); }
.ai-tool-btn { display: flex; align-items: center; gap: 6px; width: 100%; padding: 6px 10px; border-radius: 4px; font-size: 12px; color: var(--ws-accent); background: transparent; border: 1px solid var(--border-color); cursor: pointer; margin-bottom: 4px; transition: all 0.15s; }
.ai-tool-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.kb-entries { flex: 1; padding: 12px; overflow-y: auto; }
.entry-card { padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s; background: var(--bg-secondary); }
.entry-card:hover { border-color: var(--ws-accent); }
.entry-card-header { display: flex; align-items: center; justify-content: space-between; }
.entry-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 0; }
.entry-ai-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.15s; }
.entry-card:hover .entry-ai-actions { opacity: 1; }
.mini-ai-btn { background: none; border: none; color: var(--ws-accent); cursor: pointer; padding: 2px; display: flex; }
.mini-ai-btn:hover { color: var(--ws-accent-soft); }
.entry-preview { font-size: 13px; color: var(--text-tertiary); line-height: 1.5; margin: 6px 0; }
.entry-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-tertiary); margin-bottom: 6px; }
.entry-tags { display: flex; gap: 4px; }
.tag-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; background: var(--border-color); color: var(--ws-accent-soft); }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--text-tertiary); }
.empty-state p { margin-top: 12px; font-size: 14px; }
.ai-panel { width: 340px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.ai-result { color: var(--text-primary); }
.search-result-item { padding: 8px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 6px; }
.search-result-item strong { font-size: 13px; color: var(--ws-accent-soft); }
.relevance { font-size: 11px; color: var(--ws-success); margin-left: 8px; }
.snippet { font-size: 12px; color: var(--text-secondary); margin: 4px 0 0; }
.answer-text { font-size: 14px; line-height: 1.6; color: var(--text-primary); padding: 10px; background: var(--bg-secondary); border-radius: 6px; }
.answer-sources { margin-top: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sources-label { font-size: 11px; color: var(--text-tertiary); }
.source-badge { padding: 2px 8px; background: var(--border-color); border-radius: 10px; font-size: 11px; color: var(--ws-accent-soft); }
.confidence-badge { display: inline-block; margin-top: 6px; padding: 2px 8px; background: var(--bg-tertiary); border-radius: var(--radius-full); font-size: var(--font-size-xs); color: var(--ws-success); }
.summary-text { font-size: 13px; line-height: 1.6; color: var(--text-secondary); padding: 8px; background: var(--bg-secondary); border-radius: 6px; }
.key-points { margin-top: 8px; font-size: 12px; }
.key-points strong { color: var(--ws-accent-soft); }
.key-points ul { margin: 4px 0; padding-left: 16px; color: var(--text-secondary); }
.entities { margin-top: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; }
.entities strong { color: var(--ws-accent-soft); }
.entity-badge { padding: 2px 8px; background: var(--border-color); border-radius: 10px; font-size: 11px; color: var(--text-secondary); }
.topics { margin-top: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; }
.topics strong { color: var(--ws-accent-soft); }
.topic-badge { padding: 2px 8px; background: var(--bg-tertiary); border-radius: var(--radius-full); font-size: var(--font-size-xs); color: var(--ws-info); }
.suggested-tags { display: flex; flex-direction: column; gap: 4px; }
.suggested-tag { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: var(--bg-secondary); border-radius: 4px; font-size: 12px; }
.tag-name { color: var(--ws-accent-soft); flex: 1; }
.tag-confidence { color: var(--ws-success); font-size: 11px; }
.tag-category { color: var(--text-tertiary); font-size: 10px; }
.apply-btn { width: 100%; padding: 8px; background: var(--ws-accent); color: var(--bg-primary); border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); margin-top: 8px; }
.apply-btn:hover { background: var(--ws-accent-hover); }
.entity-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 4px; font-size: 12px; }
.entity-name { color: var(--text-primary); flex: 1; }
.entity-type { background: var(--ws-accent); color: var(--bg-primary); padding: 1px 6px; border-radius: var(--radius-sm); font-size: var(--font-size-xs); }
.entity-count { color: var(--text-tertiary); font-size: 11px; }
.ai-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-tertiary); font-size: 13px; }
.entry-detail-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.entry-detail-modal { background: var(--bg-secondary); border-radius: 12px; padding: 24px; width: 600px; max-height: 80vh; display: flex; flex-direction: column; border: 1px solid var(--border-color); }
.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.detail-header h3 { margin: 0; font-size: 18px; color: var(--text-primary); }
.detail-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px; }
.detail-content { flex: 1; overflow-y: auto; font-size: 14px; line-height: 1.8; color: var(--text-secondary); margin-bottom: 12px; }
.detail-tags { display: flex; gap: 4px; margin-bottom: 12px; }
.detail-ai-actions { display: flex; gap: 8px; }
.detail-ai-btn { padding: 6px 14px; background: var(--border-color); color: var(--ws-accent-soft); border: 1px solid var(--border-color); border-radius: 6px; cursor: pointer; font-size: 12px; }
.detail-ai-btn:hover { background: var(--border-color); border-color: var(--ws-accent); }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 200; }
.dialog-box { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; min-width: 360px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px; }
.dialog-box h4 { margin: 0; font-size: 15px; color: var(--text-primary); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--input-bg); color: var(--text-primary); font-size: 14px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 3px var(--ws-accent-light); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.dialog-cancel { padding: 6px 16px; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.dialog-cancel:hover { background: var(--border-color); }
.dialog-confirm { padding: 6px 16px; border-radius: var(--radius-md); background: var(--ws-accent); color: var(--bg-primary); border: none; cursor: pointer; font-size: var(--font-size-sm); }
.dialog-confirm:hover { background: var(--ws-accent-hover); }
.dialog-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
