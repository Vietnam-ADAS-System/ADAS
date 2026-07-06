const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number(process.env.PORT || 3000);
const DIST = path.resolve(__dirname, "../../frontend/dist");
const WIDTH = 960;
const HEIGHT = 540;
const FPS = 15;
const ROUTES = ["/ws/video", "/ws/lane", "/ws/traffic-sign", "/ws/warning"];
const clients = new Map(ROUTES.map((route) => [route, new Set()]));

let frameId = 0;
let latest = payload(frameId);

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  if (url.pathname === "/api/health") return json(res, 200, health());
  if (url.pathname === "/api/realtime/snapshot") return json(res, 200, latest);
  if (!url.pathname.startsWith("/api/") && !url.pathname.startsWith("/ws/")) return asset(res, url.pathname);
  return json(res, 404, { error: "not_found" });
});

server.on("upgrade", (req, socket) => {
  const route = new URL(req.url, `http://${req.headers.host || "localhost"}`).pathname;
  const key = req.headers["sec-websocket-key"];
  if (!clients.has(route) || !key) return socket.destroy();

  const accept = crypto.createHash("sha1").update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`).digest("base64");
  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${accept}\r\n\r\n`,
  );

  const client = { route, socket };
  clients.get(route).add(client);
  socket.on("close", () => clients.get(route).delete(client));
  socket.on("error", () => clients.get(route).delete(client));
  send(client, pick(route));
});

setInterval(() => {
  frameId += 1;
  latest = payload(frameId);
  for (const route of ROUTES) for (const client of clients.get(route)) send(client, pick(route));
}, 1000 / FPS);

server.listen(PORT, HOST, () => {
  console.log(`ADAS driver backend running at http://${HOST}:${PORT}`);
  console.log(`Giao dien ho tro lai: http://${HOST}:${PORT}/`);
});

function health() {
  return {
    service: "adas-driver-backend",
    status: "ok",
    frame_id: frameId,
    fps: FPS,
    websocket_paths: ROUTES,
    clients: Object.fromEntries(ROUTES.map((route) => [route, clients.get(route).size])),
  };
}

function payload(id) {
  const lane = lanePayload(id);
  const signs = signPayload(id);
  const warning = warningPayload(id, lane, signs);
  return { video: videoPayload(id, warning), lane, trafficSign: { frame_id: id, signs }, warning };
}

function lanePayload(id) {
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

function signPayload(id) {
  return [{
    frame_id: id,
    sign_id: "speed-limit-40",
    class_id: 40,
    class_name: "Giới hạn 40 km/h",
    confidence: 0.94,
    bbox: [760, 130, 832, 202],
    center: [796, 166],
    icon: "40",
    rule: "Tốc độ tối đa 40 km/h",
    warning: id % 260 > 105,
    priority: "MEDIUM",
  }];
}

function warningPayload(id, lane, signs) {
  const sign = signs.find((item) => item.warning);
  return {
    frame_id: id,
    active: lane.warning || Boolean(sign),
    warning_type: lane.warning ? "LANE_DEPARTURE" : sign ? "TRAFFIC_SIGN" : "SYSTEM",
    warning_level: lane.warning ? "HIGH" : sign ? sign.priority : "INFO",
    warning_message: lane.warning ? laneWarningMessage(lane.direction) : sign ? sign.rule : "Hệ thống đang giám sát bình thường",
    lane_status: lane.lane_status,
    traffic_sign_status: sign ? sign.class_name : "Không có cảnh báo biển báo",
    vehicle_status: "Đang theo dõi",
    system_status: { camera: "Đang hoạt động", vehicle_detection: "Đang chạy", lane_detection: "Đang chạy", traffic_sign_detection: "Đang chạy", adas: "Đang chạy" },
    timestamp: new Date().toISOString(),
  };
}

function laneWarningMessage(direction) {
  if (direction === "LEFT") return "Nguy cơ lệch làn bên trái";
  if (direction === "RIGHT") return "Nguy cơ lệch làn bên phải";
  return "Nguy cơ lệch làn";
}

function videoPayload(id, warning) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}">
<rect width="960" height="220" fill="#31495c"/><rect y="220" width="960" height="320" fill="#2c5d45"/>
<polygon points="380,210 580,210 930,540 30,540" fill="#171b20"/>
<path d="M480 235 L480 540" stroke="#eef2f7" stroke-width="5" stroke-dasharray="28 24"/>
<path d="M390 230 L250 540 M570 230 L710 540" stroke="#f8fafc" stroke-width="4" opacity=".76"/>
<rect x="424" y="425" width="112" height="48" rx="6" fill="#d8dee8"/>
<circle cx="795" cy="165" r="34" fill="#fff" stroke="#d72828" stroke-width="8"/>
<text x="795" y="173" text-anchor="middle" font-family="system-ui" font-size="24" font-weight="800" fill="#1c2430">40</text>
<text x="28" y="42" font-family="system-ui" font-size="18" font-weight="700" fill="#dce8f6">LUỒNG ADAS | ${warning.warning_level}</text>
</svg>`;
  return { frame_id: id, frame: `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`, fps: FPS, width: WIDTH, height: HEIGHT, timestamp: new Date().toISOString(), source: "backend-node" };
}

function pick(route) {
  if (route === "/ws/video") return latest.video;
  if (route === "/ws/lane") return latest.lane;
  if (route === "/ws/traffic-sign") return latest.trafficSign;
  return latest.warning;
}

function json(res, status, data) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(status, { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json; charset=utf-8" });
  res.end(body);
}

function send(client, data) {
  if (client.socket.destroyed) return;
  const body = Buffer.from(JSON.stringify(data));
  const header = body.length < 126 ? Buffer.from([0x81, body.length]) : wsHeader(body.length);
  client.socket.write(Buffer.concat([header, body]));
}

function wsHeader(length) {
  const header = length < 65536 ? Buffer.alloc(4) : Buffer.alloc(10);
  header[0] = 0x81;
  header[1] = length < 65536 ? 126 : 127;
  if (length < 65536) header.writeUInt16BE(length, 2);
  else header.writeBigUInt64BE(BigInt(length), 2);
  return header;
}

function asset(res, pathname) {
  const requested = path.resolve(DIST, pathname === "/" ? "index.html" : decodeURIComponent(pathname).replace(/^\/+/, ""));
  const file = requested.startsWith(DIST) && fs.existsSync(requested) && fs.statSync(requested).isFile() ? requested : path.join(DIST, "index.html");
  try {
    res.writeHead(200, { "Content-Type": type(file) });
    res.end(fs.readFileSync(file));
  } catch (error) {
    res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
    res.end(error.message);
  }
}

function type(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".js")) return "application/javascript; charset=utf-8";
  if (file.endsWith(".css")) return "text/css; charset=utf-8";
  if (file.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}
