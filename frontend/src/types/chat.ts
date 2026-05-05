export interface EmotionState {
  label: string
  discrete: string
  valence: number
  arousal: number
  dominance: number
  intensity: number
  intensity_desc: string
  recent_triggers?: string[]
}

export interface InnerVoice {
  text: string
  visibility: 'private' | 'thinkable' | 'visible'
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: number
  toolCalls?: ToolCall[]
  toolResults?: ToolResult[]
  emotion?: EmotionState
  innerVoice?: InnerVoice
  actionType?: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
}

export interface ToolResult {
  toolCallId: string
  name: string
  result: unknown
  error?: string
}

export type ChatStreamChunk = {
  type: 'content' | 'tool_call' | 'tool_result' | 'thinking' | 'done'
  data: unknown
}
