<template>
  <div class="clip-editor" @keydown="onKeyDown" tabindex="0">
    <div class="clip-toolbar">
      <div class="toolbar-group">
        <button class="tb-btn" @click="importFile" title="导入">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <span>导入</span>
        </button>
        <button class="tb-btn" :disabled="!selectedClipId" @click="splitSelected" title="分割">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="3" x2="6" y2="21"/><line x1="6" y1="3" x2="18" y2="21"/></svg>
          <span>分割</span>
        </button>
        <button class="tb-btn tb-btn-danger" :disabled="!selectedClipId" @click="removeSelected" title="删除">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
          <span>删除</span>
        </button>
      </div>
      <div class="toolbar-group">
        <button class="tb-btn" :disabled="!canUndo" @click="undo" title="撤销">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
        </button>
        <button class="tb-btn" :disabled="!canRedo" @click="redo" title="重做">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/></svg>
        </button>
      </div>
      <div class="toolbar-group">
        <button class="tb-btn" :class="{ active: rightPanel === 'filter' }" @click="togglePanel('filter')" title="滤镜">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
          <span>滤镜</span>
        </button>
        <button class="tb-btn" :class="{ active: rightPanel === 'assets' }" @click="togglePanel('assets')" title="素材">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 3 8 7 8 3z"/></svg>
          <span>素材</span>
        </button>
        <button class="tb-btn" :class="{ active: rightPanel === 'keyframe' }" @click="togglePanel('keyframe')" title="关键帧">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 2 7l10 5 10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          <span>关键帧</span>
        </button>
        <button class="tb-btn" :class="{ active: rightPanel === 'ai' }" @click="togglePanel('ai')" title="AI">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4c0 1.1-.5 2.1-1.3 2.8"/><path d="M12 2a4 4 0 0 0-4 4c0 1.1.5 2.1 1.3 2.8"/><path d="M12 8v4"/><circle cx="12" cy="12" r="3"/><path d="M12 15v7"/><path d="M9 18h6"/></svg>
          <span>AI</span>
        </button>
      </div>
      <div class="toolbar-spacer"></div>
      <button class="tb-btn tb-btn-export" @click="showExportDialog = true" title="导出">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <span>导出</span>
      </button>
    </div>

    <div class="clip-content">
      <div class="clip-main-area">
        <div class="clip-preview-wrap">
          <video ref="videoPlayer" class="preview-video" :src="currentVideoUrl" @loadedmetadata="onVideoLoaded" @ended="isPlaying = false"></video>
          <div v-if="subtitleClips.length" class="subtitle-overlay">
            <div v-for="c in activeSubtitles" :key="c.id" class="subtitle-text">{{ c.text || c.name }}</div>
          </div>
          <div v-if="!currentVideoUrl" class="preview-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><polygon points="10 8 10 16 16 12" fill="currentColor"/></svg>
            <span>拖拽或点击导入视频/音频</span>
          </div>
          <div class="preview-time">{{ formatTime(currentTime) }} / {{ formatTime(totalDuration) }}</div>
        </div>

        <div v-if="rightPanel !== null" class="clip-right-panel">
          <div class="panel-header">
            <span class="panel-title">{{ panelTitle }}</span>
            <button class="panel-close" @click="rightPanel = null">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="panel-body">
            <ClipFilterPanel v-if="rightPanel === 'filter'" :clip="selectedClip" @apply-filter="onApplyFilter" @ai-color-grade="onAiColorGrade" />
            <ClipAssetLibrary v-else-if="rightPanel === 'assets'" :packs="assetPacks" @import-pack="onImportAssetPack" />
            <ClipKeyframePanel v-else-if="rightPanel === 'keyframe'" :clip="selectedClip" :current-time="currentTime" @add-keyframe="onAddKeyframe" @remove-keyframe="onRemoveKeyframe" />
            <VideoAIPanel v-else-if="rightPanel === 'ai'" :ai-mode="aiMode" :ai-loading="aiLoading" :ai-result="aiResult" :chat-messages="chatMessages" @close="rightPanel = null" @send-chat="sendChatMessage" @apply-auto-edit="applyAutoEditPlan" @apply-subtitles="applySubtitles" />
          </div>
        </div>
      </div>

      <VideoTimeline
        :tracks="tracks"
        :selected-clip-id="selectedClipId"
        :current-time="currentTime"
        :total-duration="totalDuration"
        :is-playing="isPlaying"
        :zoom-level="zoomLevel"
        :px-per-sec="pxPerSec"
        :snap-enabled="snapEnabled"
        @add-track="addTrack"
        @toggle-snap="snapEnabled = !snapEnabled"
        @zoom="zoomLevel = $event"
        @toggle-track-mute="toggleTrackMute"
        @toggle-track-hidden="toggleTrackHidden"
        @select-clip="selectClip"
        @move-clip="moveClip"
        @resize-clip="onResizeClip"
        @seek="seek"
        @toggle-play="togglePlay"
        @skip-back="skipBack"
        @skip-forward="skipForward"
      />
    </div>

    <VideoExportDialog :visible="showExportDialog" @close="showExportDialog = false" @export="handleExport" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import VideoTimeline from './video/VideoTimeline.vue'
import VideoAIPanel from './video/VideoAIPanel.vue'
import VideoExportDialog from './video/VideoExportDialog.vue'
import ClipFilterPanel from './video/ClipFilterPanel.vue'
import ClipAssetLibrary from './video/ClipAssetLibrary.vue'
import ClipKeyframePanel from './video/ClipKeyframePanel.vue'
import type { ChatMessage } from '../../composables/useEditorCore'
import { useEditorCore } from '../../composables/useEditorCore'
import api from '../../utils/api'

const videoPlayer = ref<HTMLVideoElement | null>(null)
const showExportDialog = ref(false)
const aiMode = ref<'result' | 'chat'>('result')
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const chatMessages = ref<ChatMessage[]>([])
const rightPanel = ref<'filter' | 'assets' | 'keyframe' | 'ai' | null>(null)

const {
  undo, redo, canUndo, canRedo,
  isPlaying, currentTime, togglePlay, seek, skipBack, skipForward, attachVideo,
  tracks, selectedClipId, selectedClip, zoomLevel, pxPerSec, snapEnabled,
  addTrack, removeClip, updateClip, moveClip, splitClip, selectClip,
  toggleTrackMute, toggleTrackHidden,
  getTotalDuration, initDefaultTracks, importVideo, importAudio, importSubtitle,
  getProjectData, clearProject,
  addKeyframe, removeKeyframe, loadFilterPresets, loadAssetPacks,
  applyFilter, aiColorGrade, importAssetPack, assetPacks,
} = useEditorCore()

const totalDuration = computed(() => getTotalDuration())
const currentVideoUrl = computed(() => {
  const v = tracks.value.flatMap(t => t.clips).find(c => c.type === 'video' && c.previewUrl)
  return v?.previewUrl || ''
})
const subtitleClips = computed(() => tracks.value.flatMap(t => t.clips).filter(c => c.type === 'subtitle'))
const activeSubtitles = computed(() =>
  subtitleClips.value.filter(c => currentTime.value >= c.startTime && currentTime.value <= c.startTime + c.duration)
)

const panelTitle = computed(() => {
  const titles: Record<string, string> = { filter: '滤镜', assets: '素材', keyframe: '关键帧', ai: 'AI 助手' }
  return rightPanel.value ? titles[rightPanel.value] || '' : ''
})

function formatTime(sec: number): string {
  if (isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function onVideoLoaded(e: Event) {
  const target = e.target as HTMLVideoElement
  attachVideo(target)
}

async function aiAnalyze() {
  aiLoading.value = true
  try {
    const res = await api.post('/ai/workspace/video/analyze', { video_info: { duration: totalDuration.value, clips: tracks.value.flatMap(t => t.clips).length } })
    aiResult.value = res.data
  } finally { aiLoading.value = false }
}

async function sendChatMessage(msg: string) {
  chatMessages.value.push({ role: 'user', content: msg })
  try {
    const res = await api.post('/ai/workspace/video/analyze', { chat_message: msg })
    aiMode.value = 'chat'
    chatMessages.value.push({ role: 'assistant', content: res.data?.result?.reply || 'AI 正在处理' })
  } catch { chatMessages.value.push({ role: 'assistant', content: 'AI 服务暂不可用' }) }
}

function applyAutoEditPlan(_plan: any) {}
function applySubtitles(_subs: any) {}

function importFile() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'video/*,audio/*,.zip,.srt'
  input.onchange = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    if (file.name.endsWith('.zip')) {
      onImportAssetPack(file.name)
      return
    }
    if (file.name.endsWith('.srt')) {
      const text = await file.text()
      importSubtitle(text, 0, 10)
      return
    }
    if (file.type.startsWith('video')) importVideo(file)
    else if (file.type.startsWith('audio')) importAudio(file)
  }
  input.click()
}

function splitSelected() { if (selectedClipId.value) splitClip(selectedClipId.value, currentTime.value) }
function removeSelected() { if (selectedClipId.value) removeClip(selectedClipId.value) }

function togglePanel(panel: 'filter' | 'assets' | 'keyframe' | 'ai') {
  rightPanel.value = rightPanel.value === panel ? null : panel
  if (panel === 'ai' && rightPanel.value === 'ai') { aiMode.value = 'result'; aiAnalyze() }
}

function onApplyFilter(preset: string, adjustments?: Record<string, number>) {
  const compId = tracks.value[0]?.clips?.[0]?.id
  if (compId && selectedClip.value) { applyFilter(compId, compId, preset, adjustments) }
}

async function onAiColorGrade(style: string) {
  const compId = tracks.value[0]?.clips?.[0]?.id
  if (compId) {
    const res = await aiColorGrade(compId, compId, style)
    if (res?.success) alert('AI 调色已应用')
    else alert('AI 调色失败')
  }
}

async function onImportAssetPack(zipPath: string) {
  const ok = await importAssetPack(zipPath)
  if (ok) alert('素材包导入成功')
  else alert('素材包导入失败')
}

function onAddKeyframe(kf: { time: number; property: string; value: unknown; ease: string }) {
  if (selectedClip.value) { addKeyframe(selectedClip.value.id, kf) }
}

function onRemoveKeyframe(kfId: string) { if (selectedClip.value) removeKeyframe(selectedClip.value.id, kfId) }

function onResizeClip(clipId: string, start: number, end: number) {
  if (selectedClip.value) updateClip(clipId, { startTime: start, duration: end - start })
}

async function handleExport(options: any) {
  try {
    const projectData = getProjectData()
    const res = await api.post('/ai/workspace/video/export', { project: projectData, options, video_src: currentVideoUrl.value })
    if (res.data?.result?.url) {
      const a = document.createElement('a')
      a.href = res.data.result.url
      a.download = res.data.result.filename
      a.click()
      alert('导出成功')
    } else { alert('导出失败') }
  } catch { alert('导出请求失败') }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === ' ') { e.preventDefault(); togglePlay() }
  else if (e.key === 'Delete') { removeSelected() }
  else if (e.key === 'z' && (e.ctrlKey || e.metaKey) && !e.shiftKey) { e.preventDefault(); undo() }
  else if ((e.key === 'y' && (e.ctrlKey || e.metaKey)) || (e.key === 'z' && (e.ctrlKey || e.metaKey) && e.shiftKey)) { e.preventDefault(); redo() }
  else if (e.key === 's' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); splitSelected() }
  else if (e.key === 'ArrowLeft') { seek(Math.max(0, currentTime.value - 1)) }
  else if (e.key === 'ArrowRight') { seek(Math.min(totalDuration.value, currentTime.value + 1)) }
}

onMounted(() => { initDefaultTracks(); loadFilterPresets(); loadAssetPacks() })
onUnmounted(() => { clearProject() })
</script>

<style scoped>
.clip-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

.clip-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-spacer { flex: 1; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--text-primary);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.tb-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  border-color: var(--text-tertiary);
}

.tb-btn:active:not(:disabled) { transform: scale(0.97); }
.tb-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.tb-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.tb-btn.active:hover { background: var(--primary-hover); }

.tb-btn-danger { color: var(--ws-danger); }
.tb-btn-danger:hover:not(:disabled) {
  background: var(--ws-danger);
  color: #fff;
  border-color: var(--ws-danger);
}

.tb-btn-export {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
  font-weight: 500;
}

.tb-btn-export:hover { background: var(--primary-hover); }

.clip-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.clip-main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.clip-preview-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  position: relative;
  min-width: 0;
  min-height: 0;
}

.preview-video {
  max-width: 100%;
  max-height: 100%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.subtitle-overlay {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  width: 80%;
}

.subtitle-text {
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  margin-bottom: 2px;
}

.preview-time {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: var(--overlay-bg);
  color: var(--text-primary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-variant-numeric: tabular-nums;
}

.clip-right-panel {
  width: 280px;
  border-left: 1px solid var(--border-color);
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.panel-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.panel-close {
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}

.panel-close:hover { color: var(--text-primary); }

.panel-body {
  flex: 1;
  overflow-y: auto;
}
</style>
