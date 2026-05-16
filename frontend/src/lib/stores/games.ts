import { writable } from 'svelte/store';
export const liveGames = writable<any[]>([]);
export const selectedGameId = writable<number | null>(null);
