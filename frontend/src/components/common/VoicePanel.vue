<template>
  <div class="voice-panel">
    <div class="voice-status" :class="'status-' + state">
      <div class="voice-indicator" :class="{ active: state !== 'idle' }">
        <div class="voice-ring" />
        <div class="voice-ring delay" />
        <svg class="voice-mic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
      </div>
      <span class="voice-state-text">{{ stateLabels[state] || '就绪' }}</span>
    </div>
    <div class="voice-controls">
      <button class="voice-btn" :class="{ active: state === 'listening' }" @click="toggleListening" :disabled="!sessionId">
        {{ state === 'listening' ? '停止' : '按住说话' }}
      </button>
      <button class="voice-btn" @click="toggleRealtime" :disabled="!sessionId">
        {{ state === 'realtime' ? '结束对话' : '实时对话' }}
      </button>
    </div>
    <div v-if="transcript" class="voice-transcript">
      <span class="transcript-label">识别结果:</span>
      <span class="transcript-text">{{ transcript }}</span>
    </div>
    <div class="voice-settings">
      <select v-model="selectedVoice" class="voice-select" @change="updateVoice">
        <option v-for="v in voices" :key="v.id" :value="v.id">{{ v.name }}</option>
      </select>
      <label class="wake-word-toggle">
        <input type="checkbox" v-model="wakeWordEnabled" />
        <span>语音唤醒</span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'

const emit = defineEmits<{
  (e: 'transcript', text: string): void
  (e: 'tts', audioData: string): void
}>()

const sessionId = ref('')
const state = ref<'idle' | 'listening' | 'processing' | 'speaking' | 'realtime'>('idle')
const transcript = ref('')
const selectedVoice = ref('default')
const voices = ref<{ id: string; name: string }[]>([])
const wakeWordEnabled = ref(false)

const stateLabels: Record<string, string> = {
  idle: '就绪',
  listening: '聆听中...',
  processing: '处理中...',
  speaking: '播放中...',
  realtime: '实时对话',
}

let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []

async function initSession() {
  try {
    const { data } = await api.post('/voice/sessions', { language: 'zh' })
    sessionId.value = data.id
  } catch (e) {
    console.error('Failed to init voice session:', e)
  }
}

async function fetchVoices() {
  try {
    const { data } = await api.get('/voice/voices')
    voices.value = data.voices || []
  } catch { /* ignore */ }
}

async function toggleListening() {
  if (state.value === 'listening') {
    stopListening()
  } else {
    startListening()
  }
}

async function startListening() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data)
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop())
      state.value = 'processing'
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      const reader = new FileReader()
      reader.onload = async () => {
        const base64 = (reader.result as string).split(',')[1]
        try {
          const { data } = await api.post(`/voice/stt?session_id=${sessionId.value}`, {
            audio_data: base64,
            language: 'zh',
          })
          transcript.value = data.text || ''
          if (data.text) emit('transcript', data.text)
        } catch { /* ignore */ }
        state.value = 'idle'
      }
      reader.readAsDataURL(blob)
    }
    mediaRecorder.start()
    state.value = 'listening'
  } catch (e) {
    console.error('Microphone access denied:', e)
    state.value = 'idle'
  }
}

function stopListening() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop()
  }
}

async function toggleRealtime() {
  if (state.value === 'realtime') {
    try {
      await api.post(`/voice/realtime/${sessionId.value}/stop`)
    } catch { /* ignore */ }
    state.value = 'idle'
  } else {
    try {
      await api.post(`/voice/realtime/${sessionId.value}/start`)
      state.value = 'realtime'
    } catch { /* ignore */ }
  }
}

async function speak(text: string) {
  if (!sessionId.value) return
  state.value = 'speaking'
  try {
    const { data } = await api.post(`/voice/tts?session_id=${sessionId.value}`, {
      text,
      voice: selectedVoice.value,
      speed: 1.0,
      language: 'zh',
    })
    if (data.audio_data) {
      emit('tts', data.audio_data)
    }
  } catch { /* ignore */ }
  state.value = 'idle'
}

function updateVoice() { /* voice updated via v-model */ }

onMounted(() => {
  initSession()
  fetchVoices()
})

onUnmounted(() => {
  if (sessionId.value) {
    api.delete(`/voice/sessions/${sessionId.value}`).catch(() => {})
  }
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
})

defineExpose({ speak })
</script>

<style scoped>
.voice-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.voice-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.voice-indicator {
  position: relative;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.voice-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid var(--accent-color, #6366f1);
  opacity: 0;
}
.voice-indicator.active .voice-ring {
  animation: pulse-ring 1.5s ease-out infinite;
}
.voice-indicator.active .voice-ring.delay {
  animation-delay: 0.5s;
}
@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.5); opacity: 0; }
}
.voice-mic {
  width: 32px;
  height: 32px;
  color: var(--accent-color, #6366f1);
  position: relative;
  z-index: 1;
}
.voice-state-text {
  font-size: 13px;
  color: var(--text-secondary, #888);
}
.status-listening .voice-state-text { color: #4ade80; }
.status-realtime .voice-state-text { color: #60a5fa; }
.voice-controls {
  display: flex;
  gap: 8px;
}
.voice-btn {
  padding: 8px 20px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 20px;
  background: var(--bg-secondary, #2a2a4a);
  color: var(--text-primary, #e0e0e0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.voice-btn.active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}
.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.voice-transcript {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
}
.transcript-label {
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin-right: 8px;
}
.transcript-text {
  font-size: 14px;
  color: var(--text-primary, #e0e0e0);
}
.voice-settings {
  display: flex;
  gap: 16px;
  align-items: center;
}
.voice-select {
  padding: 4px 10px;
  border: 1px solid var(--border-color, #2a2a4a);
  border-radius: 4px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, #e0e0e0);
  font-size: 12px;
}
.wake-word-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #888);
  cursor: pointer;
}
.wake-word-toggle input {
  accent-color: var(--accent-color, #6366f1);
}
</style>
