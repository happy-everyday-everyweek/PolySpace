<template>
  <div class="export-dialog" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <div class="export-content">
      <div class="export-header">
        <div class="export-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          导出视频
        </div>
        <button class="export-close" @click="$emit('close')" title="关闭">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="export-form">
        <div class="form-row">
          <label>格式</label>
          <select v-model="options.format" class="form-input">
            <option value="mp4">MP4 (H.264)</option>
            <option value="webm">WebM</option>
            <option value="mov">MOV</option>
            <option value="gif">GIF</option>
          </select>
        </div>
        <div class="form-row">
          <label>质量</label>
          <select v-model="options.quality" class="form-input">
            <option value="low">低 (360p)</option>
            <option value="medium">中 (720p)</option>
            <option value="high">高 (1080p)</option>
            <option value="ultra">超高 (4K)</option>
          </select>
        </div>
        <div class="form-row">
          <label>分辨率</label>
          <select v-model="options.resolution" class="form-input">
            <option value="640x360">640x360</option>
            <option value="1280x720">1280x720</option>
            <option value="1920x1080">1920x1080</option>
            <option value="3840x2160">3840x2160</option>
          </select>
        </div>
        <div class="form-row">
          <label>帧率</label>
          <select v-model="options.fps" class="form-input">
            <option :value="24">24 fps</option>
            <option :value="30">30 fps</option>
            <option :value="60">60 fps</option>
          </select>
        </div>
        <div class="form-row form-check">
          <input type="checkbox" v-model="options.includeSubtitles" id="burnSubs" />
          <label for="burnSubs">烧录字幕</label>
        </div>
      </div>
      <div class="export-footer">
        <button class="exp-btn exp-btn-secondary" @click="$emit('close')">取消</button>
        <button class="exp-btn exp-btn-primary" @click="startExport" :disabled="exporting">
          <svg v-if="exporting" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-dasharray="30 70"/></svg>
          {{ exporting ? '导出中...' : '开始导出' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { ExportOptions } from '../../../composables/useEditorCore'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [], export: [opts: ExportOptions] }>()

const options = reactive<ExportOptions>({
  format: 'mp4',
  quality: 'high',
  resolution: '1920x1080',
  includeSubtitles: false,
  fps: 30,
})

const exporting = ref(false)

function startExport() {
  exporting.value = true
  emit('export', { ...options })
  setTimeout(() => { exporting.value = false }, 500)
}
</script>

<style scoped>
.export-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.export-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 360px;
  box-shadow: var(--shadow-lg);
}

.export-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.export-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.export-close {
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}

.export-close:hover { color: var(--text-primary); }

.export-form { padding: 16px; }

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.form-row label {
  font-size: 13px;
  color: var(--text-secondary);
}

.form-input {
  width: 160px;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.form-input:focus {
  border-color: var(--primary);
  outline: none;
}

.form-check {
  gap: 8px;
}

.form-check input[type="checkbox"] {
  accent-color: var(--primary);
}

.form-check label {
  font-size: 13px;
  color: var(--text-primary);
}

.export-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
}

.exp-btn {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all var(--transition-fast);
}

.exp-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.exp-btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.exp-btn-secondary:hover { background: var(--bg-tertiary); }

.exp-btn-primary {
  background: var(--primary);
  color: #fff;
  border: none;
}

.exp-btn-primary:hover:not(:disabled) { background: var(--primary-hover); }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
