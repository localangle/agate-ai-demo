import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { tmpdir } from 'node:os'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  // Keep Vite's cache outside node_modules so Docker startup (npm install/ci on a
  // mounted volume) cannot race with or invalidate node_modules/.vite (missing chunks).
  cacheDir: path.join(tmpdir(), 'agate-ui-vite'),
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(path.dirname(fileURLToPath(import.meta.url)), './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
  },

})

