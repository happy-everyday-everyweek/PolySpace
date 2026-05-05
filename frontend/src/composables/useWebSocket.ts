import { ref, onUnmounted } from 'vue'
import { WS_BASE } from '@/utils/constants'

type MessageHandler = (data: unknown) => void

class UnifiedWebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  isConnected = ref(false)

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return

    try {
      this.ws = new WebSocket(this.url)
    } catch {
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.isConnected.value = true
      this.reconnectAttempts = 0
    }

    this.ws.onclose = () => {
      this.isConnected.value = false
      this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.isConnected.value = false
    }

    this.ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        const channel = parsed.type || parsed.channel || 'default'
        const handlers = this.handlers.get(channel)
        if (handlers) {
          for (const handler of handlers) {
            handler(parsed)
          }
        }
        const allHandlers = this.handlers.get('*')
        if (allHandlers) {
          for (const handler of allHandlers) {
            handler(parsed)
          }
        }
      } catch {
        // skip malformed messages
      }
    }
  }

  subscribe(channel: string, handler: MessageHandler) {
    if (!this.handlers.has(channel)) {
      this.handlers.set(channel, new Set())
    }
    this.handlers.get(channel)!.add(handler)
  }

  unsubscribe(channel: string, handler: MessageHandler) {
    const handlers = this.handlers.get(channel)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.handlers.delete(channel)
      }
    }
  }

  send(data: Record<string, unknown>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected.value = false
    this.reconnectAttempts = this.maxReconnectAttempts
  }

  private _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    const delay = 3000 * Math.pow(1.5, this.reconnectAttempts)
    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => this.connect(), delay)
  }
}

let sharedManager: UnifiedWebSocketManager | null = null

function getSharedManager(): UnifiedWebSocketManager {
  if (!sharedManager) {
    sharedManager = new UnifiedWebSocketManager(`${WS_BASE}/unified`)
  }
  return sharedManager
}

export function useWebSocket(_url?: string) {
  const manager = getSharedManager()
  const messages = ref<unknown[]>([])

  function connect() {
    manager.connect()
  }

  function send(data: Record<string, unknown>) {
    manager.send(data)
  }

  function disconnect() {
    manager.disconnect()
  }

  const defaultHandler = (data: unknown) => {
    messages.value.push(data)
  }

  manager.subscribe('*', defaultHandler)

  onUnmounted(() => {
    manager.unsubscribe('*', defaultHandler)
  })

  return {
    messages,
    isConnected: manager.isConnected,
    connect,
    send,
    disconnect,
    subscribe: manager.subscribe.bind(manager),
    unsubscribe: manager.unsubscribe.bind(manager),
  }
}

export { UnifiedWebSocketManager, getSharedManager }
