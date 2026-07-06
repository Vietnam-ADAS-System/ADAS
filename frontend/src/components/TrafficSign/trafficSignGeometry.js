import { ROAD_HEIGHT, ROAD_WIDTH } from "../../services/mockTelemetry.js";

export function priorityColor(priority, warning) {
  if (warning || priority === "CRITICAL") {
    return "#ff5c5c";
  }

  if (priority === "HIGH") {
    return "#ff9f43";
  }

  if (priority === "MEDIUM") {
    return "#f2c94c";
  }

  return priority === "LOW" ? "#55b8ff" : "#2fd27f";
}

export function mapBox(box, width, height) {
  if (Array.isArray(box)) {
    return scaleBox(box[0], box[1], box[2], box[3], width, height);
  }

  return scaleBox(
    box?.x ?? 0,
    box?.y ?? 0,
    box?.width ?? box?.w ?? 0,
    box?.height ?? box?.h ?? 0,
    width,
    height
  );
}

function scaleBox(x, y, boxWidth, boxHeight, width, height) {
  const normalized =
    Math.abs(x) <= 1 &&
    Math.abs(y) <= 1 &&
    Math.abs(boxWidth) <= 1 &&
    Math.abs(boxHeight) <= 1;

  if (normalized) {
    return {
      x: x * width,
      y: y * height,
      width: boxWidth * width,
      height: boxHeight * height
    };
  }

  return {
    x: (x / ROAD_WIDTH) * width,
    y: (y / ROAD_HEIGHT) * height,
    width: (boxWidth / ROAD_WIDTH) * width,
    height: (boxHeight / ROAD_HEIGHT) * height
  };
}
