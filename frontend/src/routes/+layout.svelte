<script>
  import '../app.css';
  let { children } = $props();
</script>

<div class="min-h-screen flex flex-col">
  <nav class="border-b border-gray-200 bg-white">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">
        <div class="flex items-center gap-8">
          <a href="/" class="text-xl font-bold text-primary-700">Sports Analytics</a>
          <div class="hidden sm:flex gap-6">
            <a href="/games" class="text-sm font-medium text-gray-600 hover:text-gray-900">Games</a>
            <a href="/players" class="text-sm font-medium text-gray-600 hover:text-gray-900">Players</a>
            <a href="/predictions" class="text-sm font-medium text-gray-600 hover:text-gray-900">Predictions</a>
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
  <footer class="border-t border-gray-200 bg-white py-6">
    <div class="mx-auto max-w-7xl px-4 text-center text-sm text-gray-500">Sports Analytics Platform</div>
  </footer>
</div>
