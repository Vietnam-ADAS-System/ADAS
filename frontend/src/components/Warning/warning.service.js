import { createRealtimeClient, parseJsonLike, toFrameId } from "../../services/realtime.js";
import { makeMockWarningData, makeMockLaneData, makeMockVehicleData, makeMockPedestrianData, makeMockTrafficSigns } from "../../services/mockTelemetry.js";

const DEFAULT_SYSTEM_STATUS = {
  camera: "Đang hoạt động",
  vehicle_detection: "Đang chờ",
  lane_detection: "Đang chờ",
  traffic_sign_detection: "Đang chờ",
  adas: "Đang chạy",
};

export function normalizeWarningData(data) {
  const payload = parseJsonLike(data);

  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    frame_id: toFrameId(payload),
    vehicle_status: payload.vehicle_status || payload.vehicleStatus || "Đang chờ",
    lane_status: payload.lane_status || payload.laneStatus || "Waiting",
    traffic_sign_status:
      payload.traffic_sign_status || payload.trafficSignStatus || payload.sign_status || "Đang chờ",
    system_status: payload.system_status || payload.systemStatus || DEFAULT_SYSTEM_STATUS,
    warning_type: payload.warning_type || payload.warningType || "SYSTEM",
    warning_level: payload.warning_level || payload.warningLevel || payload.priority || "INFO",
    warning_message: payload.warning_message || payload.warningMessage || "Hệ thống đang giám sát",
    active: Boolean(payload.active),
    timestamp: payload.timestamp || new Date().toISOString(),
  };
}

function priorityToWarningLevel(priority) {
  if (priority === "CRITICAL") {
    return "CRITICAL";
  }

  if (priority === "HIGH") {
    return "HIGH";
  }

  if (priority === "MEDIUM") {
    return "MEDIUM";
  }

  return "LOW";
}

function cameraStatusLabel(cameraConnection) {
  if (cameraConnection?.state === "connected") {
    return "Đang hoạt động";
  }

  if (cameraConnection?.state === "demo") {
    return "Mô phỏng";
  }

  if (cameraConnection?.state === "reconnecting") {
    return "Đang nối lại";
  }

  return "Đang chờ";
}

export function deriveDemoWarningData({ frameId, laneData, trafficSigns, cameraConnection, vehicleState }) {
  // Use new mock telemetry
  const mockWarning = makeMockWarningData(frameId, {
    laneData,
    trafficSigns,
    vehicleState,
  });

  const systemStatus = {
    camera: cameraStatusLabel(cameraConnection),
    vehicle_detection: "Sẵn sàng",
    lane_detection: laneData ? "Đang chạy" : "Đang chờ",
    traffic_sign_detection: trafficSigns?.length ? "Đang chạy" : "Đang chờ",
    adas: "Đang chạy",
  };

  return {
    frame_id: frameId,
    vehicle_status: mockWarning.vehicle_status,
    lane_status: mockWarning.lane_status,
    traffic_sign_status: mockWarning.traffic_sign_status,
    system_status: systemStatus,
    warning_type: mockWarning.warning_type,
    warning_level: mockWarning.warning_level,
    warning_message: mockWarning.warning_message,
    warning_message_en: mockWarning.warning_message_en,
    active: mockWarning.active,
    timestamp: mockWarning.timestamp,
    lane_details: mockWarning.lane_details,
    vehicle_count: mockWarning.vehicle_count,
    pedestrian_count: mockWarning.pedestrian_count,
    active_sign: mockWarning.active_sign,
  };
}

export function createWarningStream({ onData, onStatus }) {
  return createRealtimeClient({
    path: "/ws/warning",
    connectionName: "warning",
    normalizeMessage: normalizeWarningData,
    onMessage: onData,
    onStatus,
  });
}

/**
 * Tạo mock warning data cho demo mode với đầy đủ tính năng
 */
export function createMockWarningStream(frameId) {
  return makeMockWarningData(frameId);
}
