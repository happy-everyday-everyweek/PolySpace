export interface ModelConfig {
  name: string
  tier: 'base' | 'strong' | 'performance' | 'cost_effective' | 'vertical_multimodal' | 'vertical_screen' | 'vertical_custom'
  provider: string
  modelId: string
  apiKey?: string
  apiBase?: string
  capabilities: string[]
  sceneDescription?: string
}

export interface BigFiveTraits {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

export interface CommunicationStyle {
  formality: number
  warmth: number
  humor: number
  conciseness: number
}

export interface ValueOrientation {
  growth: number
  harmony: number
  truth: number
  empathy: number
}

export interface PersonaSettings {
  name: string
  big_five: BigFiveTraits
  communication: CommunicationStyle
  values: ValueOrientation
  relationship: string
  catchphrases: string[]
  custom_instructions: string
}

export interface Settings {
  general: GeneralSettings
  agent: AgentSettings
  app: AppSettings
  distributed: DistributedSettings
  persona?: PersonaSettings
}

export interface GeneralSettings {
  language: string
  theme: 'light' | 'dark' | 'auto'
}

export interface AgentSettings {
  baseModel: ModelConfig | null
  strongModel: ModelConfig | null
  performanceModel: ModelConfig | null
  costEffectiveModel: ModelConfig | null
  verticalModels: ModelConfig[]
  executionMode: 'auto' | 'single' | 'multi'
}

export interface WeatherAppSettings {
  cityId: number | null
  cityName: string | null
  country: string | null
}

export interface EmailAppSettings {
  autoReply: boolean
  taskExtraction: boolean
  notification: boolean
  monitoring: boolean
}

export interface ScreenRecorderAppSettings {
  sourceType: 'screen' | 'window' | 'tab' | 'region'
  quality: 'low' | 'medium' | 'high' | 'original'
  template: string
  changeDetection: boolean
  includeAudio: boolean
  includeCursor: boolean
}

export interface PptAppSettings {
  theme: 'dark' | 'light' | 'blue' | 'green' | 'warm' | 'purple' | 'red'
}

export interface PdfAppSettings {
  watermarkText: string
  watermarkFontSize: number
  watermarkOpacity: number
  watermarkAngle: number
  watermarkPosition: 'center' | 'tile' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
}

export interface VideoAppSettings {
  exportFormat: 'mp4' | 'webm' | 'gif'
  exportQuality: 'low' | 'medium' | 'high'
  exportResolution: 'original' | '1920x1080' | '1280x720' | '854x480' | '640x360'
  includeSubtitles: boolean
}

export interface ImageAppSettings {
  brightness: number
  contrast: number
  saturate: number
  blur: number
  grayscale: number
  sepia: number
}

export interface DocumentAppSettings {
  fontFamily: string
  fontSize: string
  heading: string
}

export interface FocusTimerAppSettings {
  mode: 'pomodoro' | 'deep' | 'custom'
  workDuration: number
  breakDuration: number
  longBreakDuration: number
  sessionsBeforeLongBreak: number
}

export interface AppSettings {
  defaultMode: 'agent' | 'workspace'
  weather: WeatherAppSettings
  email: EmailAppSettings
  screenRecorder: ScreenRecorderAppSettings
  ppt: PptAppSettings
  pdf: PdfAppSettings
  video: VideoAppSettings
  image: ImageAppSettings
  document: DocumentAppSettings
  focusTimer: FocusTimerAppSettings
}

export const SYNC_SCOPES = ['settings', 'persona', 'mode', 'workspace', 'memory'] as const
export type SyncScope = typeof SYNC_SCOPES[number]

export const CONFLICT_STRATEGIES = ['latest', 'local', 'remote', 'merge'] as const
export type ConflictStrategy = typeof CONFLICT_STRATEGIES[number]

export interface DistributedSettings {
  enabled: boolean
  autoSync: boolean
  autoSyncIntervalSec: number
  syncOnStartup: boolean
  syncOnHandoff: boolean
  conflictStrategy: ConflictStrategy
  githubToken: string
  deviceId: string
  isMainBranch: boolean
  syncScopes: SyncScope[]
  localFirst: boolean
  encryptTransit: boolean
}

export interface EnvVarDefinition {
  key: string
  label: string
  group: string
  type: 'string' | 'bool' | 'int' | 'float' | 'secret' | 'path' | 'list'
  description: string
  value: any
  has_value: boolean
}

export interface CapabilityProviderSettings {
  internal_enabled: boolean
  mcp_enabled: boolean
  skill_enabled: boolean
  cli_enabled: boolean
  device_bridge_enabled: boolean
}

export interface CapabilitySummary {
  by_source: Record<string, number>
  by_category: Record<string, number>
  total: number
}

export interface CapabilitySettingsResponse {
  providers: CapabilityProviderSettings
  summary: CapabilitySummary
}

export interface EnvVariablesResponse {
  variables: Record<string, EnvVarDefinition[]>
  definitions: EnvVarDefinition[]
}
