import { useEffect, useMemo, useRef } from "react";
import { drawTrafficSignBox } from "./TrafficSignBox.jsx";
import { drawTrafficSignLabel } from "./TrafficSignLabel.jsx";
import TrafficSignIcon from "./TrafficSignIcon.jsx";
import TrafficSignRule from "./TrafficSignRule.jsx";
import TrafficSignWarning from "./TrafficSignWarning.jsx";
import "./traffic_sign.style.css";

const PRIORITY_COLOR = {
  LOW: "#4fb8ff",
  MEDIUM: "#f5c84c",
  HIGH: "#ff9f43",
  CRITICAL: "#ff4f5f",
};

function normalizePoint(point) {
  if (Array.isArray(point)) {
    return { x: Number(point[0]), y: Number(point[1]) };
  }

  return { x: Number(point?.x), y: Number(point?.y) };
}

function normalizeBox(box) {
  if (Array.isArray(box)) {
    if (box.length >= 4) {
      const [x1, y1, x2, y2] = box.map(Number);
      return { x1, y1, x2, y2 };
    }
  }

  return {
    x1: Number(box?.x ?? box?.left),
    y1: Number(box?.y ?? box?.top),
    x2: Number((box?.x ?? box?.left) + (box?.width ?? 0)),
    y2: Number((box?.y ?? box?.top) + (box?.height ?? 0)),
  };
}

function createGeometry(viewport, frameSize) {
  if (!viewport?.contentRect || !frameSize?.width || !frameSize?.height) {
    return null;
  }

  const { contentRect } = viewport;
  const scaleX = contentRect.width / frameSize.width;
  const scaleY = contentRect.height / frameSize.height;

  return {
    mapPoint(point) {
      const normalized = normalizePoint(point);
      return {
        x: contentRect.x + normalized.x * scaleX,
        y: contentRect.y + normalized.y * scaleY,
      };
    },
    mapBox(box) {
      const normalized = normalizeBox(box);
      return {
        x: contentRect.x + normalized.x1 * scaleX,
        y: contentRect.y + normalized.y1 * scaleY,
        width: (normalized.x2 - normalized.x1) * scaleX,
        height: (normalized.y2 - normalized.y1) * scaleY,
      };
    },
  };
}

function isSynchronized(sign, currentFrameId) {
  if (!sign || currentFrameId == null || sign.frame_id == null) {
    return Boolean(sign);
  }

  return Number(sign.frame_id) === Number(currentFrameId);
}

export default function TrafficSignLayer({ signs, currentFrameId, viewport, frameSize }) {
  const canvasRef = useRef(null);
  const geometry = useMemo(() => createGeometry(viewport, frameSize), [frameSize, viewport]);
  const visibleSigns = useMemo(
    () => (signs || []).filter((sign) => isSynchronized(sign, currentFrameId)),
    [currentFrameId, signs],
  );
  const markers = useMemo(() => {
    if (!geometry) {
      return [];
    }

    return visibleSigns.map((sign) => {
      const rect = geometry.mapBox(sign.bbox);
      return {
        sign,
        rect,
        iconStyle: {
          left: `${rect.x + rect.width + 8}px`,
          top: `${rect.y}px`,
        },
        ruleStyle: {
          left: `${Math.max(8, rect.x)}px`,
          top: `${rect.y + rect.height + 8}px`,
        },
        warningStyle: {
          left: `${Math.max(8, rect.x)}px`,
          top: `${Math.max(8, rect.y - 58)}px`,
        },
      };
    });
  }, [geometry, visibleSigns]);

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

    if (!geometry) {
      return;
    }

    markers.forEach(({ sign, rect }) => {
      const color = PRIORITY_COLOR[sign.priority] || PRIORITY_COLOR.LOW;
      drawTrafficSignBox(ctx, rect, color, sign.warning);
      drawTrafficSignLabel(ctx, rect, sign, color);
    });
  }, [geometry, markers, viewport]);

  return (
    <div className="traffic-sign-layer" aria-label="Traffic sign visualization layer">
      <canvas className="overlay-canvas" ref={canvasRef} />
      {markers.map(({ sign, iconStyle, ruleStyle, warningStyle }) => (
        <div className="traffic-sign-marker" key={sign.sign_id}>
          <TrafficSignWarning sign={sign} style={warningStyle} />
          <TrafficSignIcon sign={sign} style={iconStyle} />
          <TrafficSignRule sign={sign} style={ruleStyle} />
        </div>
      ))}
    </div>
  );
}
