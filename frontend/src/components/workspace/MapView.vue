<template>
  <div class="map-view">
    <div class="map-header">
      <div class="search-bar">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input
          v-model="searchQuery"
          placeholder="搜索地点..."
          @keydown.enter="searchLocation"
        />
        <button class="search-btn" @click="searchLocation">搜索</button>
      </div>
      <div class="map-controls">
        <button class="ctrl-btn" @click="zoomIn" title="放大">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        </button>
        <button class="ctrl-btn" @click="zoomOut" title="缩小">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg>
        </button>
        <button class="ctrl-btn" @click="resetView" title="重置视图">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 109-9 9.75 9.75 0 00-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
        </button>
      </div>
    </div>
    <div class="map-container" ref="mapContainer">
      <div class="map-placeholder">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
        <p>地图服务</p>
        <p class="hint">搜索地点或输入坐标开始使用</p>
      </div>
    </div>
    <div v-if="searchResults.length" class="search-results">
      <div
        v-for="result in searchResults"
        :key="result.id"
        class="result-item"
        @click="selectLocation(result)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
        <div class="result-info">
          <span class="result-name">{{ result.name }}</span>
          <span class="result-detail">{{ result.address }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'

interface MapResult {
  id: string
  name: string
  address: string
  latitude: number
  longitude: number
}

const searchQuery = ref('')
const searchResults = ref<MapResult[]>([])
const mapContainer = ref<HTMLElement | null>(null)

async function searchLocation() {
  if (!searchQuery.value.trim()) return
  try {
    const res = await api.post('/ai/workspace/map/search', {
      query: searchQuery.value,
      limit: 10,
    })
    searchResults.value = res.data.results || []
  } catch {
    searchResults.value = []
  }
}

function selectLocation(result: MapResult) {
  searchResults.value = []
  searchQuery.value = result.name
}

function zoomIn() {}
function zoomOut() {}
function resetView() {
  searchQuery.value = ''
  searchResults.value = []
}
</script>

<style scoped>
.map-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.map-header {
  display: flex;
  align-items: center;
  gap: 8px;
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

.map-controls {
  display: flex;
  gap: 2px;
}

.ctrl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
}

.ctrl-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary-color);
}

.map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  gap: 8px;
}

.map-placeholder p {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.map-placeholder .hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.search-results {
  position: absolute;
  top: 52px;
  left: 16px;
  width: 320px;
  max-height: 300px;
  overflow-y: auto;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 50;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: var(--bg-secondary);
}

.result-item svg {
  color: var(--primary-color);
  flex-shrink: 0;
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.result-detail {
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>
