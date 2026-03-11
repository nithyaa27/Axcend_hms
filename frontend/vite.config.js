import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  const isDev = command === 'serve'
  return {
    plugins: [
      vue(),
      ...(isDev ? [vueDevTools()] : []),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      proxy: {
        '/api': {
          target: process.env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
        },
        '/auth': {
          target: process.env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
