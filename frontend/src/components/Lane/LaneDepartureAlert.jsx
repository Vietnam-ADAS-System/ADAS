export default function LaneDepartureAlert({ laneData }) {
  if (!laneData?.warning) {
    return null;
  }

  return <div className="lane-departure-alert">Lệch làn</div>;
}
