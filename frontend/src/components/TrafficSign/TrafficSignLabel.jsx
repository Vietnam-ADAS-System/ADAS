import { getTrafficSignLabel } from "../../services/labelMapping.js";

export function drawTrafficSignLabel(ctx, rect, sign, color) {
  const confidence = Math.round((Number(sign.confidence) || 0) * 100);
  const label_vi = getTrafficSignLabel(sign.class_name);
  const label = `${label_vi} ${confidence}%`;
  const labelHeight = 24;
  const labelWidth = Math.max(96, ctx.measureText(label).width + 18);
  const x = rect.x;
  const y = Math.max(4, rect.y - labelHeight - 6);

  ctx.save();
  ctx.fillStyle = "rgba(8, 12, 18, 0.84)";
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(x, y, labelWidth, labelHeight, 6);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#f5f8fc";
  ctx.font = "600 12px system-ui, sans-serif";
  ctx.textBaseline = "middle";
  ctx.fillText(label, x + 9, y + labelHeight / 2);
  ctx.restore();
}
