<template>
  <div class="image-view">
    <div class="image-header">
      <h3 class="section-label">Image Editor</h3>
      <button class="add-btn" @click="loadImage">Open Image</button>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiDescribe">AI Describe</button>
        <button class="ai-header-btn" @click="aiSuggestEdit">AI Edit</button>
        <button class="ai-header-btn" @click="aiGeneratePrompt">AI Prompt</button>
      </div>
    </div>
    <div class="image-body">
      <div class="image-canvas">
        <div v-if="imageUrl" class="image-preview">
          <img :src="imageUrl" :style="filterStyle" alt="Preview" />
        </div>
        <div v-else class="image-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
          <p>Open an image to edit</p>
        </div>
      </div>
      <div class="image-sidebar">
        <h4 class="sidebar-title">Adjustments</h4>
        <div class="filter-group">
          <label>Brightness</label><input type="range" min="0" max="200" v-model.number="filters.brightness" /><span>{{ filters.brightness }}%</span>
        </div>
        <div class="filter-group">
          <label>Contrast</label><input type="range" min="0" max="200" v-model.number="filters.contrast" /><span>{{ filters.contrast }}%</span>
        </div>
        <div class="filter-group">
          <label>Saturate</label><input type="range" min="0" max="200" v-model.number="filters.saturate" /><span>{{ filters.saturate }}%</span>
        </div>
        <div class="filter-group">
          <label>Blur</label><input type="range" min="0" max="20" v-model.number="filters.blur" /><span>{{ filters.blur }}px</span>
        </div>
        <div class="filter-group">
          <label>Grayscale</label><input type="range" min="0" max="100" v-model.number="filters.grayscale" /><span>{{ filters.grayscale }}%</span>
        </div>
        <div class="filter-group">
          <label>Sepia</label><input type="range" min="0" max="100" v-model.number="filters.sepia" /><span>{{ filters.sepia }}%</span>
        </div>
        <button class="reset-btn" @click="resetFilters">Reset</button>
      </div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Image Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is analyzing...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.description" class="ai-section"><h5>Description</h5><p>{{ aiResult.description }}</p></div>
          <div v-if="aiResult.edits?.length" class="ai-section"><h5>Suggested Edits</h5><div v-for="(e, i) in aiResult.edits" :key="i" class="edit-item">{{ e.type }}: {{ e.description }}</div></div>
          <div v-if="aiResult.prompt" class="ai-section"><h5>Generation Prompt</h5><p class="prompt-text">{{ aiResult.prompt }}</p></div>
          <div v-if="aiResult.result && !aiResult.description && !aiResult.edits && !aiResult.prompt" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>Generate Image</h4>
        <input ref="dialogInput" v-model="dialogValue" class="dialog-input" placeholder="Describe the image..." @keydown.enter="confirmDialog" @keydown.escape="dialogVisible = false" />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmDialog" :disabled="!dialogValue.trim()">Generate</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import api from '../../utils/api'
import { useAppSettings } from '@/composables/useAppSettings'

const imageDefaults = useAppSettings('image').settings.value

const imageUrl = ref('')
const filters = ref({ brightness: imageDefaults.brightness, contrast: imageDefaults.contrast, saturate: imageDefaults.saturate, blur: imageDefaults.blur, grayscale: imageDefaults.grayscale, sepia: imageDefaults.sepia })
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

const filterStyle = computed(() => ({
  filter: `brightness(${filters.value.brightness}%) contrast(${filters.value.contrast}%) saturate(${filters.value.saturate}%) blur(${filters.value.blur}px) grayscale(${filters.value.grayscale}%) sepia(${filters.value.sepia}%)`
}))

function loadImage() {
  const input = document.createElement('input')
  input.type = 'file'; input.accept = 'image/*'
  input.onchange = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) { const reader = new FileReader(); reader.onload = (ev) => { imageUrl.value = ev.target?.result as string }; reader.readAsDataURL(file) }
  }
  input.click()
}

function resetFilters() { filters.value = { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0, sepia: 0 } }

async function aiDescribe() {
  if (!imageUrl.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/image/assist', { action: 'describe', params: { has_image: true, filters: filters.value } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Description failed.' } }
  finally { aiLoading.value = false }
}

async function aiSuggestEdit() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/image/assist', { action: 'suggest_edit', params: { filters: filters.value } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Edit suggestion failed.' } }
  finally { aiLoading.value = false }
}

const dialogVisible = ref(false)
const dialogValue = ref('')
const dialogCallback = ref<((val: string) => void) | null>(null)
const dialogInput = ref<HTMLInputElement | null>(null)

function showDialog(_label: string, callback: (val: string) => void) {
  dialogValue.value = ''; dialogCallback.value = callback
  dialogVisible.value = true; nextTick(() => dialogInput.value?.focus())
}

function confirmDialog() {
  if (dialogCallback.value && dialogValue.value.trim()) dialogCallback.value(dialogValue.value.trim())
  dialogVisible.value = false
}

async function aiGeneratePrompt() {
  showDialog('Describe the image you want to generate:', async (desc) => {
    aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
    try { const res = await api.post('/ai/workspace/image/assist', { action: 'generate_prompt', params: { description: desc } }); aiResult.value = res.data }
    catch { aiResult.value = { result: 'Prompt generation failed.' } }
    finally { aiLoading.value = false }
  })
}
</script>

<style scoped>
.image-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.image-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.add-btn { padding: 6px 12px; border-radius: var(--radius-sm); background: var(--ws-accent); color: var(--bg-primary); font-size: var(--font-size-sm); border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.image-body { flex: 1; display: flex; overflow: hidden; }
.image-canvas { flex: 1; display: flex; align-items: center; justify-content: center; padding: 16px; }
.image-preview { max-width: 100%; max-height: 100%; }
.image-preview img { max-width: 100%; max-height: 500px; border-radius: 8px; }
.image-empty { display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-tertiary); }
.image-sidebar { width: 220px; border-left: 1px solid var(--border-color); padding: 16px; overflow-y: auto; }
.sidebar-title { font-size: 13px; color: var(--text-tertiary); margin: 0 0 12px; text-transform: uppercase; }
.filter-group { margin-bottom: 12px; }
.filter-group label { font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px; }
.filter-group input[type="range"] { width: 100%; accent-color: var(--ws-accent); }
.filter-group span { font-size: 11px; color: var(--text-tertiary); }
.reset-btn { width: 100%; padding: 8px; background: var(--border-color); color: var(--text-primary); border: none; border-radius: 5px; cursor: pointer; font-size: 12px; margin-top: 8px; }
.reset-btn:hover { background: var(--border-color); }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.edit-item { font-size: 12px; color: var(--text-secondary); padding: 6px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 4px; }
.prompt-text { font-size: 13px; color: var(--ws-accent-soft); padding: 8px; background: var(--bg-secondary); border-radius: 6px; font-family: monospace; }
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
