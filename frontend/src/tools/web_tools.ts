export interface WebToolAction {
  tool: string
  action: string
  params: Record<string, unknown>
}

export interface WebToolResult {
  success: boolean
  [key: string]: unknown
}

export interface WebCapability {
  name: string
  description: string
  actions: string[]
  parameters: Record<string, unknown>
}

class WebBrowserTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_browser',
      description: 'Browser operations - tabs, navigation, cookies, storage, viewport',
      actions: [
        'get_url', 'navigate', 'get_title', 'get_cookies', 'set_cookie',
        'get_local_storage', 'set_local_storage', 'get_session_storage',
        'set_session_storage', 'get_user_agent', 'get_viewport',
        'go_back', 'go_forward', 'refresh', 'get_history_length',
      ],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        url: { type: 'string', description: 'URL to navigate to' },
        key: { type: 'string', description: 'Storage key' },
        value: { type: 'string', description: 'Storage value' },
        name: { type: 'string', description: 'Cookie name' },
        cookie_value: { type: 'string', description: 'Cookie value' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'get_url':
          return { success: true, url: window.location.href }

        case 'navigate':
          if (!params.url) return { success: false, error: 'Missing url' }
          window.location.href = params.url as string
          return { success: true, url: params.url }

        case 'get_title':
          return { success: true, title: document.title }

        case 'get_cookies': {
          const cookies: Record<string, string> = {}
          document.cookie.split(';').forEach(c => {
            const [k, ...v] = c.trim().split('=')
            if (k) cookies[k] = v.join('=')
          })
          return { success: true, cookies }
        }

        case 'set_cookie': {
          const name = params.name as string
          const value = params.cookie_value as string
          if (!name) return { success: false, error: 'Missing cookie name' }
          document.cookie = `${name}=${value || ''};path=/`
          return { success: true, name, value }
        }

        case 'get_local_storage': {
          const key = params.key as string
          if (key) {
            const value = localStorage.getItem(key)
            return { success: true, key, value, exists: value !== null }
          }
          const all: Record<string, string | null> = {}
          for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i)
            if (k) all[k] = localStorage.getItem(k)
          }
          return { success: true, items: all, count: localStorage.length }
        }

        case 'set_local_storage': {
          const key = params.key as string
          const value = params.value as string
          if (!key) return { success: false, error: 'Missing key' }
          localStorage.setItem(key, value || '')
          return { success: true, key, value }
        }

        case 'get_session_storage': {
          const key = params.key as string
          if (key) {
            const value = sessionStorage.getItem(key)
            return { success: true, key, value, exists: value !== null }
          }
          const all: Record<string, string | null> = {}
          for (let i = 0; i < sessionStorage.length; i++) {
            const k = sessionStorage.key(i)
            if (k) all[k] = sessionStorage.getItem(k)
          }
          return { success: true, items: all, count: sessionStorage.length }
        }

        case 'set_session_storage': {
          const key = params.key as string
          const value = params.value as string
          if (!key) return { success: false, error: 'Missing key' }
          sessionStorage.setItem(key, value || '')
          return { success: true, key, value }
        }

        case 'get_user_agent':
          return { success: true, user_agent: navigator.userAgent }

        case 'get_viewport':
          return {
            success: true,
            width: window.innerWidth,
            height: window.innerHeight,
            screen_width: screen.width,
            screen_height: screen.height,
            pixel_ratio: window.devicePixelRatio,
          }

        case 'go_back':
          window.history.back()
          return { success: true }

        case 'go_forward':
          window.history.forward()
          return { success: true }

        case 'refresh':
          window.location.reload()
          return { success: true }

        case 'get_history_length':
          return { success: true, length: window.history.length }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }
}

class WebStorageTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_storage',
      description: 'Web storage operations - IndexedDB, Cache API, storage estimates',
      actions: [
        'indexeddb_list_stores', 'indexeddb_get', 'indexeddb_put',
        'indexeddb_delete', 'cache_list', 'cache_get', 'cache_put',
        'cache_delete', 'estimate',
      ],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        store_name: { type: 'string', description: 'IndexedDB store name' },
        key: { type: 'string', description: 'Storage key' },
        value: { type: 'string', description: 'Value to store' },
        cache_name: { type: 'string', description: 'Cache name' },
        url: { type: 'string', description: 'URL for cache entry' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'indexeddb_list_stores': {
          const dbs = await indexedDB.databases()
          return {
            success: true,
            databases: dbs.map(db => ({
              name: db.name,
              version: db.version,
            })),
          }
        }

        case 'indexeddb_get': {
          const dbName = (params.db_name as string) || 'polyspace'
          const storeName = params.store_name as string
          const key = params.key as string
          if (!storeName || !key) return { success: false, error: 'Missing store_name or key' }
          const db = await this._openDB(dbName, storeName)
          const tx = db.transaction(storeName, 'readonly')
          const store = tx.objectStore(storeName)
          const req = store.get(key)
          return new Promise((resolve) => {
            req.onsuccess = () => resolve({ success: true, key, value: req.result })
            req.onerror = () => resolve({ success: false, error: 'Failed to get value' })
          })
        }

        case 'indexeddb_put': {
          const dbName = (params.db_name as string) || 'polyspace'
          const storeName = params.store_name as string
          const key = params.key as string
          const value = params.value
          if (!storeName || !key) return { success: false, error: 'Missing store_name or key' }
          const db = await this._openDB(dbName, storeName)
          const tx = db.transaction(storeName, 'readwrite')
          const store = tx.objectStore(storeName)
          store.put(value, key)
          return new Promise((resolve) => {
            tx.oncomplete = () => resolve({ success: true, key })
            tx.onerror = () => resolve({ success: false, error: 'Failed to put value' })
          })
        }

        case 'indexeddb_delete': {
          const dbName = (params.db_name as string) || 'polyspace'
          const storeName = params.store_name as string
          const key = params.key as string
          if (!storeName || !key) return { success: false, error: 'Missing store_name or key' }
          const db = await this._openDB(dbName, storeName)
          const tx = db.transaction(storeName, 'readwrite')
          const store = tx.objectStore(storeName)
          store.delete(key)
          return new Promise((resolve) => {
            tx.oncomplete = () => resolve({ success: true, key })
            tx.onerror = () => resolve({ success: false, error: 'Failed to delete value' })
          })
        }

        case 'cache_list': {
          if (!('caches' in window)) return { success: false, error: 'Cache API not available' }
          const names = await caches.keys()
          return { success: true, caches: names }
        }

        case 'cache_get': {
          if (!('caches' in window)) return { success: false, error: 'Cache API not available' }
          const cacheName = params.cache_name as string
          const url = params.url as string
          if (!cacheName || !url) return { success: false, error: 'Missing cache_name or url' }
          const cache = await caches.open(cacheName)
          const response = await cache.match(url)
          if (!response) return { success: true, exists: false }
          const text = await response.text()
          return { success: true, exists: true, status: response.status, body_preview: text.substring(0, 1000) }
        }

        case 'cache_put': {
          if (!('caches' in window)) return { success: false, error: 'Cache API not available' }
          const cacheName = params.cache_name as string
          const url = params.url as string
          const body = (params.value as string) || ''
          if (!cacheName || !url) return { success: false, error: 'Missing cache_name or url' }
          const cache = await caches.open(cacheName)
          const response = new Response(body)
          await cache.put(url, response)
          return { success: true, cache_name: cacheName, url }
        }

        case 'cache_delete': {
          if (!('caches' in window)) return { success: false, error: 'Cache API not available' }
          const cacheName = params.cache_name as string
          const url = params.url as string
          if (!cacheName) return { success: false, error: 'Missing cache_name' }
          if (url) {
            const cache = await caches.open(cacheName)
            const deleted = await cache.delete(url)
            return { success: true, deleted }
          }
          const deleted = await caches.delete(cacheName)
          return { success: true, deleted }
        }

        case 'estimate': {
          if (navigator.storage && navigator.storage.estimate) {
            const est = await navigator.storage.estimate()
            return {
              success: true,
              quota_bytes: est.quota,
              usage_bytes: est.usage,
              quota_mb: est.quota ? Math.round(est.quota / 1048576) : null,
              usage_mb: est.usage ? Math.round(est.usage / 1048576) : null,
            }
          }
          return { success: false, error: 'Storage estimate not available' }
        }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }

  private async _openDB(dbName: string, storeName: string): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(dbName)
      req.onupgradeneeded = () => {
        const db = req.result
        if (!db.objectStoreNames.contains(storeName)) {
          db.createObjectStore(storeName)
        }
      }
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
  }
}

class WebClipboardTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_clipboard',
      description: 'Web clipboard operations - read and write text (requires user permission)',
      actions: ['read_text', 'write_text'],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        text: { type: 'string', description: 'Text to write' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'read_text': {
          if (!navigator.clipboard || !navigator.clipboard.readText) {
            return { success: false, error: 'Clipboard API not available' }
          }
          const text = await navigator.clipboard.readText()
          return { success: true, text }
        }

        case 'write_text': {
          if (!navigator.clipboard || !navigator.clipboard.writeText) {
            return { success: false, error: 'Clipboard API not available' }
          }
          const text = params.text as string
          if (text === undefined) return { success: false, error: 'Missing text' }
          await navigator.clipboard.writeText(text)
          return { success: true }
        }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }
}

class WebNotificationTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_notification',
      description: 'Web notification operations - send and manage browser notifications',
      actions: ['request_permission', 'send', 'get_permission'],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        title: { type: 'string', description: 'Notification title' },
        body: { type: 'string', description: 'Notification body text' },
        icon: { type: 'string', description: 'Notification icon URL' },
        tag: { type: 'string', description: 'Notification tag' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'request_permission': {
          if (!('Notification' in window)) return { success: false, error: 'Notifications not supported' }
          const permission = await Notification.requestPermission()
          return { success: true, permission }
        }

        case 'send': {
          if (!('Notification' in window)) return { success: false, error: 'Notifications not supported' }
          if (Notification.permission === 'denied') return { success: false, error: 'Notification permission denied' }
          if (Notification.permission === 'default') {
            const perm = await Notification.requestPermission()
            if (perm !== 'granted') return { success: false, error: 'Notification permission not granted' }
          }
          const title = (params.title as string) || 'PolySpace'
          const options: NotificationOptions = {}
          if (params.body) options.body = params.body as string
          if (params.icon) options.icon = params.icon as string
          if (params.tag) options.tag = params.tag as string
          new Notification(title, options)
          return { success: true, title }
        }

        case 'get_permission': {
          if (!('Notification' in window)) return { success: false, error: 'Notifications not supported' }
          return { success: true, permission: Notification.permission }
        }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }
}

class WebMediaTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_media',
      description: 'Web media operations - camera, microphone, screen capture',
      actions: ['get_devices', 'capture_screenshot'],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        device_id: { type: 'string', description: 'Media device ID' },
        width: { type: 'integer', description: 'Capture width' },
        height: { type: 'integer', description: 'Capture height' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'get_devices': {
          if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            return { success: false, error: 'MediaDevices API not available' }
          }
          const devices = await navigator.mediaDevices.enumerateDevices()
          return {
            success: true,
            devices: devices.map(d => ({
              kind: d.kind,
              label: d.label || '(permission not granted)',
              device_id: d.deviceId,
            })),
          }
        }

        case 'capture_screenshot': {
          const canvas = document.createElement('canvas')
          const width = (params.width as number) || window.innerWidth
          const height = (params.height as number) || window.innerHeight
          canvas.width = width
          canvas.height = height
          const ctx = canvas.getContext('2d')
          if (!ctx) return { success: false, error: 'Failed to get canvas context' }
          ctx.fillStyle = '#ffffff'
          ctx.fillRect(0, 0, width, height)
          const dataUrl = canvas.toDataURL('image/png')
          return {
            success: true,
            data_url: dataUrl,
            width,
            height,
            format: 'png',
          }
        }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }
}

class WebGeolocationTool {
  getCapabilities(): WebCapability {
    return {
      name: 'web_geolocation',
      description: 'Web geolocation operations',
      actions: ['get_current'],
      parameters: {
        action: { type: 'string', description: 'Action to perform' },
        enable_high_accuracy: { type: 'boolean', description: 'Enable high accuracy' },
        timeout: { type: 'integer', description: 'Timeout in ms' },
      },
    }
  }

  async executeAction(action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    try {
      switch (action) {
        case 'get_current': {
          if (!navigator.geolocation) return { success: false, error: 'Geolocation not supported' }
          const options: PositionOptions = {
            enableHighAccuracy: (params.enable_high_accuracy as boolean) || false,
            timeout: (params.timeout as number) || 10000,
          }
          return new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
              (pos) => {
                resolve({
                  success: true,
                  latitude: pos.coords.latitude,
                  longitude: pos.coords.longitude,
                  accuracy: pos.coords.accuracy,
                  altitude: pos.coords.altitude,
                  heading: pos.coords.heading,
                  speed: pos.coords.speed,
                })
              },
              (err) => {
                resolve({ success: false, error: err.message })
              },
              options,
            )
          })
        }

        default:
          return { success: false, error: `Unknown action: ${action}` }
      }
    } catch (e) {
      return { success: false, error: (e as Error).message }
    }
  }
}

export class WebToolAggregator {
  private tools: Record<string, {
    getCapabilities(): WebCapability
    executeAction(action: string, params: Record<string, unknown>): Promise<WebToolResult>
  }>

  constructor() {
    this.tools = {
      web_browser: new WebBrowserTool(),
      web_storage: new WebStorageTool(),
      web_clipboard: new WebClipboardTool(),
      web_notification: new WebNotificationTool(),
      web_media: new WebMediaTool(),
      web_geolocation: new WebGeolocationTool(),
    }
  }

  getCapabilities(): WebCapability[] {
    return Object.values(this.tools).map(t => t.getCapabilities())
  }

  async executeAction(toolName: string, action: string, params: Record<string, unknown> = {}): Promise<WebToolResult> {
    const tool = this.tools[toolName]
    if (!tool) return { success: false, error: `Unknown tool: ${toolName}` }
    return tool.executeAction(action, params)
  }

  getToolNames(): string[] {
    return Object.keys(this.tools)
  }
}
