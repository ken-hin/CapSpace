export function createGameSocket(gameId: string | number, onEvent: (data: any) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const socket = new WebSocket(`${protocol}//${window.location.host}/ws/game/${gameId}`);
  socket.onopen = () => console.log(`[WS] Connected to game ${gameId}`);
  socket.onmessage = (event) => { try { onEvent(JSON.parse(event.data)); } catch (err) { console.error('[WS] Parse error:', err); } };
  socket.onclose = (event) => { if (event.code !== 1000) setTimeout(() => createGameSocket(gameId, onEvent), 3000); };
  socket.onerror = (err) => console.error('[WS] Error:', err);
  return socket;
}
