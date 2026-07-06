const STATUS_LABELS = {
  connected: "TRỰC TIẾP",
  connecting: "ĐANG KẾT NỐI",
  reconnecting: "ĐANG NỐI LẠI",
  disconnected: "MẤT KẾT NỐI",
  demo: "MÔ PHỎNG",
  message_error: "LỖI LUỒNG",
};

export default function CameraStatus({ state }) {
  const normalizedState = state || "connecting";
  const label = STATUS_LABELS[normalizedState] || normalizedState.toUpperCase();

  return (
    <span className={`camera-status camera-status--${normalizedState}`}>
      <span className="camera-status__dot" aria-hidden="true" />
      {label}
    </span>
  );
}
