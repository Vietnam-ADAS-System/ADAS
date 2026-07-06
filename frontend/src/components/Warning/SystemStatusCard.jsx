const STATUS_LABELS = {
  camera: "Camera",
  vehicle_detection: "Nhận diện xe",
  lane_detection: "Nhận diện làn",
  traffic_sign_detection: "Nhận diện biển báo",
  adas: "ADAS",
};

const VALUE_LABELS = {
  Online: "Đang hoạt động",
  Running: "Đang chạy",
  Waiting: "Đang chờ",
  Tracking: "Đang theo dõi",
  Reconnecting: "Đang nối lại",
  Demo: "Mô phỏng",
};

export default function SystemStatusCard({ status }) {
  const entries = Object.entries(status || {});

  return (
    <section className="warning-section">
      <div className="section-title">Trạng thái hệ thống</div>
      <div className="system-status-list">
        {entries.map(([key, value]) => (
          <div className="system-status-row" key={key}>
            <span>{STATUS_LABELS[key] || key}</span>
            <strong>{VALUE_LABELS[value] || value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
