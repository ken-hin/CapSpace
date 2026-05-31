<!--
  Predictions page (route: /predictions).

  Lists upcoming (scheduled) games as entry points to their ML-generated pre-game
  forecasts; each card links to the game detail page.
-->
<script>
  import { onMount } from 'svelte';
  import { fetchGames } from '$api/client';
  // Reactive state: the upcoming games and a loading flag.
  let upcomingGames = $state([]);
  let loading = $state(true);
  // On mount, fetch games scheduled for the future.
  onMount(async () => { try { upcomingGames = await fetchGames({ status: 'scheduled' }); } catch (err) { console.error(err); } finally { loading = false; } });
</script>

<div class="space-y-6">
  <div><h1 class="text-3xl font-bold text-gray-900">Pre-Game Predictions</h1><p class="mt-2 text-gray-600">ML-generated forecasts for upcoming games.</p></div>
  {#if loading}<p class="text-gray-500">Loading predictions...</p>
  {:else if upcomingGames.length === 0}<p class="text-gray-500">No upcoming games with predictions.</p>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2">
      {#each upcomingGames as game}
        <a href="/games/{game.id}" class="block rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
          <div class="flex justify-between items-center mb-4"><span class="text-lg font-semibold">{game.home_team_id}</span><span class="text-gray-400">vs</span><span class="text-lg font-semibold">{game.away_team_id}</span></div>
          <p class="text-sm text-gray-500">{new Date(game.scheduled_at).toLocaleDateString()} • {new Date(game.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
          <p class="mt-2 text-sm text-primary-600">View predictions →</p>
        </a>
      {/each}
    </div>
  {/if}
</div>
