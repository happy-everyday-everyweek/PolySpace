<template>
  <div class="focus-view">
    <div class="focus-header">
      <h3 class="section-label">Focus Timer</h3>
      <div class="mode-tabs">
        <button :class="['mode-btn', { active: mode === 'pomodoro' }]" @click="setMode('pomodoro')">Pomodoro</button>
        <button :class="['mode-btn', { active: mode === 'deep' }]" @click="setMode('deep')">Deep Work</button>
        <button :class="['mode-btn', { active: mode === 'custom' }]" @click="setMode('custom')">Custom</button>
      </div>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiRecommend">AI Duration</button>
        <button class="ai-header-btn" @click="aiWeeklyReport">AI Report</button>
      </div>
    </div>
    <div class="focus-body">
      <div class="timer-section">
        <div class="timer-ring" :style="ringStyle">
          <div class="timer-inner">
            <span class="timer-time">{{ displayTime }}</span>
            <span class="timer-label">{{ isRunning ? (isBreak ? 'Break' : 'Focusing') : 'Ready' }}</span>
          </div>
        </div>
        <div class="timer-controls">
          <button v-if="!isRunning" class="control-btn start" @click="startTimer">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
          </button>
          <button v-else class="control-btn pause" @click="pauseTimer">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          </button>
          <button class="control-btn reset" @click="resetTimer">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
          </button>
        </div>
        <div class="task-input">
          <input v-model="currentTask" placeholder="What are you working on?" />
        </div>
      </div>
      <div class="sessions-section">
        <h4 class="section-title">Today's Sessions</h4>
        <div v-for="s in todaySessions" :key="s.id" class="session-item">
          <span class="session-task">{{ s.task }}</span>
          <span class="session-duration">{{ Math.round(s.duration / 60) }}min</span>
          <span class="session-type">{{ s.type }}</span>
        </div>
        <p v-if="!todaySessions.length" class="no-sessions">No sessions yet today</p>
      </div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Focus Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is analyzing...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.duration_minutes" class="ai-section"><h5>Recommended Duration</h5><div class="recommend-card"><span class="rec-dur">{{ aiResult.duration_minutes }}min</span><span class="rec-break">Break: {{ aiResult.break_minutes }}min</span><span class="rec-reason">{{ aiResult.reason }}</span><button class="apply-btn" @click="applyRecommendation">Apply</button></div></div>
          <div v-if="aiResult.total_hours != null" class="ai-section"><h5>Weekly Report</h5><div class="report-card"><span>Total: {{ aiResult.total_hours }}h</span><span>Sessions: {{ aiResult.sessions }}</span></div></div>
          <div v-if="aiResult.result && !aiResult.duration_minutes && aiResult.total_hours == null" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import api from '../../utils/api'
import type { FocusSession } from '../../types/workspace'
import { useAppSettings } from '@/composables/useAppSettings'

type TimerMode = 'pomodoro' | 'deep' | 'custom'
const timerDefaults = useAppSettings('focusTimer').settings.value
const mode = ref<TimerMode>(timerDefaults.mode)
const durations: Record<TimerMode, number> = { pomodoro: timerDefaults.workDuration * 60, deep: 90 * 60, custom: 45 * 60 }
const isRunning = ref(false)
const isBreak = ref(false)
const remaining = ref(durations.pomodoro)
const totalDuration = ref(durations.pomodoro)
const currentTask = ref('')
const sessions = ref<FocusSession[]>([])
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
let timerInterval: ReturnType<typeof setInterval> | null = null

const displayTime = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const ringStyle = computed(() => {
  const pct = totalDuration.value > 0 ? (remaining.value / totalDuration.value) * 100 : 100
  return { background: `conic-gradient(var(--ws-accent) ${pct}%, var(--border-color) ${pct}%)` }
})

const todaySessions = computed(() => {
  const today = new Date().toDateString()
  return sessions.value.filter(s => new Date(s.completedAt).toDateString() === today)
})

function setMode(m: TimerMode) { mode.value = m; resetTimer(); remaining.value = durations[m]; totalDuration.value = durations[m] }

function startTimer() {
  isRunning.value = true
  timerInterval = setInterval(() => {
    if (remaining.value > 0) { remaining.value-- }
    else { completeSession() }
  }, 1000)
}

function pauseTimer() { isRunning.value = false; if (timerInterval) clearInterval(timerInterval) }

function resetTimer() { pauseTimer(); remaining.value = durations[mode.value]; totalDuration.value = durations[mode.value]; isBreak.value = false }

function completeSession() {
  pauseTimer()
  sessions.value.push({ id: Date.now().toString(36), task: currentTask.value || 'Untitled', duration: totalDuration.value, completedAt: Date.now(), type: mode.value })
  isBreak.value = !isBreak.value
  if (isBreak.value) { remaining.value = 5 * 60; totalDuration.value = 5 * 60 }
  else { remaining.value = durations[mode.value]; totalDuration.value = durations[mode.value] }
}

async function aiRecommend() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/focus/assist', { action: 'recommend_duration', params: { task: currentTask.value, mode: mode.value } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Recommendation failed.' } }
  finally { aiLoading.value = false }
}

function applyRecommendation() {
  if (aiResult.value?.duration_minutes) { remaining.value = aiResult.value.duration_minutes * 60; totalDuration.value = remaining.value; showAIPanel.value = false }
}

async function aiWeeklyReport() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/focus/assist', { action: 'weekly_report', params: { sessions: sessions.value.slice(-20) } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Report generation failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.focus-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.focus-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.mode-tabs { display: flex; gap: 4px; }
.mode-btn { padding: 4px 12px; border-radius: 6px; font-size: 12px; color: var(--text-tertiary); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.mode-btn.active { background: var(--ws-accent); color: #fff; border-color: var(--ws-accent); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.focus-body { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 32px; gap: 24px; overflow-y: auto; }
.timer-ring { width: 220px; height: 220px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.timer-inner { width: 200px; height: 200px; border-radius: 50%; background: var(--bg-primary); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.timer-time { font-size: 42px; font-weight: 200; color: var(--text-primary); }
.timer-label { font-size: 13px; color: var(--ws-accent); }
.timer-controls { display: flex; gap: 12px; }
.control-btn { width: 48px; height: 48px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.control-btn.start { background: var(--ws-success); color: #fff; }
.control-btn.pause { background: var(--ws-warning); color: #fff; }
.control-btn.reset { background: var(--border-color); color: var(--text-tertiary); }
.task-input { width: 100%; max-width: 400px; }
.task-input input { width: 100%; padding: 10px 16px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); font-size: 14px; outline: none; }
.task-input input::placeholder { color: var(--text-tertiary); }
.sessions-section { width: 100%; max-width: 500px; }
.section-title { font-size: 13px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.session-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 4px; }
.session-task { flex: 1; font-size: 13px; color: var(--text-secondary); }
.session-duration { font-size: 12px; color: var(--ws-accent); }
.session-type { font-size: 10px; padding: 1px 6px; background: var(--border-color); color: var(--ws-accent-soft); border-radius: 3px; }
.no-sessions { font-size: 13px; color: var(--text-tertiary); }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: #fff; }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.recommend-card { padding: 12px; background: var(--bg-secondary); border-radius: 8px; display: flex; flex-direction: column; gap: 4px; }
.rec-dur { font-size: 24px; font-weight: 600; color: var(--ws-accent); }
.rec-break { font-size: 13px; color: var(--ws-success); }
.rec-reason { font-size: 12px; color: var(--text-tertiary); }
.apply-btn { width: 100%; padding: 8px; background: var(--ws-accent); color: #fff; border: none; border-radius: 5px; cursor: pointer; font-size: 12px; margin-top: 8px; }
.report-card { padding: 12px; background: var(--bg-secondary); border-radius: 8px; display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
</style>
