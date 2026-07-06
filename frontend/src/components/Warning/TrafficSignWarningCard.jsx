export default function TrafficSignWarningCard({ warningData }) {
  const signLabels = {
    "Speed Limit 40": "Giới hạn 40 km/h",
    "No active sign warning": "Không có cảnh báo biển báo",
    Waiting: "Đang chờ",
  };

  return (
    <section className="warning-section">
      <div className="section-title">Luật giao thông</div>
      <strong>{signLabels[warningData?.traffic_sign_status] || warningData?.traffic_sign_status || "Đang chờ"}</strong>
      <p>{warningData?.warning_type === "TRAFFIC_SIGN" ? warningData.warning_message : "Không có cảnh báo biển báo"}</p>
    </section>
  );
}
