<!--
  Players list page (route: /players).

  Fetches all players on mount and renders them in a table; each name links to
  the player's detail page.
-->
<script>
  import { onMount } from 'svelte';
  import { fetchPlayers } from '$api/client';
  // Reactive state: the fetched players and a loading flag.
  let players = $state([]);
  let loading = $state(true);
  // Load the full player list once the component mounts.
  onMount(async () => { try { players = await fetchPlayers(); } catch (err) { console.error(err); } finally { loading = false; } });
</script>

<div class="space-y-6">
  <h1 class="text-3xl font-bold text-gray-900">Players</h1>
  {#if loading}<p class="text-gray-500">Loading players...</p>
  {:else if players.length === 0}<p class="text-gray-500">No players found. Ingest some data first!</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left border border-gray-200 bg-white">
        <thead class="bg-gray-50 text-gray-600"><tr><th class="px-4 py-3">Name</th><th class="px-4 py-3">Position</th><th class="px-4 py-3">Jersey #</th><th class="px-4 py-3">Team</th></tr></thead>
        <tbody>
          {#each players as player}
            <tr class="border-t border-gray-100 hover:bg-gray-50">
              <td class="px-4 py-2"><a href="/players/{player.id}" class="text-primary-600 hover:underline font-medium">{player.first_name} {player.last_name}</a></td>
              <td class="px-4 py-2">{player.position ?? '—'}</td><td class="px-4 py-2">{player.jersey_number ?? '—'}</td><td class="px-4 py-2">{player.team_id ?? '—'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
