// Vite configuration for the dev server and build.
// Registers the SvelteKit and Tailwind plugins and sets up a dev proxy so that
// frontend `/api` and `/ws` requests are forwarded to the FastAPI backend on
// :8000 (avoiding CORS during local development).

import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit(), tailwindcss()],
  server: {
    port: 5173,
    // Forward API and WebSocket traffic to the backend during development.
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true }
    }
  }
});
