<script>
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { fetchGame, fetchGameStats } from '$api/client';
  import { createGameSocket } from '$lib/websocket';

  let game = $state(null);
  let stats = $state([]);
  let liveEvents = $state([]);
  let loading = $state(true);
  let socket = null;
  const gameId = $derived($page.params.id);

  onMount(async () => {
    try {
      const [gameData, statsData] = await Promise.all([fetchGame(gameId), fetchGameStats(gameId)]);
      game = gameData;
      stats = statsData;
      if (game.status === 'live') {
        socket = createGameSocket(gameId, (event) => {
          liveEvents = [event, ...liveEvents.slice(0, 49)];
          if (event.home_score !== undefined) game = { ...game, home_score: event.home_score, away_score: event.away_score };
        });
      }
    } catch (err) { console.error('Failed to load game:', err); }
    finally { loading = false; }
  });
  onDestroy(() => { if (socket) socket.close(); });
</script>

{#if loading}
  <p class="text-gray-500">Loading game...</p>
{:else if !game}
  <p class="text-gray-500">Game not found.</p>
{:else}
  <div class="space-y-8">
    <div class="rounded-lg bg-white border border-gray-200 p-6 text-center shadow-sm">
      <div class="flex items-center justify-center gap-8">
        <div class="text-center"><p class="text-2xl font-bold">{game.home_team_id}</p><p class="text-sm text-gray-500">Home</p></div>
        <div class="text-center">
          <p class="text-4xl font-bold">{game.home_score} - {game.away_score}</p>
          {#if game.status === 'live'}<span class="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800 mt-2">LIVE</span>{:else}<p class="text-sm text-gray-500 mt-2 capitalize">{game.status}</p>{/if}
        </div>
        <div class="text-center"><p class="text-2xl font-bold">{game.away_team_id}</p><p class="text-sm text-gray-500">Away</p></div>
      </div>
    </div>
    {#if game.status === 'live' && liveEvents.length > 0}
      <section>
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Live Feed</h2>
        <div class="space-y-2 max-h-96 overflow-y-auto">
          {#each liveEvents as event}
            <div class="rounded border border-gray-100 bg-gray-50 px-4 py-2 text-sm">
              <span class="font-medium">{event.event_type}</span>
              {#if event.player_id}<span class="text-gray-500"> — Player #{event.player_id}</span>{/if}
            </div>
          {/each}
        </div>
      </section>
    {/if}
    <section>
      <h2 class="text-xl font-semibold text-gray-800 mb-4">Box Score</h2>
      {#if stats.length === 0}<p class="text-gray-500">No stats available yet.</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left border border-gray-200">
            <thead class="bg-gray-50 text-gray-600"><tr><th class="px-4 py-3">Player</th><th class="px-4 py-3">Stat</th><th class="px-4 py-3 text-right">Count</th><th class="px-4 py-3 text-right">Total</th></tr></thead>
            <tbody>
              {#each stats as stat}<tr class="border-t border-gray-100"><td class="px-4 py-2">{stat.player_id ?? 'Team'}</td><td class="px-4 py-2">{stat.event_type}</td><td class="px-4 py-2 text-right">{stat.count}</td><td class="px-4 py-2 text-right">{stat.total}</td></tr>{/each}
            </tbody>
          </table>
        </div>
      {/if}
    </section>
  </div>
{/if}
