<template>
  <div class="screen-recorder">
    <div class="recorder-header">
      <h3>Screen Recorder</h3>
      <div class="recorder-status" :class="{ recording: isRecording, paused: isPaused }">
        <span class="status-dot"></span>
        <span v-if="isRecording && !isPaused">Recording {{ formatTime(elapsed) }}</span>
        <span v-else-if="isPaused">Paused {{ formatTime(elapsed) }}</span>
        <span v-else>Ready</span>
      </div>
    </div>
    <div class="recorder-body">
      <div class="preview-area" ref="previewContainer">
        <video v-if="recordedUrl" :src="recordedUrl" controls class="preview-video" @loadedmetadata="onVideoLoaded"></video>
        <div v-else-if="isRecording" class="preview-live">
          <video ref="livePreview" autoplay muted class="preview-video"></video>
          <div class="live-badge">
            <span class="live-dot"></span>
            LIVE
          </div>
          <div v-if="annotations.length > 0" class="annotation-overlay">
            <div v-for="(ann, idx) in visibleAnnotations" :key="idx" class="annotation-marker" :style="{ top: '10px', left: `${10 + idx * 120}px` }">
              <span class="annotation-step">{{ idx + 1 }}</span>
              <span class="annotation-label">{{ ann.text }}</span>
            </div>
          </div>
          <div v-if="scheduledRecording && scheduleCountdown > 0" class="schedule-countdown">
            Starting in {{ scheduleCountdown }}s
          </div>
        </div>
        <div v-else class="preview-placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <path d="M8 21h8M12 17v4"/>
          </svg>
          <p>Click Record to start capturing your screen</p>
        </div>
      </div>
      <div class="recorder-controls">
        <div class="control-row">
          <div class="source-select">
            <label>Source:</label>
            <select v-model="sourceType" :disabled="isRecording">
              <option value="screen">Screen</option>
              <option value="window">Window</option>
              <option value="tab">Browser Tab</option>
              <option value="region">Region</option>
            </select>
          </div>
          <div class="quality-select">
            <label>Quality:</label>
            <select v-model="quality" :disabled="isRecording">
              <option value="low">Low (720p/15fps)</option>
              <option value="medium">Medium (1080p/24fps)</option>
              <option value="high">High (1080p/30fps)</option>
              <option value="original">Original</option>
            </select>
          </div>
          <div class="template-select">
            <label>Template:</label>
            <select v-model="selectedTemplate" :disabled="isRecording">
              <option value="">None</option>
              <option value="tutorial">Tutorial</option>
              <option value="bug_report">Bug Report</option>
              <option value="meeting">Meeting</option>
              <option value="demo">Product Demo</option>
            </select>
          </div>
        </div>
        <div v-if="sourceType === 'region' && !isRecording" class="region-config">
          <label>Region (x,y,w,h):</label>
          <input type="number" v-model.number="regionX" placeholder="X" min="0" class="region-input" />
          <input type="number" v-model.number="regionY" placeholder="Y" min="0" class="region-input" />
          <input type="number" v-model.number="regionW" placeholder="Width" min="100" class="region-input" />
          <input type="number" v-model.number="regionH" placeholder="Height" min="100" class="region-input" />
          <button class="btn-select-region" @click="selectRegion">Select Area</button>
        </div>
        <div v-if="!isRecording" class="smart-record-row">
          <label class="smart-label">
            <input type="checkbox" v-model="scheduledRecording" />
            Scheduled
          </label>
          <input v-if="scheduledRecording" type="datetime-local" v-model="scheduleTime" class="schedule-input" />
          <label v-if="scheduledRecording" class="smart-label">
            Duration (min):
            <input type="number" v-model.number="scheduleDuration" min="1" max="480" class="duration-input" />
          </label>
          <label class="smart-label">
            <input type="checkbox" v-model="changeDetection" />
            Change Detection
          </label>
        </div>
        <div class="control-buttons">
          <button v-if="!isRecording" class="btn-record" @click="startRecording">
            <svg width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="var(--ws-danger)"/></svg>
            Record
          </button>
          <template v-else>
            <button v-if="!isPaused" class="btn-pause" @click="pauseRecording">
              <svg width="16" height="16" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" fill="white"/><rect x="14" y="4" width="4" height="16" fill="white"/></svg>
              Pause
            </button>
            <button v-else class="btn-resume" @click="resumeRecording">
              <svg width="16" height="16" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21" fill="white"/></svg>
              Resume
            </button>
            <button class="btn-stop" @click="stopRecording">
              <svg width="16" height="16" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" fill="white"/></svg>
              Stop
            </button>
          </template>
          <button v-if="recordedUrl && !isRecording" class="btn-upload" @click="uploadRecording" :disabled="uploading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            {{ uploading ? 'Uploading...' : 'Save to Server' }}
          </button>
          <button v-if="recordedUrl && !isRecording" class="btn-download" @click="downloadRecording">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
            Download
          </button>
          <button v-if="recordedUrl && !isRecording" class="btn-discard" @click="discardRecording">Discard</button>
        </div>
        <div v-if="isRecording" class="annotation-row">
          <input type="text" v-model="annotationText" placeholder="Add annotation..." class="annotation-input" @keydown.enter="addAnnotation" />
          <button class="btn-annotate" @click="addAnnotation" :disabled="!annotationText.trim()">Mark</button>
        </div>
        <div v-if="recordedUrl && !isRecording" class="narration-section">
          <div class="narration-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
            <span>Voice Narration</span>
          </div>
          <div class="narration-controls">
            <textarea v-model="narrationText" placeholder="Enter narration text..." class="narration-input" rows="2"></textarea>
            <div class="narration-actions">
              <select v-model="ttsVoice" class="voice-select">
                <option value="en-Carter_man">Carter (EN/M)</option>
                <option value="en-Emma_woman">Emma (EN/F)</option>
                <option value="en-Grace_woman">Grace (EN/F)</option>
                <option value="en-Mike_man">Mike (EN/M)</option>
              </select>
              <button class="btn-tts" @click="generateNarration" :disabled="!narrationText.trim() || ttsLoading">
                {{ ttsLoading ? 'Generating...' : 'Generate' }}
              </button>
              <button v-if="narrationAudioUrl" class="btn-play-narration" @click="playNarration">
                {{ isPlayingNarration ? 'Stop' : 'Play' }}
              </button>
              <button v-if="narrationAudioUrl" class="btn-mix-narration" @click="mixNarration">Mix into Video</button>
            </div>
          </div>
        </div>
        <div class="ai-assist-section" v-if="recordedUrl && !isRecording">
          <div class="ai-assist-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            <span>AI 辅助</span>
            <span v-if="currentRecordingId" class="ai-badge">Visual Analysis</span>
          </div>
          <div class="ai-assist-buttons">
            <button class="btn-ai" @click="aiAssist('summarize_recording')" :disabled="aiLoading">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              AI 总结
            </button>
            <button class="btn-ai" @click="aiAssist('extract_highlights')" :disabled="aiLoading">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              提取亮点
            </button>
            <button class="btn-ai" @click="aiAssist('suggest_title')" :disabled="aiLoading">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              推荐标题
            </button>
            <button class="btn-ai" @click="aiAssist('generate_chapters')" :disabled="aiLoading">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
              生成章节
            </button>
            <button class="btn-ai" @click="aiAssist('extract_text')" :disabled="aiLoading">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
              OCR 提取
            </button>
          </div>
          <div v-if="aiLoading" class="ai-loading">
            <span class="loading-spinner"></span>
            Analyzing recording content...
          </div>
          <div v-if="aiResult" class="ai-result">
            <div class="ai-result-header">
              <span>{{ aiResultTitle }}</span>
              <button class="btn-close-result" @click="aiResult = null">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="ai-result-content">{{ aiResult }}</div>
          </div>
        </div>
        <div class="options">
          <label><input type="checkbox" v-model="includeAudio" :disabled="isRecording" /> Include Audio</label>
          <label><input type="checkbox" v-model="includeCursor" :disabled="isRecording" /> Show Cursor</label>
        </div>
        <div v-if="recordedUrl && !isRecording" class="recording-info">
          <span>Duration: {{ formatTime(recordingDuration) }}</span>
          <span>Size: {{ formatFileSize(recordingSize) }}</span>
          <span>Format: webm/vp9</span>
        </div>
      </div>
    </div>
    <div v-if="recordings.length > 0" class="recordings-list">
      <div class="recordings-header">
        <h4>Saved Recordings</h4>
        <span class="recordings-count">{{ recordings.length }}</span>
      </div>
      <div class="recordings-items">
        <div v-for="rec in recordings" :key="rec.id" class="recording-item" @click="loadRecording(rec)">
          <div class="recording-thumb">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="5,3 19,12 5,21"/></svg>
          </div>
          <div class="recording-meta">
            <div class="recording-title">{{ rec.title }}</div>
            <div class="recording-details">{{ formatTime(rec.duration) }} | {{ formatFileSize(rec.file_size) }} | {{ formatDate(rec.created_at) }}</div>
          </div>
          <button class="btn-delete-rec" @click.stop="deleteRecording(rec.id)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import api from '../../utils/api'
import { useWorkspaceStore } from '../../stores/workspace'
import { useAppSettings } from '@/composables/useAppSettings'

interface Recording {
  id: string
  title: string
  duration: number
  file_size: number
  source_type: string
  has_audio: boolean
  created_at: string
  thumbnail_url?: string
}

const workspaceStore = useWorkspaceStore()
const { settings: recorderSettings } = useAppSettings('screenRecorder')

const isRecording = ref(false)
const isPaused = ref(false)
const elapsed = ref(0)
const sourceType = ref(recorderSettings.value.sourceType)
const quality = ref(recorderSettings.value.quality)
const includeAudio = ref(recorderSettings.value.includeAudio)
const includeCursor = ref(recorderSettings.value.includeCursor)
const recordedUrl = ref('')
const recordedBlob = ref<Blob | null>(null)
const recordingDuration = ref(0)
const recordingSize = ref(0)
const previewContainer = ref<HTMLDivElement | null>(null)
const livePreview = ref<HTMLVideoElement | null>(null)
const aiLoading = ref(false)
const aiResult = ref<string | null>(null)
const aiResultTitle = ref('')
const uploading = ref(false)
const currentRecordingId = ref<string | null>(null)
const recordings = ref<Recording[]>([])
const selectedTemplate = ref(recorderSettings.value.template)
const regionX = ref(0)
const regionY = ref(0)
const regionW = ref(1920)
const regionH = ref(1080)
const scheduledRecording = ref(false)
const scheduleTime = ref('')
const scheduleDuration = ref(10)
const scheduleCountdown = ref(0)
const changeDetection = ref(recorderSettings.value.changeDetection)
const annotationText = ref('')
const annotations = ref<{ time: number; text: string }[]>([])
const visibleAnnotations = ref<{ time: number; text: string }[]>([])
const narrationText = ref('')
const ttsVoice = ref('en-Carter_man')
const ttsLoading = ref(false)
const narrationAudioUrl = ref('')
const narrationAudioBlob = ref<Blob | null>(null)
const isPlayingNarration = ref(false)

let mediaRecorder: MediaRecorder | null = null
let chunks: Blob[] = []
let timer: ReturnType<typeof setInterval> | null = null
let stream: MediaStream | null = null
let scheduleTimer: ReturnType<typeof setInterval> | null = null
let changeDetectionTimer: ReturnType<typeof setInterval> | null = null
let lastFrameData: string | null = null
let narrationAudio: HTMLAudioElement | null = null

const TEMPLATES: Record<string, { watermark: string; stepPrefix: string; autoAnnotate: boolean }> = {
  tutorial: { watermark: 'Tutorial', stepPrefix: 'Step', autoAnnotate: true },
  bug_report: { watermark: 'Bug Report', stepPrefix: 'Issue', autoAnnotate: false },
  meeting: { watermark: 'Meeting', stepPrefix: 'Topic', autoAnnotate: false },
  demo: { watermark: 'Demo', stepPrefix: 'Feature', autoAnnotate: true },
}

const QUALITY_PRESETS: Record<string, { maxWidth: number; fps: number; bitrate: number }> = {
  low: { maxWidth: 1280, fps: 15, bitrate: 1000000 },
  medium: { maxWidth: 1920, fps: 24, bitrate: 2500000 },
  high: { maxWidth: 1920, fps: 30, bitrate: 5000000 },
  original: { maxWidth: 3840, fps: 60, bitrate: 8000000 },
}

const AI_ACTION_TITLES: Record<string, string> = {
  summarize_recording: 'AI 总结',
  extract_highlights: '亮点提取',
  suggest_title: '推荐标题',
  generate_chapters: '章节生成',
  extract_text: 'OCR 文字提取',
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
  } catch {
    return dateStr
  }
}

function onVideoLoaded(e: Event) {
  const video = e.target as HTMLVideoElement
  recordingDuration.value = Math.floor(video.duration || 0)
}

async function extractKeyFrames(blob: Blob, intervalSeconds: number = 5): Promise<string[]> {
  const frames: string[] = []
  const video = document.createElement('video')
  video.muted = true
  video.playsInline = true
  const url = URL.createObjectURL(blob)
  video.src = url

  await new Promise<void>((resolve) => {
    video.onloadedmetadata = () => resolve()
    video.onerror = () => resolve()
  })

  const duration = video.duration
  if (!duration || !isFinite(duration)) {
    URL.revokeObjectURL(url)
    return frames
  }

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')!
  const maxWidth = 1280
  const scale = video.videoWidth > maxWidth ? maxWidth / video.videoWidth : 1
  canvas.width = video.videoWidth * scale
  canvas.height = video.videoHeight * scale

  for (let t = 0; t < duration; t += intervalSeconds) {
    video.currentTime = t
    await new Promise<void>((resolve) => {
      video.onseeked = () => resolve()
      setTimeout(resolve, 2000)
    })
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.6)
    frames.push(dataUrl)
  }

  URL.revokeObjectURL(url)
  return frames
}

async function startRecording() {
  if (scheduledRecording.value && scheduleTime.value) {
    const target = new Date(scheduleTime.value).getTime()
    const now = Date.now()
    if (target > now) {
      scheduleCountdown.value = Math.ceil((target - now) / 1000)
      scheduleTimer = setInterval(() => {
        scheduleCountdown.value--
        if (scheduleCountdown.value <= 0) {
          if (scheduleTimer) { clearInterval(scheduleTimer); scheduleTimer = null }
          doStartRecording()
        }
      }, 1000)
      workspaceStore.addRecentAction(`录制已计划: ${scheduleTime.value}`)
      return
    }
  }
  await doStartRecording()
}

function selectRegion() {
  regionX.value = Math.max(0, regionX.value)
  regionY.value = Math.max(0, regionY.value)
  regionW.value = Math.max(100, regionW.value)
  regionH.value = Math.max(100, regionH.value)
}

function addAnnotation() {
  if (!annotationText.value.trim() || !isRecording.value) return
  const template = TEMPLATES[selectedTemplate.value]
  const prefix = template ? `${template.stepPrefix} ${annotations.value.length + 1}: ` : ''
  annotations.value.push({
    time: elapsed.value,
    text: `${prefix}${annotationText.value.trim()}`,
  })
  visibleAnnotations.value = [...annotations.value]
  annotationText.value = ''
  workspaceStore.addRecentAction(`添加标注: ${annotations.value[annotations.value.length - 1].text}`)
}

async function generateNarration() {
  if (!narrationText.value.trim()) return
  ttsLoading.value = true
  try {
    const res = await api.post('/ai/workspace/tts/generate', {
      text: narrationText.value,
      voice: ttsVoice.value,
    }, { responseType: 'blob', timeout: 60000 })
    const blob = res.data
    narrationAudioBlob.value = blob
    if (narrationAudioUrl.value) URL.revokeObjectURL(narrationAudioUrl.value)
    narrationAudioUrl.value = URL.createObjectURL(blob)
    workspaceStore.addRecentAction('生成语音旁白')
  } catch (e) {
    console.error('TTS generation failed:', e)
    try {
      const utterance = new SpeechSynthesisUtterance(narrationText.value)
      utterance.lang = ttsVoice.value.startsWith('en') ? 'en-US' : 'zh-CN'
      speechSynthesis.speak(utterance)
      workspaceStore.addRecentAction('使用浏览器TTS播放旁白')
    } catch (e2) {
      console.error('Browser TTS also failed:', e2)
    }
  } finally {
    ttsLoading.value = false
  }
}

function playNarration() {
  if (!narrationAudioUrl.value) return
  if (isPlayingNarration.value) {
    narrationAudio?.pause()
    isPlayingNarration.value = false
    return
  }
  narrationAudio = new Audio(narrationAudioUrl.value)
  narrationAudio.onended = () => { isPlayingNarration.value = false }
  narrationAudio.play()
  isPlayingNarration.value = true
}

async function mixNarration() {
  if (!currentRecordingId.value || !narrationAudioBlob.value) return
  try {
    const formData = new FormData()
    formData.append('narration', narrationAudioBlob.value, 'narration.wav')
    await api.post(`/recordings/${currentRecordingId.value}/mix-narration`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    workspaceStore.addRecentAction('旁白已混入视频')
  } catch (e) {
    console.error('Mix narration failed:', e)
  }
}

function startChangeDetection() {
  if (!livePreview.value || !stream) return
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')!
  canvas.width = 320
  canvas.height = 180

  changeDetectionTimer = setInterval(() => {
    if (!livePreview.value || !isRecording.value) return
    try {
      ctx.drawImage(livePreview.value, 0, 0, 320, 180)
      const data = ctx.getImageData(0, 0, 320, 180).data
      let hash = 0
      for (let i = 0; i < data.length; i += 40) hash = ((hash << 5) - hash + data[i]) | 0
      const currentHash = String(hash)
      if (lastFrameData !== null && currentHash === lastFrameData) {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          mediaRecorder.pause()
          isPaused.value = true
        }
      } else {
        if (mediaRecorder && mediaRecorder.state === 'paused') {
          mediaRecorder.resume()
          isPaused.value = false
        }
      }
      lastFrameData = currentHash
    } catch {}
  }, 2000)
}

async function doStartRecording() {
  try {
    const preset = QUALITY_PRESETS[quality.value] || QUALITY_PRESETS.high
    const displayMediaOptions: DisplayMediaStreamOptions = {
      video: {
        displaySurface: sourceType.value === 'screen' ? 'monitor' : sourceType.value === 'window' ? 'window' : 'browser',
        width: { ideal: preset.maxWidth },
        frameRate: { ideal: preset.fps },
      } as MediaTrackConstraints,
      audio: includeAudio.value,
    }
    stream = await navigator.mediaDevices.getDisplayMedia(displayMediaOptions)

    let mimeType = 'video/webm;codecs=vp9'
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = 'video/webm;codecs=vp8'
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'video/webm'
      }
    }

    chunks = []
    mediaRecorder = new MediaRecorder(stream, {
      mimeType,
      videoBitsPerSecond: preset.bitrate,
    })
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType })
      recordedBlob.value = blob
      recordingSize.value = blob.size
      recordedUrl.value = URL.createObjectURL(blob)
    }
    mediaRecorder.start(1000)
    isRecording.value = true
    isPaused.value = false
    elapsed.value = 0
    timer = setInterval(() => { if (!isPaused.value) elapsed.value++ }, 1000)
    stream.getVideoTracks()[0].onended = () => { stopRecording() }

    if (livePreview.value && stream) {
      livePreview.value.srcObject = stream
    }

    annotations.value = []
    visibleAnnotations.value = []

    if (changeDetection.value) {
      startChangeDetection()
    }

    if (scheduleDuration.value > 0 && !scheduledRecording.value) {
      setTimeout(() => {
        if (isRecording.value) stopRecording()
      }, scheduleDuration.value * 60 * 1000)
    }

    workspaceStore.addRecentAction('开始屏幕录制')
  } catch (e) {
    console.error('Failed to start recording:', e)
  }
}

function pauseRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.pause()
    isPaused.value = true
    workspaceStore.addRecentAction('暂停屏幕录制')
  }
}

function resumeRecording() {
  if (mediaRecorder && mediaRecorder.state === 'paused') {
    mediaRecorder.resume()
    isPaused.value = false
    workspaceStore.addRecentAction('恢复屏幕录制')
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  if (timer) { clearInterval(timer); timer = null }
  if (scheduleTimer) { clearInterval(scheduleTimer); scheduleTimer = null }
  if (changeDetectionTimer) { clearInterval(changeDetectionTimer); changeDetectionTimer = null }
  lastFrameData = null
  isRecording.value = false
  isPaused.value = false
  recordingDuration.value = elapsed.value
  workspaceStore.addRecentAction('停止屏幕录制')
}

async function uploadRecording() {
  if (!recordedBlob.value) return
  uploading.value = true
  try {
    const keyFrames = await extractKeyFrames(recordedBlob.value, 5)
    const formData = new FormData()
    formData.append('file', recordedBlob.value, `recording_${Date.now()}.webm`)
    formData.append('duration', String(recordingDuration.value))
    formData.append('source_type', sourceType.value)
    formData.append('has_audio', String(includeAudio.value))
    formData.append('quality', quality.value)
    if (keyFrames.length > 0) {
      formData.append('key_frames', JSON.stringify(keyFrames))
    }
    if (annotations.value.length > 0) {
      formData.append('annotations', JSON.stringify(annotations.value))
    }
    if (selectedTemplate.value) {
      formData.append('template', selectedTemplate.value)
    }
    const res = await api.post('/recordings/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    currentRecordingId.value = res.data.id
    await fetchRecordings()
    workspaceStore.addRecentAction('录制已保存至服务器')
  } catch (e) {
    console.error('Failed to upload recording:', e)
  } finally {
    uploading.value = false
  }
}

function downloadRecording() {
  if (!recordedUrl.value) return
  const a = document.createElement('a')
  a.href = recordedUrl.value
  a.download = `recording_${Date.now()}.webm`
  a.click()
}

function discardRecording() {
  if (recordedUrl.value) {
    URL.revokeObjectURL(recordedUrl.value)
    recordedUrl.value = ''
  }
  recordedBlob.value = null
  chunks = []
  aiResult.value = null
  currentRecordingId.value = null
  recordingDuration.value = 0
  recordingSize.value = 0
}

async function aiAssist(action: string) {
  aiLoading.value = true
  aiResult.value = null
  aiResultTitle.value = AI_ACTION_TITLES[action] || action
  workspaceStore.addRecentAction(`录制-${AI_ACTION_TITLES[action]}`)
  try {
    if (currentRecordingId.value) {
      const res = await api.post(`/recordings/${currentRecordingId.value}/analyze`, {
        action,
        params: {
          duration: recordingDuration.value,
          source_type: sourceType.value,
        },
      })
      formatAiResult(res.data)
    } else {
      let keyFrames: string[] = []
      if (recordedBlob.value) {
        keyFrames = await extractKeyFrames(recordedBlob.value, 5)
      }
      const res = await api.post('/ai/workspace/recorder/assist', {
        action,
        params: {
          duration: recordingDuration.value,
          source_type: sourceType.value,
          key_frame_count: keyFrames.length,
        },
      })
      formatAiResult(res.data)
    }
  } catch {
    aiResult.value = 'AI 辅助暂时不可用，请稍后再试。'
  } finally {
    aiLoading.value = false
  }
}

function formatAiResult(data: any) {
  if (data.summary) {
    aiResult.value = data.summary
  } else if (data.highlights) {
    aiResult.value = data.highlights.map((h: any) => `${h.timestamp || ''} ${h.description || h}`).join('\n')
  } else if (data.titles) {
    aiResult.value = data.titles.map((t: any) => typeof t === 'string' ? t : t.text).join('\n')
  } else if (data.chapters) {
    aiResult.value = data.chapters.map((c: any) => `${c.start_time || ''} ${c.title}`).join('\n')
  } else if (data.text) {
    aiResult.value = data.text
  } else if (data.result) {
    aiResult.value = typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2)
  } else {
    aiResult.value = JSON.stringify(data, null, 2)
  }
}

async function fetchRecordings() {
  try {
    const res = await api.get('/recordings', { params: { limit: 20 } })
    recordings.value = res.data.items || res.data || []
  } catch {
    recordings.value = []
  }
}

async function loadRecording(rec: Recording) {
  try {
    const res = await api.get(`/recordings/${rec.id}/download`, { responseType: 'blob' })
    if (recordedUrl.value) URL.revokeObjectURL(recordedUrl.value)
    const blob = res.data
    recordedBlob.value = blob
    recordingSize.value = blob.size
    recordedUrl.value = URL.createObjectURL(blob)
    currentRecordingId.value = rec.id
    recordingDuration.value = rec.duration
  } catch (e) {
    console.error('Failed to load recording:', e)
  }
}

async function deleteRecording(id: string) {
  try {
    await api.delete(`/recordings/${id}`)
    recordings.value = recordings.value.filter(r => r.id !== id)
    if (currentRecordingId.value === id) {
      currentRecordingId.value = null
    }
  } catch (e) {
    console.error('Failed to delete recording:', e)
  }
}

fetchRecordings()

onUnmounted(() => {
  stopRecording()
  discardRecording()
  if (scheduleTimer) { clearInterval(scheduleTimer); scheduleTimer = null }
  if (changeDetectionTimer) { clearInterval(changeDetectionTimer); changeDetectionTimer = null }
  if (narrationAudio) { narrationAudio.pause(); narrationAudio = null }
  if (narrationAudioUrl.value) { URL.revokeObjectURL(narrationAudioUrl.value) }
})
</script>

<style scoped>
.screen-recorder { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); }
.recorder-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.recorder-header h3 { margin: 0; font-size: 15px; }
.recorder-status { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text-secondary); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #999; }
.recorder-status.recording .status-dot { background: var(--ws-danger); animation: pulse 1s infinite; }
.recorder-status.paused .status-dot { background: var(--ws-warning); animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.recorder-body { flex: 1; display: flex; flex-direction: column; padding: 16px; gap: 12px; overflow: auto; }
.preview-area { flex: 1; min-height: 280px; background: var(--bg-secondary); border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }
.preview-video { width: 100%; height: 100%; object-fit: contain; }
.preview-live { width: 100%; height: 100%; position: relative; }
.live-badge { position: absolute; top: 8px; left: 8px; background: rgba(255,0,0,0.8); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: white; animation: pulse 1s infinite; }
.preview-placeholder { text-align: center; color: var(--text-tertiary); }
.preview-placeholder p { margin-top: 12px; font-size: 14px; }
.recorder-controls { display: flex; flex-direction: column; gap: 10px; }
.control-row { display: flex; gap: 16px; flex-wrap: wrap; }
.source-select, .quality-select { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.source-select select, .quality-select select { padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-primary); }
.control-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-record, .btn-stop, .btn-pause, .btn-resume, .btn-upload, .btn-download, .btn-discard { display: flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-record { background: var(--primary-color); color: white; }
.btn-record:hover { background: var(--primary-hover); }
.btn-pause { background: var(--text-secondary); color: white; }
.btn-pause:hover { background: var(--text-primary); }
.btn-resume { background: var(--text-secondary); color: white; }
.btn-resume:hover { background: var(--text-primary); }
.btn-stop { background: var(--text-secondary); color: white; }
.btn-upload { background: var(--primary-color); color: white; }
.btn-upload:hover:not(:disabled) { background: var(--primary-hover); }
.btn-upload:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-download { background: var(--primary-color); color: white; }
.btn-discard { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); }
.options { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.options label { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.recording-info { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); padding: 4px 0; }
.ai-assist-section { margin-top: 4px; padding: 10px; background: var(--bg-secondary, #f5f5f5); border-radius: 8px; }
.ai-assist-header { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
.ai-badge { font-size: 10px; background: var(--text-secondary); color: white; padding: 1px 6px; border-radius: 3px; font-weight: 400; }
.ai-assist-buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.btn-ai { display: flex; align-items: center; gap: 4px; padding: 5px 10px; border: 1px solid var(--border-color); border-radius: 6px; background: white; cursor: pointer; font-size: 12px; color: var(--text-primary); transition: all 0.15s; }
.btn-ai:hover:not(:disabled) { border-color: var(--text-secondary); color: var(--text-primary); }
.btn-ai:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-loading { display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 12px; color: var(--text-secondary); }
.loading-spinner { width: 14px; height: 14px; border: 2px solid var(--border-color); border-top-color: var(--text-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { margin-top: 10px; padding: 10px; background: white; border-radius: 6px; border: 1px solid var(--border-color); }
.ai-result-header { display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.btn-close-result { background: none; border: none; cursor: pointer; color: var(--text-secondary); padding: 2px; display: flex; }
.ai-result-content { font-size: 12px; line-height: 1.6; white-space: pre-wrap; color: var(--text-primary); }
.recordings-list { border-top: 1px solid var(--border-color); padding: 12px 16px; max-height: 200px; overflow-y: auto; }
.recordings-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.recordings-header h4 { margin: 0; font-size: 13px; }
.recordings-count { font-size: 11px; background: var(--bg-secondary, var(--text-primary)); padding: 1px 6px; border-radius: 10px; color: var(--text-secondary); }
.recordings-items { display: flex; flex-direction: column; gap: 4px; }
.recording-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
.recording-item:hover { background: var(--bg-secondary, #f0f0f0); }
.recording-thumb { width: 32px; height: 24px; background: var(--bg-secondary); border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.recording-meta { flex: 1; min-width: 0; }
.recording-title { font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recording-details { font-size: 11px; color: var(--text-secondary); }
.btn-delete-rec { background: none; border: none; cursor: pointer; color: var(--text-secondary); padding: 4px; border-radius: 4px; display: flex; }
.btn-delete-rec:hover { color: var(--ws-danger); background: rgba(255,68,68,0.1); }
.region-config { display: flex; align-items: center; gap: 6px; font-size: 13px; flex-wrap: wrap; }
.region-input { width: 70px; padding: 3px 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; }
.btn-select-region { padding: 4px 10px; border: 1px solid var(--text-secondary); border-radius: 4px; background: transparent; color: var(--text-primary); cursor: pointer; font-size: 12px; }
.btn-select-region:hover { background: var(--text-secondary); color: white; }
.smart-record-row { display: flex; align-items: center; gap: 10px; font-size: 13px; flex-wrap: wrap; }
.smart-label { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.schedule-input { padding: 3px 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; }
.duration-input { width: 50px; padding: 3px 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; }
.template-select { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.template-select select { padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-primary); }
.annotation-row { display: flex; gap: 6px; }
.annotation-input { flex: 1; padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 13px; }
.btn-annotate { padding: 6px 14px; border: 1px solid var(--primary-color); border-radius: 6px; background: var(--primary-color); color: white; cursor: pointer; font-size: 13px; }
.btn-annotate:hover:not(:disabled) { background: var(--primary-hover); }
.btn-annotate:disabled { opacity: 0.5; cursor: not-allowed; }
.annotation-overlay { position: absolute; top: 0; left: 0; right: 0; pointer-events: none; display: flex; gap: 8px; padding: 8px; flex-wrap: wrap; }
.annotation-marker { display: flex; align-items: center; gap: 4px; background: rgba(0,0,0,0.75); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.annotation-step { background: white; color: var(--text-primary); width: 16px; height: 16px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; }
.annotation-label { max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.schedule-countdown { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.8); color: white; padding: 16px 32px; border-radius: 12px; font-size: 24px; font-weight: 700; }
.narration-section { margin-top: 4px; padding: 10px; background: var(--bg-secondary, #f5f5f5); border-radius: 8px; }
.narration-header { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
.narration-controls { display: flex; flex-direction: column; gap: 6px; }
.narration-input { width: 100%; padding: 6px 10px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 13px; resize: vertical; font-family: inherit; }
.narration-actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.voice-select { padding: 4px 8px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; }
.btn-tts { padding: 5px 12px; border: 1px solid var(--primary-color); border-radius: 6px; background: var(--primary-color); color: white; cursor: pointer; font-size: 12px; }
.btn-tts:hover:not(:disabled) { background: var(--primary-hover); }
.btn-tts:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-play-narration { padding: 5px 12px; border: 1px solid var(--text-secondary); border-radius: 6px; background: var(--text-secondary); color: white; cursor: pointer; font-size: 12px; }
.btn-play-narration:hover { background: var(--text-primary); }
.btn-mix-narration { padding: 5px 12px; border: 1px solid var(--border-color); border-radius: 6px; background: transparent; color: var(--text-secondary); cursor: pointer; font-size: 12px; }
.btn-mix-narration:hover { background: var(--bg-tertiary); color: var(--text-primary); }
</style>
