import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ActivityEntry {
  id: string
  type: 'document' | 'tab' | 'tool' | 'ai_action'
  name: string
  detail?: string
  timestamp: number
}

const MAX_HISTORY = 20

export const useActivityStore = defineStore('activity', () => {
  const history = ref<ActivityEntry[]>([])

  const recentContext = computed(() => {
    const now = Date.now()
    const thirtyMinutes = 30 * 60 * 1000
    return history.value.filter(
      (entry) => now - entry.timestamp < thirtyMinutes
    )
  })

  const recentDocuments = computed(() => {
    return recentContext.value
      .filter((e) => e.type === 'document')
      .map((e) => ({ name: e.name, detail: e.detail, timestamp: e.timestamp }))
  })

  const recentTabs = computed(() => {
    return recentContext.value
      .filter((e) => e.type === 'tab')
      .map((e) => ({ name: e.name, timestamp: e.timestamp }))
  })

  function recordActivity(entry: Omit<ActivityEntry, 'id' | 'timestamp'>) {
    const newEntry: ActivityEntry = {
      ...entry,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    }
    history.value.unshift(newEntry)
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY)
    }
  }

  function recordDocumentView(name: string, detail?: string) {
    recordActivity({ type: 'document', name, detail })
  }

  function recordTabSwitch(tabName: string) {
    recordActivity({ type: 'tab', name: tabName })
  }

  function recordAIAction(action: string, detail?: string) {
    recordActivity({ type: 'ai_action', name: action, detail })
  }

  function getContextSummary(): string {
    if (recentContext.value.length === 0) return ''
    const parts: string[] = []
    const docs = recentDocuments.value
    if (docs.length > 0) {
      parts.push(
        'Recent documents: ' + docs.map((d) => d.name).join(', ')
      )
    }
    const tabs = recentTabs.value
    if (tabs.length > 0) {
      parts.push('Recent tabs: ' + tabs.map((t) => t.name).join(', '))
    }
    return parts.join('; ')
  }

  function clearHistory() {
    history.value = []
  }

  return {
    history,
    recentContext,
    recentDocuments,
    recentTabs,
    recordActivity,
    recordDocumentView,
    recordTabSwitch,
    recordAIAction,
    getContextSummary,
    clearHistory,
  }
}, {
  persist: {
    key: 'polyspace-activity',
    paths: ['history'],
  },
})
