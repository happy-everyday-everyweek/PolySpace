import { ref, onMounted, onUnmounted } from 'vue'
import { WebDeviceBridgeClient } from '../tools/web_bridge_client'
import { API_BASE } from '../utils/constants'

const bridgeClient = ref<WebDeviceBridgeClient | null>(null)
const connected = ref(false)
const deviceId = ref('')
const toolNames = ref<string[]>([])

let initAttempted = false

function getBackendWsUrl(): string {
  const host = window.location.hostname
  const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80')
  return `${window.location.protocol}//${host}:${port}`
}

export function useWebBridge() {
  function initBridge() {
    if (bridgeClient.value || initAttempted) return
    initAttempted = true

    const backendUrl = getBackendWsUrl()
    const client = new WebDeviceBridgeClient(backendUrl, 'PolySpace-Web')

    client.setCallbacks(
      () => {
        connected.value = true
        deviceId.value = client.getDeviceId()
        toolNames.value = client.getToolAggregator().getToolNames()
      },
      () => {
        connected.value = false
      },
    )

    bridgeClient.value = client
    client.connect()
  }

  async function executeWebTool(toolName: string, action: string, params: Record<string, unknown> = {}) {
    if (!bridgeClient.value) {
      return { success: false, error: 'Web bridge not initialized' }
    }
    return await bridgeClient.value.getToolAggregator().executeAction(toolName, action, params)
  }

  async function executeRemoteTool(deviceId: string, toolName: string, action: string, params: Record<string, unknown> = {}) {
    const resp = await fetch(`${API_BASE}/devices/${deviceId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: toolName, action, params }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return resp.json()
  }

  function disconnect() {
    if (bridgeClient.value) {
      bridgeClient.value.disconnect()
      bridgeClient.value = null
    }
    connected.value = false
    initAttempted = false
  }

  onMounted(() => {
    initBridge()
  })

  onUnmounted(() => {
  })

  return {
    bridgeClient,
    connected,
    deviceId,
    toolNames,
    initBridge,
    executeWebTool,
    executeRemoteTool,
    disconnect,
  }
}
