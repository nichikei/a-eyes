import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables with VITE_ prefix
  const env = loadEnv(mode, '.', 'VITE_')
  
  // Get backend URL from environment variables
  const backendUrl = env.VITE_BACKEND_URL || 'http://127.0.0.1:8011'
  
  console.log(`[Vite] Mode: ${mode}, Backend URL: ${backendUrl}`)
  
  return {
    plugins: [react()],
    server: {
      // Dynamic proxy to backend with environment variable support
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
        },
        '/health': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
        },
        '/diag': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
        }
      }
    },
    define: {
      // Ensure environment variables are available at build time
      'process.env': {}
    }
  }
})