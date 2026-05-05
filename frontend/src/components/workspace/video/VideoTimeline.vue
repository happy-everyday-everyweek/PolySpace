<template>
  <div class="video-timeline">
    <div class="timeline-toolbar">
      <button class="tl-btn" @click="$emit('add-track', 'video')" title="添加视频轨道">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><polygon points="10,8 10,14 16,11" fill="currentColor"/></svg>
        +视频
      </button>
      <button class="tl-btn" @click="$emit('add-track', 'audio')" title="添加音频轨道">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
        +音频
      </button>
      <button class="tl-btn" :class="{ active: snapEnabled }" @click="$emit('toggle-snap')" title="吸附">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
        吸附
      </button>
      <div class="tl-spacer"></div>
      <button class="tl-btn tl-btn-icon" @click="$emit('skip-back')" title="跳到开头">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/></svg>
      </button>
      <button class="tl-btn tl-btn-play" @click="$emit('toggle-play')" :title="isPlaying ? '暂停' : '播放'">
        <svg v-if="isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3" fill="currentColor"/></svg>
      </button>
      <button class="tl-btn tl-btn-icon" @click="$emit('skip-forward')" title="跳到结尾">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>
      <div class="tl-spacer"></div>
      <input class="tl-zoom" type="range" min="1" max="10" :value="zoomLevel" @input="$emit('zoom', +($event.target as HTMLInputElement).value)" />
    </div>
    <div class="timeline-scroll" ref="scrollEl" @mousedown="onRulerClick">
      <div class="ruler" :style="{ width: totalWidth + 'px' }">
        <template v-for="i in 120" :key="i">
          <span v-if="(i - 1) * 10 * pxPerSec / 10 < totalWidth" :style="{ left: ((i - 1) * 10 * pxPerSec / 10) + 'px' }" class="mark">{{ formatTime((i - 1)) }}</span>
        </template>
      </div>
      <div v-for="track in tracks" :key="track.id" class="track" :style="{ width: totalWidth + 'px' }">
        <div class="track-head">
          <span class="track-name">{{ track.name }}</span>
          <button class="track-ctrl" :class="{ muted: track.muted }" @click="$emit('toggle-track-mute', track.id)" title="静音">M</button>
          <button class="track-ctrl" :class="{ muted: track.hidden }" @click="$emit('toggle-track-hidden', track.id)" title="隐藏">H</button>
        </div>
        <div class="track-body">
          <div v-for="clip in track.clips" :key="clip.id" class="clip"
            :class="[clip.type, { selected: clip.id === selectedClipId }]"
            :style="clipStyle(clip)"
            @mousedown.stop="startDrag($event, clip)"
          >
            <div class="clip-resize left" @mousedown.stop="startResize($event, clip, 'left')"></div>
            <span class="clip-name">{{ clip.name }}</span>
            <div v-if="clip.keyframes.length" class="clip-kf-dots">
              <span v-for="kf in clip.keyframes" :key="kf.id" class="kf-dot" :style="{ left: ((kf.time - clip.startTime) / clip.duration * 100) + '%' }"></span>
            </div>
            <div class="clip-resize right" @mousedown.stop="startResize($event, clip, 'right')"></div>
          </div>
        </div>
      </div>
      <div class="playhead" :style="{ left: playheadPx + 'px' }">
        <div class="playhead-head"></div>
        <div class="playhead-line"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import type { TimelineTrack, TimelineClip } from '../../../composables/useEditorCore'

const props = defineProps<{
  tracks: TimelineTrack[]
  selectedClipId: string | null
  currentTime: number
  totalDuration: number
  isPlaying: boolean
  zoomLevel: number
  pxPerSec: number
  snapEnabled: boolean
}>()

const emit = defineEmits<{
  'add-track': [type: 'video' | 'audio' | 'subtitle']
  'toggle-snap': []
  'zoom': [level: number]
  'toggle-track-mute': [trackId: string]
  'toggle-track-hidden': [trackId: string]
  'select-clip': [clipId: string]
  'move-clip': [clipId: string, start: number]
  'resize-clip': [clipId: string, start: number, end: number]
  'seek': [time: number]
  'toggle-play': []
  'skip-back': []
  'skip-forward': []
}>()

const scrollEl = ref<HTMLElement | null>(null)
const totalWidth = computed(() => Math.max(600, props.totalDuration * props.pxPerSec + 200))
const playheadPx = computed(() => props.currentTime * props.pxPerSec)

function formatTime(minOrSec: number): string {
  const m = Math.floor(minOrSec / 60)
  const s = Math.floor(minOrSec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function clipStyle(clip: TimelineClip) {
  const left = clip.startTime * props.pxPerSec
  const width = clip.duration * props.pxPerSec
  return { left: `${left}px`, width: `${width}px` }
}

function startDrag(e: MouseEvent, clip: TimelineClip) {
  emit('select-clip', clip.id)
  const startX = e.clientX
  const startLeft = clip.startTime
  const move = (ev: MouseEvent) => {
    const dx = ev.clientX - startX
    let newStart = Math.max(0, startLeft + dx / props.pxPerSec)
    if (props.snapEnabled) newStart = Math.round(newStart * 4) / 4
    emit('move-clip', clip.id, newStart)
  }
  const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  window.addEventListener('mousemove', move)
  window.addEventListener('mouseup', up)
}

function startResize(e: MouseEvent, clip: TimelineClip, side: 'left' | 'right') {
  e.stopPropagation()
  emit('select-clip', clip.id)
  const startX = e.clientX
  const origStart = clip.startTime
  const origEnd = clip.startTime + clip.duration
  const move = (ev: MouseEvent) => {
    const dx = ev.clientX - startX
    const delta = dx / props.pxPerSec
    if (side === 'left') {
      const newStart = Math.max(0, Math.min(origEnd - 0.5, origStart + delta))
      emit('resize-clip', clip.id, newStart, origEnd)
    } else {
      const newEnd = Math.max(origStart + 0.5, origEnd + delta)
      emit('resize-clip', clip.id, origStart, newEnd)
    }
  }
  const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  window.addEventListener('mousemove', move)
  window.addEventListener('mouseup', up)
}

function onRulerClick(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.clip')) return
  const rect = scrollEl.value?.getBoundingClientRect()
  if (!rect || !scrollEl.value) return
  const x = e.clientX - rect.left + scrollEl.value.scrollLeft
  emit('seek', x / props.pxPerSec)
}

watch(() => props.currentTime, async (t) => {
  await nextTick()
  const el = scrollEl.value
  if (!el) return
  const pos = t * props.pxPerSec
  const left = el.scrollLeft
  const right = left + el.clientWidth
  if (pos < left + 40) el.scrollLeft = Math.max(0, pos - 40)
  else if (pos > right - 40) el.scrollLeft = pos - el.clientWidth + 40
})

onUnmounted(() => { window.removeEventListener('mousemove', () => {}); window.removeEventListener('mouseup', () => {}) })
</script>

<style scoped>
.video-timeline {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
  height: 200px;
}

.timeline-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.tl-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tl-btn:hover { background: var(--bg-tertiary); color: var(--text-primary); }

.tl-btn.active {
  background: var(--primary-light);
  color: var(--primary);
}

.tl-btn-play {
  color: var(--text-primary);
  padding: 4px 10px;
}

.tl-btn-play:hover { background: var(--bg-tertiary); }

.tl-btn-icon { padding: 4px; }

.tl-spacer { flex: 1; }

.tl-zoom { width: 80px; accent-color: var(--primary); }

.timeline-scroll {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  position: relative;
}

.ruler {
  height: 20px;
  position: relative;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.mark {
  position: absolute;
  top: 0;
  font-size: 10px;
  color: var(--text-tertiary);
  transform: translateX(-50%);
  border-left: 1px solid var(--border-color);
  padding-left: 3px;
  line-height: 18px;
}

.track {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.track-head {
  width: 100px;
  flex-shrink: 0;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
}

.track-name {
  flex: 1;
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-ctrl {
  width: 18px;
  height: 18px;
  font-size: 9px;
  border-radius: 3px;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.track-ctrl:hover { background: var(--bg-tertiary); }
.track-ctrl.muted { background: var(--ws-danger); color: #fff; }

.track-body {
  flex: 1;
  position: relative;
  height: 56px;
  background: var(--bg-primary);
}

.clip {
  position: absolute;
  top: 4px;
  height: 48px;
  border-radius: var(--radius-md);
  border: 2px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 12px;
  overflow: hidden;
  cursor: grab;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.clip:hover { box-shadow: var(--shadow); }

.clip.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-light);
}

.clip.video { background: var(--primary-light); border-color: var(--text-tertiary); }
.clip.audio { background: rgba(76, 175, 80, 0.1); border-color: rgba(76, 175, 80, 0.3); }
.clip.subtitle { background: rgba(255, 152, 0, 0.1); border-color: rgba(255, 152, 0, 0.3); }
.clip.image { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.3); }

.clip-name {
  display: block;
  padding: 4px 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: var(--text-primary);
}

.clip-kf-dots { position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; }
.kf-dot { position: absolute; top: 50%; width: 6px; height: 6px; border-radius: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 0 1px var(--bg-primary); }

.clip-resize {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: ew-resize;
}

.clip-resize.left { left: 0; border-radius: var(--radius-md) 0 0 var(--radius-md); }
.clip-resize.right { right: 0; border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.clip-resize:hover { background: rgba(255, 255, 255, 0.15); }

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  pointer-events: none;
}

.playhead-head {
  width: 12px;
  height: 12px;
  border-radius: 50% 50% 0 0;
  background: var(--ws-danger);
  margin-left: -5px;
}

.playhead-line {
  width: 2px;
  height: calc(100% - 12px);
  background: var(--ws-danger);
  margin-left: 0;
  opacity: 0.8;
}
</style>
