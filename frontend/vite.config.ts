// Vite 配置文件：统一管理 Vue 插件、路径别名与本地开发代理。
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig(({ mode }) => {
  // Vite 配置文件中需要显式 loadEnv，才能稳定读取 frontend/.env 与 .env.development。
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          // 支持通过 VITE_API_PROXY_TARGET 覆盖后端地址，便于本地规避端口冲突。
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  }
})
