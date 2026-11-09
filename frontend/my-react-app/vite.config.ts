import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxy = { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true, rewrite: (path: string) => path.replace(/^\/api/, '') } }
  return {
    plugins: [react()],
    define: {
      'import.meta.env.BACKEND_BASE_URL': JSON.stringify(env.BACKEND_BASE_URL || env.VITE_API_BASE_URL || '/api'),
    },
    server: { proxy },
    preview: { proxy },
  }
})
