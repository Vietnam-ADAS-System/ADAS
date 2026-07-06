export function drawSafeZone(ctx, geometry, laneData, color) {
  if (!geometry || !laneData) {
    return;
  }

  const left = geometry.mapPoints(laneData.lane_left);
  const right = geometry.mapPoints(laneData.lane_right);

  if (left.length < 2 || right.length < 2) {
    return;
  }

  const safeZone = [...left, ...right.slice().reverse()];
  ctx.save();
  ctx.beginPath();
  safeZone.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();
}
