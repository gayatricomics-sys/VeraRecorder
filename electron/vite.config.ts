import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import electron from 'vite-plugin-electron'
import path from 'path'
import fs from 'fs'

// Offline support: Electron 43 downloads its runtime the first time it is
// launched. If the offline kit's cache exists (offline/prepare-offline-kit.sh),
// point Electron's downloader at it so `npm run dev` works without internet.
const offlineElectronCache = path.resolve(__dirname, '../offline/electron-cache')
if (!process.env.electron_config_cache && fs.existsSync(offlineElectronCache)) {
  process.env.electron_config_cache = offlineElectronCache
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: 'electron/main.ts',
      },
      {
        entry: 'electron/preload.ts',
        onstart(options) {
          options.reload()
        },
        vite: {
          build: {
            rollupOptions: {
              output: {
                format: 'cjs',
                entryFileNames: '[name].js',
              }
            }
          }
        }
      }
    ]),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
