/**
 * Svelte stores for shared game UI state.
 *
 * These writable stores hold cross-component state for live game data: the list
 * of currently live games and the id of the game the user has selected. Any
 * component can subscribe to react to changes.
 */
import { writable } from 'svelte/store';

/** Currently live games, kept up to date from polling / WebSocket updates. */
export const liveGames = writable<any[]>([]);

/** Id of the game the user has currently selected, or `null` if none. */
export const selectedGameId = writable<number | null>(null);
