import { ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useModeStore } from '@/stores/mode'
import { useWorkspaceStore } from '@/stores/workspace'
import type { SyncScope } from '@/types/settings'
import api from '@/utils/api'

export interface SyncStatus {
  device_id: string
  device_name: string
  branch: string
  last_sync: string | null
  local_changes: number
  remote_pending: number
  registered_devices: number
  sync_scopes: string[]
  conflict_strategy: string
}

export interface SyncConflict {
  conflict_id: string
  path: string
  local_hash: string | null
  remote_hash: string | null
  auto_resolvable: boolean
  resolved: boolean
}

const syncing = ref(false)
const lastSyncTime = ref<string | null>(null)
const syncError = ref<string | null>(null)
const conflicts = ref<SyncConflict[]>([])
let autoSyncTimer: ReturnType<typeof setInterval> | null = null

function getDeviceId(): string {
  let id = localStorage.getItem('polyspace-device-id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('polyspace-device-id', id)
  }
  return id
}

function collectLocalChanges(scopes?: SyncScope[]): Array<{ type: string; path: string; content: string }> {
  const changes: Array<{ type: string; path: string; content: string }> = []
  const settingsStore = useSettingsStore()
  const effectiveScopes = scopes || settingsStore.settings.distributed.syncScopes

  if (effectiveScopes.includes('settings')) {
    changes.push({
      type: 'update',
      path: 'settings',
      content: JSON.stringify(settingsStore.settings),
    })
  }

  if (effectiveScopes.includes('persona') && settingsStore.persona) {
    changes.push({
      type: 'update',
      path: 'persona',
      content: JSON.stringify(settingsStore.persona),
    })
  }

  if (effectiveScopes.includes('mode')) {
    const modeStore = useModeStore()
    changes.push({
      type: 'update',
      path: 'mode',
      content: JSON.stringify({ currentMode: modeStore.currentMode }),
    })
  }

  if (effectiveScopes.includes('workspace')) {
    const workspaceStore = useWorkspaceStore()
    changes.push({
      type: 'update',
      path: 'workspace',
      content: JSON.stringify({
        activeTab: workspaceStore.activeTab,
        activeDocument: workspaceStore.activeDocument,
        activeDocumentType: workspaceStore.activeDocumentType,
        completedTasksCount: workspaceStore.completedTasksCount,
      }),
    })
  }

  return changes
}

function applyRemoteChanges(remoteChanges: Array<Record<string, unknown>>) {
  const settingsStore = useSettingsStore()
  const modeStore = useModeStore()
  const workspaceStore = useWorkspaceStore()

  for (const change of remoteChanges) {
    const path = change.path as string
    const content = change.content as string
    if (!content) continue

    try {
      const data = JSON.parse(content)
      switch (path) {
        case 'settings':
          if (data.general) Object.assign(settingsStore.settings.general, data.general)
          if (data.agent) Object.assign(settingsStore.settings.agent, data.agent)
          if (data.app) Object.assign(settingsStore.settings.app, data.app)
          if (data.distributed) Object.assign(settingsStore.settings.distributed, data.distributed)
          break
        case 'persona':
          if (settingsStore.persona) {
            Object.assign(settingsStore.persona, data)
          } else {
            settingsStore.persona = data
          }
          break
        case 'mode':
          if (data.currentMode) {
            modeStore.switchMode(data.currentMode)
          }
          break
        case 'workspace':
          if (data.activeTab) workspaceStore.setActiveTab(data.activeTab)
          if (data.activeDocument && data.activeDocumentType) {
            workspaceStore.setActiveDocument(data.activeDocument, data.activeDocumentType)
          }
          break
      }
    } catch {
      continue
    }
  }
}

export function useCloudSync() {
  const settingsStore = useSettingsStore()
  const deviceId = getDeviceId()

  async function register() {
    try {
      const res = await api.post('/sync/register', {
        device_id: deviceId,
        device_name: navigator.userAgent.includes('Android') ? 'Android Web' : 'Desktop Web',
        platform: 'web',
        sync_scopes: settingsStore.settings.distributed.syncScopes,
      })
      const data = res.data
      if (data.sync_scopes) {
        settingsStore.updateDistributed({ syncScopes: data.sync_scopes as SyncScope[] })
      }
    } catch {
      syncError.value = 'Failed to register for sync'
    }
  }

  async function push(scopes?: SyncScope[]) {
    syncing.value = true
    syncError.value = null
    try {
      const changes = collectLocalChanges(scopes)
      if (changes.length === 0) {
        syncing.value = false
        return
      }
      await api.post('/sync/push', {
        device_id: deviceId,
        changes,
      })
      lastSyncTime.value = new Date().toISOString()
    } catch (e: any) {
      syncError.value = e.message || 'Push failed'
    } finally {
      syncing.value = false
    }
  }

  async function pull(since?: string, scopes?: SyncScope[]) {
    syncing.value = true
    syncError.value = null
    try {
      const res = await api.post('/sync/pull', {
        device_id: deviceId,
        since: since || lastSyncTime.value || undefined,
        scopes: scopes || settingsStore.settings.distributed.syncScopes,
      })
      const data = res.data
      if (data.changes && data.changes.length > 0) {
        applyRemoteChanges(data.changes)
      }
      lastSyncTime.value = new Date().toISOString()
    } catch (e: any) {
      syncError.value = e.message || 'Pull failed'
    } finally {
      syncing.value = false
    }
  }

  async function sync(scopes?: SyncScope[]) {
    syncing.value = true
    syncError.value = null
    try {
      await register()
      await push(scopes)
      await pull(undefined, scopes)
    } catch (e: any) {
      syncError.value = e.message || 'Sync failed'
    } finally {
      syncing.value = false
    }
  }

  async function fetchConflicts() {
    try {
      const res = await api.get(`/sync/conflicts/${deviceId}`)
      conflicts.value = res.data.conflicts || []
    } catch {
      conflicts.value = []
    }
  }

  async function resolveConflict(conflictId: string, resolution: string = 'local') {
    try {
      await api.post('/sync/resolve-conflict', {
        conflict_id: conflictId,
        resolution,
      })
      conflicts.value = conflicts.value.filter(c => c.conflict_id !== conflictId)
    } catch (e: any) {
      syncError.value = e.message || 'Resolve failed'
    }
  }

  async function syncToGitHub(repo: string, token: string, encryptionKey: string = '') {
    syncing.value = true
    syncError.value = null
    try {
      await api.post('/sync/github', {
        device_id: deviceId,
        repo,
        token,
        encryption_key: encryptionKey,
      })
      lastSyncTime.value = new Date().toISOString()
    } catch (e: any) {
      syncError.value = e.message || 'GitHub sync failed'
    } finally {
      syncing.value = false
    }
  }

  async function fetchStatus(): Promise<SyncStatus | null> {
    try {
      const res = await api.get(`/sync/status/${deviceId}`)
      return res.data
    } catch {
      return null
    }
  }

  async function triggerHandoffSync(targetDeviceId: string) {
    try {
      await api.post('/sync/handoff', {
        source_device_id: deviceId,
        target_device_id: targetDeviceId,
      })
    } catch (e: any) {
      syncError.value = e.message || 'Handoff sync failed'
    }
  }

  async function updateSyncScopes(scopes: SyncScope[]) {
    try {
      await api.put('/sync/scopes', {
        device_id: deviceId,
        scopes,
      })
      settingsStore.updateDistributed({ syncScopes: scopes })
    } catch (e: any) {
      syncError.value = e.message || 'Update scopes failed'
    }
  }

  function startAutoSync(intervalSec: number = 300) {
    stopAutoSync()
    autoSyncTimer = setInterval(async () => {
      if (!settingsStore.settings.distributed.enabled || !settingsStore.settings.distributed.autoSync) {
        return
      }
      await sync()
    }, intervalSec * 1000)
  }

  function stopAutoSync() {
    if (autoSyncTimer) {
      clearInterval(autoSyncTimer)
      autoSyncTimer = null
    }
  }

  async function initSync() {
    if (!settingsStore.settings.distributed.enabled) return
    await register()
    if (settingsStore.settings.distributed.syncOnStartup) {
      await pull()
    }
    if (settingsStore.settings.distributed.autoSync) {
      startAutoSync(settingsStore.settings.distributed.autoSyncIntervalSec)
    }
  }

  return {
    deviceId,
    syncing,
    lastSyncTime,
    syncError,
    conflicts,
    register,
    push,
    pull,
    sync,
    fetchConflicts,
    resolveConflict,
    syncToGitHub,
    fetchStatus,
    triggerHandoffSync,
    updateSyncScopes,
    startAutoSync,
    stopAutoSync,
    initSync,
  }
}
