const STATUS_LABEL = {
  SAFE: "AN TOÀN",
  NEAR_BOUNDARY: "GẦN VẠCH LÀN",
  LANE_DEPARTURE: "LỆCH LÀN",
};

export default function LaneStatus({ laneData }) {
  if (!laneData) {
    return null;
  }

  const status = laneData.lane_status || "SAFE";

  return (
    <div className={`lane-status lane-status--${status}`}>
      <span className="lane-status__dot" aria-hidden="true" />
      {STATUS_LABEL[status] || status}
    </div>
  );
}
