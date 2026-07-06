export default function CameraLoading({ state }) {
  const label = state === "reconnecting" ? "Đang nối lại camera..." : "Đang tải camera...";

  return (
    <div className="camera-loading" role="status" aria-live="polite">
      <div className="camera-loading__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
