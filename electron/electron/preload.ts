import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  // Add any IPC methods here
  sendMessage: (channel: string, data: any) => ipcRenderer.send(channel, data),
  onMessage: (channel: string, callback: (event: any, ...args: any[]) => void) => {
    ipcRenderer.on(channel, callback);
  }
});
