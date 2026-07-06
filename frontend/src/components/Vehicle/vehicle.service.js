import { createRealtimeClient, parseJsonLike, toFrameId } from "../../services/realtime.js";

export const VEHICLE_CLASSES = {
  car: "car",
  motorcycle: "motorcycle",
  truck: "truck",
  bus: "bus",
  vehicle: "vehicle",
};

export const VEHICLE_CLASS_LABELS = {
  car: "Ô tô",
  motorcycle: "Xe máy",
  truck: "Xe tải",
  bus: "Xe buýt",
  vehicle: "Xe",
};

export const VEHICLE_CLASS_LABELS_EN = {
  car: "Car",
  motorcycle: "Motorcycle",
  truck: "Truck",
  bus: "Bus",
  vehicle: "Vehicle",
};

export function normalizeVehicleData(data) {
  const payload = parseJsonLike(data);
  const frameId = toFrameId(payload);

  if (!payload || typeof payload !== "object") {
    return null;
  }

  let detections = [];

  if (Array.isArray(payload)) {
    detections = payload;
  } else if (payload.detections) {
    detections = payload.detections;
  } else if (payload.vehicles) {
    detections = payload.vehicles;
  } else if (payload.objects) {
    detections = payload.objects;
  }

  const normalizedDetections = detections.map((det) => {
    let bbox = det.bbox;
    if (!bbox && det.x1 !== undefined) {
      bbox = [det.x1, det.y1, det.x2, det.y2];
    }

    const className = det.class_name || det.className || det.label || det.label_vi || "vehicle";

    return {
      frame_id: toFrameId(det) || frameId,
      bbox,
      class_id: det.class_id ?? det.classId ?? -1,
      class_name: className,
      label: className,
      confidence: Number(det.confidence ?? det.conf ?? 0),
      track_id: det.track_id || det.trackId,
      center: det.center,
    };
  });

  return {
    frame_id: frameId,
    detections: normalizedDetections,
    count: normalizedDetections.length,
  };
}

export function createVehicleDataStream({ onData, onStatus }) {
  return createRealtimeClient({
    path: "/ws/vehicle",
    connectionName: "vehicle",
    normalizeMessage: normalizeVehicleData,
    onMessage: onData,
    onStatus,
  });
}

export function createMockVehicleStream(frameId) {
  const centerX = 480;
  const horizon = 540 * 0.39;
  
  // Car - đi thẳng làn giữa
  const carProgress = (frameId / 200) % 1;
  const carScale = 0.3 + carProgress * 0.7;
  const carX = centerX + Math.sin(frameId / 90) * 3;
  const carY = horizon + 60 + (1 - carProgress) * 250;
  const carW = 960 * 0.14 * carScale;
  const carH = 540 * 0.1 * carScale;
  
  // Truck - đi thẳng làn phải
  const truckProgress = (frameId / 250) % 1;
  const truckScale = 0.4 + truckProgress * 0.6;
  const truckX = centerX + 120;
  const truckY = horizon + 40 + (1 - truckProgress) * 280;
  const truckW = 960 * 0.12 * truckScale;
  const truckH = 540 * 0.14 * truckScale;
  
  // Motorcycle - đi thẳng làn trái
  const motoProgress = (frameId / 150) % 1;
  const motoScale = 0.3 + motoProgress * 0.7;
  const motoX = centerX - 130;
  const motoY = horizon + 50 + (1 - motoProgress) * 260;
  const motoW = 50 * motoScale;
  const motoH = 35 * motoScale;

  // Car lệch làn - để demo cảnh báo
  const deviatedCarProgress = (frameId / 300) % 1;
  const deviatedCarScale = 0.5 + deviatedCarProgress * 0.5;
  const deviatedCarX = centerX - 80 + Math.sin(frameId / 40) * 40;
  const deviatedCarY = horizon + 80 + (1 - deviatedCarProgress) * 220;
  const deviatedCarW = 960 * 0.13 * deviatedCarScale;
  const deviatedCarH = 540 * 0.09 * deviatedCarScale;

  return {
    frame_id: frameId,
    detections: [
      {
        track_id: 1,
        class_name: "car",
        bbox: [carX - carW / 2, carY, carX + carW / 2, carY + carH],
        confidence: 0.93,
      },
      {
        track_id: 2,
        class_name: "truck",
        bbox: [truckX - truckW / 2, truckY, truckX + truckW / 2, truckY + truckH],
        confidence: 0.88,
      },
      {
        track_id: 3,
        class_name: "motorcycle",
        bbox: [motoX - motoW / 2, motoY, motoX + motoW / 2, motoY + motoH],
        confidence: 0.85,
      },
      {
        track_id: 5,
        class_name: "car",
        bbox: [deviatedCarX - deviatedCarW / 2, deviatedCarY, deviatedCarX + deviatedCarW / 2, deviatedCarY + deviatedCarH],
        confidence: 0.95,
        deviating: true,
      },
    ],
    count: 4,
  };
}
