import { ref } from 'vue'
import api from '../utils/api'

export interface ChatStats {
  session_count: number
  user_message_count: number
  assistant_message_count: number
  user_characters_typed: number
}

export interface DocumentStats {
  documents_edited: number
  document_total_chars: number
  document_estimated_words: number
}

export interface AIActivityStats {
  ai_tasks_completed: number
  tool_calls_made: number
  ai_duration_seconds: number
  ai_estimated_time_saved_minutes: number
  file_edits: number
}

export interface TokenModelStats {
  model_name: string
  count: number
  input_tokens: number
  output_tokens: number
}

export interface TokenStats {
  total_records: number
  total_input_tokens: number
  total_output_tokens: number
  total_tokens: number
  by_model: TokenModelStats[]
}

export interface OverviewStats {
  period: string
  chat: ChatStats
  documents: DocumentStats
  ai_activity: AIActivityStats
  tokens: TokenStats
}

const stats = ref<OverviewStats | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchStats(period?: string) {
  loading.value = true
  error.value = null
  try {
    const params: Record<string, string> = {}
    if (period && period !== 'all') {
      params.period = period
    }
    const resp = await api.get('/overview/stats', { params })
    stats.value = resp.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch overview stats'
  } finally {
    loading.value = false
  }
}

export function useOverview() {
  return {
    stats,
    loading,
    error,
    fetchStats,
  }
}
