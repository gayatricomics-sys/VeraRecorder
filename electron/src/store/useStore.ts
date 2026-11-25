import { create } from 'zustand'

export interface RecorderCommand {
  id: string
  command: string
  target: string
  value?: string
  confidence?: number
}

interface RecorderState {
  isRecording: boolean
  url: string
  commands: RecorderCommand[]
  exportsVersion: number
  bumpExports: () => void
  /** Last error reported by the backend, shown to the user. */
  error: string | null
  setError: (error: string | null) => void
  /** Whether the app is connected to the local backend. */
  connected: boolean
  setConnected: (connected: boolean) => void
  setUrl: (url: string) => void
  startRecording: () => void
  stopRecording: () => void
  addCommand: (command: RecorderCommand) => void
  clearCommands: () => void
}

export const useStore = create<RecorderState>((set) => ({
  isRecording: false,
  url: '',
  commands: [],
  exportsVersion: 0,
  error: null,
  setError: (error) => set({ error }),
  connected: false,
  setConnected: (connected) => set({ connected }),
  bumpExports: () => set((state) => ({ exportsVersion: state.exportsVersion + 1 })),
  setUrl: (url) => set({ url }),
  startRecording: () => set({ isRecording: true }),
  stopRecording: () => set({ isRecording: false }),
  addCommand: (command) =>
    set((state) => ({ commands: [...state.commands, command] })),
  clearCommands: () => set({ commands: [] }),
}))
