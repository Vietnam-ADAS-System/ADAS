import { useEffect, useMemo, useRef } from "react";
import { getSpriteConfig, preloadSprites } from "../../services/spriteManager.js";
import { getVehicleLabel } from "../../services/labelMapping.js";
import "./object.style.css";

// Module-level sprite state
let spritesPreloading = false;
let spritesReady = false;

// Preload sprites once
if (typeof window !== "undefined" && !spritesPreloading) {
  spritesPreloading = true;
  preloadSprites().then(() => {
    spritesReady = true;
  });
}

const CLASS_COLORS = {
  car: { stroke: "#4fb8ff", fill: "rgba(79, 184, 255, 0.15)" },
  motorcycle: { stroke: "#ff9f43", fill: "rgba(255, 159, 67, 0.15)" },
  truck: { stroke: "#a855f7", fill: "rgba(168, 85, 247, 0.15)" },
  bus: { stroke: "#06b6d4", fill: "rgba(6, 182, 212, 0.15)" },
  vehicle: { stroke: "#4fb8ff", fill: "rgba(79, 184, 255, 0.15)" },
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

function drawVehicle(ctx, mappedBbox, detection, geometry) {
  const { x, y, width, height } = mappedBbox;
  const className = detection.class_name || detection.className || detection.label || "vehicle";
  const label_vi = getVehicleLabel(className);
  const trackId = detection.track_id || detection.trackId;
  const color = CLASS_COLORS[className] || CLASS_COLORS.vehicle;

  // Try to use sprite for car/motorcycle
  if ((className === "car" || className === "motorcycle") && spritesReady) {
    // Get variant index based on trackId for visual variety
    const variantIndex = trackId ? (trackId - 1) % 3 : 0;
    const spriteConfig = getSpriteConfig(className, { x1: x, y1: y, x2: x + width, y2: y + height });
    
    if (spriteConfig?.sprite?.img) {
      // Draw sprite instead of rectangle
      ctx.save();
      ctx.drawImage(
        spriteConfig.sprite.img,
        spriteConfig.drawX,
        spriteConfig.drawY,
        spriteConfig.drawWidth,
        spriteConfig.drawHeight
      );
      ctx.restore();
    } else {
      // Fallback to styled rectangle if sprite not loaded
      drawVehicleStyled(ctx, x, y, width, height, color);
    }
  } else {
    // For truck/bus or if sprites not ready, use styled rectangle
    drawVehicleStyled(ctx, x, y, width, height, color);
  }

  // Draw bounding box outline (subtle dashed)
  ctx.strokeStyle = color.stroke;
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 3]);
  ctx.globalAlpha = 0.6;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 4);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = 1;

  // Draw label
  let label = `${label_vi}`;
  if (trackId !== undefined) {
    label = `ID ${trackId} ${label}`;
  }
  const conf = detection.confidence || detection.conf || 0;
  if (conf > 0) {
    label += ` ${Math.round(conf * 100)}%`;
  }

  const labelPadding = 4;
  ctx.font = "bold 11px system-ui, sans-serif";
  const textMetrics = ctx.measureText(label);
  const textHeight = 14;

  ctx.fillStyle = "rgba(8, 12, 18, 0.85)";
  ctx.fillRect(x, y - textHeight - labelPadding * 2, textMetrics.width + labelPadding * 2, textHeight + labelPadding);

  ctx.fillStyle = "#fff";
  ctx.fillText(label, x + labelPadding, y - labelPadding - 2);
}

function drawVehicleStyled(ctx, x, y, width, height, color) {
  // Gradient fill for vehicle body
  const gradient = ctx.createLinearGradient(x, y, x, y + height);
  gradient.addColorStop(0, color.fill);
  gradient.addColorStop(1, "rgba(0, 0, 0, 0.3)");

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, 6);
  ctx.fill();

  // Subtle shadow
  ctx.shadowColor = "rgba(0, 0, 0, 0.3)";
  ctx.shadowBlur = 10;
  ctx.shadowOffsetY = 5;
  ctx.strokeStyle = color.stroke;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.shadowColor = "transparent";
}

function isSynchronized(data, currentFrameId) {
  if (!data || currentFrameId == null) return Boolean(data);
  return Number(data.frame_id) === Number(currentFrameId);
}

export default function VehicleLayer({ detections, currentFrameId, viewport, frameSize }) {
  const canvasRef = useRef(null);
  const synchronized = isSynchronized(detections, currentFrameId);
  const geometry = useMemo(() => createGeometry(viewport, frameSize), [frameSize, viewport]);
  const visibleDetections = synchronized ? (detections?.detections || detections?.vehicles || []) : [];

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
      let rawBbox = detection.bbox;
      if (!rawBbox && detection.detections) {
        const firstDet = detection.detections[0];
        if (firstDet) rawBbox = firstDet.bbox || firstDet;
      }
      if (!rawBbox) continue;

      const rawBboxArray = Array.isArray(rawBbox) ? rawBbox : [rawBbox.x1, rawBbox.y1, rawBbox.x2, rawBbox.y2];
      const bbox = {
        x1: Number(rawBboxArray[0]),
        y1: Number(rawBboxArray[1]),
        x2: Number(rawBboxArray[2]),
        y2: Number(rawBboxArray[3]),
      };

      if (bbox.x1 >= bbox.x2 || bbox.y1 >= bbox.y2) continue;

      const mappedBbox = geometry.mapBbox(bbox);
      drawVehicle(ctx, mappedBbox, detection, geometry);
    }
  }, [geometry, visibleDetections, viewport]);

  return (
    <div className="vehicle-layer" aria-label="Vehicle detection layer">
      <canvas className="overlay-canvas" ref={canvasRef} />
    </div>
  );
}

export function getVehicleCount(detections) {
  if (!detections) return 0;
  const list = detections.detections || detections.vehicles || detections;
  return Array.isArray(list) ? list.length : 0;
}
