<template>
  <div class="keyframe-panel">
    <div v-if="!clip" class="panel-empty">请先选择一个片段</div>
    <template v-else>
      <div class="section">
        <div class="section-header">
          <span class="section-title">关键帧列表</span>
          <button class="add-kf-btn" @click="addKeyframeAtPlayhead">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            添加
          </button>
        </div>
        <div v-if="clip.keyframes.length === 0" class="empty-hint">暂无关键帧，点击添加按钮在当前播放头位置创建</div>
        <div v-for="kf in sortedKeyframes" :key="kf.id" class="kf-item">
          <div class="kf-dot" :style="{ background: 'var(--primary)' }"></div>
          <div class="kf-info">
            <span class="kf-time">{{ formatKfTime(kf.time) }}</span>
            <span class="kf-prop">{{ propertyLabels[kf.property] || kf.property }}</span>
          </div>
          <span class="kf-val">{{ kf.value }}</span>
          <button class="kf-del" @click="$emit('remove-keyframe', kf.id)" title="删除">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>
      <div class="section">
        <div class="section-title">添加关键帧</div>
        <div class="kf-form">
          <div class="form-row">
            <label>属性</label>
            <select v-model="newKf.property">
              <option v-for="(label, key) in propertyLabels" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>时间</label>
            <input type="number" v-model.number="newKf.time" step="0.1" min="0" />
          </div>
          <div class="form-row">
            <label>值</label>
            <input type="number" v-model.number="newKf.value" step="0.1" />
          </div>
          <div class="form-row">
            <label>缓动</label>
            <select v-model="newKf.ease">
              <option value="linear">线性</option>
              <option value="easeIn">缓入</option>
              <option value="easeOut">缓出</option>
              <option value="easeInOut">缓入缓出</option>
              <option value="back">回弹</option>
              <option value="elastic">弹性</option>
            </select>
          </div>
          <button class="add-kf-btn full" @click="addCustomKeyframe">添加关键帧</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { TimelineClip } from '../../../composables/useEditorCore'

const props = defineProps<{
  clip: TimelineClip | null
  currentTime: number
}>()
const emit = defineEmits<{
  'add-keyframe': [kf: { time: number; property: string; value: unknown; ease: string }]
  'remove-keyframe': [kfId: string]
}>()

const propertyLabels: Record<string, string> = {
  x: 'X 位置', y: 'Y 位置', scale: '缩放', opacity: '透明度',
  rotation: '旋转', volume: '音量', brightness: '亮度',
  contrast: '对比度', saturation: '饱和度', blur: '模糊',
}

const newKf = reactive({ property: 'scale', time: 0, value: 1, ease: 'linear' })

const sortedKeyframes = computed(() => {
  if (!props.clip) return []
  return [...props.clip.keyframes].sort((a, b) => a.time - b.time)
})

function formatKfTime(t: number): string {
  const m = Math.floor(t / 60)
  const s = (t % 60).toFixed(1)
  return `${m}:${s.padStart(4, '0')}`
}

function addKeyframeAtPlayhead() {
  if (!props.clip) return
  emit('add-keyframe', {
    time: props.currentTime,
    property: newKf.property,
    value: newKf.value,
    ease: newKf.ease,
  })
}

function addCustomKeyframe() {
  emit('add-keyframe', { ...newKf })
}
</script>

<style scoped>
.keyframe-panel { padding: 12px; }
.panel-empty { text-align: center; color: var(--text-tertiary); padding: 40px 0; font-size: 13px; }
.section { margin-bottom: 16px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.section-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.add-kf-btn { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border: 1px solid var(--primary); background: transparent; color: var(--primary); border-radius: 4px; cursor: pointer; font-size: 11px; }
.add-kf-btn:hover { background: var(--primary-light); }
.add-kf-btn.full { width: 100%; justify-content: center; margin-top: 8px; }
.empty-hint { text-align: center; color: var(--text-tertiary); padding: 16px 0; font-size: 12px; }
.kf-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 4px; margin-bottom: 4px; background: var(--bg-primary); }
.kf-item:hover { background: var(--bg-tertiary); }
.kf-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.kf-info { flex: 1; display: flex; flex-direction: column; }
.kf-time { font-size: 11px; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.kf-prop { font-size: 10px; color: var(--text-tertiary); }
.kf-val { font-size: 11px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.kf-del { border: none; background: none; color: var(--text-tertiary); cursor: pointer; padding: 2px; border-radius: 3px; }
.kf-del:hover { color: var(--ws-danger); background: var(--bg-tertiary); }
.kf-form { display: flex; flex-direction: column; gap: 8px; }
.form-row { display: flex; align-items: center; gap: 8px; }
.form-row label { font-size: 12px; color: var(--text-secondary); width: 40px; flex-shrink: 0; }
.form-row input, .form-row select { flex: 1; padding: 4px 8px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary); font-size: 12px; }
.form-row input:focus, .form-row select:focus { outline: none; border-color: var(--primary); }
</style>
