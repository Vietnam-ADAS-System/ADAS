import { ROAD_HEIGHT, ROAD_WIDTH } from "../../services/mockTelemetry.js";

export function mapPoint(point, width, height) {
  if (Array.isArray(point)) {
    const [x, y] = point;
    return scalePoint(x, y, width, height);
  }

  return scalePoint(point.x, point.y, width, height);
}

function scalePoint(x, y, width, height) {
  const normalized = Math.abs(x) <= 1 && Math.abs(y) <= 1;

  if (normalized) {
    return {
      x: x * width,
      y: y * height
    };
  }

  return {
    x: (x / ROAD_WIDTH) * width,
    y: (y / ROAD_HEIGHT) * height
  };
}
