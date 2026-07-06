export default function TrafficSignWarning({ sign, style }) {
  if (!sign?.warning) {
    return null;
  }

  return (
    <div className={`traffic-sign-warning traffic-sign-warning--${sign.priority}`} style={style}>
      Đang cảnh báo
    </div>
  );
}
