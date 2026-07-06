import { useEffect, useRef, useState } from "react";
import CameraCanvas from "./CameraCanvas.jsx";
import CameraHeader from "./CameraHeader.jsx";
import CameraLoading from "./CameraLoading.jsx";
import SceneLayer from "./SceneLayer.jsx";

function createFpsTracker() {
  return { count: 0, startedAt: performance.now(), lastFps: 0 };
}

function updateMeasuredFps(tracker) {
  const now = performance.now();
  tracker.count += 1;
  const elapsed = now - tracker.startedAt;
  if (elapsed >= 1000) {
    tracker.lastFps = (tracker.count * 1000) / elapsed;
    tracker.count = 0;
    tracker.startedAt = now;
  }
  return tracker.lastFps;
}

export default function CameraView({ overlayRenderer, onFrameChange, onConnectionChange, vehicleState }) {
  const [connection, setConnection] = useState({ state: "connecting" });
  const [frame, setFrame] = useState(null);
  const [metrics, setMetrics] = useState({ fps: 0, frameSize: null });
  const [viewport, setViewport] = useState(null);
  const fpsTrackerRef = useRef(createFpsTracker());
  const connectionRef = useRef(connection);
  const frameIdRef = useRef(0);

  useEffect(() => {
    // Demo mode - simulate frame updates for overlay components
    const targetFps = 30;
    let running = true;
    let lastTime = 0;
    let rafId;

    function tick(timestamp) {
      if (!running) return;

      if (timestamp - lastTime >= 1000 / targetFps) {
        lastTime = timestamp;
        frameIdRef.current++;

        const measuredFps = updateMeasuredFps(fpsTrackerRef.current);
        const nextFrame = {
          frameId: frameIdRef.current,
          fps: targetFps,
          width: 960,
          height: 540,
          timestamp: Date.now(),
          source: "demo",
        };

        setFrame(nextFrame);
        setMetrics({ fps: targetFps, frameSize: { width: 960, height: 540 } });
        setConnection({ state: "demo", connected: false });

        const conn = connectionRef.current;
        onFrameChange?.({ ...nextFrame, connection: conn });
        window.dispatchEvent(new CustomEvent("adas:frame", { detail: { ...nextFrame, connection: conn } }));
      }

      rafId = requestAnimationFrame(tick);
    }

    rafId = requestAnimationFrame(tick);

    return () => {
      running = false;
      cancelAnimationFrame(rafId);
    };
  }, [onFrameChange]);

  const cameraContext = {
    frameId: frame?.frameId ?? null,
    frameSize: metrics.frameSize,
    connection,
    fps: metrics.fps,
    frame,
  };

  return (
    <section className="camera-panel" aria-label="Realtime camera dashboard">
      <CameraHeader connection={connection} frame={frame} metrics={metrics} />
      <div className="camera-stage">
        <CameraCanvas frame={frame} onViewportChange={setViewport}>
          {(vp) => (
            <>
              <SceneLayer viewport={vp} frameId={cameraContext.frameId} vehicleState={vehicleState} />
              {overlayRenderer?.({ ...cameraContext, viewport: vp })}
            </>
          )}
        </CameraCanvas>
        {!frame && <CameraLoading state={connection.state} />}
      </div>
    </section>
  );
}
