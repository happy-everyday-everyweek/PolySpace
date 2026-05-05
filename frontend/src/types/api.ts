export interface ApiError {
  error: {
    code: string
    message: string
    detail?: unknown
  }
}

export interface ChatRequest {
  message: string
  session_id?: string
  mode?: 'agent' | 'workspace'
  operation_path?: string
}

export interface ChatResponse {
  session_id: string
  reply: string
  tool_calls: ToolCallResult[]
  emotion: EmotionResponse
  inner_voice: InnerVoiceResponse | null
  action_type: string
  reflection: ReflectionResponse | null
}

export interface ToolCallResult {
  name: string
  arguments: Record<string, unknown>
  result?: unknown
  error?: string
}

export interface EmotionResponse {
  label: string
  discrete: string
  valence: number
  arousal: number
  dominance: number
  intensity: number
  intensity_desc: string
}

export interface InnerVoiceResponse {
  text: string
  visibility: 'private' | 'thinkable' | 'visible'
}

export interface ReflectionResponse {
  summary: string
  adjustments: string[]
}

export interface PersonaResponse {
  name: string
  relationship: string
  big_five: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
  communication: {
    formality: number
    warmth: number
    humor: number
    conciseness: number
  }
  evolution_summary: string
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  version: string
  database: 'ok' | 'unavailable'
  services: Record<string, string>
  devices: {
    total: number
    online: number
  }
}

export interface ModelListResponse {
  models: ModelEntry[]
}

export interface ModelEntry {
  id: string
  name: string
  tier: string
  provider: string
  model_id: string
  capabilities: string[]
  scene_description: string
}

export interface StreamChunk {
  type: 'content' | 'tool_call' | 'tool_result' | 'thinking' | 'emotion' | 'inner_voice' | 'done' | 'error'
  data: Record<string, unknown>
}

export interface ToolListResponse {
  tools: ToolEntry[]
}

export interface ToolEntry {
  name: string
  description: string
  state: string
}

export interface AuditLogEntry {
  id: string
  category: string
  action: string
  level: string
  actor_type: string
  actor_id: string
  resource_type: string
  resource_id: string
  status: string
  detail: string
  created_at: string
}

export interface AuditLogResponse {
  logs: AuditLogEntry[]
  total: number
  page: number
  page_size: number
}
