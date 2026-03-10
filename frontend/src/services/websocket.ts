const _apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9405'
const WS_URL = _apiBase.replace(/^http/, 'ws') + '/ws'

type MessageHandler = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectTimer: number | null = null

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(WS_URL)

    this.ws.onopen = () => {
      console.log('[WS] Connected to site builder backend')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type
        if (type && this.handlers.has(type)) {
          this.handlers.get(type)!.forEach(handler => handler(data))
        }
        // Also fire wildcard handlers
        if (this.handlers.has('*')) {
          this.handlers.get('*')!.forEach(handler => handler(data))
        }
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('[WS] Disconnected, reconnecting in 3s...')
      this.reconnectTimer = window.setTimeout(() => this.connect(), 3000)
    }

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err)
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type)!.push(handler)
  }

  off(type: string, handler: MessageHandler) {
    const list = this.handlers.get(type)
    if (list) {
      const idx = list.indexOf(handler)
      if (idx >= 0) list.splice(idx, 1)
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }
}

export const wsService = new WebSocketService()
