import WarningPriority from "./WarningPriority.jsx";

export default function WarningBanner({ warningData }) {
  if (!warningData) {
    return null;
  }

  const warningTypeLabels = {
    SYSTEM: "Giám sát hành trình",
    LANE_DEPARTURE: "Cảnh báo lệch làn",
    TRAFFIC_SIGN: "Cảnh báo biển báo",
  };

  const isCritical = warningData.warning_level === "CRITICAL" || warningData.warning_level === "HIGH";
  const bannerClass = `warning-banner ${warningData.active ? "warning-banner--active" : ""} ${isCritical ? "warning-banner--critical" : ""}`;

  return (
    <section className={bannerClass}>
      <div>
        <span className="panel-label">Cảnh báo người lái</span>
        <strong>{warningData.active ? warningTypeLabels[warningData.warning_type] || warningData.warning_type.replaceAll("_", " ") : "Không có cảnh báo"}</strong>
        <p>{warningData.warning_message}</p>
      </div>
      <WarningPriority level={warningData.warning_level} />
    </section>
  );
}
