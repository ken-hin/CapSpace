const API_BASE = '/api';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function fetchGames(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  return apiFetch(`/games/${query ? `?${query}` : ''}`);
}
export async function fetchGame(id: string | number) { return apiFetch(`/games/${id}`); }
export async function fetchGameStats(gameId: string | number) { return apiFetch(`/stats/game/${gameId}`); }
export async function fetchPlayers(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  return apiFetch(`/players/${query ? `?${query}` : ''}`);
}
export async function fetchPlayer(id: string | number) { return apiFetch(`/players/${id}`); }
export async function fetchPlayerStats(playerId: string | number) { return apiFetch(`/stats/player/${playerId}`); }
export async function fetchPredictions(gameId: string | number) { return apiFetch(`/predictions/game/${gameId}`); }
