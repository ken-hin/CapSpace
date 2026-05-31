/**
 * Typed HTTP client for the backend REST API.
 *
 * Wraps `fetch` with JSON defaults and error handling (`apiFetch`) and exposes a
 * set of thin, named helpers for each resource (games, players, stats,
 * predictions). All requests are relative to `/api`, which Vite proxies to the
 * FastAPI backend in development (see vite.config.js).
 */

/** Base path prefixed onto every request; proxied to the backend by Vite. */
const API_BASE = '/api';

/**
 * Perform a JSON `fetch` against the API and parse the response.
 *
 * @typeParam T - Expected shape of the parsed JSON response.
 * @param path - API path appended to {@link API_BASE} (e.g. `/games/`).
 * @param options - Optional `fetch` overrides (method, body, etc.).
 * @returns The parsed JSON body typed as `T`.
 * @throws Error if the response status is not OK (non-2xx).
 */
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

/**
 * Fetch a list of games, optionally filtered/paginated via query params.
 * @param params - Query parameters (e.g. `{ status: 'live', limit: 20 }`).
 */
export async function fetchGames(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  return apiFetch(`/games/${query ? `?${query}` : ''}`);
}
/** Fetch a single game by id. */
export async function fetchGame(id: string | number) { return apiFetch(`/games/${id}`); }
/** Fetch aggregated stat totals for a single game. */
export async function fetchGameStats(gameId: string | number) { return apiFetch(`/stats/game/${gameId}`); }
/**
 * Fetch a list of players, optionally filtered/paginated via query params.
 * @param params - Query parameters (e.g. `{ limit: 50 }`).
 */
export async function fetchPlayers(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
  return apiFetch(`/players/${query ? `?${query}` : ''}`);
}
/** Fetch a single player by id. */
export async function fetchPlayer(id: string | number) { return apiFetch(`/players/${id}`); }
/** Fetch aggregated stat totals for a single player. */
export async function fetchPlayerStats(playerId: string | number) { return apiFetch(`/stats/player/${playerId}`); }
/** Fetch the model predictions associated with a game. */
export async function fetchPredictions(gameId: string | number) { return apiFetch(`/predictions/game/${gameId}`); }
