export default function TrafficSignIcon({ sign, style }) {
  if (!sign?.icon) {
    return null;
  }

  return (
    <div className={`traffic-sign-icon traffic-sign-icon--${sign.priority}`} style={style}>
      {sign.icon}
    </div>
  );
}
