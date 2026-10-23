/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// FOX3_API points the dev proxy at another backend, e.g. FOX3_API=http://localhost:8001 npm run dev
export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, '.', '').FOX3_API || 'http://localhost:8000';
  return {
    plugins: [react()],
    server: { proxy: { '/api': { target, changeOrigin: false } } },
    build: { outDir: 'dist', sourcemap: false },
    test: { environment: 'jsdom', include: ['src/**/*.test.ts'] },
  };
});
