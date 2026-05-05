<template>
  <div class="filter-panel">
    <div v-if="!clip" class="panel-empty">请先选择一个片段</div>
    <template v-else>
      <div class="section">
        <div class="section-title">滤镜预设</div>
        <div class="filter-grid">
          <button v-for="(preset, key) in localPresets" :key="key" class="filter-item" :class="{ active: clip.filterPreset === key }" @click="applyPreset(key as string)">
            <div class="filter-thumb" :style="preset.css ? { filter: preset.css.replace('filter: ', '').replace(')', ')') } : {}">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m21 15-5-5L5 21"/></svg>
            </div>
            <span class="filter-name">{{ preset.label }}</span>
          </button>
        </div>
      </div>
      <div class="section">
        <div class="section-title">手动调节</div>
        <div class="slider-group">
          <label>亮度</label>
          <input type="range" min="0" max="200" :value="clip.brightness" @input="adjust('brightness', +($event.target as HTMLInputElement).value)" />
          <span class="slider-val">{{ clip.brightness }}%</span>
        </div>
        <div class="slider-group">
          <label>对比度</label>
          <input type="range" min="0" max="200" :value="clip.contrast" @input="adjust('contrast', +($event.target as HTMLInputElement).value)" />
          <span class="slider-val">{{ clip.contrast }}%</span>
        </div>
        <div class="slider-group">
          <label>饱和度</label>
          <input type="range" min="0" max="200" :value="clip.saturation" @input="adjust('saturation', +($event.target as HTMLInputElement).value)" />
          <span class="slider-val">{{ clip.saturation }}%</span>
        </div>
        <div class="slider-group">
          <label>色相</label>
          <input type="range" min="-180" max="180" :value="clip.hueRotate" @input="adjust('hueRotate', +($event.target as HTMLInputElement).value)" />
          <span class="slider-val">{{ clip.hueRotate }}°</span>
        </div>
        <div class="slider-group">
          <label>模糊</label>
          <input type="range" min="0" max="20" step="0.5" :value="clip.blur" @input="adjust('blur', +($event.target as HTMLInputElement).value)" />
          <span class="slider-val">{{ clip.blur }}px</span>
        </div>
      </div>
      <div class="section">
        <div class="section-title">AI 调色</div>
        <div class="ai-styles">
          <button v-for="style in aiStyles" :key="style.id" class="ai-style-btn" @click="$emit('ai-color-grade', style.id)">
            <span class="ai-style-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" v-html="style.svgPath"></svg></span>
            <span class="ai-style-name">{{ style.name }}</span>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { TimelineClip } from '../../../composables/useEditorCore'

const props = defineProps<{ clip: TimelineClip | null }>()
const emit = defineEmits<{
  'apply-filter': [preset: string, adjustments?: Record<string, number>]
  'ai-color-grade': [style: string]
}>()

const localPresets: Record<string, { label: string; css: string }> = {
  none: { label: '无', css: '' },
  grayscale: { label: '黑白', css: 'grayscale(100%)' },
  sepia: { label: '复古', css: 'sepia(80%)' },
  warm: { label: '暖色', css: 'sepia(30%) saturate(140%)' },
  cool: { label: '冷色', css: 'saturate(80%) hue-rotate(10deg)' },
  vintage: { label: '怀旧', css: 'sepia(40%) contrast(90%)' },
  cinematic: { label: '电影', css: 'contrast(110%) saturate(85%)' },
  vivid: { label: '鲜艳', css: 'saturate(160%) contrast(110%)' },
  fade: { label: '褪色', css: 'contrast(85%) brightness(110%)' },
  noir: { label: '黑色电影', css: 'grayscale(100%) contrast(130%)' },
  teal_orange: { label: '青橙', css: 'contrast(115%) saturate(120%)' },
  dreamy: { label: '梦幻', css: 'brightness(110%) contrast(90%)' },
  high_contrast: { label: '高对比', css: 'contrast(150%)' },
  low_contrast: { label: '低对比', css: 'contrast(70%)' },
  portrait: { label: '人像', css: 'brightness(105%) contrast(95%)' },
  landscape_filter: { label: '风景', css: 'saturate(130%) contrast(105%)' },
}

const aiStyles = [
  { id: 'cinematic', name: '电影', svgPath: '<rect x="2" y="2" width="20" height="20" rx="2"/><polygon points="10 8 10 16 16 12" fill="currentColor"/>' },
  { id: 'vintage', name: '复古', svgPath: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>' },
  { id: 'vivid', name: '鲜艳', svgPath: '<circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>' },
  { id: 'noir', name: '黑色电影', svgPath: '<circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 0 20z" fill="currentColor"/>' },
  { id: 'warm', name: '暖色', svgPath: '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>' },
  { id: 'cool', name: '冷色', svgPath: '<path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="4"/>' },
  { id: 'dreamy', name: '梦幻', svgPath: '<path d="M12 3l1.5 4.5H18l-3.5 2.5L16 14.5 12 11.5 8 14.5l1.5-4.5L6 7.5h4.5z"/>' },
  { id: 'portrait', name: '人像', svgPath: '<circle cx="12" cy="8" r="4"/><path d="M6 21v-2a6 6 0 0 1 12 0v2"/>' },
  { id: 'landscape_grade', name: '风景', svgPath: '<path d="M3 18l5-5 4 4 5-7 4 8H3z"/><circle cx="8" cy="7" r="2"/>' },
]

function applyPreset(key: string) {
  emit('apply-filter', key)
}

function adjust(prop: string, value: number) {
  emit('apply-filter', props.clip?.filterPreset || 'none', { [prop]: value })
}
</script>

<style scoped>
.filter-panel { padding: 12px; }
.panel-empty { text-align: center; color: var(--text-tertiary); padding: 40px 0; font-size: 13px; }
.section { margin-bottom: 16px; }
.section-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.filter-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.filter-item { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 6px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); cursor: pointer; transition: border-color 0.15s; }
.filter-item:hover { border-color: var(--text-tertiary); }
.filter-item.active { border-color: var(--primary); background: var(--primary-light); }
.filter-thumb { width: 36px; height: 36px; border-radius: 3px; background: var(--bg-tertiary); display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); overflow: hidden; }
.filter-name { font-size: 10px; color: var(--text-secondary); text-align: center; line-height: 1.2; }
.slider-group { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.slider-group label { font-size: 12px; color: var(--text-secondary); width: 48px; flex-shrink: 0; }
.slider-group input[type="range"] { flex: 1; accent-color: var(--primary); }
.slider-val { font-size: 11px; color: var(--text-tertiary); width: 40px; text-align: right; font-variant-numeric: tabular-nums; }
.ai-styles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.ai-style-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); cursor: pointer; transition: all 0.15s; }
.ai-style-btn:hover { border-color: var(--primary); background: var(--primary-light); }
.ai-style-icon { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); }
.ai-style-name { font-size: 10px; color: var(--text-secondary); }
</style>
