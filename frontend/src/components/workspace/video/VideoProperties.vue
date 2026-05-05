<template>
  <div v-if="clip" class="properties-panel">
    <h4 class="panel-title">Properties</h4>
    <div class="prop-group">
      <label>Name</label>
      <input :value="clip.name" @input="onUpdate('name', ($event.target as HTMLInputElement).value)" class="prop-input" />
    </div>
    <div class="prop-group">
      <label>Start</label>
      <input type="number" :value="clip.startTime.toFixed(2)" @change="onUpdate('startTime', +($event.target as HTMLInputElement).value)" class="prop-input" step="0.1" />
    </div>
    <div class="prop-group">
      <label>Duration</label>
      <input type="number" :value="clip.duration.toFixed(2)" @change="onUpdate('duration', +($event.target as HTMLInputElement).value)" class="prop-input" step="0.1" />
    </div>
    <div class="prop-group" v-if="clip.type === 'video'">
      <label>Opacity</label>
      <div class="prop-slider-row">
        <input type="range" min="0" max="1" step="0.1" :value="clip.opacity" @input="onUpdate('opacity', +($event.target as HTMLInputElement).value)" class="prop-slider" />
        <span class="prop-value">{{ (clip.opacity * 100).toFixed(0) }}%</span>
      </div>
    </div>
    <div class="prop-group" v-if="clip.type === 'video' || clip.type === 'audio'">
      <label>Volume</label>
      <div class="prop-slider-row">
        <input type="range" min="0" max="1" step="0.1" :value="clip.volume" @input="onUpdate('volume', +($event.target as HTMLInputElement).value)" class="prop-slider" />
        <span class="prop-value">{{ (clip.volume * 100).toFixed(0) }}%</span>
      </div>
    </div>
    <div class="prop-group" v-if="clip.type === 'video' || clip.type === 'audio'">
      <label>Speed</label>
      <div class="prop-slider-row">
        <input type="range" min="0.25" max="4" step="0.25" :value="clip.playbackRate" @input="onUpdate('playbackRate', +($event.target as HTMLInputElement).value)" class="prop-slider" />
        <span class="prop-value">{{ clip.playbackRate }}x</span>
      </div>
    </div>
    <div class="prop-group">
      <label class="checkbox-label">
        <input type="checkbox" :checked="clip.muted" @change="onUpdate('muted', ($event.target as HTMLInputElement).checked)" />
        <span>Muted</span>
      </label>
    </div>
    <div class="prop-group">
      <label class="checkbox-label">
        <input type="checkbox" :checked="clip.hidden" @change="onUpdate('hidden', ($event.target as HTMLInputElement).checked)" />
        <span>Hidden</span>
      </label>
    </div>
    <div class="prop-group" v-if="clip.type === 'subtitle' && clip.text">
      <label>Subtitle Text</label>
      <textarea :value="clip.text" @input="onUpdate('text', ($event.target as HTMLTextAreaElement).value)" class="prop-textarea" rows="3"></textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TimelineClip } from '../../../composables/useEditorCore'

const props = defineProps<{
  clip: TimelineClip | null
}>()

const emit = defineEmits<{
  update: [clipId: string, updates: Partial<TimelineClip>]
}>()

function onUpdate(key: string, value: unknown) {
  if (!props.clip) return
  emit('update', props.clip.id, { [key]: value })
}
</script>

<style scoped>
.properties-panel { width: 220px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); padding: 12px; overflow-y: auto; }
.panel-title { font-size: 13px; color: var(--text-secondary); margin: 0 0 12px; }
.prop-group { margin-bottom: 10px; }
.prop-group label { display: block; font-size: 11px; color: var(--text-tertiary); margin-bottom: 4px; }
.prop-input { width: 100%; padding: 4px 8px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-primary); font-size: 12px; outline: none; box-sizing: border-box; }
.prop-input:focus { border-color: var(--primary); }
.prop-slider-row { display: flex; align-items: center; gap: 8px; }
.prop-slider { flex: 1; accent-color: var(--primary); }
.prop-value { font-size: 11px; color: var(--text-tertiary); min-width: 36px; text-align: right; }
.checkbox-label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.checkbox-label input { accent-color: var(--primary); }
.prop-textarea { width: 100%; padding: 4px 8px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-primary); font-size: 12px; outline: none; resize: vertical; box-sizing: border-box; }
.prop-textarea:focus { border-color: var(--primary); }
</style>
