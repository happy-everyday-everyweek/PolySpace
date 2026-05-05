import { ref, computed } from 'vue'
import api from '@/utils/api'

export interface DeviceCapability {
  name: string
  description: string
  actions: string[]
  parameters: Record<string, unknown>
}

export interface ConnectedDeviceInfo {
  device_id: string
  device_name: string
  platform: string
  status: string
  capabilities: DeviceCapability[]
  connected_at: string
  last_heartbeat: number
  metadata: Record<string, unknown>
}

const devices = ref<ConnectedDeviceInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

export function useCrossDevice() {
  const onlineDevices = computed(() =>
    devices.value.filter(d => d.status !== 'offline')
  )

  const devicesByPlatform = computed(() => {
    const map: Record<string, ConnectedDeviceInfo[]> = {}
    for (const d of onlineDevices.value) {
      if (!map[d.platform]) map[d.platform] = []
      map[d.platform].push(d)
    }
    return map
  })

  const allCapabilities = computed(() => {
    const caps: Array<{ device: ConnectedDeviceInfo; capability: DeviceCapability }> = []
    for (const d of onlineDevices.value) {
      for (const c of d.capabilities) {
        caps.push({ device: d, capability: c })
      }
    }
    return caps
  })

  async function fetchDevices() {
    loading.value = true
    error.value = null
    try {
      const res = await api.get('/devices/list')
      devices.value = res.data.devices || []
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch devices'
    } finally {
      loading.value = false
    }
  }

  async function getDevice(deviceId: string): Promise<ConnectedDeviceInfo | null> {
    try {
      const res = await api.get(`/devices/${deviceId}`)
      return res.data
    } catch {
      return null
    }
  }

  async function getDeviceCapabilities(deviceId: string): Promise<DeviceCapability[]> {
    try {
      const res = await api.get(`/devices/${deviceId}/capabilities`)
      return res.data.capabilities || []
    } catch {
      return []
    }
  }

  async function executeOnDevice(
    deviceId: string,
    toolName: string,
    action: string = 'execute',
    params: Record<string, unknown> = {},
    timeout: number = 60
  ): Promise<Record<string, unknown>> {
    try {
      const res = await api.post(`/devices/${deviceId}/execute`, {
        tool_name: toolName,
        action,
        params,
        timeout,
      })
      return res.data
    } catch (e: any) {
      return { status: 'error', message: e.message || 'Execution failed' }
    }
  }

  async function disconnectDevice(deviceId: string): Promise<boolean> {
    try {
      await api.delete(`/devices/${deviceId}`)
      devices.value = devices.value.filter(d => d.device_id !== deviceId)
      return true
    } catch {
      return false
    }
  }

  function findDeviceForTool(toolName: string, action?: string): ConnectedDeviceInfo | undefined {
    for (const d of onlineDevices.value) {
      for (const c of d.capabilities) {
        if (c.name === toolName) {
          if (action && !c.actions.includes(action)) continue
          return d
        }
      }
    }
    return undefined
  }

  function findDevicesByCapability(capabilityName: string): ConnectedDeviceInfo[] {
    return onlineDevices.value.filter(d =>
      d.capabilities.some(c => c.name === capabilityName)
    )
  }

  return {
    devices,
    onlineDevices,
    devicesByPlatform,
    allCapabilities,
    loading,
    error,
    fetchDevices,
    getDevice,
    getDeviceCapabilities,
    executeOnDevice,
    disconnectDevice,
    findDeviceForTool,
    findDevicesByCapability,
  }
}
