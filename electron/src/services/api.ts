import { useStore } from '../store/useStore'

export class WebSocketService {
  private socket: WebSocket | null = null
  private readonly url: string

  constructor(url: string = 'ws://127.0.0.1:8000/ws') {
    this.url = url
  }

  connect() {
    this.socket = new WebSocket(this.url)

    this.socket.onopen = () => {
      console.log('Connected to Backend WebSocket')
    }

    this.socket.onmessage = (event) => {
      console.log('Message from server:', event.data)
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'COMMAND') {
          useStore.getState().addCommand(data.payload)
        }
      } catch (e) {
        // Handle non-JSON or other formats
      }
    }

    this.socket.onclose = () => {
      console.log('Disconnected from Backend WebSocket')
      // Try to reconnect in 3s
      setTimeout(() => this.connect(), 3000)
    }
  }

  sendCommand(action: string, payload?: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ action, payload }))
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
    }
  }
}

export const wsService = new WebSocketService()
