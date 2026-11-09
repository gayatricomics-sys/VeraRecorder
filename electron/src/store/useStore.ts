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
  bumpExports: () => set((state) => ({ exportsVersion: state.exportsVersion + 1 })),
  setUrl: (url) => set({ url }),
  startRecording: () => set({ isRecording: true }),
  stopRecording: () => set({ isRecording: false }),
  addCommand: (command) =>
    set((state) => ({ commands: [...state.commands, command] })),
  clearCommands: () => set({ commands: [] }),
}))
