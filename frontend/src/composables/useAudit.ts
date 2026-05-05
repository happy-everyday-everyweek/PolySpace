import { ref } from 'vue'
import api from '../utils/api'

export interface AuditLogEntry {
  id: string
  trace_id: string
  span_id: string
  parent_span_id: string | null
  timestamp: string | null
  category: string
  level: string
  action: string
  actor_type: string
  actor_id: string
  actor_ip: string
  source_device_id: string | null
  source_platform: string | null
  target_device_id: string | null
  target_platform: string | null
  resource_type: string
  resource_id: string
  status: string
  duration_ms: number | null
  request_summary: string
  response_summary: string
  detail: string
  checksum: string | null
}

export interface AuditStats {
  total: number
  by_category: Record<string, number>
  by_level: Record<string, number>
  by_status: Record<string, number>
  by_device: Record<string, number>
}

export interface IntegrityResult {
  total: number
  verified: number
  failed: number
  failed_ids: string[]
  integrity_rate: number
}

const logs = ref<AuditLogEntry[]>([])
const stats = ref<AuditStats | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const totalCount = ref(0)

async function fetchLogs(params: {
  category?: string
  level?: string
  actor_type?: string
  source_device_id?: string
  target_device_id?: string
  trace_id?: string
  status?: string
  start_time?: string
  end_time?: string
  limit?: number
  offset?: number
} = {}) {
  loading.value = true
  error.value = null
  try {
    const resp = await api.get('/audit/logs', { params })
    logs.value = resp.data.logs
    totalCount.value = resp.data.count
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch audit logs'
  } finally {
    loading.value = false
  }
}

async function fetchStats(params: {
  start_time?: string
  end_time?: string
} = {}) {
  try {
    const resp = await api.get('/audit/stats', { params })
    stats.value = resp.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch audit stats'
  }
}

async function fetchTraceChain(traceId: string) {
  try {
    const resp = await api.get(`/audit/trace/${traceId}`)
    return resp.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch trace chain'
    return null
  }
}

async function verifyIntegrity(params: {
  start_time?: string
  end_time?: string
} = {}) {
  try {
    const resp = await api.post('/audit/verify', params)
    return resp.data as IntegrityResult
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Integrity verification failed'
    return null
  }
}

export function useAudit() {
  return {
    logs,
    stats,
    loading,
    error,
    totalCount,
    fetchLogs,
    fetchStats,
    fetchTraceChain,
    verifyIntegrity,
  }
}
