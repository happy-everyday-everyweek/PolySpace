<template>
  <div class="video-toolbar">
    <div class="toolbar-group">
      <button class="tool-btn" @click="$emit('import')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
        <span>Import</span>
      </button>
      <button class="tool-btn" @click="$emit('split')" :disabled="!hasSelection">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>
        <span>Split</span>
      </button>
      <button class="tool-btn" @click="$emit('delete')" :disabled="!hasSelection">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M5 6v14a2 2 0 002 2h10a2 2 0 002-2V6"/></svg>
        <span>Delete</span>
      </button>
      <div class="toolbar-divider"></div>
      <button class="tool-btn" @click="$emit('undo')" :disabled="!canUndo">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10h10a5 5 0 015 5v2M3 10l5-5M3 10l5 5"/></svg>
        <span>Undo</span>
      </button>
      <button class="tool-btn" @click="$emit('redo')" :disabled="!canRedo">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10H11a5 5 0 00-5 5v2M21 10l-5-5M21 10l-5 5"/></svg>
        <span>Redo</span>
      </button>
      <div class="toolbar-divider"></div>
      <button class="tool-btn" @click="$emit('export')" :disabled="!hasClips">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        <span>Export</span>
      </button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group ai-group">
      <button class="tool-btn ai-btn" @click="$emit('ai-analyze')" :disabled="!hasClips">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        <span>AI Analyze</span>
      </button>
      <button class="tool-btn ai-btn" @click="$emit('ai-auto-edit')" :disabled="!hasClips">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>
        <span>AI Auto Edit</span>
      </button>
      <button class="tool-btn ai-btn" @click="$emit('ai-style')" :disabled="!hasClips">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
        <span>AI Style</span>
      </button>
      <button class="tool-btn ai-btn" @click="$emit('ai-subtitles')" :disabled="!hasClips">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 12h4M14 12h4M6 16h12"/></svg>
        <span>AI Subtitles</span>
      </button>
      <button class="tool-btn ai-btn" @click="$emit('ai-chat')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        <span>AI Chat</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  hasClips: boolean
  hasSelection: boolean
  canUndo: boolean
  canRedo: boolean
}>()

defineEmits<{
  import: []
  split: []
  delete: []
  undo: []
  redo: []
  export: []
  'ai-analyze': []
  'ai-auto-edit': []
  'ai-style': []
  'ai-subtitles': []
  'ai-chat': []
}>()
</script>

<style scoped>
.video-toolbar { display: flex; gap: 4px; padding: 6px 12px; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary); align-items: center; flex-wrap: wrap; }
.toolbar-group { display: flex; gap: 2px; }
.toolbar-divider { width: 1px; height: 24px; background: var(--border-color); margin: 0 8px; }
.tool-btn { display: flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: 5px; font-size: 12px; color: var(--text-secondary); background: transparent; border: 1px solid transparent; cursor: pointer; transition: all 0.15s; }
.tool-btn:hover:not(:disabled) { background: var(--border-color); color: var(--text-primary); border-color: var(--border-color); }
.tool-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.ai-btn { color: var(--primary); }
.ai-btn:hover:not(:disabled) { background: var(--primary-light); color: var(--text-primary); border-color: var(--primary); }
.ai-group { margin-left: auto; }
</style>
