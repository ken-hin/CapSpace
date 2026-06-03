<!--
  Root layout for the entire app.

  Wraps every page in the shared chrome: global stylesheet import, top navigation
  bar (Games / Players / Predictions), the main content area where the active
  page is rendered, and the footer. Applied to all routes by SvelteKit.
-->
<script>
  // Global Tailwind / shadcn styles, loaded once for the whole app.
  import '../app.css';
  // `children` is the active page's content, rendered via {@render children()} below.
  let { children } = $props();
</script>

<div class="min-h-screen flex flex-col">
  <nav class="border-b border-gray-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">
        <div class="flex items-center gap-8">
          <a href="/" class="text-xl font-bold">Sports Analytics</a>
          <div class="hidden sm:flex gap-6">
            <a href="/games" class="text-sm font-medium hover:text-gray-300">Games</a>
            <a href="/players" class="text-sm font-medium hover:text-gray-300">Players</a>
            <a href="/predictions" class="text-sm font-medium hover:text-gray-300">Predictions</a>
          </div>
        </div>
      </div>
    </div>
  </nav>
  <main class="flex-1">
    <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {@render children()}
    </div>
  </main>
  <footer class="border-t border-gray-200 py-6">
    <div class="mx-auto max-w-7xl px-4 text-center text-sm">Sports Analytics Platform</div>
  </footer>
</div>
