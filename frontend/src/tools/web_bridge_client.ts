import { WebToolAggregator } from './web_tools'

interface BridgeMessage {
  type: string
  [key: string]: unknown
}

interface PendingRequest {
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
  timer: ReturnType<typeof setTimeout>
}

export class WebDeviceBridgeClient {
  private ws: WebSocket | null = null
  private deviceId: string = ''
  private deviceName: string = ''
  private backendUrl: string = ''
  private connected: boolean = false
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 10
  private reconnectInterval: number = 3000
  private heartbeatInterval: number = 15000
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private pendingRequests: Map<string, PendingRequest> = new Map()
  private toolAggregator: WebToolAggregator
  private onConnectedCallback: (() => void) | null = null
  private onDisconnectedCallback: (() => void) | null = null

  constructor(backendUrl: string, deviceName?: string) {
    this.backendUrl = backendUrl
    this.deviceName = deviceName || `web-${this._generateDeviceId().slice(0, 8)}`
    this.deviceId = this._generateDeviceId()
    this.toolAggregator = new WebToolAggregator()
  }

  private _generateDeviceId(): string {
    const parts = [
      navigator.userAgent.length.toString(36),
      screen.width.toString(36),
      screen.height.toString(36),
      Date.now().toString(36),
    ]
    let hash = 0
    for (const part of parts) {
      for (let i = 0; i < part.length; i++) {
        hash = ((hash << 5) - hash + part.charCodeAt(i)) | 0
      }
    }
    return Math.abs(hash).toString(16).padStart(8, '0') + Date.now().toString(16).slice(-8)
  }

  setCallbacks(onConnected: (() => void) | null, onDisconnected: (() => void) | null) {
    this.onConnectedCallback = onConnected
    this.onDisconnectedCallback = onDisconnected
  }

  connect() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsBase = this.backendUrl.replace(/^https?:/, wsProtocol).replace(/\/$/, '')
    const wsUrl = `${wsBase}/api/v1/devices/ws/${this.deviceId}`
    console.log(`[WebBridge] Connecting to ${wsUrl}`)

    try {
      this.ws = new WebSocket(wsUrl)
    } catch (e) {
      console.error(`[WebBridge] Failed to create WebSocket: ${(e as Error).message}`)
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      console.log('[WebBridge] WebSocket connected')
      this.connected = true
      this.reconnectAttempts = 0

      const capabilities = this.toolAggregator.getCapabilities()
      this._send({
        type: 'register',
        device_name: this.deviceName,
        platform: 'web',
        capabilities,
        metadata: {
          user_agent: navigator.userAgent,
          viewport: { width: window.innerWidth, height: window.innerHeight },
          pixel_ratio: window.devicePixelRatio,
          language: navigator.language,
          online: navigator.onLine,
        },
      })

      this._startHeartbeat()

      if (this.onConnectedCallback) {
        this.onConnectedCallback()
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data as string)
        this._handleMessage(message)
      } catch (e) {
        console.error(`[WebBridge] Failed to parse message: ${(e as Error).message}`)
      }
    }

    this.ws.onclose = () => {
      console.log('[WebBridge] WebSocket closed')
      this._onDisconnect()
    }

    this.ws.onerror = () => {
      console.error('[WebBridge] WebSocket error')
      this._onDisconnect()
    }
  }

  private _onDisconnect() {
    this.connected = false
    this._stopHeartbeat()

    for (const [, pending] of this.pendingRequests) {
      clearTimeout(pending.timer)
      pending.reject(new Error('WebSocket disconnected'))
    }
    this.pendingRequests.clear()

    if (this.onDisconnectedCallback) {
      this.onDisconnectedCallback()
    }

    this._scheduleReconnect()
  }

  private _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`[WebBridge] Max reconnect attempts reached`)
      return
    }
    const delay = this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts)
    this.reconnectAttempts++
    console.log(`[WebBridge] Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})`)
    setTimeout(() => this.connect(), delay)
  }

  private _startHeartbeat() {
    this._stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this._send({ type: 'heartbeat' })
    }, this.heartbeatInterval)
  }

  private _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private _send(data: BridgeMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private async _handleMessage(message: Record<string, unknown>) {
    const msgType = (message.type as string) || ''

    switch (msgType) {
      case 'register_ack':
        console.log(`[WebBridge] Registration acknowledged, tools: ${JSON.stringify(message.registered_tools || [])}`)
        break

      case 'heartbeat_ack':
        break

      case 'tool_call': {
        const requestId = message.request_id as string
        const tool = message.tool as string
        const action = message.action as string
        const params = (message.params as Record<string, unknown>) || {}

        console.log(`[WebBridge] Tool call: ${tool}/${action} (request: ${requestId})`)

        try {
          const result = await this.toolAggregator.executeAction(tool, action, params)
          this._send({
            type: 'tool_result',
            request_id: requestId,
            result,
          })
        } catch (e) {
          this._send({
            type: 'tool_error',
            request_id: requestId,
            error: (e as Error).message,
          })
        }
        break
      }

      case 'disconnect':
        console.log(`[WebBridge] Server requested disconnect: ${message.reason || ''}`)
        this.disconnect()
        break

      default:
        console.log(`[WebBridge] Unknown message type: ${msgType}`)
    }
  }

  sendCapabilityUpdate() {
    const capabilities = this.toolAggregator.getCapabilities()
    this._send({
      type: 'capability_update',
      capabilities,
    })
  }

  disconnect() {
    this._stopHeartbeat()
    this.reconnectAttempts = this.maxReconnectAttempts
    if (this.ws) {
      try {
        this._send({ type: 'disconnect', reason: 'client_shutdown' })
        this.ws.close()
      } catch (_) {}
      this.ws = null
    }
    this.connected = false
  }

  getDeviceId(): string {
    return this.deviceId
  }

  isConnected(): boolean {
    return this.connected
  }

  getToolAggregator(): WebToolAggregator {
    return this.toolAggregator
  }
}
