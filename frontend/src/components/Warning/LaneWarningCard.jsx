import { getLaneStatusLabel } from "../../services/labelMapping.js";

export default function LaneWarningCard({ warningData }) {
  const laneStatus = warningData?.lane_status || "Waiting";
  const label = getLaneStatusLabel(laneStatus);

  return (
    <section className="warning-section">
      <div className="section-title">Giữ làn (Làn phải)</div>
      <div className={`status-line status-line--${laneStatus}`}>
        <span className="status-line__dot" aria-hidden="true" />
        <strong>{label}</strong>
      </div>
    </section>
  );
}
