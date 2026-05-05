<template>
  <div class="video-preview" ref="previewArea">
    <div v-if="!hasClips" class="preview-placeholder">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="14" rx="2"/><polygon points="10,8 10,14 16,11" fill="currentColor" stroke="none"/></svg>
      <p>Import a video to start editing</p>
      <button class="import-btn" @click="$emit('import')">Choose File</button>
    </div>
    <template v-else>
      <video
        ref="videoPlayer"
        class="preview-video"
        :src="videoSrc"
        @loadedmetadata="onVideoLoaded"
        @ended="onVideoEnded"
      ></video>
      <div v-if="currentSubtitle" class="subtitle-overlay">{{ currentSubtitle }}</div>
      <div class="preview-info">
        <span v-if="duration > 0" class="time-badge">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  hasClips: boolean
  videoSrc: string
  currentTime: number
  duration: number
  subtitleText: string | null
}>()

const emit = defineEmits<{
  import: []
  loaded: [el: HTMLVideoElement]
  ended: []
}>()

const videoPlayer = ref<HTMLVideoElement | null>(null)
const previewArea = ref<HTMLDivElement | null>(null)

const currentSubtitle = computed(() => props.subtitleText)

function onVideoLoaded() {
  if (videoPlayer.value) {
    emit('loaded', videoPlayer.value)
  }
}

function onVideoEnded() {
  emit('ended')
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function getVideoElement(): HTMLVideoElement | null {
  return videoPlayer.value
}

defineExpose({ getVideoElement })
</script>

<style scoped>
.video-preview { flex: 1; display: flex; align-items: center; justify-content: center; background: var(--bg-primary); position: relative; overflow: hidden; }
.preview-placeholder { display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-tertiary); }
.preview-placeholder p { font-size: 14px; }
.import-btn { padding: 8px 20px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.import-btn:hover { background: var(--primary-hover); }
.preview-video { max-width: 100%; max-height: 100%; }
.subtitle-overlay { position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.75); color: #fff; padding: 6px 16px; border-radius: 4px; font-size: 16px; max-width: 80%; text-align: center; pointer-events: none; }
.preview-info { position: absolute; top: 8px; right: 8px; display: flex; gap: 6px; }
.time-badge { background: rgba(0,0,0,0.6); color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-variant-numeric: tabular-nums; }
</style>
