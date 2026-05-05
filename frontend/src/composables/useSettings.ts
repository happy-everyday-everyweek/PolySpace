import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import type { SyncScope, ConflictStrategy } from '@/types/settings'
import api from '@/utils/api'

export function useSettings() {
  const settingsStore = useSettingsStore()
  const settings = computed(() => settingsStore.settings)

  async function fetchSettings() {
    try {
      const response = await api.get('/settings')
      const data = response.data
      if (data.general) settingsStore.updateGeneral(data.general)
      if (data.agent) settingsStore.updateAgent({
        executionMode: data.agent.agent_execution_mode ?? 'auto',
      })
      if (data.app) {
        const a = data.app
        settingsStore.updateApp({
          defaultMode: a.default_mode ?? 'agent',
          weather: {
            cityId: a.weather?.city_id ?? null,
            cityName: a.weather?.city_name ?? null,
            country: a.weather?.country ?? null,
          },
          email: {
            autoReply: a.email?.auto_reply ?? true,
            taskExtraction: a.email?.task_extraction ?? true,
            notification: a.email?.notification ?? true,
            monitoring: a.email?.monitoring ?? false,
          },
          screenRecorder: {
            sourceType: a.screen_recorder?.source_type ?? 'screen',
            quality: a.screen_recorder?.quality ?? 'medium',
            template: a.screen_recorder?.template ?? '',
            changeDetection: a.screen_recorder?.change_detection ?? false,
            includeAudio: a.screen_recorder?.include_audio ?? true,
            includeCursor: a.screen_recorder?.include_cursor ?? true,
          },
          ppt: { theme: a.ppt?.theme ?? 'light' },
          pdf: {
            watermarkText: a.pdf?.watermark_text ?? '',
            watermarkFontSize: a.pdf?.watermark_font_size ?? 36,
            watermarkOpacity: a.pdf?.watermark_opacity ?? 0.3,
            watermarkAngle: a.pdf?.watermark_angle ?? -30,
            watermarkPosition: a.pdf?.watermark_position ?? 'tile',
          },
          video: {
            exportFormat: a.video?.export_format ?? 'mp4',
            exportQuality: a.video?.export_quality ?? 'medium',
            exportResolution: a.video?.export_resolution ?? 'original',
            includeSubtitles: a.video?.include_subtitles ?? false,
          },
          image: {
            brightness: a.image?.brightness ?? 100,
            contrast: a.image?.contrast ?? 100,
            saturate: a.image?.saturate ?? 100,
            blur: a.image?.blur ?? 0,
            grayscale: a.image?.grayscale ?? 0,
            sepia: a.image?.sepia ?? 0,
          },
          document: {
            fontFamily: a.document?.font_family ?? 'Default',
            fontSize: a.document?.font_size ?? 'Default',
            heading: a.document?.heading ?? 'p',
          },
          focusTimer: {
            mode: a.focus_timer?.mode ?? 'pomodoro',
            workDuration: a.focus_timer?.work_duration ?? 25,
            breakDuration: a.focus_timer?.break_duration ?? 5,
            longBreakDuration: a.focus_timer?.long_break_duration ?? 15,
            sessionsBeforeLongBreak: a.focus_timer?.sessions_before_long_break ?? 4,
          },
        })
      }
      if (data.distributed) {
        settingsStore.updateDistributed({
          enabled: data.distributed.enabled ?? true,
          autoSync: data.distributed.auto_sync ?? true,
          autoSyncIntervalSec: data.distributed.auto_sync_interval_sec ?? 300,
          syncOnStartup: data.distributed.sync_on_startup ?? true,
          syncOnHandoff: data.distributed.sync_on_handoff ?? true,
          conflictStrategy: (data.distributed.conflict_strategy ?? 'latest') as ConflictStrategy,
          githubToken: data.distributed.github_token ?? '',
          syncScopes: (data.distributed.sync_scopes ?? ['settings', 'persona', 'mode', 'workspace', 'memory']) as SyncScope[],
          localFirst: data.distributed.local_first ?? true,
          encryptTransit: data.distributed.encrypt_transit ?? true,
        })
      }
    } catch {
      // use defaults
    }
  }

  async function updateGeneral(updates: Record<string, unknown>) {
    await api.put('/settings/general', updates)
    settingsStore.updateGeneral(updates as any)
  }

  async function updateAgent(updates: Record<string, unknown>) {
    const payload: Record<string, unknown> = {}
    if ('executionMode' in updates) payload.agent_execution_mode = updates.executionMode
    await api.put('/settings/agent', payload)
    settingsStore.updateAgent(updates as any)
  }

  async function updateApp(updates: Record<string, unknown>) {
    const payload: Record<string, unknown> = {}
    if ('defaultMode' in updates) payload.default_mode = updates.defaultMode
    if ('weather' in updates) {
      const w = updates.weather as Record<string, unknown>
      payload.weather = {
        city_id: w.cityId,
        city_name: w.cityName,
        country: w.country,
      }
    }
    if ('email' in updates) {
      const e = updates.email as Record<string, unknown>
      payload.email = {
        auto_reply: e.autoReply,
        task_extraction: e.taskExtraction,
        notification: e.notification,
        monitoring: e.monitoring,
      }
    }
    if ('screenRecorder' in updates) {
      const s = updates.screenRecorder as Record<string, unknown>
      payload.screen_recorder = {
        source_type: s.sourceType,
        quality: s.quality,
        template: s.template,
        change_detection: s.changeDetection,
        include_audio: s.includeAudio,
        include_cursor: s.includeCursor,
      }
    }
    if ('ppt' in updates) payload.ppt = updates.ppt
    if ('pdf' in updates) {
      const p = updates.pdf as Record<string, unknown>
      payload.pdf = {
        watermark_text: p.watermarkText,
        watermark_font_size: p.watermarkFontSize,
        watermark_opacity: p.watermarkOpacity,
        watermark_angle: p.watermarkAngle,
        watermark_position: p.watermarkPosition,
      }
    }
    if ('video' in updates) {
      const v = updates.video as Record<string, unknown>
      payload.video = {
        export_format: v.exportFormat,
        export_quality: v.exportQuality,
        export_resolution: v.exportResolution,
        include_subtitles: v.includeSubtitles,
      }
    }
    if ('image' in updates) payload.image = updates.image
    if ('document' in updates) {
      const d = updates.document as Record<string, unknown>
      payload.document = {
        font_family: d.fontFamily,
        font_size: d.fontSize,
        heading: d.heading,
      }
    }
    if ('focusTimer' in updates) {
      const f = updates.focusTimer as Record<string, unknown>
      payload.focus_timer = {
        mode: f.mode,
        work_duration: f.workDuration,
        break_duration: f.breakDuration,
        long_break_duration: f.longBreakDuration,
        sessions_before_long_break: f.sessionsBeforeLongBreak,
      }
    }
    await api.put('/settings/app', payload)
    settingsStore.updateApp(updates as any)
  }

  async function updateDistributed(updates: Record<string, unknown>) {
    const payload: Record<string, unknown> = {}
    if ('autoSync' in updates) payload.auto_sync = updates.autoSync
    if ('autoSyncIntervalSec' in updates) payload.auto_sync_interval_sec = updates.autoSyncIntervalSec
    if ('syncOnStartup' in updates) payload.sync_on_startup = updates.syncOnStartup
    if ('syncOnHandoff' in updates) payload.sync_on_handoff = updates.syncOnHandoff
    if ('conflictStrategy' in updates) payload.conflict_strategy = updates.conflictStrategy
    if ('githubToken' in updates) payload.github_token = updates.githubToken
    if ('syncScopes' in updates) payload.sync_scopes = updates.syncScopes
    if ('localFirst' in updates) payload.local_first = updates.localFirst
    if ('encryptTransit' in updates) payload.encrypt_transit = updates.encryptTransit
    if ('enabled' in updates) payload.enabled = updates.enabled

    await api.put('/settings/distributed', payload)
    settingsStore.updateDistributed(updates as any)
  }

  return {
    settings,
    fetchSettings,
    updateGeneral,
    updateAgent,
    updateApp,
    updateDistributed,
  }
}
