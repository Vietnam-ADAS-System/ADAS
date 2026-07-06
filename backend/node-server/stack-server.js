const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number(process.env.PORT || 3000);
const FPS = 15;
const WIDTH = 960;
const HEIGHT = 540;
const DIST_DIR = path.resolve(__dirname, "../../frontend/dist");
const WS_PATHS = ["/ws/video", "/ws/lane", "/ws/traffic-sign", "/ws/warning"];
const clients = new Map(WS_PATHS.map((route) => [route, new Set()]));

let frameId = 0;
let latest = createPayload(frameId);

const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, `http://${req.headers.host || "localhost"}`).pathname;

  if (pathname === "/api/health") {
    sendJson(res, 200, {
      service: "adas-realtime-backend",
      status: "ok",
      frame_id: frameId,
      fps: FPS,
      websocket_paths: WS_PATHS,
      clients: Object.fromEntries(WS_PATHS.map((route) => [route, clients.get(route).size])),
    });
    return;
  }

  if (pathname === "/api/realtime/snapshot") {
    sendJson(res, 200, latest);
    return;
  }

  if (req.method === "GET" && !pathname.startsWith("/api/") && !pathname.startsWith("/ws/")) {
    serveStatic(res, pathname);
    return;
  }

  sendJson(res, 404, { error: "not_found" });
});

server.on("upgrade", (req, socket) => {
  const pathname = new URL(req.url, `http://${req.headers.host || "localhost"}`).pathname;
  const key = req.headers["sec-websocket-key"];

  if (!clients.has(pathname) || !key) {
    socket.destroy();
    return;
  }

  const accept = crypto
    .createHash("sha1")
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest("base64");

  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${accept}\r\n\r\n`,
  );

  const client = { route: pathname, socket };
  clients.get(pathname).add(client);
  socket.on("close", () => clients.get(pathname).delete(client));
  socket.on("error", () => clients.get(pathname).delete(client));
  sendWs(client, payloadFor(pathname));
});

setInterval(() => {
  frameId += 1;
  latest = createPayload(frameId);
  for (const route of WS_PATHS) {
    for (const client of clients.get(route)) sendWs(client, payloadFor(route));
  }
}, 1000 / FPS);

server.listen(PORT, HOST, () => {
  console.log(`ADAS realtime backend running at http://${HOST}:${PORT}`);
  console.log(`WebSocket streams: ${WS_PATHS.join(", ")}`);
});

function createPayload(id) {
  const lane = createLane(id);
  const signs = createSigns(id);
  const warning = createWarning(id, lane, signs);
  return {
    video: createVideo(id, warning),
    lane,
    trafficSign: { frame_id: id, signs },
    warning,
  };
}

function createLane(id) {
  const offset = Math.sin(id / 45) * 110;
  const normalized = offset / 220;
  const laneStatus =
    Math.abs(normalized) > 0.72 ? "LANE_DEPARTURE" : Math.abs(normalized) > 0.48 ? "NEAR_BOUNDARY" : "SAFE";
  return {
    frame_id: id,
    lane_left: [[390, 260], [350, 335], [305, 420], [250, 520]],
    lane_right: [[570, 260], [610, 335], [655, 420], [710, 520]],
    lane_center: [[480, 260], [480, 520]],
    lane_width: 440,
    vehicle_center: [Math.round(480 + offset), 475],
    offset: Math.round(offset),
    normalized_offset: Number(normalized.toFixed(3)),
    direction: offset < -8 ? "LEFT" : offset > 8 ? "RIGHT" : "CENTER",
    lane_status: laneStatus,
    warning: laneStatus === "LANE_DEPARTURE",
  };
}

function createSigns(id) {
  return [{
    frame_id: id,
    sign_id: "speed-limit-40",
    class_id: 40,
    class_name: "Speed Limit 40",
    confidence: 0.94,
    bbox: [760, 130, 832, 202],
    center: [796, 166],
    icon: "40",
    rule: "Maximum Speed 40 km/h",
    warning: id % 260 > 105,
    priority: "MEDIUM",
  }];
}

function createWarning(id, lane, signs) {
  const sign = signs.find((item) => item.warning);
  const active = lane.warning || Boolean(sign);
  return {
    frame_id: id,
    active,
    warning_type: lane.warning ? "LANE_DEPARTURE" : sign ? "TRAFFIC_SIGN" : "SYSTEM",
    warning_level: lane.warning ? "HIGH" : sign ? sign.priority : "INFO",
    warning_message: lane.warning ? `Lane departure risk on ${lane.direction.toLowerCase()} side` : sign ? sign.rule : "System monitoring",
    lane_status: lane.lane_status,
    traffic_sign_status: sign ? sign.class_name : "No warning",
    vehicle_status: "Tracked by backend",
    system_status: {
      camera: "Online",
      vehicle_detection: "Streaming",
      lane_detection: "Streaming",
      traffic_sign_detection: "Streaming",
      adas: "Running",
    },
    timestamp: new Date().toISOString(),
  };
}

function createVideo(id, warning) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}">
<rect width="960" height="220" fill="#32495b"/><rect y="220" width="960" height="320" fill="#315a43"/>
<polygon points="380,210 580,210 930,540 30,540" fill="#171b20"/>
<path d="M480 235 L480 540" stroke="#eef2f7" stroke-width="5" stroke-dasharray="28 24"/>
<path d="M390 230 L250 540 M570 230 L710 540" stroke="#f8fafc" stroke-width="4" opacity=".75"/>
<rect x="424" y="425" width="112" height="48" rx="6" fill="#d8dee8"/>
<circle cx="795" cy="165" r="34" fill="#fff" stroke="#d72828" stroke-width="8"/>
<text x="795" y="173" text-anchor="middle" font-family="system-ui" font-size="24" font-weight="800" fill="#1c2430">40</text>
<text x="30" y="42" font-family="system-ui" font-size="18" font-weight="700" fill="#dce8f6">Frame ${id} | ${warning.warning_level}</text>
</svg>`;
  return {
    frame_id: id,
    frame: `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`,
    fps: FPS,
    width: WIDTH,
    height: HEIGHT,
    timestamp: new Date().toISOString(),
    source: "backend-node",
  };
}

function payloadFor(route) {
  if (route === "/ws/video") return latest.video;
  if (route === "/ws/lane") return latest.lane;
  if (route === "/ws/traffic-sign") return latest.trafficSign;
  return latest.warning;
}

function sendJson(res, status, data) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(status, {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendWs(client, data) {
  if (client.socket.destroyed) return;
  const body = Buffer.from(JSON.stringify(data));
  const header = body.length < 126 ? Buffer.from([0x81, body.length]) : wsLongHeader(body.length);
  client.socket.write(Buffer.concat([header, body]));
}

function wsLongHeader(length) {
  const header = length < 65536 ? Buffer.alloc(4) : Buffer.alloc(10);
  header[0] = 0x81;
  header[1] = length < 65536 ? 126 : 127;
  if (length < 65536) header.writeUInt16BE(length, 2);
  else header.writeBigUInt64BE(BigInt(length), 2);
  return header;
}

function serveStatic(res, pathname) {
  if (!fs.existsSync(DIST_DIR)) {
    res.writeHead(503, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Frontend build not found. Run: npm --prefix frontend run build");
    return;
  }

  const relative = pathname === "/" ? "index.html" : decodeURIComponent(pathname).replace(/^\/+/, "");
  const requested = path.resolve(DIST_DIR, relative);
  const filePath = requested.startsWith(DIST_DIR) && fs.existsSync(requested) && fs.statSync(requested).isFile()
    ? requested
    : path.join(DIST_DIR, "index.html");
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, { "Content-Type": contentType(filePath) });
    res.end(data);
  } catch (error) {
    res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
    res.end(`Failed to read frontend asset: ${error.message}`);
  }
}

function contentType(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js")) return "application/javascript; charset=utf-8";
  if (filePath.endsWith(".css")) return "text/css; charset=utf-8";
  if (filePath.endsWith(".svg")) return "image/svg+xml";
  if (filePath.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}
