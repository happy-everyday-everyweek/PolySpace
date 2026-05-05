import { ref, onMounted, onUnmounted } from 'vue'
import type { ConnectedDevice, DeviceListResponse, DeviceExecuteRequest } from '../types/tool'
import { API_BASE } from '../utils/constants'

const devices = ref<ConnectedDevice[]>([])
const onlineCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

let statusWs: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

async function fetchDevices() {
  loading.value = true
  error.value = null
  try {
    const resp = await fetch(`${API_BASE}/devices/list`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data: DeviceListResponse = await resp.json()
    devices.value = data.devices
    onlineCount.value = data.online
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch devices'
  } finally {
    loading.value = false
  }
}

function connectStatusWs() {
  if (statusWs && statusWs.readyState === WebSocket.OPEN) return

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/devices/status/ws`

  try {
    statusWs = new WebSocket(wsUrl)
  } catch {
    return
  }

  statusWs.onopen = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  statusWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'initial') {
        devices.value = data.devices
        onlineCount.value = data.online
      } else if (data.type === 'device_status') {
        const updatedDevice = data.device as ConnectedDevice
        if (data.event === 'connected') {
          const idx = devices.value.findIndex(d => d.device_id === updatedDevice.device_id)
          if (idx >= 0) {
            devices.value[idx] = updatedDevice
          } else {
            devices.value.push(updatedDevice)
          }
        } else if (data.event === 'disconnected') {
          devices.value = devices.value.filter(d => d.device_id !== updatedDevice.device_id)
        }
        onlineCount.value = data.online
      }
    } catch {
      // skip
    }
  }

  statusWs.onclose = () => {
    reconnectTimer = setTimeout(connectStatusWs, 5000)
  }

  statusWs.onerror = () => {
    statusWs?.close()
  }
}

function disconnectStatusWs() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (statusWs) {
    statusWs.close()
    statusWs = null
  }
}

async function executeOnDevice(deviceId: string, request: DeviceExecuteRequest) {
  const resp = await fetch(`${API_BASE}/devices/${deviceId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return resp.json()
}

async function disconnectDevice(deviceId: string) {
  const resp = await fetch(`${API_BASE}/devices/${deviceId}`, {
    method: 'DELETE',
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return resp.json()
}

export function useDevices() {
  onMounted(() => {
    fetchDevices()
    connectStatusWs()
  })
  onUnmounted(() => {
    disconnectStatusWs()
  })

  return {
    devices,
    onlineCount,
    loading,
    error,
    fetchDevices,
    executeOnDevice,
    disconnectDevice,
  }
}
