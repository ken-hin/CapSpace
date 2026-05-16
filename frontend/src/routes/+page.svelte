<script>
  import { onMount } from 'svelte';
  import { fetchGames } from '$api/client';

  let liveGames = $state([]);
  let upcomingGames = $state([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      const [live, upcoming] = await Promise.all([
        fetchGames({ status: 'live' }),
        fetchGames({ status: 'scheduled', limit: 5 }),
      ]);
      liveGames = live;
      upcomingGames = upcoming;
    } catch (err) {
      console.error('Failed to fetch games:', err);
    } finally {
      loading = false;
    }
  });
</script>

<div class="space-y-8">
  <div>
    <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
    <p class="mt-2 text-gray-600">Live scores, stats, and pre-game predictions.</p>
  </div>

  <section>
    <h2 class="text-xl font-semibold text-gray-800 mb-4">Live Games</h2>
    {#if loading}
      <p class="text-gray-500">Loading...</p>
    {:else if liveGames.length === 0}
      <div class="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center text-gray-500">No live games right now.</div>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {#each liveGames as game}
          <a href="/games/{game.id}" class="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
            <div class="flex justify-between items-center">
              <span class="font-medium">{game.home_team_id}</span>
              <span class="text-2xl font-bold">{game.home_score} - {game.away_score}</span>
              <span class="font-medium">{game.away_team_id}</span>
            </div>
            <div class="mt-2 text-center">
              <span class="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">LIVE</span>
            </div>
          </a>
        {/each}
      </div>
    {/if}
  </section>

  <section>
    <h2 class="text-xl font-semibold text-gray-800 mb-4">Upcoming Games</h2>
    {#if upcomingGames.length === 0}
      <p class="text-gray-500">No upcoming games scheduled.</p>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {#each upcomingGames as game}
          <a href="/games/{game.id}" class="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
            <div class="flex justify-between items-center">
              <span class="font-medium">{game.home_team_id}</span>
              <span class="text-gray-400">vs</span>
              <span class="font-medium">{game.away_team_id}</span>
            </div>
            <p class="mt-2 text-center text-sm text-gray-500">{new Date(game.scheduled_at).toLocaleDateString()}</p>
          </a>
        {/each}
      </div>
    {/if}
  </section>
</div>
