import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // 使用 3000 端口（或者你可以改成 5173）
    host: true, // 允许外部访问
    proxy: {
      // 可选：如果 CORS 仍有问题，可以通过代理解决
      // '/api': {
      //   target: 'http://localhost:8000',
      //   changeOrigin: true,
      // },
    },
  },
  preview: {
    port: 3000,
    host: true,
  },
});
