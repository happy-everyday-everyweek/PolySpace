export interface ToolDefinition {
  type: 'function'
  function: {
    name: string
    description: string
    parameters: {
      type: string
      properties: Record<string, ToolParameter>
      required?: string[]
    }
  }
}

export interface ToolParameter {
  type: string
  description?: string
  enum?: string[]
}

export interface ToolInfo {
  name: string
  description: string
  state: 'inactive' | 'activating' | 'active' | 'calling' | 'hibernating' | 'error'
  definition: ToolDefinition
  isRemote?: boolean
}

export interface DeviceCapability {
  name: string
  description: string
  actions: string[]
  parameters: Record<string, unknown>
}

export interface ConnectedDevice {
  device_id: string
  device_name: string
  platform: 'android' | 'windows' | 'web' | 'linux' | 'macos'
  status: 'online' | 'offline' | 'busy' | 'error'
  capabilities: DeviceCapability[]
  connected_at: string
  last_heartbeat: number
  metadata: Record<string, unknown>
}

export interface DeviceListResponse {
  devices: ConnectedDevice[]
  total: number
  online: number
}

export interface DeviceExecuteRequest {
  tool_name: string
  action: string
  params: Record<string, unknown>
  timeout?: number
}
