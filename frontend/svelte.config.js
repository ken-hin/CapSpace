// SvelteKit configuration.
// Selects the Node server adapter (for `adapter-node` production builds), enables
// TypeScript/PostCSS preprocessing via vitePreprocess, and defines the `$`-prefixed
// import aliases used throughout the app (e.g. `$api/client`).

import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    // Path aliases resolved by both SvelteKit and the TypeScript tooling.
    alias: {
      '$components': 'src/lib/components',
      '$stores': 'src/lib/stores',
      '$api': 'src/lib/api'
    }
  }
};

export default config;
