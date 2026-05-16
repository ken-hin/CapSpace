<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { fetchPlayer, fetchPlayerStats } from '$api/client';
  let player = $state(null);
  let stats = $state([]);
  let loading = $state(true);
  const playerId = $derived($page.params.id);
  onMount(async () => {
    try { const [p, s] = await Promise.all([fetchPlayer(playerId), fetchPlayerStats(playerId)]); player = p; stats = s; }
    catch (err) { console.error(err); } finally { loading = false; }
  });
</script>

{#if loading}<p class="text-gray-500">Loading player...</p>
{:else if !player}<p class="text-gray-500">Player not found.</p>
{:else}
  <div class="space-y-8">
    <div><h1 class="text-3xl font-bold text-gray-900">{player.first_name} {player.last_name}</h1><p class="text-gray-600">{player.position ?? 'Unknown position'} • #{player.jersey_number ?? '—'}</p></div>
    <section>
      <h2 class="text-xl font-semibold text-gray-800 mb-4">Season Stats</h2>
      {#if stats.length === 0}<p class="text-gray-500">No stats available yet.</p>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {#each stats as stat}
            <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p class="text-sm text-gray-500">{stat.event_type}</p><p class="text-2xl font-bold text-gray-900">{stat.average}</p>
              <p class="text-xs text-gray-400">avg per game • {stat.total} total</p>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  </div>
{/if}
