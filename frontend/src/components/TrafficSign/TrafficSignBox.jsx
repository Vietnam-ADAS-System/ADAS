export function drawTrafficSignBox(ctx, rect, color, warning) {
  ctx.save();
  ctx.lineWidth = warning ? 4 : 3;
  ctx.strokeStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = warning ? 12 : 6;
  ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
  ctx.restore();
}
