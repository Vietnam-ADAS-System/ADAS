import { createRealtimeClient, parseJsonLike, toFrameId } from "../../services/realtime.js";
import {
  makeMockLaneData,
  makeMockVehicleData,
  makeMockPedestrianData,
  makeMockTrafficSigns,
  makeMockWarningData,
  makeMockFrameData,
} from "../../services/mockTelemetry.js";

export const LANE_STATUS = {
  SAFE: "SAFE",
  NEAR_BOUNDARY: "NEAR_BOUNDARY",
  LANE_DEPARTURE: "LANE_DEPARTURE",
};

export function normalizeLaneData(data) {
  const payload = parseJsonLike(data);
  const frameId = toFrameId(payload);

  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    frame_id: frameId,
    lane_left: payload.lane_left || payload.laneLeft || [],
    lane_right: payload.lane_right || payload.laneRight || [],
    lane_center: payload.lane_center || payload.laneCenter || [],
    lane_width: Number(payload.lane_width ?? payload.laneWidth) || 0,
    vehicle_center: payload.vehicle_center || payload.vehicleCenter || null,
    offset: Number(payload.offset) || 0,
    normalized_offset: Number(payload.normalized_offset ?? payload.normalizedOffset) || 0,
    direction: payload.direction || "CENTER",
    lane_status: payload.lane_status || payload.laneStatus || LANE_STATUS.SAFE,
    warning: Boolean(payload.warning),
    lane_type: payload.lane_type || "highway",
    is_two_way: Boolean(payload.is_two_way),
    center_divider: payload.center_divider || [],
    is_changing_lane: Boolean(payload.is_changing_lane),
    lane_change_direction: payload.lane_change_direction || null,
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
    points.push([centerX + halfWidth * direction + curve, y]);
  }

  return points;
}

export function getDemoLaneVisualization(frameId, frameSize, vehicleState) {
  const width = frameSize?.width || 960;
  const height = frameSize?.height || 540;

  const laneWidth = 260;

  let vehicleCenterX = width * 0.5;
  let currentLane = 2;
  let offsetX = 0;
  let laneStatus = LANE_STATUS.SAFE;
  let direction = "CENTER";
  let isOpposite = false;

  if (vehicleState) {
    currentLane = vehicleState.lane ?? 2;
    offsetX = vehicleState.offsetX ?? 0;
    laneStatus = vehicleState.laneStatus || LANE_STATUS.SAFE;

    const laneStart = 320 + currentLane * 260;
    const thisLaneCenter = laneStart + laneWidth / 2;

    vehicleCenterX = thisLaneCenter + offsetX * (laneWidth / 2);

    isOpposite = currentLane < 2;

    if (isOpposite) {
      direction = "OPPOSITE";
    } else if (offsetX < -0.3) {
      direction = "LEFT";
    } else if (offsetX > 0.3) {
      direction = "RIGHT";
    } else {
      direction = "CENTER";
    }
  } else {
    const laneStart = 320 + 2 * 260;
    vehicleCenterX = laneStart + laneWidth / 2;
  }

  const roadCenterX = width * 0.5;
  const offset = vehicleCenterX - roadCenterX;
  const laneHalfBottom = width * 0.23;
  const normalizedOffset = offset / laneHalfBottom;
  const absOffset = Math.abs(normalizedOffset);

  laneStatus = isOpposite || laneStatus === LANE_STATUS.LANE_DEPARTURE
    ? LANE_STATUS.LANE_DEPARTURE
    : absOffset > 0.40
      ? LANE_STATUS.NEAR_BOUNDARY
      : LANE_STATUS.SAFE;

  const centerBottom = roadCenterX;
  const centerTop = roadCenterX;
  const laneHalfTop = width * 0.068;

  const isWarning = isOpposite || laneStatus === LANE_STATUS.LANE_DEPARTURE;

  return {
    frame_id: frameId,
    lane_left: makeLanePoints(centerBottom, laneHalfBottom, centerTop, laneHalfTop, height, "left"),
    lane_right: makeLanePoints(centerBottom, laneHalfBottom, centerTop, laneHalfTop, height, "right"),
    lane_center: [
      [centerTop, height * 0.48],
      [centerBottom, height * 0.96],
    ],
    lane_width: laneWidth,
    vehicle_center: [vehicleCenterX, height * 0.88],
    offset: Math.round(offset),
    normalized_offset: Number(normalizedOffset.toFixed(3)),
    direction,
    lane_status: laneStatus,
    warning: isWarning,
    is_changing_lane: absOffset > 0.5,
  };
}

export function createLaneDataStream({ onData, onStatus }) {
  return createRealtimeClient({
    path: "/ws/lane",
    connectionName: "lane",
    normalizeMessage: normalizeLaneData,
    onMessage: onData,
    onStatus,
  });
}

export function createMockLaneStream(frameId) {
  return makeMockLaneData(frameId);
}
