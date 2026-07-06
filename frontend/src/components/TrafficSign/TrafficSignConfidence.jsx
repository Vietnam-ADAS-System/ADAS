export default function TrafficSignConfidence({ confidence }) {
  const value = Math.round((Number(confidence) || 0) * 100);
  return <span className="traffic-sign-confidence">{value}%</span>;
}
