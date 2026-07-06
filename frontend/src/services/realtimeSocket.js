export function buildWebSocketUrl(path) {
  const explicitBase = import.meta.env.VITE_WS_BASE_URL;

  if (explicitBase) {
    return new URL(path, explicitBase).toString();
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}

export function openJsonStream(path, handlers = {}) {
  let socket = null;
  let closedByClient = false;
  let reconnectTimer = null;
  let reconnectAttempt = 0;

  const connect = () => {
    if (closedByClient) {
      return;
    }

    socket = new WebSocket(buildWebSocketUrl(path));
    socket.binaryType = "blob";

    socket.onopen = () => {
      reconnectAttempt = 0;
      handlers.onStatus?.("CONNECTED");
    };

    socket.onmessage = async (event) => {
      try {
        if (typeof event.data === "string") {
          handlers.onMessage?.(JSON.parse(event.data));
          return;
        }

        handlers.onBinary?.(event.data);
      } catch (error) {
        handlers.onError?.(error);
      }
    };

    socket.onerror = () => {
      handlers.onStatus?.("DISCONNECTED");
    };

    socket.onclose = () => {
      if (closedByClient) {
        return;
      }

      handlers.onStatus?.("DISCONNECTED");
      const delay = Math.min(8000, 800 * 2 ** reconnectAttempt);
      reconnectAttempt += 1;
      reconnectTimer = window.setTimeout(connect, delay);
    };
  };

  connect();

  return () => {
    closedByClient = true;
    window.clearTimeout(reconnectTimer);

    if (socket && socket.readyState <= WebSocket.OPEN) {
      socket.close();
    }
  };
}

export function isExactFrame(data, frameId) {
  return Boolean(data && Number(data.frame_id) === Number(frameId));
}

export function syncStatusFor(data, frameId) {
  if (!data || !frameId) {
    return "WAITING";
  }

  if (isExactFrame(data, frameId)) {
    return "SYNCED";
  }

  return Number(data.frame_id) < Number(frameId) ? "STALE" : "AHEAD";
}
