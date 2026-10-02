/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1' }, // solo localhost
  test: { environment: 'jsdom', globals: true, setupFiles: './src/setupTests.ts' },
})
