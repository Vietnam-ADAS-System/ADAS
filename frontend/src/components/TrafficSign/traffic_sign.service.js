import { createRealtimeClient, parseJsonLike, toFrameId } from "../../services/realtime.js";

export const TRAFFIC_SIGN_TYPES = {
  SPEED_LIMIT: "speed_limit",
  STOP: "stop",
  NO_ENTRY: "no_entry",
  YIELD: "yield",
  WARNING: "warning",
  PEDESTRIAN: "pedestrian",
  SCHOOL: "school",
  CURVE: "curve",
};

export const TRAFFIC_SIGN_LABELS = {
  speed_limit: "Giới hạn tốc độ",
  stop: "Dừng lại",
  no_entry: "Cấm đi vào",
  yield: "Nhường đường",
  warning: "Cảnh báo",
  pedestrian: "Người đi bộ",
  school: "Trường học",
  curve: "Đường cong",
};

export function normalizeTrafficSignData(data) {
  const payload = parseJsonLike(data);
  const frameId = toFrameId(payload);

  if (!payload || typeof payload !== "object") {
    return [];
  }

  let signs = [];

  if (Array.isArray(payload)) {
    signs = payload;
  } else if (payload.signs) {
    signs = payload.signs;
  } else if (payload.traffic_signs) {
    signs = payload.traffic_signs;
  } else if (payload.detections) {
    signs = payload.detections;
  }

  return signs.map((sign) => ({
    frame_id: frameId,
    sign_id: sign.sign_id || sign.id || `sign-${Math.random()}`,
    class_name: sign.class_name || sign.className || sign.label || "Unknown",
    class_name_en: sign.class_name_en || sign.labelEn || sign.class_name || "Unknown",
    icon: sign.icon || "⚠",
    confidence: Number(sign.confidence ?? sign.conf ?? 0),
    bbox: sign.bbox || { x: 0, y: 0, width: 50, height: 50 },
    center: sign.center || { x: 0, y: 0 },
    priority: sign.priority || "LOW",
    warning: Boolean(sign.warning),
    rule: sign.rule || sign.class_name || "",
    ruleEn: sign.ruleEn || sign.rule || sign.class_name_en || "",
  }));
}

export function createTrafficSignStream({ onData, onStatus }) {
  return createRealtimeClient({
    path: "/ws/traffic-sign",
    connectionName: "trafficSign",
    normalizeMessage: normalizeTrafficSignData,
    onMessage: onData,
    onStatus,
  });
}

/**
 * Tạo mock traffic sign data cho demo mode
 */
export function createMockTrafficSignStream(frameId) {
  const signs = [
    {
      sign_id: "speed-60",
      class_name: "Giới hạn 60 km/h",
      class_name_en: "Speed Limit 60 km/h",
      icon: "60",
      confidence: 0.92,
      bbox: { x: 900, y: 100, width: 80, height: 80 },
      center: { x: 940, y: 140 },
      priority: "MEDIUM",
      warning: Math.sin(frameId / 40) > 0.5,
      rule: "Tốc độ tối đa 60 km/h",
      ruleEn: "Maximum speed 60 km/h",
    },
    {
      sign_id: "stop-1",
      class_name: "Dừng lại",
      class_name_en: "Stop",
      icon: "STOP",
      confidence: 0.88,
      bbox: { x: 200, y: 150, width: 70, height: 70 },
      center: { x: 235, y: 185 },
      priority: "CRITICAL",
      warning: Math.sin(frameId / 35) > 0.7,
      rule: "Chuẩn bị dừng xe",
      ruleEn: "Prepare to stop",
    },
    {
      sign_id: "pedestrian-1",
      class_name: "Có người đi bộ",
      class_name_en: "Pedestrian Crossing",
      icon: "🚶",
      confidence: 0.85,
      bbox: { x: 500, y: 120, width: 60, height: 60 },
      center: { x: 530, y: 150 },
      priority: "HIGH",
      warning: Math.sin(frameId / 50) > 0.6,
      rule: "Cẩn thận người đi bộ",
      ruleEn: "Watch for pedestrians",
    },
  ];

  return signs;
}
