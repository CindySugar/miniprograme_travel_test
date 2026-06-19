import { defineConfig } from 'vite'
import { default as uni } from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni.default ? uni.default() : uni()],
})
