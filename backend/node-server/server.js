const crypto = require("crypto");
const http = require("http");

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number(process.env.PORT || 3000);
const FRAME_WIDTH = Number(process.env.ADAS_FRAME_WIDTH || 960);
const FRAME_HEIGHT = Number(process.env.ADAS_FRAME_HEIGHT || 540);
const FPS = Number(process.env.ADAS_STREAM_FPS || 30);
const FRAME_INTERVAL_MS = Math.max(33, Math.round(1000 / FPS));

// Mode: 'mock' = tự sinh data, 'ai' = nhận từ Python AI
let MODE = process.env.ADAS_MODE || "mock";

const WS_PATHS = new Set(["/ws/video", "/ws/lane", "/ws/traffic-sign", "/ws/warning", "/ws/pedestrian", "/ws/vehicle"]);
const clientsByPath = new Map(Array.from(WS_PATHS).map((path) => [path, new Set()]));

let frameId = 0;
// AI data từ Python backend (khi MODE='ai')
let latestAiData = null;
// Mock data (khi MODE='mock')
let latestTelemetry = buildTelemetry(frameId);

function writeJson(res, statusCode, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(statusCode, {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function getPathname(req) {
  try {
    return new URL(req.url, `http://${req.headers.host || "localhost"}`).pathname;
  } catch {
    return "/";
  }
}

const server = http.createServer((req, res) => {
  const pathname = getPathname(req);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    });
    res.end();
    return;
  }

  if (pathname === "/" || pathname === "/api/health") {
    writeJson(res, 200, {
      service: "adas-node-server",
      status: "ok",
      frame_id: latestAiData?.frame_id || latestTelemetry.video.frame_id,
      fps: FPS,
      mode: MODE,
      websocket_paths: Array.from(WS_PATHS),
      clients: getClientCounts(),
      uptime_seconds: Math.round(process.uptime()),
    });
    return;
  }

  // Endpoint nhận AI data từ Python backend
  if (pathname === "/api/ai/frame" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", () => {
      try {
        latestAiData = JSON.parse(body);
        latestAiData.frame_id = latestAiData.frame_id || frameId;
        // Tự động chuyển sang mode AI khi nhận được data
        MODE = "ai";
        writeJson(res, 200, { status: "ok", received: true });
      } catch {
        writeJson(res, 400, { status: "error", message: "Invalid JSON" });
      }
    });
    return;
  }

  // Endpoint chuyển đổi mode
  if (pathname === "/api/mode" && req.method === "POST") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", () => {
      try {
        const { mode } = JSON.parse(body);
        if (mode === "ai" || mode === "mock") {
          MODE = mode;
          writeJson(res, 200, { status: "ok", mode: MODE });
        } else {
          writeJson(res, 400, { status: "error", message: "Invalid mode" });
        }
      } catch {
        writeJson(res, 400, { status: "error", message: "Invalid JSON" });
      }
    });
    return;
  }

  if (pathname === "/api/realtime/snapshot") {
    const current = getCurrentTelemetry();
    writeJson(res, 200, {
      video: {
        ...current.video,
        frame: undefined,
        frame_url: undefined,
      },
      lane: current.lane,
      traffic_sign: current.trafficSign,
      warning: current.warning,
    });
    return;
  }

  writeJson(res, 404, {
    error: "not_found",
    message: `No route for ${req.method} ${pathname}`,
  });
});

server.on("upgrade", (req, socket) => {
  const pathname = getPathname(req);

  if (!WS_PATHS.has(pathname)) {
    socket.write("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n");
    socket.destroy();
    return;
  }

  const key = req.headers["sec-websocket-key"];
  if (!key) {
    socket.write("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
    socket.destroy();
    return;
  }

  const accept = crypto
    .createHash("sha1")
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest("base64");

  socket.write(
    [
      "HTTP/1.1 101 Switching Protocols",
      "Upgrade: websocket",
      "Connection: Upgrade",
      `Sec-WebSocket-Accept: ${accept}`,
      "\r\n",
    ].join("\r\n"),
  );

  const client = { path: pathname, socket };
  clientsByPath.get(pathname).add(client);
  socket.setNoDelay(true);
  socket.on("data", (buffer) => handleClientFrame(client, buffer));
  socket.on("error", () => removeClient(client));
  socket.on("close", () => removeClient(client));

  // Gửi data hiện tại khi client kết nối
  sendForPath(pathname, client);
});

// Broadcast loop - gửi data theo mode
setInterval(() => {
  const current = getCurrentTelemetry();
  frameId = current.video.frame_id || frameId + 1;

  broadcast("/ws/video", current.video);
  broadcast("/ws/lane", current.lane);
  broadcast("/ws/traffic-sign", current.trafficSign);
  broadcast("/ws/warning", current.warning);
  broadcast("/ws/pedestrian", current.pedestrian);
  broadcast("/ws/vehicle", current.vehicle);
}, FRAME_INTERVAL_MS);

server.listen(PORT, HOST, () => {
  console.log(`ADAS realtime backend running at http://${HOST}:${PORT}`);
  console.log(`WebSocket streams: ${Array.from(WS_PATHS).join(", ")}`);
});

function getClientCounts() {
  return Array.from(clientsByPath.entries()).reduce((counts, [path, clients]) => {
    counts[path] = clients.size;
    return counts;
  }, {});
}

function removeClient(client) {
  const clients = clientsByPath.get(client.path);
  if (clients) {
    clients.delete(client);
  }
}

function handleClientFrame(client, buffer) {
  if (!buffer || buffer.length < 2) {
    return;
  }

  const opcode = buffer[0] & 0x0f;
  if (opcode === 0x8) {
    removeClient(client);
    client.socket.end();
    return;
  }

  if (opcode === 0x9) {
    sendControlFrame(client.socket, 0x0a);
  }
}

function getCurrentTelemetry() {
  if (MODE === "ai" && latestAiData) {
    return convertAiDataToTelemetry(latestAiData);
  }
  return latestTelemetry;
}

function convertAiDataToTelemetry(aiData) {
  const lane = aiData.lane || {};
  const signs = aiData.traffic_signs || [];
  const pedestrians = aiData.pedestrians || [];
  const vehicles = aiData.vehicles || [];

  const laneStatus = lane.lane_status || "SAFE";
  const hasWarning = laneStatus === "LANE_DEPARTURE" || signs.some(s => s.warning);

  return {
    video: {
      frame_id: aiData.frame_id || 0,
      frame: aiData.annotated_frame,
      fps: FPS,
      width: aiData.width || FRAME_WIDTH,
      height: aiData.height || FRAME_HEIGHT,
      timestamp: new Date().toISOString(),
      source: "ai-backend",
    },
    lane: {
      frame_id: aiData.frame_id || 0,
      lane_left: lane.lane_left || [],
      lane_right: lane.lane_right || [],
      lane_center: lane.lane_center || [],
      lane_width: lane.lane_width || 0,
      vehicle_center: lane.vehicle_center || [FRAME_WIDTH / 2, FRAME_HEIGHT * 0.88],
      offset: lane.offset || 0,
      normalized_offset: lane.normalized_offset || 0,
      direction: lane.direction || "CENTER",
      lane_status: laneStatus,
      warning: laneStatus === "LANE_DEPARTURE",
    },
    trafficSign: {
      frame_id: aiData.frame_id || 0,
      signs: signs.map(s => ({
        frame_id: aiData.frame_id || 0,
        sign_id: s.sign_id || s.class_name || "unknown",
        class_id: s.class_id || 0,
        class_name: s.class_name || "Unknown",
        confidence: s.confidence || 0.9,
        bbox: s.bbox || [0, 0, 50, 50],
        center: s.center || [25, 25],
        icon: s.icon || "?",
        rule: s.rule || "",
        warning: s.warning || false,
        priority: s.priority || "LOW",
      })),
    },
    warning: {
      frame_id: aiData.frame_id || 0,
      vehicle_status: "Tracked by AI",
      lane_status: laneStatus,
      traffic_sign_status: signs.find(s => s.warning)?.class_name || "No warning",
      system_status: {
        camera: "Online",
        vehicle_detection: pedestrians.length + vehicles.length > 0 ? "Detecting" : "No detection",
        lane_detection: "Running",
        traffic_sign_detection: signs.length > 0 ? "Sign detected" : "No sign",
        adas: "Running",
      },
      warning_type: laneStatus === "LANE_DEPARTURE" ? "LANE_DEPARTURE" : signs.some(s => s.warning) ? "TRAFFIC_SIGN" : "SYSTEM",
      warning_level: laneStatus === "LANE_DEPARTURE" ? "HIGH" : signs.find(s => s.warning)?.priority || "INFO",
      warning_message: laneStatus === "LANE_DEPARTURE" ? "Lane departure detected" : signs.find(s => s.warning)?.rule || "System monitoring",
      active: hasWarning,
      timestamp: new Date().toISOString(),
    },
    pedestrian: {
      frame_id: aiData.frame_id || 0,
      detections: pedestrians.map(p => ({
        frame_id: aiData.frame_id || 0,
        track_id: p.track_id || 0,
        class_name: "person",
        confidence: p.confidence || 0.9,
        bbox: p.bbox || [0, 0, 50, 100],
        center: p.center || [25, 50],
      })),
      count: pedestrians.length,
    },
    vehicle: {
      frame_id: aiData.frame_id || 0,
      detections: vehicles.map(v => ({
        frame_id: aiData.frame_id || 0,
        track_id: v.track_id || 0,
        class_name: v.class_name || "car",
        label: v.class_name || "car",
        label_vi: v.class_name === "motorcycle" ? "Xe máy" : "Ô tô",
        confidence: v.confidence || 0.9,
        bbox: v.bbox || { x1: 0, y1: 0, x2: 50, y2: 50 },
        center: v.center || [25, 25],
      })),
      count: vehicles.length,
    },
  };
}

function broadcast(path, payload) {
  const clients = clientsByPath.get(path);
  if (!clients || clients.size === 0) {
    return;
  }

  for (const client of clients) {
    sendJson(client, payload);
  }
}

function sendForPath(path, client) {
  const current = getCurrentTelemetry();
  if (path === "/ws/video") {
    sendJson(client, current.video);
  } else if (path === "/ws/lane") {
    sendJson(client, current.lane);
  } else if (path === "/ws/traffic-sign") {
    sendJson(client, current.trafficSign);
  } else if (path === "/ws/warning") {
    sendJson(client, current.warning);
  } else if (path === "/ws/pedestrian") {
    sendJson(client, current.pedestrian);
  } else if (path === "/ws/vehicle") {
    sendJson(client, current.vehicle);
  }
}

function sendJson(client, payload) {
  if (client.socket.destroyed) {
    removeClient(client);
    return;
  }

  try {
    sendTextFrame(client.socket, JSON.stringify(payload));
  } catch {
    removeClient(client);
    client.socket.destroy();
  }
}

function sendTextFrame(socket, text) {
  sendFrame(socket, 0x1, Buffer.from(text));
}

function sendControlFrame(socket, opcode) {
  sendFrame(socket, opcode, Buffer.alloc(0));
}

function sendFrame(socket, opcode, payload) {
  const length = payload.length;
  let header;

  if (length < 126) {
    header = Buffer.alloc(2);
    header[1] = length;
  } else if (length < 65536) {
    header = Buffer.alloc(4);
    header[1] = 126;
    header.writeUInt16BE(length, 2);
  } else {
    header = Buffer.alloc(10);
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(length), 2);
  }

  header[0] = 0x80 | opcode;
  socket.write(Buffer.concat([header, payload]));
}

function buildTelemetry(id) {
  const lane = buildLaneData(id);
  const signs = buildTrafficSigns(id);
  const warning = buildWarningData(id, lane, signs);
  const video = buildVideoFrame(id, lane, signs, warning);
  const pedestrians = buildPedestrians(id);
  const vehicles = buildVehicles(id);

  return {
    video,
    lane,
    trafficSign: {
      frame_id: id,
      signs,
    },
    warning,
    pedestrian: {
      frame_id: id,
      detections: pedestrians,
      count: pedestrians.length,
    },
    vehicle: {
      frame_id: id,
      detections: vehicles,
      count: vehicles.length,
    },
  };
}

function buildVideoFrame(id, lane, signs, warning) {
  const svg = buildFrameSvg(id, lane, signs, warning);
  const frameUrl = `data:image/svg+xml;base64,${Buffer.from(svg, "utf8").toString("base64")}`;

  return {
    frame_id: id,
    frame: frameUrl,
    fps: FPS,
    width: FRAME_WIDTH,
    height: FRAME_HEIGHT,
    timestamp: new Date().toISOString(),
    source: "backend-node",
  };
}

function buildLaneData(id) {
  const width = FRAME_WIDTH;
  const height = FRAME_HEIGHT;
  const centerBottom = width * 0.5 + Math.sin(id / 90) * 18;
  const centerTop = width * 0.5 + Math.sin(id / 120) * 12;
  const laneHalfBottom = width * 0.23;
  const laneHalfTop = width * 0.068;
  const vehicleCenterX = centerBottom + Math.sin(id / 45) * width * 0.11;
  const vehicleCenter = [vehicleCenterX, height * 0.88];
  const laneWidth = laneHalfBottom * 2;
  const offset = vehicleCenterX - centerBottom;
  const normalizedOffset = offset / laneHalfBottom;
  const absOffset = Math.abs(normalizedOffset);
  const laneStatus =
    absOffset > 0.72 ? "LANE_DEPARTURE" : absOffset > 0.48 ? "NEAR_BOUNDARY" : "SAFE";

  return {
    frame_id: id,
    lane_left: makeLanePoints(centerBottom, laneHalfBottom, centerTop, laneHalfTop, height, "left"),
    lane_right: makeLanePoints(centerBottom, laneHalfBottom, centerTop, laneHalfTop, height, "right"),
    lane_center: [
      [centerTop, height * 0.48],
      [centerBottom, height * 0.96],
    ],
    lane_width: Math.round(laneWidth),
    vehicle_center: vehicleCenter.map((value) => Math.round(value)),
    offset: Math.round(offset),
    normalized_offset: Number(normalizedOffset.toFixed(3)),
    direction: offset < -8 ? "LEFT" : offset > 8 ? "RIGHT" : "CENTER",
    lane_status: laneStatus,
    warning: laneStatus === "LANE_DEPARTURE",
  };
}

function makeLanePoints(centerBottom, laneHalfBottom, centerTop, laneHalfTop, height, side) {
  const points = [];
  const direction = side === "left" ? -1 : 1;

  for (let index = 0; index < 8; index += 1) {
    const ratio = index / 7;
    const y = height * (0.48 + ratio * 0.48);
    const centerX = centerTop + (centerBottom - centerTop) * ratio;
    const halfWidth = laneHalfTop + (laneHalfBottom - laneHalfTop) * ratio;
    const curve = Math.sin(ratio * Math.PI) * 18 * direction;
    points.push([
      Math.round(centerX + halfWidth * direction + curve),
      Math.round(y),
    ]);
  }

  return points;
}

function buildTrafficSigns(id) {
  const signs = [];
  const speedSignVisible = id % 260 < 210;
  const stopSignVisible = id % 420 > 250;

  if (speedSignVisible) {
    const x = FRAME_WIDTH * 0.79 + Math.sin(id / 50) * 8;
    const y = FRAME_HEIGHT * 0.26;
    signs.push({
      frame_id: id,
      sign_id: "speed-limit-40",
      class_id: 40,
      class_name: "Speed Limit 40",
      confidence: 0.94,
      bbox: [
        Math.round(x),
        Math.round(y),
        Math.round(x + FRAME_WIDTH * 0.075),
        Math.round(y + FRAME_HEIGHT * 0.13),
      ],
      center: [
        Math.round(x + FRAME_WIDTH * 0.037),
        Math.round(y + FRAME_HEIGHT * 0.065),
      ],
      icon: "40",
      rule: "Tốc độ tối đa 40 km/h",
      warning: id % 260 > 105,
      priority: "MEDIUM",
    });
  }

  if (stopSignVisible) {
    const x = FRAME_WIDTH * 0.15;
    const y = FRAME_HEIGHT * 0.31 + Math.sin(id / 38) * 5;
    signs.push({
      frame_id: id,
      sign_id: "stop",
      class_id: 1,
      class_name: "STOP",
      confidence: 0.91,
      bbox: [
        Math.round(x),
        Math.round(y),
        Math.round(x + FRAME_WIDTH * 0.085),
        Math.round(y + FRAME_HEIGHT * 0.13),
      ],
      center: [
        Math.round(x + FRAME_WIDTH * 0.043),
        Math.round(y + FRAME_HEIGHT * 0.065),
      ],
      icon: "DỪNG",
      rule: "Chuẩn bị dừng xe",
      warning: true,
      priority: "HIGH",
    });
  }

  return signs;
}

function buildPedestrians(id) {
  const pedestrians = [];
  const personVisible = id % 180 < 140;

  if (personVisible) {
    const baseX = FRAME_WIDTH * 0.35 + Math.sin(id / 60) * 30;
    const baseY = FRAME_HEIGHT * 0.45;
    const personHeight = FRAME_HEIGHT * 0.35;
    const personWidth = FRAME_WIDTH * 0.06;

    pedestrians.push({
      frame_id: id,
      track_id: 1,
      class_name: "person",
      confidence: 0.88 + Math.sin(id / 30) * 0.05,
      bbox: [
        Math.round(baseX),
        Math.round(baseY),
        Math.round(baseX + personWidth),
        Math.round(baseY + personHeight),
      ],
      center: [
        Math.round(baseX + personWidth / 2),
        Math.round(baseY + personHeight / 2),
      ],
    });
  }

  if (id % 220 > 150) {
    const baseX = FRAME_WIDTH * 0.58 + Math.sin(id / 45) * 20;
    const baseY = FRAME_HEIGHT * 0.50;
    const personHeight = FRAME_HEIGHT * 0.30;
    const personWidth = FRAME_WIDTH * 0.05;

    pedestrians.push({
      frame_id: id,
      track_id: 2,
      class_name: "person",
      confidence: 0.85 + Math.cos(id / 25) * 0.05,
      bbox: [
        Math.round(baseX),
        Math.round(baseY),
        Math.round(baseX + personWidth),
        Math.round(baseY + personHeight),
      ],
      center: [
        Math.round(baseX + personWidth / 2),
        Math.round(baseY + personHeight / 2),
      ],
    });
  }

  return pedestrians;
}

function buildVehicles(id) {
  const vehicles = [];
  const carVisible = id % 300 < 280;

  if (carVisible) {
    const carX = FRAME_WIDTH * 0.25 + Math.sin(id / 80) * 40;
    const carY = FRAME_HEIGHT * 0.55;
    const carW = FRAME_WIDTH * 0.12;
    const carH = FRAME_HEIGHT * 0.18;

    vehicles.push({
      frame_id: id,
      track_id: 1,
      class_name: "car",
      label: "car",
      label_vi: "Ô tô",
      confidence: 0.92 + Math.sin(id / 35) * 0.03,
      bbox: {
        x1: Math.round(carX),
        y1: Math.round(carY),
        x2: Math.round(carX + carW),
        y2: Math.round(carY + carH),
      },
      center: [
        Math.round(carX + carW / 2),
        Math.round(carY + carH / 2),
      ],
    });
  }

  if (id % 350 > 100) {
    const carX = FRAME_WIDTH * 0.65 + Math.cos(id / 55) * 30;
    const carY = FRAME_HEIGHT * 0.50;
    const carW = FRAME_WIDTH * 0.14;
    const carH = FRAME_HEIGHT * 0.22;

    vehicles.push({
      frame_id: id,
      track_id: 2,
      class_name: "car",
      label: "car",
      label_vi: "Ô tô",
      confidence: 0.89 + Math.cos(id / 40) * 0.04,
      bbox: {
        x1: Math.round(carX),
        y1: Math.round(carY),
        x2: Math.round(carX + carW),
        y2: Math.round(carY + carH),
      },
      center: [
        Math.round(carX + carW / 2),
        Math.round(carY + carH / 2),
      ],
    });
  }

  if (id % 200 > 80) {
    const motoX = FRAME_WIDTH * 0.45 + Math.sin(id / 70) * 25;
    const motoY = FRAME_HEIGHT * 0.68;
    const motoW = FRAME_WIDTH * 0.04;
    const motoH = FRAME_HEIGHT * 0.12;

    vehicles.push({
      frame_id: id,
      track_id: 3,
      class_name: "motorcycle",
      label: "motorcycle",
      label_vi: "Xe máy",
      confidence: 0.86,
      bbox: {
        x1: Math.round(motoX),
        y1: Math.round(motoY),
        x2: Math.round(motoX + motoW),
        y2: Math.round(motoY + motoH),
      },
      center: [
        Math.round(motoX + motoW / 2),
        Math.round(motoY + motoH / 2),
      ],
    });
  }

  return vehicles;
}

function buildWarningData(id, lane, signs) {
  const activeSign = signs.find((sign) => sign.warning);
  const systemStatus = {
    camera: "Online",
    vehicle_detection: "Đang theo dõi",
    lane_detection: "Đang theo dõi",
    traffic_sign_detection: signs.length ? "Đã phát hiện" : "Không có biển báo",
    adas: "Đang chạy",
  };

  if (lane.warning) {
    return {
      frame_id: id,
      vehicle_status: "Được theo dõi",
      lane_status: lane.lane_status,
      traffic_sign_status: activeSign ? activeSign.class_name : "Không có cảnh báo",
      system_status: systemStatus,
      warning_type: "LANE_DEPARTURE",
      warning_level: "HIGH",
      warning_message:
        lane.direction === "LEFT"
          ? "Nguy cơ lệch làn bên trái"
          : "Nguy cơ lệch làn bên phải",
      active: true,
      timestamp: new Date().toISOString(),
    };
  }

  if (activeSign) {
    return {
      frame_id: id,
      vehicle_status: "Được theo dõi",
      lane_status: lane.lane_status,
      traffic_sign_status: activeSign.class_name,
      system_status: systemStatus,
      warning_type: "TRAFFIC_SIGN",
      warning_level: activeSign.priority,
      warning_message: activeSign.rule,
      active: true,
      timestamp: new Date().toISOString(),
    };
  }

  return {
    frame_id: id,
    vehicle_status: "Được theo dõi",
    lane_status: lane.lane_status,
    traffic_sign_status: "Không có cảnh báo",
    system_status: systemStatus,
    warning_type: "SYSTEM",
    warning_level: "INFO",
    warning_message: "Hệ thống giám sát",
    active: false,
    timestamp: new Date().toISOString(),
  };
}

function buildFrameSvg(id, lane, signs, warning) {
  const width = FRAME_WIDTH;
  const height = FRAME_HEIGHT;
  const horizon = height * 0.39;
  const roadTopWidth = width * 0.22;
  const roadBottomWidth = width * 0.96;
  const centerX = width / 2 + Math.sin(id / 90) * 20;
  const roadLeftTop = centerX - roadTopWidth / 2;
  const roadRightTop = centerX + roadTopWidth / 2;
  const roadLeftBottom = centerX - roadBottomWidth / 2;
  const roadRightBottom = centerX + roadBottomWidth / 2;
  const laneColor = lane.warning ? "#ff4f5f" : lane.lane_status === "NEAR_BOUNDARY" ? "#f5c84c" : "#f8fafc";
  const vehicleCenter = point(lane.vehicle_center);
  const carWidth = width * 0.11;
  const carHeight = height * 0.085;
  const carX = vehicleCenter.x - carWidth / 2;
  const carY = vehicleCenter.y - carHeight;

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    "<defs>",
    '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2633"/><stop offset="1" stop-color="#435667"/></linearGradient>',
    '<linearGradient id="road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#343a40"/><stop offset="1" stop-color="#111418"/></linearGradient>',
    "</defs>",
    `<rect x="0" y="0" width="${width}" height="${horizon}" fill="url(#sky)"/>`,
    `<rect x="0" y="${horizon}" width="${width}" height="${height - horizon}" fill="#2d5a46"/>`,
    `<polygon points="${roadLeftTop},${horizon} ${roadRightTop},${horizon} ${roadRightBottom},${height} ${roadLeftBottom},${height}" fill="url(#road)"/>`,
    `<polyline points="${points(lane.lane_left)}" fill="none" stroke="${laneColor}" stroke-width="4" stroke-linecap="round" opacity="0.78"/>`,
    `<polyline points="${points(lane.lane_right)}" fill="none" stroke="${laneColor}" stroke-width="4" stroke-linecap="round" opacity="0.78"/>`,
    `<polyline points="${points(lane.lane_center)}" fill="none" stroke="#e9eef6" stroke-width="5" stroke-dasharray="24 22" stroke-linecap="round" opacity="0.85"/>`,
    `<rect x="${carX}" y="${carY}" width="${carWidth}" height="${carHeight}" rx="6" fill="#d8dee8"/>`,
    `<rect x="${carX + carWidth * 0.22}" y="${carY + 10}" width="${carWidth * 0.56}" height="${carHeight * 0.28}" rx="3" fill="#263442"/>`,
    `<rect x="${carX + carWidth * 0.1}" y="${carY + carHeight - 10}" width="${carWidth * 0.18}" height="12" rx="2" fill="#0d1117"/>`,
    `<rect x="${carX + carWidth * 0.72}" y="${carY + carHeight - 10}" width="${carWidth * 0.18}" height="12" rx="2" fill="#0d1117"/>`,
    signs.map(drawSignSvg).join(""),
    `<rect x="16" y="16" width="224" height="54" rx="8" fill="rgba(8,13,20,0.76)"/>`,
    '<text x="30" y="39" fill="#dce8f6" font-family="system-ui, sans-serif" font-size="15" font-weight="700">LUỒNG BACKEND</text>',
    `<text x="30" y="58" fill="#9fb3c8" font-family="system-ui, sans-serif" font-size="13">Khung ${id} | ${escapeXml(warning.warning_level)}</text>`,
    "</svg>",
  ].join("");
}

function drawSignSvg(sign) {
  const [x1, y1, x2, y2] = sign.bbox;
  const width = x2 - x1;
  const height = y2 - y1;
  const centerX = x1 + width / 2;
  const centerY = y1 + height / 2;
  const postX = centerX - 3;
  const postY = y2;

  if (sign.class_name === "STOP") {
    return [
      `<rect x="${postX}" y="${postY}" width="6" height="94" fill="#e8edf5"/>`,
      `<polygon points="${octagonPoints(centerX, centerY, Math.min(width, height) / 2)}" fill="#cf2d2d" stroke="#f8fafc" stroke-width="5"/>`,
      `<text x="${centerX}" y="${centerY + 5}" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="16" font-weight="800">DỪNG</text>`,
    ].join("");
  }

  return [
    `<rect x="${postX}" y="${postY}" width="6" height="110" fill="#e8edf5"/>`,
    `<circle cx="${centerX}" cy="${centerY}" r="${Math.min(width, height) / 2}" fill="#f8fafc" stroke="#d72828" stroke-width="7"/>`,
    `<text x="${centerX}" y="${centerY + 7}" text-anchor="middle" fill="#1c2430" font-family="system-ui, sans-serif" font-size="23" font-weight="800">${escapeXml(sign.icon)}</text>`,
  ].join("");
}

function octagonPoints(cx, cy, radius) {
  const pointsList = [];
  for (let index = 0; index < 8; index += 1) {
    const angle = Math.PI / 8 + (index * Math.PI) / 4;
    pointsList.push(`${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`);
  }
  return pointsList.join(" ");
}

function points(values) {
  return values.map((value) => `${point(value).x},${point(value).y}`).join(" ");
}

function point(value) {
  if (Array.isArray(value)) {
    return { x: Number(value[0]), y: Number(value[1]) };
  }

  return { x: Number(value.x), y: Number(value.y) };
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

