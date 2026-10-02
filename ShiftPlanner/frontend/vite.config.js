import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// В dev-режиме запросы /api проксируются на локальный бэкенд,
// чтобы не настраивать CORS вручную. В Docker эту роль выполняет nginx.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
