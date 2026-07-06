const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number(process.env.PORT || 3000);
const DIST_DIR = path.resolve(__dirname, "../../frontend/dist");
const WIDTH = 960;
const HEIGHT = 540;
const FPS = 15;
const PATHS = ["/ws/video", "/ws/lane", "/ws/traffic-sign", "/ws/warning"];
const clients = new Map(PATHS.map((path) => [path, new Set()]));

let frameId = 0;
let latest = makePayloads(frameId);

const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, `http://${req.headers.host || "localhost"}`).pathname;

  if (pathname === "/" || pathname === "/api/health") {
    sendJson(res, 200, {
      service: "adas-node-server",
      status: "ok",
      frame_id: frameId,
      fps: FPS,
      websocket_paths: PATHS,
      clients: Object.fromEntries(PATHS.map((path) => [path, clients.get(path).size])),
    });
    return;
  }

  if (pathname === "/api/realtime/snapshot") {
    sendJson(res, 200, latest);
    return;
  }

  if (req.method === "GET" && !pathname.startsWith("/api/") && !pathname.startsWith("/ws/")) {
    serveFrontend(res, pathname);
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

  const client = { path: pathname, socket };
  clients.get(pathname).add(client);
  socket.on("close", () => clients.get(pathname).delete(client));
  socket.on("error", () => clients.get(pathname).delete(client));
  sendSocketJson(client, payloadFor(pathname));
});

setInterval(() => {
  frameId += 1;
  latest = makePayloads(frameId);
  for (const path of PATHS) {
    for (const client of clients.get(path)) {
      sendSocketJson(client, payloadFor(path));
    }
  }
}, 1000 / FPS);

server.listen(PORT, HOST, () => {
  console.log(`ADAS realtime backend running at http://${HOST}:${PORT}`);
  console.log(`WebSocket streams: ${PATHS.join(", ")}`);
});

function payloadFor(path) {
  if (path === "/ws/video") return latest.video;
  if (path === "/ws/lane") return latest.lane;
  if (path === "/ws/traffic-sign") return latest.trafficSign;
  return latest.warning;
}

function sendJson(res, statusCode, data) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(statusCode, {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function serveFrontend(res, pathname) {
  if (!fs.existsSync(DIST_DIR)) {
    const message = "Frontend build not found. Run: npm --prefix frontend run build";
    res.writeHead(503, { "Content-Type": "text/plain; charset=utf-8" });
    res.end(message);
    return;
  }

  const decodedPath = decodeURIComponent(pathname);
  const relativePath = decodedPath === "/" ? "index.html" : decodedPath.replace(/^\/+/, "");
  const filePath = path.resolve(DIST_DIR, relativePath);

  if (!filePath.startsWith(DIST_DIR)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  const finalPath = fs.existsSync(filePath) && fs.statSync(filePath).isFile()
    ? filePath
    : path.join(DIST_DIR, "index.html");

  fs.readFile(finalPath, (error, data) => {
    if (error) {
      res.writeHead(500);
      res.end("Failed to read frontend asset");
      return;
    }

    res.writeHead(200, { "Content-Type": contentTypeFor(finalPath) });
    res.end(data);
  });
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js")) return "application/javascript; charset=utf-8";
  if (filePath.endsWith(".css")) return "text/css; charset=utf-8";
  if (filePath.endsWith(".svg")) return "image/svg+xml";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  return "application/octet-stream";
}

function sendSocketJson(client, data) {
  if (client.socket.destroyed) return;
  const payload = Buffer.from(JSON.stringify(data));
  const header = payload.length < 126 ? Buffer.from([0x81, payload.length]) : longHeader(payload.length);
  client.socket.write(Buffer.concat([header, payload]));
}

function longHeader(length) {
  if (length < 65536) {
    const header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(length, 2);
    return header;
  }

  const header = Buffer.alloc(10);
  header[0] = 0x81;
  header[1] = 127;
  header.writeBigUInt64BE(BigInt(length), 2);
  return header;
}

function makePayloads(id) {
  const lane = makeLane(id);
  const signs = makeSigns(id);
  const warning = makeWarning(id, lane, signs);
  return {
    video: makeVideo(id, warning),
    lane,
    trafficSign: { frame_id: id, signs },
    warning,
  };
}

function makeVideo(id, warning) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}">
<rect width="960" height="220" fill="#32495b"/><rect y="220" width="960" height="320" fill="#315a43"/>
<polygon points="380,210 580,210 930,540 30,540" fill="#171b20"/>
<path d="M480 235 L480 540" stroke="#eef2f7" stroke-width="5" stroke-dasharray="28 24"/>
<path d="M390 230 L250 540 M570 230 L710 540" stroke="#f8fafc" stroke-width="4" opacity=".75"/>
<rect x="424" y="425" width="112" height="48" rx="6" fill="#d8dee8"/>
<circle cx="795" cy="165" r="34" fill="#fff" stroke="#d72828" stroke-width="8"/>
<text x="795" y="173" text-anchor="middle" font-family="system-ui" font-size="24" font-weight="800" fill="#1c2430">40</text>
<rect x="16" y="16" width="230" height="54" rx="8" fill="rgba(8,13,20,.76)"/>
<text x="30" y="39" font-family="system-ui" font-size="15" font-weight="700" fill="#dce8f6">BACKEND STREAM</text>
<text x="30" y="58" font-family="system-ui" font-size="13" fill="#9fb3c8">Frame ${id} | ${warning.warning_level}</text>
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

function makeLane(id) {
  const offset = Math.sin(id / 45) * 110;
  const normalized = offset / 220;
  const status = Math.abs(normalized) > 0.72 ? "LANE_DEPARTURE" : Math.abs(normalized) > 0.48 ? "NEAR_BOUNDARY" : "SAFE";
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
    lane_status: status,
    warning: status === "LANE_DEPARTURE",
  };
}

function makeSigns(id) {
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

function makeWarning(id, lane, signs) {
  const activeSign = signs.find((sign) => sign.warning);
  const base = {
    frame_id: id,
    vehicle_status: "Tracked by backend",
    lane_status: lane.lane_status,
    traffic_sign_status: activeSign ? activeSign.class_name : "No warning",
    system_status: {
      camera: "Online",
      vehicle_detection: "Streaming",
      lane_detection: "Streaming",
      traffic_sign_detection: "Streaming",
      adas: "Running",
    },
    timestamp: new Date().toISOString(),
  };

  if (lane.warning) {
    return {
      ...base,
      warning_type: "LANE_DEPARTURE",
      warning_level: "HIGH",
      warning_message: `Lane departure risk on ${lane.direction.toLowerCase()} side`,
      active: true,
    };
  }

  if (activeSign) {
    return {
      ...base,
      warning_type: "TRAFFIC_SIGN",
      warning_level: activeSign.priority,
      warning_message: activeSign.rule,
      active: true,
    };
  }

  return {
    ...base,
    warning_type: "SYSTEM",
    warning_level: "INFO",
    warning_message: "System monitoring",
    active: false,
  };
}
