<template>
  <div class="music-view">
    <div class="music-header">
      <h3 class="section-label">Music</h3>
      <div class="mode-tabs">
        <button :class="['mode-btn', { active: mode === 'music' }]" @click="mode = 'music'">Music</button>
        <button :class="['mode-btn', { active: mode === 'ambient' }]" @click="mode = 'ambient'">Ambient</button>
      </div>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiRecommend">AI Recommend</button>
        <button class="ai-header-btn" @click="aiMoodMatch">AI Mood</button>
      </div>
    </div>
    <div class="music-body">
      <div v-if="mode === 'music'" class="music-mode">
        <div class="now-playing" v-if="currentTrack">
          <div class="album-art">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--ws-accent)" stroke-width="1"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg>
          </div>
          <div class="track-info">
            <span class="track-title">{{ currentTrack.title }}</span>
            <span class="track-artist">{{ currentTrack.artist }}</span>
          </div>
          <div class="playback-controls">
            <button class="ctrl-btn" @click="prevTrack">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
            </button>
            <button class="ctrl-btn play" @click="togglePlay">
              <svg v-if="!isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
            </button>
            <button class="ctrl-btn" @click="nextTrack">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
            </button>
          </div>
          <div class="progress-bar"><div class="progress-fill" :style="{ width: progress + '%' }"></div></div>
        </div>
        <div class="playlist">
          <h4 class="section-title">Playlist</h4>
          <div v-for="(t, i) in playlist" :key="t.id" :class="['playlist-item', { active: currentTrackIndex === i }]" @click="playTrack(i)">
            <span class="pl-index">{{ i + 1 }}</span>
            <div class="pl-info"><span class="pl-title">{{ t.title }}</span><span class="pl-artist">{{ t.artist }}</span></div>
            <span class="pl-duration">{{ formatDuration(t.duration) }}</span>
          </div>
          <p v-if="!playlist.length" class="no-tracks">No tracks in playlist</p>
        </div>
      </div>
      <div v-else class="ambient-mode">
        <h4 class="section-title">Ambient Sounds</h4>
        <div class="ambient-grid">
          <div v-for="sound in ambientSounds" :key="sound.name" :class="['ambient-card', { active: activeAmbient === sound.name }]" @click="toggleAmbient(sound.name)">
            <div class="ambient-icon" v-html="sound.icon"></div>
            <span class="ambient-name">{{ sound.name }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Music Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is thinking...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.tracks?.length" class="ai-section"><h5>Recommendations</h5><div v-for="t in aiResult.tracks" :key="t.title" class="rec-item"><span class="rec-title">{{ t.title }}</span><span class="rec-artist">{{ t.artist }}</span><span class="rec-reason">{{ t.reason }}</span></div></div>
          <div v-if="aiResult.sounds?.length" class="ai-section"><h5>Ambient Suggestions</h5><div v-for="s in aiResult.sounds" :key="s.name" class="ambient-rec"><span class="amb-name">{{ s.name }}</span><span class="amb-benefit">{{ s.benefit }}</span></div></div>
          <div v-if="aiResult.result && !aiResult.tracks && !aiResult.sounds" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../../utils/api'
import type { MusicTrack } from '../../types/workspace'

const mode = ref<'music' | 'ambient'>('music')
const playlist = ref<MusicTrack[]>([])
const currentTrackIndex = ref(-1)
const isPlaying = ref(false)
const progress = ref(0)
const activeAmbient = ref('')
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

const currentTrack = ref<MusicTrack | null>(null)

const ambientSounds = [
  { name: 'Rain', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ws-info)" stroke-width="1.5"><path d="M16 12h.5a3.5 3.5 0 000-7h-.2a5 5 0 00-9.8 1.5A3.5 3.5 0 008 12h8z"/><path d="M8 16v2M12 16v2M16 16v2" stroke-width="1"/></svg>' },
  { name: 'Ocean', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ws-success)" stroke-width="1.5"><path d="M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0M2 16c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/></svg>' },
  { name: 'Forest', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ws-success)" stroke-width="1.5"><path d="M12 2L7 12h3l-2 8 8-10h-3z"/></svg>' },
  { name: 'Fireplace', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ff6b35" stroke-width="1.5"><path d="M12 2c-4 4-6 8-4 12a4 4 0 008 0c2-4 0-8-4-12z"/></svg>' },
  { name: 'Wind', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ws-accent-soft)" stroke-width="1.5"><path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2"/></svg>' },
  { name: 'Cafe', icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ws-warning)" stroke-width="1.5"><path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8zM6 1v3M10 1v3M14 1v3"/></svg>' },
]

function formatDuration(s: number) { return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` }

function playTrack(index: number) {
  if (index < 0 || index >= playlist.value.length) return
  currentTrackIndex.value = index
  currentTrack.value = playlist.value[index]
  isPlaying.value = true
}

function togglePlay() { isPlaying.value = !isPlaying.value }

function prevTrack() { if (currentTrackIndex.value > 0) playTrack(currentTrackIndex.value - 1) }
function nextTrack() { if (currentTrackIndex.value < playlist.value.length - 1) playTrack(currentTrackIndex.value + 1) }

function toggleAmbient(name: string) { activeAmbient.value = activeAmbient.value === name ? '' : name }

async function aiRecommend() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/music/assist', { action: 'recommend', params: { mode: mode.value, current_mood: 'focus' } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Recommendation failed.' } }
  finally { aiLoading.value = false }
}

async function aiMoodMatch() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/music/assist', { action: mode.value === 'ambient' ? 'ambient_suggest' : 'mood_match', params: { mood: 'focused' } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Mood match failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.music-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.music-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.mode-tabs { display: flex; gap: 4px; }
.mode-btn { padding: 4px 12px; border-radius: 6px; font-size: 12px; color: var(--text-tertiary); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.mode-btn.active { background: var(--ws-accent); color: var(--bg-primary); border-color: var(--ws-accent); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.music-body { flex: 1; overflow-y: auto; padding: 16px; }
.now-playing { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; background: var(--bg-secondary); border-radius: 12px; margin-bottom: 20px; }
.album-art { width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; }
.track-info { text-align: center; }
.track-title { font-size: 16px; font-weight: 600; color: var(--text-primary); display: block; }
.track-artist { font-size: 13px; color: var(--text-tertiary); }
.playback-controls { display: flex; align-items: center; gap: 16px; }
.ctrl-btn { width: 40px; height: 40px; border-radius: 50%; border: none; background: var(--border-color); color: var(--text-primary); cursor: pointer; display: flex; align-items: center; justify-content: center; }
.ctrl-btn.play { width: 52px; height: 52px; background: var(--ws-accent); }
.ctrl-btn.play:hover { background: var(--ws-accent-hover); }
.progress-bar { width: 100%; height: 4px; background: var(--border-color); border-radius: 2px; }
.progress-fill { height: 100%; background: var(--ws-accent); border-radius: 2px; transition: width 0.3s; }
.playlist { margin-top: 12px; }
.section-title { font-size: 13px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.playlist-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; }
.playlist-item:hover { background: var(--bg-secondary); }
.playlist-item.active { background: var(--ws-accent-light); }
.pl-index { font-size: 12px; color: var(--text-tertiary); min-width: 20px; }
.pl-info { flex: 1; }
.pl-title { font-size: 13px; color: var(--text-primary); display: block; }
.pl-artist { font-size: 11px; color: var(--text-tertiary); }
.pl-duration { font-size: 11px; color: var(--text-tertiary); }
.no-tracks { color: var(--text-tertiary); text-align: center; padding: 16px; }
.ambient-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.ambient-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; background: var(--bg-secondary); border-radius: 12px; cursor: pointer; border: 2px solid transparent; }
.ambient-card:hover { border-color: var(--border-color); }
.ambient-card.active { border-color: var(--ws-accent); background: var(--ws-accent-light); }
.ambient-icon { display: flex; align-items: center; justify-content: center; }
.ambient-name { font-size: 13px; color: var(--text-primary); }
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
.rec-item { padding: 8px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 4px; }
.rec-title { font-size: 13px; color: var(--ws-accent-soft); display: block; }
.rec-artist { font-size: 11px; color: var(--text-tertiary); }
.rec-reason { font-size: 11px; color: var(--text-tertiary); }
.ambient-rec { padding: 6px 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 4px; }
.amb-name { font-size: 13px; color: var(--ws-accent-soft); margin-right: 8px; }
.amb-benefit { font-size: 12px; color: var(--text-secondary); }
</style>
