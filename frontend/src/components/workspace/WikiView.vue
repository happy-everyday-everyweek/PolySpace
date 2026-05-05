<template>
  <div class="wiki-view">
    <div class="wiki-header">
      <div class="search-bar">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input
          v-model="searchQuery"
          placeholder="搜索百科词条..."
          @keydown.enter="searchWiki"
        />
        <button class="search-btn" @click="searchWiki">搜索</button>
      </div>
    </div>

    <div class="wiki-content">
      <div v-if="loading" class="wiki-loading">
        <div class="spinner"></div>
        <span>搜索中...</span>
      </div>

      <div v-else-if="currentArticle" class="article-view">
        <button class="back-btn" @click="currentArticle = null">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          返回搜索结果
        </button>
        <h1 class="article-title">{{ currentArticle.title }}</h1>
        <div class="article-meta" v-if="currentArticle.url">
          <a :href="currentArticle.url" target="_blank" class="source-link">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            查看原文
          </a>
        </div>
        <div class="article-body" v-html="currentArticle.content"></div>
      </div>

      <div v-else-if="searchResults.length" class="results-list">
        <div
          v-for="result in searchResults"
          :key="result.id"
          class="result-card"
          @click="openArticle(result)"
        >
          <h3 class="result-title">{{ result.title }}</h3>
          <p class="result-snippet">{{ result.snippet }}</p>
        </div>
      </div>

      <div v-else class="wiki-empty">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>
        <p>百科全书</p>
        <p class="hint">搜索任何主题，获取百科知识</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'

interface WikiSearchResult {
  id: string
  title: string
  snippet: string
  url?: string
}

interface WikiArticle {
  id: string
  title: string
  content: string
  url?: string
}

const searchQuery = ref('')
const searchResults = ref<WikiSearchResult[]>([])
const currentArticle = ref<WikiArticle | null>(null)
const loading = ref(false)

async function searchWiki() {
  if (!searchQuery.value.trim()) return
  loading.value = true
  currentArticle.value = null
  try {
    const res = await api.post('/ai/workspace/wiki/search', {
      query: searchQuery.value,
      limit: 10,
      language: 'zh',
    })
    searchResults.value = res.data.results || []
  } catch {
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

async function openArticle(result: WikiSearchResult) {
  loading.value = true
  try {
    const res = await api.post('/ai/workspace/wiki/article', {
      id: result.id,
      title: result.title,
    })
    currentArticle.value = res.data
  } catch {
    currentArticle.value = {
      id: result.id,
      title: result.title,
      content: result.snippet,
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wiki-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.wiki-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 6px 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.search-bar svg {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-bar input {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.search-bar input::placeholder {
  color: var(--text-tertiary);
}

.search-btn {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  border: none;
}

.search-btn:hover {
  opacity: 0.9;
}

.wiki-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.wiki-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px;
  color: var(--text-tertiary);
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.article-view {
  max-width: 720px;
  margin: 0 auto;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  margin-bottom: 16px;
}

.back-btn:hover {
  color: var(--primary-color);
}

.article-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
  line-height: 1.3;
}

.article-meta {
  margin-bottom: 16px;
}

.source-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--primary-color);
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.article-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
}

.article-body :deep(h2) {
  font-size: 18px;
  margin-top: 24px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 4px;
}

.article-body :deep(h3) {
  font-size: 15px;
  margin-top: 16px;
  margin-bottom: 6px;
}

.article-body :deep(p) {
  margin: 8px 0;
}

.article-body :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
}

.article-body :deep(a:hover) {
  text-decoration: underline;
}

.results-list {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-card {
  padding: 14px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.result-card:hover {
  border-color: var(--primary-color);
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.result-snippet {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

.wiki-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  gap: 8px;
}

.wiki-empty p {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.wiki-empty .hint {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
