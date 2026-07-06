import { useEffect, useMemo, useRef } from "react";
import { getVehicleLabel } from "../../services/labelMapping.js";
import "./object.style.css";

const CLASS_COLORS = {
  person: { stroke: "#00ff88", fill: "rgba(0, 255, 136, 0.15)" },
};

function normalizeBbox(bbox) {
  if (!bbox) return null;
  if (Array.isArray(bbox)) {
    return {
      x1: Number(bbox[0]),
      y1: Number(bbox[1]),
      x2: Number(bbox[2]),
      y2: Number(bbox[3]),
    };
  }
  return {
    x1: Number(bbox.x1 ?? bbox.x ?? 0),
    y1: Number(bbox.y1 ?? bbox.y ?? 0),
    x2: Number(bbox.x2 ?? 0),
    y2: Number(bbox.y2 ?? 0),
  };
}

function createGeometry(viewport, frameSize) {
  if (!viewport?.contentRect || !frameSize?.width || !frameSize?.height) {
    return null;
  }

  const { contentRect } = viewport;

  function mapCoord(x, y) {
    return {
      x: contentRect.x + (x / frameSize.width) * contentRect.width,
      y: contentRect.y + (y / frameSize.height) * contentRect.height,
    };
  }

  return {
    mapBbox(bbox) {
      const topLeft = mapCoord(bbox.x1, bbox.y1);
      const bottomRight = mapCoord(bbox.x2, bbox.y2);
      return {
        x: topLeft.x,
        y: topLeft.y,
        width: bottomRight.x - topLeft.x,
        height: bottomRight.y - topLeft.y,
      };
    },
    mapPoint(x, y) {
      return mapCoord(x, y);
    },
  };
}

function drawPedestrian(ctx, mappedBbox, detection, geometry) {
  const { x, y, width, height } = mappedBbox;
  const className = detection.class_name || detection.className || "person";
  const label_vi = getVehicleLabel(className);
  const color = CLASS_COLORS[className] || CLASS_COLORS.person;

  ctx.strokeStyle = color.stroke;
  ctx.lineWidth = 2;
  ctx.fillStyle = color.fill;
  ctx.setLineDash([]);

  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 4);
  ctx.fill();
  ctx.stroke();

  const conf = Math.round((detection.confidence || detection.conf || 0) * 100);
  const label = `${label_vi} ${conf}%`;
  const labelPadding = 4;
  ctx.font = "bold 11px system-ui, sans-serif";
  const textMetrics = ctx.measureText(label);
  const textHeight = 14;

  ctx.fillStyle = "rgba(8, 12, 18, 0.85)";
  ctx.fillRect(x, y - textHeight - labelPadding * 2, textMetrics.width + labelPadding * 2, textHeight + labelPadding);

  ctx.fillStyle = "#fff";
  ctx.fillText(label, x + labelPadding, y - labelPadding - 2);
}

function isSynchronized(data, currentFrameId) {
  if (!data || currentFrameId == null) return Boolean(data);
  return Number(data.frame_id) === Number(currentFrameId);
}

export default function PedestrianLayer({ detections, currentFrameId, viewport, frameSize }) {
  const canvasRef = useRef(null);
  const synchronized = isSynchronized(detections, currentFrameId);
  const geometry = useMemo(() => createGeometry(viewport, frameSize), [frameSize, viewport]);
  const visibleDetections = synchronized ? (detections?.detections || detections?.pedestrians || []) : [];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !viewport) return;

    const dpr = viewport.dpr || window.devicePixelRatio || 1;
    canvas.width = Math.round(viewport.width * dpr);
    canvas.height = Math.round(viewport.height * dpr);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, viewport.width, viewport.height);

    if (!visibleDetections.length || !geometry) return;

    for (const detection of visibleDetections) {
      const rawBbox = detection.bbox || detection;
      const rawBboxArray = Array.isArray(rawBbox) ? rawBbox : [rawBbox.x1, rawBbox.y1, rawBbox.x2, rawBbox.y2];
      const bbox = {
        x1: Number(rawBboxArray[0]),
        y1: Number(rawBboxArray[1]),
        x2: Number(rawBboxArray[2]),
        y2: Number(rawBboxArray[3]),
      };

      if (bbox.x1 >= bbox.x2 || bbox.y1 >= bbox.y2) continue;

      const mappedBbox = geometry.mapBbox(bbox);
      drawPedestrian(ctx, mappedBbox, detection, geometry);
    }
  }, [geometry, visibleDetections, viewport]);

  return (
    <div className="pedestrian-layer" aria-label="Pedestrian detection layer">
      <canvas className="overlay-canvas" ref={canvasRef} />
    </div>
  );
}

export function getPedestrianCount(detections) {
  if (!detections) return 0;
  const list = detections.detections || detections.pedestrians || detections;
  return Array.isArray(list) ? list.length : 0;
}
