import CameraStatus from "./CameraStatus.jsx";

function formatFps(fps) {
  return Number.isFinite(fps) && fps > 0 ? fps.toFixed(1) : "--";
}

export default function CameraHeader({ connection, frame, metrics }) {
  const frameLabel = frame?.frameId ?? "--";
  const width = frame?.width ?? metrics?.frameSize?.width;
  const height = frame?.height ?? metrics?.frameSize?.height;
  const sizeLabel = width && height ? `${width}x${height}` : "--";

  return (
    <div className="camera-header">
      <div>
        <p className="eyebrow">Camera phía trước</p>
        <h1>Hỗ trợ lái ADAS</h1>
      </div>

      <div className="camera-metrics" aria-label="Thông số camera">
        <CameraStatus state={connection?.state} />
        <div className="metric">
          <span>Khung hình</span>
          <strong>{frameLabel}</strong>
        </div>
        <div className="metric">
          <span>FPS</span>
          <strong>{formatFps(metrics?.fps)}</strong>
        </div>
        <div className="metric">
          <span>Độ phân giải</span>
          <strong>{sizeLabel}</strong>
        </div>
      </div>
    </div>
  );
}
