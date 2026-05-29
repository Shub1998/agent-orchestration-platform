import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    host: '0.0.0.0',
    proxy: {
      '/api': { target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: (process.env.VITE_PROXY_TARGET || 'http://localhost:8000').replace(/^http/, 'ws'), ws: true },
    },
  },
})
