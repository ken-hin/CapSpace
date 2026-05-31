/**
 * WebSocket helper for live game updates.
 *
 * Connects to the backend's per-game live-stats WebSocket endpoint and invokes a
 * callback for each parsed event. Includes basic auto-reconnect on unexpected
 * disconnects.
 */

/**
 * Open a WebSocket to the live-stats stream for a game.
 *
 * Chooses ws/wss based on the page protocol, connects to `/ws/game/{gameId}`
 * (proxied to the backend in dev), and forwards each parsed message to
 * `onEvent`. If the socket closes with a non-normal code (anything other than
 * 1000), it transparently reconnects after 3 seconds.
 *
 * @param gameId - Id of the game to subscribe to.
 * @param onEvent - Called with each parsed JSON event payload from the server.
 * @returns The created `WebSocket` instance (e.g. so callers can close it).
 */
export function createGameSocket(gameId: string | number, onEvent: (data: any) => void): WebSocket {
  // Use a secure socket when the page itself is served over HTTPS.
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const socket = new WebSocket(`${protocol}//${window.location.host}/ws/game/${gameId}`);
  socket.onopen = () => console.log(`[WS] Connected to game ${gameId}`);
  // Parse each incoming frame as JSON and hand it to the caller's handler.
  socket.onmessage = (event) => { try { onEvent(JSON.parse(event.data)); } catch (err) { console.error('[WS] Parse error:', err); } };
  // Auto-reconnect on abnormal closes (code 1000 is a clean, intentional close).
  socket.onclose = (event) => { if (event.code !== 1000) setTimeout(() => createGameSocket(gameId, onEvent), 3000); };
  socket.onerror = (err) => console.error('[WS] Error:', err);
  return socket;
}
