import { getTrafficSignLabel } from "../../services/labelMapping.js";

export default function TrafficSignRule({ sign, style }) {
  if (!sign?.rule) {
    return null;
  }

  return (
    <div className="traffic-sign-rule" style={style}>
      <span>{getTrafficSignLabel(sign.class_name)}</span>
      <strong>{sign.rule}</strong>
    </div>
  );
}
