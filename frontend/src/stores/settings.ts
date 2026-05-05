import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Settings, PersonaSettings, SyncScope, ConflictStrategy } from '@/types/settings'
import { SYNC_SCOPES } from '@/types/settings'
import api from '@/utils/api'

const DEFAULT_APP_SETTINGS = {
  defaultMode: 'agent' as const,
  weather: { cityId: null, cityName: null, country: null },
  email: { autoReply: true, taskExtraction: true, notification: true, monitoring: false },
  screenRecorder: { sourceType: 'screen' as const, quality: 'medium' as const, template: '', changeDetection: false, includeAudio: true, includeCursor: true },
  ppt: { theme: 'light' as const },
  pdf: { watermarkText: '', watermarkFontSize: 36, watermarkOpacity: 0.3, watermarkAngle: -30, watermarkPosition: 'tile' as const },
  video: { exportFormat: 'mp4' as const, exportQuality: 'medium' as const, exportResolution: 'original' as const, includeSubtitles: false },
  image: { brightness: 100, contrast: 100, saturate: 100, blur: 0, grayscale: 0, sepia: 0 },
  document: { fontFamily: 'Default', fontSize: 'Default', heading: 'p' },
  focusTimer: { mode: 'pomodoro' as const, workDuration: 25, breakDuration: 5, longBreakDuration: 15, sessionsBeforeLongBreak: 4 },
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Settings>({
    general: {
      language: 'zh-CN',
      theme: 'auto',
    },
    agent: {
      baseModel: null,
      strongModel: null,
      performanceModel: null,
      costEffectiveModel: null,
      verticalModels: [],
      executionMode: 'auto' as const,
    },
    app: { ...DEFAULT_APP_SETTINGS },
    distributed: {
      enabled: true,
      autoSync: true,
      autoSyncIntervalSec: 300,
      syncOnStartup: true,
      syncOnHandoff: true,
      conflictStrategy: 'latest' as ConflictStrategy,
      githubToken: '',
      deviceId: '',
      isMainBranch: false,
      syncScopes: [...SYNC_SCOPES] as SyncScope[],
      localFirst: true,
      encryptTransit: true,
    },
  })

  const persona = ref<PersonaSettings | null>(null)

  function updateGeneral(updates: Partial<Settings['general']>) {
    Object.assign(settings.value.general, updates)
  }

  function updateAgent(updates: Partial<Settings['agent']>) {
    Object.assign(settings.value.agent, updates)
  }

  function updateDistributed(updates: Partial<Settings['distributed']>) {
    Object.assign(settings.value.distributed, updates)
  }

  function updateApp(updates: Partial<Settings['app']>) {
    Object.assign(settings.value.app, updates)
  }

  async function fetchPersona() {
    try {
      const res = await api.get('/settings/persona')
      persona.value = res.data
    } catch {
      persona.value = null
    }
  }

  async function updatePersona(updates: Partial<PersonaSettings>) {
    try {
      await api.put('/settings/persona', updates)
      if (persona.value) {
        Object.assign(persona.value, updates)
      }
    } catch (error) {
      console.error('Failed to update persona:', error)
    }
  }

  return {
    settings,
    persona,
    updateGeneral,
    updateAgent,
    updateDistributed,
    updateApp,
    fetchPersona,
    updatePersona,
  }
}, {
  persist: {
    key: 'polyspace-settings',
    paths: ['settings', 'persona'],
  },
})
