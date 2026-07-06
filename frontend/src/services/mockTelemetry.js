/**
 * Mock Telemetry - Mô phỏng dữ liệu ADAS cho Dashboard
 * Bao gồm: làn đường, phương tiện, người đi bộ, biển báo giao thông
 */

// Kích thước frame mặc định
export const ROAD_WIDTH = 1280;
export const ROAD_HEIGHT = 720;

// Các loại làn đường
export const LANE_TYPES = {
  HIGHWAY: "highway",       // Đường cao tốc (2 làn)
  TWO_WAY: "two_way",       // Đường 2 chiều (có vạch vàng giữa)
  CITY: "city",             // Đường đô thị (có làn xe máy)
  ONE_WAY: "one_way",      // Đường 1 chiều
};

// Các loại phương tiện
export const VEHICLE_TYPES = {
  CAR: "car",
  MOTORCYCLE: "motorcycle",
  TRUCK: "truck",
  BUS: "bus",
};

// Các loại biển báo
export const SIGN_TYPES = {
  SPEED_40: { id: "speed_40", icon: "40", label: "Giới hạn 40 km/h", labelEn: "Speed Limit 40", priority: "MEDIUM" },
  SPEED_60: { id: "speed_60", icon: "60", label: "Giới hạn 60 km/h", labelEn: "Speed Limit 60", priority: "MEDIUM" },
  SPEED_80: { id: "speed_80", icon: "80", label: "Giới hạn 80 km/h", labelEn: "Speed Limit 80", priority: "HIGH" },
  SPEED_100: { id: "speed_100", icon: "100", label: "Giới hạn 100 km/h", labelEn: "Speed Limit 100", priority: "HIGH" },
  STOP: { id: "stop", icon: "STOP", label: "Dừng lại", labelEn: "Stop", priority: "CRITICAL" },
  NO_ENTRY: { id: "no_entry", icon: "NO", label: "Cấm đi vào", labelEn: "No Entry", priority: "CRITICAL" },
  NO_LEFT: { id: "no_left", icon: "←", label: "Cấm rẽ trái", labelEn: "No Left Turn", priority: "HIGH" },
  NO_RIGHT: { id: "no_right", icon: "→", label: "Cấm rẽ phải", labelEn: "No Right Turn", priority: "HIGH" },
  YIELD: { id: "yield", icon: "△", label: "Nhường đường", labelEn: "Yield", priority: "HIGH" },
  PEDESTRIAN: { id: "pedestrian", icon: "🚶", label: "Có người đi bộ", labelEn: "Pedestrian Crossing", priority: "MEDIUM" },
  SCHOOL: { id: "school", icon: "SCHOOL", label: "Khu vực trường học", labelEn: "School Zone", priority: "HIGH" },
  CURVE_LEFT: { id: "curve_left", icon: "←↰", label: "Đường cong trái", labelEn: "Curve Left", priority: "MEDIUM" },
  CURVE_RIGHT: { id: "curve_right", icon: "↱→", label: "Đường cong phải", labelEn: "Curve Right", priority: "MEDIUM" },
  roundabout: { id: "roundabout", icon: "↺", label: "Vòng xuyến", labelEn: "Roundabout", priority: "MEDIUM" },
 parking: { id: "parking", icon: "P", label: "Khu vực đỗ xe", labelEn: "Parking", priority: "LOW" },
  TRAFFIC_LIGHT: { id: "traffic_light", icon: "🚦", label: "Đèn tín hiệu", labelEn: "Traffic Light", priority: "CRITICAL" },
  LANE_END: { id: "lane_end", icon: "≠", label: "Làn kết thúc", labelEn: "Lane Ends", priority: "HIGH" },
  WARNING: { id: "warning", icon: "⚠", label: "Cảnh báo chung", labelEn: "Warning", priority: "MEDIUM" },
  NO_PARKING: { id: "no_parking", icon: "P⊘", label: "Cấm đỗ xe", labelEn: "No Parking", priority: "LOW" },
  SPEED_HUMP: { id: "speed_hump", icon: "凸", label: "Gồ giảm tốc", labelEn: "Speed Hump", priority: "MEDIUM" },
};

// State cho simulation
let simulationState = {
  laneType: LANE_TYPES.HIGHWAY,
  vehicleX: ROAD_WIDTH / 2,
  vehicleTargetX: ROAD_WIDTH / 2,
  vehicleY: ROAD_HEIGHT * 0.88,
  laneOffset: 0,
  laneOffsetTarget: 0,
  steeringAngle: 0,
  speed: 60,
  isChangingLane: false,
  laneChangeDirection: null,
  laneChangeProgress: 0,
  lastLaneChange: 0,
  nearbyVehicles: [],
  pedestrians: [],
  activeSigns: [],
  signPhases: [],
  time: 0,
};

/**
 * Reset simulation state
 */
export function resetSimulation() {
  simulationState = {
    laneType: LANE_TYPES.HIGHWAY,
    vehicleX: ROAD_WIDTH / 2,
    vehicleTargetX: ROAD_WIDTH / 2,
    vehicleY: ROAD_HEIGHT * 0.88,
    laneOffset: 0,
    laneOffsetTarget: 0,
    steeringAngle: 0,
    speed: 60,
    isChangingLane: false,
    laneChangeDirection: null,
    laneChangeProgress: 0,
    lastLaneChange: 0,
    nearbyVehicles: [],
    pedestrians: [],
    activeSigns: [],
    signPhases: [],
    time: 0,
  };
}

/**
 * Chuyển loại làn đường ngẫu nhiên
 */
export function setLaneType(laneType) {
  simulationState.laneType = laneType;
  resetSimulation();
}

/**
 * Tạo xe mô phỏng (ô tô, xe máy, xe tải, xe buýt)
 */
function generateNearbyVehicles(frameId) {
  const vehicles = [];
  const vehicleCount = Math.floor(Math.sin(frameId / 100) * 2 + 3); // 1-5 xe

  for (let i = 0; i < vehicleCount; i++) {
    const type = [VEHICLE_TYPES.CAR, VEHICLE_TYPES.MOTORCYCLE, VEHICLE_TYPES.TRUCK, VEHICLE_TYPES.BUS][i % 4];
    const relSpeed = (Math.random() - 0.5) * 40; // -20 to +20 km/h relative
    const laneOffset = (i % 2 === 0 ? 1 : -1) * (120 + i * 30); // Các làn khác
    const verticalOffset = ((frameId * 2 + i * 150) % 800) - 100; // Xe chạy qua

    const baseWidth = type === VEHICLE_TYPES.TRUCK ? 180 : type === VEHICLE_TYPES.BUS ? 160 : type === VEHICLE_TYPES.MOTORCYCLE ? 60 : 120;
    const baseHeight = type === VEHICLE_TYPES.TRUCK ? 220 : type === VEHICLE_TYPES.BUS ? 200 : type === VEHICLE_TYPES.MOTORCYCLE ? 80 : 100;

    const centerX = ROAD_WIDTH / 2 + laneOffset;
    const centerY = verticalOffset;

    vehicles.push({
      track_id: i + 1,
      class_name: type,
      bbox: [
        Math.max(0, centerX - baseWidth / 2),
        Math.max(0, centerY - baseHeight / 2),
        Math.min(ROAD_WIDTH, centerX + baseWidth / 2),
        Math.min(ROAD_HEIGHT, centerY + baseHeight / 2),
      ],
      confidence: 0.85 + Math.random() * 0.14,
      speed: simulationState.speed + relSpeed,
      distance: Math.abs(verticalOffset - simulationState.vehicleY),
    });
  }

  // Xe đang ở làn kế cạnh
  if (simulationState.isChangingLane) {
    const offset = simulationState.laneChangeDirection === "LEFT" ? -150 : 150;
    vehicles.push({
      track_id: 99,
      class_name: VEHICLE_TYPES.CAR,
      bbox: [
        ROAD_WIDTH / 2 + offset - 60,
        simulationState.vehicleY - 50,
        ROAD_WIDTH / 2 + offset + 60,
        simulationState.vehicleY + 50,
      ],
      confidence: 0.92,
      speed: simulationState.speed - 10,
      distance: 50,
      warning: true,
    });
  }

  return vehicles;
}

/**
 * Tạo người đi bộ mô phỏng
 */
function generatePedestrians(frameId) {
  const pedestrians = [];

  // Thỉnh thoảng có người đi bộ
  if (frameId % 180 < 30) {
    const count = Math.floor(frameId / 90) % 3 + 1;
    for (let i = 0; i < count; i++) {
      const x = 200 + i * 100 + Math.sin(frameId / 20) * 30;
      const y = 400 + i * 40 + Math.cos(frameId / 25) * 20;

      pedestrians.push({
        track_id: i + 10,
        class_name: "person",
        bbox: [x - 25, y - 50, x + 25, y + 50],
        confidence: 0.80 + Math.random() * 0.15,
        action: Math.random() > 0.5 ? "walking" : "standing",
      });
    }
  }

  return pedestrians;
}

/**
 * Tạo biển báo mô phỏng
 */
function generateTrafficSigns(frameId) {
  const signs = [];
  const signKeys = Object.keys(SIGN_TYPES);
  const numSigns = 3;

  for (let i = 0; i < numSigns; i++) {
    const signKey = signKeys[(Math.floor(frameId / 120) + i) % signKeys.length];
    const signType = SIGN_TYPES[signKey];
    const x = 100 + i * 400 + Math.sin(frameId / 50) * 20;
    const y = 100 + (i % 2) * 80;
    const shouldWarn = Math.sin(frameId / 40 + i) > 0.7;

    signs.push({
      sign_id: `${signType.id}-${i}`,
      class_name: signType.label,
      class_name_en: signType.labelEn,
      icon: signType.icon,
      confidence: 0.82 + Math.random() * 0.16,
      bbox: { x: x - 40, y: y - 40, width: 80, height: 80 },
      center: { x: x, y: y },
      priority: signType.priority,
      warning: shouldWarn,
      rule: signType.label,
      ruleEn: signType.labelEn,
    });
  }

  return signs;
}

/**
 * Tạo dữ liệu làn đường với mô phỏng xe đi làn phải (quy tắc VN)
 * CHỈ tạo làn ĐANG ĐI (1 làn), không phải toàn bộ đường
 */
export function makeMockLaneData(frameId, vehicleState) {
  const t = frameId / 24;
  const ROAD_WIDTH = 1280;
  const roadCenter = ROAD_WIDTH / 2;
  
  // Làn đang đi = làn phải (bên phải của center divider)
  // 4 làn: 0-320 (ngược), 320-640 (ngược), 640-960 (cùng), 960-1280 (cùng/phải)
  const laneWidth = 260;
  const laneLeftEdge = roadCenter + 280;  // 920
  const laneRightEdge = ROAD_WIDTH - 40;   // 1240
  const laneCenter = (laneLeftEdge + laneRightEdge) / 2; // 1080
  
  // Xác định vị trí xe
  let vehicleCenterX = laneCenter;
  let currentLane = 2; // Mặc định làn 2 (cùng chiều phải)
  let offsetX = 0;
  let laneStatus = "SAFE";
  let direction = "CENTER";
  let isOpposite = false;
  
  if (vehicleState) {
    currentLane = vehicleState.lane ?? 2;
    offsetX = vehicleState.offsetX ?? 0;
    laneStatus = vehicleState.laneStatus || "SAFE";
    
    // Tính vị trí xe dựa trên làn
    // Làn 0: 320-580, Làn 1: 580-840, Làn 2: 840-1100, Làn 3: 1100-1280
    const laneStart = 320 + currentLane * 260;
    const laneEnd = laneStart + laneWidth;
    const thisLaneCenter = (laneStart + laneEnd) / 2;
    
    // Offset trong làn (-1 to 1, 0 là giữa làn)
    vehicleCenterX = thisLaneCenter + offsetX * (laneWidth / 2);
    
    // Xác định ngược chiều
    isOpposite = currentLane < 2;
    
    // Hướng lệch
    if (isOpposite) {
      direction = "OPPOSITE";
    } else if (offsetX < -0.3) {
      direction = "LEFT";
    } else if (offsetX > 0.3) {
      direction = "RIGHT";
    } else {
      direction = "CENTER";
    }
  }

  const laneOffset = vehicleCenterX - laneCenter;
  const laneHalfWidth = (laneRightEdge - laneLeftEdge) / 2;
  const normalizedOffset = laneOffset / laneHalfWidth;

  // Tính perspective - điểm hội tụ ở phía xa
  const vanishingY = 200;
  const baseY = 720;

  // Điểm làn đường (perspective - thu hẹp về phía xa)
  const lane_left = [
    { x: laneLeftEdge + 20, y: baseY },
    { x: laneLeftEdge - 30, y: 560 },
    { x: laneLeftEdge - 60, y: 400 },
    { x: laneLeftEdge - 80, y: vanishingY },
  ];

  const lane_right = [
    { x: laneRightEdge - 20, y: baseY },
    { x: laneRightEdge + 50, y: 560 },
    { x: laneRightEdge + 80, y: 400 },
    { x: laneRightEdge + 100, y: vanishingY },
  ];

  const lane_center = [
    { x: laneCenter, y: baseY },
    { x: laneCenter, y: 560 },
    { x: laneCenter, y: 400 },
    { x: laneCenter, y: vanishingY },
  ];

  // Xác định màu boundary dựa trên trạng thái
  const boundaryColor = laneStatus === "LANE_DEPARTURE" ? "#ff4f5f" 
    : laneStatus === "NEAR_BOUNDARY" ? "#f5c84c" 
    : "#2fd17f";
  
  // Nguy hiểm: ngược chiều hoặc thực sự lệch khỏi làn
  const isLaneWarning = isOpposite || laneStatus === "LANE_DEPARTURE";

  return {
    frame_id: frameId,
    lane_type: simulationState.laneType,
    is_two_way: false,
    lane_left,
    lane_right,
    lane_center,
    center_divider: [],
    lane_width: Math.round(laneRightEdge - laneLeftEdge),
    vehicle_center: { x: vehicleCenterX, y: simulationState.vehicleY },
    offset: Math.round(laneOffset),
    normalized_offset: Number(normalizedOffset.toFixed(3)),
    direction,
    lane_status: laneStatus,
    lane_boundary_color: boundaryColor,
    warning: isLaneWarning,
    is_changing_lane: vehicleState?.isChangingLane || false,
    lane_change_direction: vehicleState?.laneChangeDirection || null,
    steering_angle: 0,
    speed: simulationState.speed,
    // Debug info
    _debug: {
      currentLane,
      offsetX,
      isOpposite,
      vehicleCenterX,
    },
  };
}

/**
 * Tạo dữ liệu phương tiện mô phỏng
 */
export function makeMockVehicleData(frameId) {
  const vehicles = generateNearbyVehicles(frameId);

  return {
    frame_id: frameId,
    detections: vehicles,
    count: vehicles.length,
    types: {
      car: vehicles.filter(v => v.class_name === VEHICLE_TYPES.CAR).length,
      motorcycle: vehicles.filter(v => v.class_name === VEHICLE_TYPES.MOTORCYCLE).length,
      truck: vehicles.filter(v => v.class_name === VEHICLE_TYPES.TRUCK).length,
      bus: vehicles.filter(v => v.class_name === VEHICLE_TYPES.BUS).length,
    },
    nearby_warning: vehicles.some(v => v.warning),
  };
}

/**
 * Tạo dữ liệu người đi bộ mô phỏng
 */
export function makeMockPedestrianData(frameId) {
  const pedestrians = generatePedestrians(frameId);

  return {
    frame_id: frameId,
    detections: pedestrians,
    count: pedestrians.length,
    has_crossing: pedestrians.length > 0,
  };
}

/**
 * Tạo dữ liệu biển báo mô phỏng
 */
export function makeMockTrafficSigns(frameId) {
  return generateTrafficSigns(frameId);
}

/**
 * Tạo dữ liệu cảnh báo tổng hợp
 * ƯU TIÊN: Biển báo tốc độ > Lệch làn > Xe kề > Người đi bộ
 */
export function makeMockWarningData(frameId, context = {}) {
  const lane = context.laneData || makeMockLaneData(frameId, context.vehicleState);
  const signs = context.trafficSigns || makeMockTrafficSigns(frameId);
  const vehicles = context.vehicleData || makeMockVehicleData(frameId);
  const pedestrians = context.pedestrianData || makeMockPedestrianData(frameId);
  const vehicleState = context.vehicleState; // Xe điều khiển bằng bàn phím

  // Tìm biển báo tốc độ active (kiểm tra cả "Giới hạn" và "Speed Limit")
  const activeSpeedSign = signs.find(s => s.warning && (s.class_name.includes("Tốc độ") || s.class_name.includes("Giới hạn") || s.class_name.includes("Speed") || s.icon?.match(/^\d+$/)));
  const currentSpeed = vehicleState?.speed ?? 60;

  let warningType = "SYSTEM";
  let warningLevel = "INFO";
  let warningMessage = "Hệ thống giám sát bình thường";
  let warningMessageEn = "System monitoring normal";

  // ƯU TIÊN 1: Biển báo tốc độ (NGUY HIỂM NHẤT)
  if (activeSpeedSign) {
    const signSpeed = parseInt(activeSpeedSign.icon) || 60;
    const isSpeeding = currentSpeed > signSpeed;

    if (isSpeeding) {
      warningType = "SPEED_LIMIT";
      warningLevel = "HIGH";
      warningMessage = `Vượt quá tốc độ! ${currentSpeed} > ${signSpeed} km/h`;
      warningMessageEn = `Speeding! ${currentSpeed} > ${signSpeed} km/h`;
    } else {
      warningType = "TRAFFIC_SIGN";
      warningLevel = "INFO";
      warningMessage = `Biển báo: ${signSpeed} km/h`;
      warningMessageEn = `Speed limit: ${signSpeed} km/h`;
    }
  }
  // ƯU TIÊN 2: Lệch làn (dùng vehicleState nếu có)
  else if (vehicleState?.laneStatus === "LANE_DEPARTURE" || lane.warning) {
    warningType = "LANE_DEPARTURE";
    warningLevel = "CRITICAL";
    const isOpposite = (vehicleState?.lane || 2) < 2;
    warningMessage = isOpposite
      ? "NGUY HIỂM! Xe đang ngược chiều!"
      : "Lệch làn đường!";
    warningMessageEn = isOpposite
      ? "DANGER! Wrong direction lane!"
      : "Lane departure detected!";
  }
  // ƯU TIÊN 3: Xe kề đang chuyển làn
  else if (vehicles.nearby_warning) {
    warningType = "VEHICLE_NEARBY";
    warningLevel = "HIGH";
    warningMessage = "Xe bên cạnh đang chuyển làn";
    warningMessageEn = "Vehicle adjacent is changing lane";
  }
  // ƯU TIÊN 4: Người đi bộ
  else if (pedestrians.has_crossing) {
    warningType = "PEDESTRIAN";
    warningLevel = "HIGH";
    warningMessage = "Có người đi bộ qua đường";
    warningMessageEn = "Pedestrian crossing ahead";
  }
  // ƯU TIÊN 5: Gần vạch làn
  else if (vehicleState?.laneStatus === "NEAR_BOUNDARY" || lane.lane_status === "NEAR_BOUNDARY") {
    warningType = "LANE";
    warningLevel = "MEDIUM";
    warningMessage = "Gần vạch làn đường";
    warningMessageEn = "Near lane boundary";
  }

  const hasWarning = warningType !== "SYSTEM";

  return {
    frame_id: frameId,
    vehicle_status: "RUNNING",
    lane_status: vehicleState?.laneStatus || lane.lane_status,
    traffic_sign_status: activeSpeedSign ? activeSpeedSign.class_name : "No active sign",
    camera_status: "CONNECTED",
    warning_type: warningType,
    warning_level: warningLevel,
    warning_message: warningMessage,
    warning_message_en: warningMessageEn,
    active: hasWarning,
    timestamp: new Date().toISOString(),
    // Chi tiết bổ sung
    lane_details: {
      offset: lane.offset,
      direction: lane.direction,
      speed: lane.speed,
      is_changing_lane: lane.is_changing_lane,
      lane_change_direction: lane.lane_change_direction,
      steering_angle: lane.steering_angle,
    },
    vehicle_count: vehicles.count,
    pedestrian_count: pedestrians.count,
    active_sign: activeSpeedSign || signs.find(s => s.warning),
  };
}

/**
 * Export tất cả data cho 1 frame (để gọi 1 lần)
 */
export function makeMockFrameData(frameId) {
  const laneData = makeMockLaneData(frameId);
  const vehicleData = makeMockVehicleData(frameId);
  const pedestrianData = makeMockPedestrianData(frameId);
  const trafficSigns = makeMockTrafficSigns(frameId);
  const warningData = makeMockWarningData(frameId, {
    laneData,
    vehicleData,
    pedestrianData,
    trafficSigns,
  });

  return {
    frame_id: frameId,
    lane: laneData,
    vehicles: vehicleData,
    pedestrians: pedestrianData,
    traffic_signs: trafficSigns,
    warning: warningData,
  };
}
