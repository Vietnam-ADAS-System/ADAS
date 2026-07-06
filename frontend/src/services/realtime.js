const DEFAULT_RECONNECT_DELAY_MS = 1500;
const FALLBACK_DELAY_MS = 1800;

function normalizePath(path) {
  return path.startsWith("/") ? path : `/${path}`;
}

export function resolveApiUrl(path) {
  const normalizedPath = normalizePath(path);
  const configuredBase = import.meta.env.VITE_API_BASE_URL;

  if (configuredBase) {
    return new URL(normalizedPath, configuredBase).toString();
  }

  return normalizedPath;
}

export function resolveWsUrl(path) {
  const normalizedPath = normalizePath(path);
  const configuredBase = import.meta.env.VITE_WS_BASE_URL;

  if (configuredBase) {
    return new URL(normalizedPath, configuredBase).toString();
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${normalizedPath}`;
}

function shouldOpenBackendSocket(url) {
  return import.meta.env.VITE_ENABLE_BACKEND_WS !== "false";
}

export function toFrameId(payload) {
  const rawFrameId = payload?.frame_id ?? payload?.frameId ?? payload?.id;
  const frameId = Number(rawFrameId);
  return Number.isFinite(frameId) ? frameId : null;
}

export function parseJsonLike(data) {
  if (typeof data !== "string") {
    return data;
  }

  try {
    return JSON.parse(data);
  } catch {
    return data;
  }
}

export function createRealtimeClient({
  path,
  url,
  normalizeMessage = (data) => parseJsonLike(data),
  onMessage,
  onStatus,
  fallback,
  reconnectDelayMs = DEFAULT_RECONNECT_DELAY_MS,
  connectionName = "stream",
}) {
  let socket = null;
  let stopped = false;
  let reconnectTimer = null;
  let fallbackTimer = null;
  let fallbackStop = null;

  function emitStatus(state, detail = {}) {
    onStatus?.({
      connectionName,
      state,
      connected: state === "connected",
      usingFallback: state === "demo",
      ...detail,
    });
  }

  function stopFallback() {
    if (fallbackStop) {
      fallbackStop();
      fallbackStop = null;
    }
  }

  function startFallback(reason) {
    if (!fallback || fallbackStop || stopped) {
      return;
    }

    emitStatus("demo", { reason });
    fallbackStop = fallback(onMessage, (detail = {}) => {
      emitStatus("demo", { reason, ...detail });
    });
  }

  function scheduleFallback(reason) {
    window.clearTimeout(fallbackTimer);
    fallbackTimer = window.setTimeout(() => startFallback(reason), FALLBACK_DELAY_MS);
  }

  function scheduleReconnect() {
    if (stopped) {
      return;
    }

    window.clearTimeout(reconnectTimer);
    reconnectTimer = window.setTimeout(connect, reconnectDelayMs);
  }

  function connect() {
    if (stopped) {
      return;
    }

    const targetUrl = url || resolveWsUrl(path);
    emitStatus("connecting", { url: targetUrl });
    scheduleFallback("waiting_for_backend");

    try {
      socket = new WebSocket(targetUrl);
      socket.binaryType = "arraybuffer";
    } catch (error) {
      emitStatus("reconnecting", { error: error.message, url: targetUrl });
      startFallback("backend_unavailable");
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      window.clearTimeout(fallbackTimer);
      stopFallback();
      emitStatus("connected", { url: targetUrl });
    };

    socket.onmessage = async (event) => {
      try {
        const normalized = await normalizeMessage(event.data);
        if (normalized) {
          onMessage?.(normalized);
        }
      } catch (error) {
        emitStatus("message_error", { error: error.message, url: targetUrl });
      }
    };

    socket.onerror = () => {
      emitStatus("reconnecting", { url: targetUrl });
    };

    socket.onclose = () => {
      if (stopped) {
        return;
      }

      emitStatus("reconnecting", { url: targetUrl });
      startFallback("backend_disconnected");
      scheduleReconnect();
    };
  }

  function start() {
    stopped = false;

    if (!shouldOpenBackendSocket(url)) {
      if (fallback) {
        startFallback("demo_mode");
      } else {
        emitStatus("demo", { reason: "demo_mode" });
      }
      return;
    }

    connect();
  }

  function stop() {
    stopped = true;
    window.clearTimeout(reconnectTimer);
    window.clearTimeout(fallbackTimer);
    stopFallback();

    if (socket) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      socket.close();
      socket = null;
    }

    emitStatus("disconnected");
  }

  return {
    start,
    stop,
  };
}
