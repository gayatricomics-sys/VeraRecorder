import { useStore } from '../store/useStore'

export class WebSocketService {
  private socket: WebSocket | null = null
  private readonly url: string
  private shouldReconnect = false
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private pending: string[] = []

  constructor(url: string = 'ws://127.0.0.1:8000/ws') {
    this.url = url
  }

  connect() {
    this.shouldReconnect = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    // Never open a second socket: duplicate sockets each receive every
    // broadcast, which duplicated every recorded command in the timeline.
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    const socket = new WebSocket(this.url)
    this.socket = socket

    socket.onopen = () => {
      console.log('Connected to Backend WebSocket')
      const queued = this.pending
      this.pending = []
      queued.forEach((msg) => socket.send(msg))
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'COMMAND') {
          useStore.getState().addCommand(data.payload)
        } else if (data.type === 'EXPORT_SUCCESS') {
          useStore.getState().bumpExports()
        } else if (data.type === 'ERROR') {
          console.error('Backend error:', data.message)
        }
      } catch {
        // Ignore non-JSON messages
      }
    }

    socket.onclose = () => {
      if (this.socket !== socket) return
      this.socket = null
      console.log('Disconnected from Backend WebSocket')
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000)
      }
    }
  }

  sendCommand(action: string, payload?: unknown) {
    const msg = JSON.stringify({ action, payload })
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(msg)
    } else {
      // Backend may still be booting; deliver once connected.
      this.pending.push(msg)
      this.connect()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      const socket = this.socket
      this.socket = null
      socket.close()
    }
  }
}

export const wsService = new WebSocketService()
