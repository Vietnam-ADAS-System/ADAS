/**
 * Vietnamese Label Mapping
 * Maps YOLO class names to Vietnamese display labels
 * Used for internationalization support
 */

export const VEHICLE_LABELS = {
  // YOLO class names (lowercase)
  car: "Ô tô",
  motorcycle: "Xe máy",
  truck: "Xe tải",
  bus: "Xe buýt",
  vehicle: "Phương tiện",
  bicycle: "Xe đạp",
  pedestrian: "Người đi bộ",
};

export const TRAFFIC_SIGN_LABELS = {
  // Speed limits
  speed_limit_20: "Giới hạn tốc độ 20 km/h",
  speed_limit_30: "Giới hạn tốc độ 30 km/h",
  speed_limit_40: "Giới hạn tốc độ 40 km/h",
  speed_limit_50: "Giới hạn tốc độ 50 km/h",
  speed_limit_60: "Giới hạn tốc độ 60 km/h",
  speed_limit_70: "Giới hạn tốc độ 70 km/h",
  speed_limit_80: "Giới hạn tốc độ 80 km/h",
  speed_limit_90: "Giới hạn tốc độ 90 km/h",
  speed_limit_100: "Giới hạn tốc độ 100 km/h",
  speed_limit_110: "Giới hạn tốc độ 110 km/h",
  speed_limit_120: "Giới hạn tốc độ 120 km/h",
  speed_limit: "Giới hạn tốc độ",

  // Common signs
  stop: "Dừng lại",
  no_entry: "Cấm đi vào",
  yield: "Nhường đường",
  pedestrian_crossing: "Có người đi bộ",
  school: "Khu vực trường học",
  curve_left: "Đường cong trái",
  curve_right: "Đường cong phải",
  winding_road: "Đường gồ ghề",
  bump: "Đường lồi",
  slippery: "Đường trơn",
  narrow_road: "Đường hẹp",
  road_work: "Đang thi công",
  traffic_light: "Đèn tín hiệu",
  stop_ahead: "Dừng phía trước",
  yield_ahead: "Nhường đường phía trước",

  // Warning signs
  warning: "Cảnh báo",
  danger: "Nguy hiểm",
  children: "Trẻ em",
  animals: "Động vật",
  cyclist: "Người đi xe đạp",

  // Default/fallback
  default: "Biển báo giao thông",
};

export const WARNING_LABELS = {
  // Lane warnings
  lane_departure: "Cảnh báo lệch làn",
  lane_departure_left: "Lệch làn trái",
  lane_departure_right: "Lệch làn phải",
  lane_change: "Chuyển làn",
  out_of_lane: "Ra khỏi làn đường",

  // Collision warnings
  collision_warning: "Cảnh báo va chạm",
  forward_collision: "Va chạm phía trước",
  rear_collision: "Va chạm phía sau",
  blind_spot: "Điểm mù",
  adjacent_vehicle: "Xe bên cạnh",

  // Speed warnings
  overspeed: "Vượt tốc độ",
  speed_limit_exceeded: "Vượt quá tốc độ cho phép",
  too_fast: "Đang chạy quá nhanh",

  // Traffic sign warnings
  traffic_sign_detected: "Phát hiện biển báo",
  speed_limit_active: "Biển báo giới hạn tốc độ",
  stop_sign_active: "Biển báo dừng lại",
  yield_sign_active: "Biển báo nhường đường",

  // Pedestrian warnings
  pedestrian_detected: "Phát hiện người đi bộ",
  pedestrian_crossing: "Người đi bộ băng qua",
  pedestrian_warning: "Cảnh báo người đi bộ",

  // System status
  system: "Hệ thống",
  system_ok: "Hệ thống hoạt động tốt",
  system_warning: "Cảnh báo hệ thống",
  system_error: "Lỗi hệ thống",

  // Default
  default: "Cảnh báo",
};

export const LANE_STATUS_LABELS = {
  safe: "An toàn",
  lane_safe: "An toàn",
  inside_lane: "Trong làn",
  near_boundary: "Gần vạch",
  near_boundary_short: "Gần vạch",
  lane_departure: "Lệch làn",
  lane_departure_short: "Lệch làn",
  waiting: "Đang chờ",
  unknown: "Không xác định",
};

export const SYSTEM_STATUS_LABELS = {
  camera: "Camera",
  vehicle_detection: "Nhận diện xe",
  pedestrian_detection: "Nhận diện người đi bộ",
  lane_detection: "Nhận diện làn đường",
  traffic_sign_detection: "Nhận diện biển báo",
  adas: "Hệ thống ADAS",
  fusion: "Hệ thống Fusion",

  // Status values
  online: "Đang hoạt động",
  running: "Đang chạy",
  waiting: "Đang chờ",
  tracking: "Đang theo dõi",
  reconnecting: "Đang nối lại",
  error: "Lỗi",
  offline: "Ngoại tuyến",
  demo: "Mô phỏng",
};

export const DETECTION_STATUS_LABELS = {
  detected: "Đã phát hiện",
  tracking: "Đang theo dõi",
  no_detection: "Không phát hiện",
  scanning: "Đang quét",
  waiting: "Đang chờ",
};

export const ACTION_LABELS = {
  prepare_to_stop: "Chuẩn bị dừng xe",
  slow_down: "Giảm tốc độ",
  maintain_speed: "Giữ tốc độ",
  change_lane: "Chuyển làn",
  stay_in_lane: "Giữ làn đường",
  brake: "Phanh",
  accelerate: "Tăng tốc",
  check_blind_spot: "Kiểm tra điểm mù",
  watch_pedestrian: "Cẩn thận người đi bộ",
};

/**
 * Get Vietnamese label for a YOLO class name
 * @param {string} className - YOLO class name (lowercase)
 * @returns {string} Vietnamese label
 */
export function getVehicleLabel(className) {
  if (!className) return VEHICLE_LABELS.vehicle;
  const normalized = className.toLowerCase().trim();
  return VEHICLE_LABELS[normalized] || VEHICLE_LABELS.vehicle;
}

/**
 * Get Vietnamese label for a traffic sign
 * @param {string} signName - Traffic sign name/class
 * @returns {string} Vietnamese label
 */
export function getTrafficSignLabel(signName) {
  if (!signName) return TRAFFIC_SIGN_LABELS.default;

  const normalized = signName.toLowerCase().trim();

  // Direct match
  if (TRAFFIC_SIGN_LABELS[normalized]) {
    return TRAFFIC_SIGN_LABELS[normalized];
  }

  // Check for speed limit patterns
  const speedMatch = normalized.match(/speed[_\s]?limit[_\s]?(\d+)/i);
  if (speedMatch) {
    return `Giới hạn tốc độ ${speedMatch[1]} km/h`;
  }

  // Check for Speed Limit X patterns
  const speedMatch2 = normalized.match(/speed[_\s]?limit\s*(\d+)/i);
  if (speedMatch2) {
    return `Giới hạn tốc độ ${speedMatch2[1]} km/h`;
  }

  // Check for patterns like "40" or "60" alone (common in YOLO)
  const numberMatch = normalized.match(/^(\d+)$/);
  if (numberMatch) {
    return `Giới hạn tốc độ ${numberMatch[1]} km/h`;
  }

  // Check for Stop sign
  if (normalized.includes('stop')) {
    return TRAFFIC_SIGN_LABELS.stop;
  }

  // Check for No Entry
  if (normalized.includes('no_entry') || normalized.includes('noentry')) {
    return TRAFFIC_SIGN_LABELS.no_entry;
  }

  // Check for Yield
  if (normalized.includes('yield') || normalized.includes('give')) {
    return TRAFFIC_SIGN_LABELS.yield;
  }

  // Check for Pedestrian
  if (normalized.includes('pedestrian') || normalized.includes('walk')) {
    return TRAFFIC_SIGN_LABELS.pedestrian_crossing;
  }

  // Check for School
  if (normalized.includes('school') || normalized.includes('children')) {
    return TRAFFIC_SIGN_LABELS.school;
  }

  // Default
  return signName;
}

/**
 * Get Vietnamese label for a warning type
 * @param {string} warningType - Warning type name
 * @returns {string} Vietnamese label
 */
export function getWarningLabel(warningType) {
  if (!warningType) return WARNING_LABELS.default;
  const normalized = warningType.toLowerCase().trim();
  return WARNING_LABELS[normalized] || WARNING_LABELS.default;
}

/**
 * Get Vietnamese label for lane status
 * @param {string} status - Lane status
 * @returns {string} Vietnamese label
 */
export function getLaneStatusLabel(status) {
  if (!status) return LANE_STATUS_LABELS.waiting;
  const normalized = status.toLowerCase().trim();
  return LANE_STATUS_LABELS[normalized] || status;
}

/**
 * Get Vietnamese label for system status value
 * @param {string} status - System status value
 * @returns {string} Vietnamese label
 */
export function getSystemStatusLabel(status) {
  if (!status) return SYSTEM_STATUS_LABELS.waiting;
  const normalized = status.toLowerCase().trim();
  return SYSTEM_STATUS_LABELS[normalized] || status;
}

/**
 * Default export with all mappings
 */
export default {
  VEHICLE_LABELS,
  TRAFFIC_SIGN_LABELS,
  WARNING_LABELS,
  LANE_STATUS_LABELS,
  SYSTEM_STATUS_LABELS,
  DETECTION_STATUS_LABELS,
  ACTION_LABELS,
  getVehicleLabel,
  getTrafficSignLabel,
  getWarningLabel,
  getLaneStatusLabel,
  getSystemStatusLabel,
};
