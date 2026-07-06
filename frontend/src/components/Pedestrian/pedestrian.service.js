import { createRealtimeClient, parseJsonLike, toFrameId } from "../../services/realtime.js";

export const PEDESTRIAN_CLASSES = {
  0: "person",
  person: "person",
};

export function normalizePedestrianData(data) {
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
  } else if (payload.pedestrians) {
    detections = payload.pedestrians;
  } else if (payload.objects) {
    detections = payload.objects.filter((obj) => {
      const className = obj.class_name || obj.className || "";
      return className.toLowerCase().includes("person");
    });
  }

  const normalizedDetections = detections.map((det) => {
    let bbox = det.bbox;
    if (!bbox && det.x1 !== undefined) {
      bbox = [det.x1, det.y1, det.x2, det.y2];
    }

    return {
      frame_id: toFrameId(det) || frameId,
      bbox,
      class_id: det.class_id ?? det.classId ?? 0,
      class_name: det.class_name || det.className || PEDESTRIAN_CLASSES[0] || "person",
      confidence: Number(det.confidence ?? det.conf ?? 0),
      track_id: det.track_id || det.trackId,
    };
  });

  return {
    frame_id: frameId,
    detections: normalizedDetections,
    count: normalizedDetections.length,
  };
}

export function createPedestrianDataStream({ onData, onStatus }) {
  return createRealtimeClient({
    path: "/ws/pedestrian",
    connectionName: "pedestrian",
    normalizeMessage: normalizePedestrianData,
    onMessage: onData,
    onStatus,
  });
}

/**
 * Tạo mock pedestrian data cho demo mode
 */
export function createMockPedestrianStream(frameId) {
  // Person walking on side of road
  const personProgress = (frameId / 180) % 1;
  const personX = 250 + personProgress * 460;
  const personY = 540 * 0.88;
  const personH = 35;

  return {
    frame_id: frameId,
    detections: [
      {
        track_id: 4,
        class_name: "person",
        bbox: [personX - 12, personY - 12, personX + 12, personY + personH + 4],
        confidence: 0.91,
      },
    ],
    count: 1,
  };
}
