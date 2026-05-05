<template>
  <div class="reader-view">
    <div class="reader-header">
      <h3 class="section-label">Reader</h3>
      <button class="add-btn" @click="addArticle">+ Add URL</button>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiDigest">AI Digest</button>
        <button class="ai-header-btn" @click="aiSummarize">AI Summary</button>
      </div>
    </div>
    <div class="reader-body">
      <div class="reader-sidebar">
        <div v-for="a in articles" :key="a.id" :class="['article-item', { active: activeId === a.id }]" @click="activeId = a.id">
          <span class="article-title">{{ a.title }}</span>
          <span class="article-source">{{ a.source }}</span>
          <div class="article-meta">
            <span class="article-category">{{ a.category }}</span>
            <span class="article-progress">{{ Math.round(a.readProgress * 100) }}%</span>
          </div>
        </div>
      </div>
      <div class="reader-content" v-if="activeArticle">
        <h2 class="reader-title">{{ activeArticle.title }}</h2>
        <div class="reader-url">{{ activeArticle.url }}</div>
        <div class="reader-text">{{ activeArticle.content || activeArticle.summary || 'No content available' }}</div>
      </div>
      <div v-else class="reader-empty">Add an article URL to start reading</div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Reader Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is reading...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.digest?.length" class="ai-section"><h5>Daily Digest</h5><div v-for="d in aiResult.digest" :key="d.title" class="digest-item"><span class="digest-title">{{ d.title }}</span><span class="digest-summary">{{ d.summary }}</span></div></div>
          <div v-if="aiResult.summary" class="ai-section"><h5>Summary</h5><p class="summary-text">{{ aiResult.summary }}</p></div>
          <div v-if="aiResult.result && !aiResult.digest && !aiResult.summary" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>Add Article</h4>
        <input ref="dialogInput" v-model="dialogUrl" class="dialog-input" placeholder="Article URL" @keydown.enter="confirmAddArticle" @keydown.escape="dialogVisible = false" />
        <input v-model="dialogTitle" class="dialog-input" placeholder="Title (optional)" @keydown.enter="confirmAddArticle" />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmAddArticle" :disabled="!dialogUrl.trim()">Add</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import api from '../../utils/api'
import type { ReaderArticle } from '../../types/workspace'

const articles = ref<ReaderArticle[]>([])
const activeId = ref<string | null>(null)
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

const activeArticle = computed(() => articles.value.find(a => a.id === activeId.value) || null)

function genId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }

const dialogVisible = ref(false)
const dialogUrl = ref('')
const dialogTitle = ref('')
const dialogInput = ref<HTMLInputElement | null>(null)

function addArticle() {
  dialogUrl.value = ''
  dialogTitle.value = ''
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function confirmAddArticle() {
  if (!dialogUrl.value.trim()) return
  try {
    articles.value.unshift({ id: genId(), title: dialogTitle.value.trim() || dialogUrl.value.trim(), url: dialogUrl.value.trim(), source: new URL(dialogUrl.value.trim()).hostname, category: 'general', savedAt: Date.now(), readProgress: 0 })
    activeId.value = articles.value[0].id
  } catch { return }
  dialogVisible.value = false
}

async function aiDigest() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/reader/assist', { action: 'digest', params: { articles: articles.value.slice(0, 10).map(a => ({ title: a.title, url: a.url, category: a.category })) } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Digest failed.' } }
  finally { aiLoading.value = false }
}

async function aiSummarize() {
  if (!activeArticle.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/reader/assist', { action: 'summarize_article', params: { title: activeArticle.value.title, url: activeArticle.value.url } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Summary failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.reader-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.reader-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.add-btn { padding: 6px 12px; border-radius: 6px; background: var(--ws-accent); color: #fff; font-size: 13px; border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.reader-body { flex: 1; display: flex; overflow: hidden; }
.reader-sidebar { width: 240px; border-right: 1px solid var(--border-color); overflow-y: auto; padding: 8px; }
.article-item { padding: 10px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; }
.article-item:hover { background: var(--bg-secondary); }
.article-item.active { background: var(--ws-accent-light); }
.article-title { font-size: 13px; color: var(--text-primary); display: block; }
.article-source { font-size: 11px; color: var(--text-tertiary); }
.article-meta { display: flex; justify-content: space-between; margin-top: 4px; }
.article-category { font-size: 10px; padding: 1px 6px; background: var(--border-color); color: var(--ws-accent-soft); border-radius: 3px; }
.article-progress { font-size: 10px; color: var(--ws-success); }
.reader-content { flex: 1; padding: 24px; overflow-y: auto; }
.reader-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin: 0 0 8px; }
.reader-url { font-size: 12px; color: var(--ws-accent); margin-bottom: 16px; }
.reader-text { font-size: 14px; line-height: 1.8; color: var(--text-secondary); }
.reader-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: #fff; }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.digest-item { padding: 8px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 4px; }
.digest-title { font-size: 13px; color: var(--ws-accent-soft); display: block; }
.digest-summary { font-size: 12px; color: var(--text-secondary); }
.summary-text { font-size: 13px; line-height: 1.6; color: var(--text-secondary); padding: 8px; background: var(--bg-secondary); border-radius: 6px; }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.dialog-box { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; min-width: 360px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px; }
.dialog-box h4 { margin: 0; font-size: 15px; color: var(--text-primary); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--input-bg); color: var(--text-primary); font-size: 14px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 3px var(--ws-accent-light); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.dialog-cancel { padding: 6px 16px; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.dialog-cancel:hover { background: var(--border-color); }
.dialog-confirm { padding: 6px 16px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; border: none; cursor: pointer; font-size: 13px; }
.dialog-confirm:hover { background: var(--ws-accent-hover); }
.dialog-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
