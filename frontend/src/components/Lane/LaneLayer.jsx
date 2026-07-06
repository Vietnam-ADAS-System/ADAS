import { useEffect, useMemo, useRef } from "react";
import { drawLaneBoundary } from "./LaneBoundary.jsx";
import { drawLaneCenter } from "./LaneCenter.jsx";
import { drawSafeZone } from "./SafeZone.jsx";
import { drawVehiclePosition } from "./VehiclePosition.jsx";
import OffsetIndicator from "./OffsetIndicator.jsx";
import LaneStatus from "./LaneStatus.jsx";
import LaneDepartureAlert from "./LaneDepartureAlert.jsx";
import "./lane.style.css";

const STATUS_COLOR = {
  SAFE: "#2ecc71",
  NEAR_BOUNDARY: "#f1c40f",
  LANE_DEPARTURE: "#e74c3c",
};

const STATUS_FILL = {
  SAFE: "rgba(46, 204, 113, 0.7)",
  NEAR_BOUNDARY: "rgba(241, 196, 15, 0.75)",
  LANE_DEPARTURE: "rgba(231, 76, 60, 0.8)",
};

function normalizePoint(point) {
  if (Array.isArray(point)) {
    return { x: Number(point[0]), y: Number(point[1]) };
  }

  return { x: Number(point?.x), y: Number(point?.y) };
}

function createGeometry(viewport, frameSize) {
  if (!viewport?.contentRect || !frameSize?.width || !frameSize?.height) {
    return null;
  }

  const { contentRect } = viewport;

  function mapPoint(point) {
    const normalized = normalizePoint(point);
    return {
      x: contentRect.x + (normalized.x / frameSize.width) * contentRect.width,
      y: contentRect.y + (normalized.y / frameSize.height) * contentRect.height,
    };
  }

  return {
    mapPoint,
    mapPoints(points = []) {
      return points
        .map(mapPoint)
        .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
    },
  };
}

function isSynchronized(laneData, currentFrameId) {
  if (!laneData || currentFrameId == null || laneData.frame_id == null) {
    return Boolean(laneData);
  }

  return Number(laneData.frame_id) === Number(currentFrameId);
}

export default function LaneLayer({ laneData, currentFrameId, viewport, frameSize }) {
  const canvasRef = useRef(null);
  const synchronized = isSynchronized(laneData, currentFrameId);
  const geometry = useMemo(() => createGeometry(viewport, frameSize), [frameSize, viewport]);
  const visibleLaneData = synchronized ? laneData : null;

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas || !viewport) {
      return;
    }

    const dpr = viewport.dpr || window.devicePixelRatio || 1;
    canvas.width = Math.round(viewport.width * dpr);
    canvas.height = Math.round(viewport.height * dpr);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, viewport.width, viewport.height);

    if (!visibleLaneData || !geometry) {
      return;
    }

    const status = visibleLaneData.lane_status || "SAFE";
    drawSafeZone(ctx, geometry, visibleLaneData, STATUS_FILL[status] || STATUS_FILL.SAFE);
    drawLaneBoundary(ctx, geometry, visibleLaneData, STATUS_COLOR[status] || STATUS_COLOR.SAFE);
    drawLaneCenter(ctx, geometry, visibleLaneData);
    drawVehiclePosition(ctx, geometry, visibleLaneData);
  }, [geometry, visibleLaneData, viewport]);

  return (
    <div className="lane-layer" aria-label="Lane visualization layer">
      <canvas className="overlay-canvas" ref={canvasRef} />
      <OffsetIndicator laneData={visibleLaneData} />
      <LaneStatus laneData={visibleLaneData} />
      <LaneDepartureAlert laneData={visibleLaneData} />
    </div>
  );
}
