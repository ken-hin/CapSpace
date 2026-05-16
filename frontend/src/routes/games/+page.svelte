<script>
  import { onMount } from 'svelte';
  import { fetchGames } from '$api/client';

  let games = $state([]);
  let loading = $state(true);
  let filter = $state('all');

  onMount(() => loadGames());

  async function loadGames() {
    loading = true;
    try {
      const params = filter === 'all' ? {} : { status: filter };
      games = await fetchGames(params);
    } catch (err) {
      console.error('Failed to fetch games:', err);
    } finally {
      loading = false;
    }
  }
</script>

<div class="space-y-6">
  <h1 class="text-3xl font-bold text-gray-900">Games</h1>
  <div class="flex gap-2">
    {#each ['all', 'scheduled', 'live', 'final'] as status}
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors {filter === status ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
        onclick={() => { filter = status; loadGames(); }}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </button>
    {/each}
  </div>
  {#if loading}
    <p class="text-gray-500">Loading games...</p>
  {:else if games.length === 0}
    <p class="text-gray-500">No games found.</p>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each games as game}
        <a href="/games/{game.id}" class="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
          <div class="flex justify-between items-center">
            <span class="font-medium">{game.home_team_id}</span>
            {#if game.status === 'scheduled'}<span class="text-gray-400">vs</span>{:else}<span class="text-xl font-bold">{game.home_score} - {game.away_score}</span>{/if}
            <span class="font-medium">{game.away_team_id}</span>
          </div>
          <div class="mt-2 flex justify-between text-sm text-gray-500">
            <span>{new Date(game.scheduled_at).toLocaleDateString()}</span>
            <span class="capitalize {game.status === 'live' ? 'text-red-600 font-semibold' : ''}">{game.status}</span>
          </div>
        </a>
      {/each}
    </div>
  {/if}
</div>
