import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/ws': {
        target: 'ws://127.0.0.1:9876',
        ws: true,
      },
      '/health': {
        target: 'http://127.0.0.1:9876',
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
