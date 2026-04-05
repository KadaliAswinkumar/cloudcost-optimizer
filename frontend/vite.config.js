import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8801'
  // UI on 8080, API on 8801 (no 5xxx). Override: VITE_UI_PORT / VITE_DEV_PROXY_TARGET
  const uiPort = Number.parseInt(env.VITE_UI_PORT || '8080', 10) || 8080

  return {
  plugins: [react()],
  // Use /cloudcost-optimizer/ for GitHub Pages, / for local dev
  base: mode === 'production' ? '/cloudcost-optimizer/' : '/',
  server: {
    port: uiPort,
    strictPort: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/health': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  }
})

