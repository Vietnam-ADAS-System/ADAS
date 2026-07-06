export default function OffsetIndicator({ laneData }) {
  if (!laneData) {
    return null;
  }

  const offset = Number(laneData.offset) || 0;

  return (
    <div className="lane-offset-indicator">
      <span>Độ lệch</span>
      <strong>{offset > 0 ? `+${offset}` : offset} px</strong>
    </div>
  );
}
