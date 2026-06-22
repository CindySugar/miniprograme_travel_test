import { defineConfig } from 'vite'
import { default as uni } from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni.default ? uni.default() : uni()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
