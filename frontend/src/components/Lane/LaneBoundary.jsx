export function drawLaneBoundary(ctx, geometry, laneData, color) {
  if (!geometry || !laneData) {
    return;
  }

  const left = geometry.mapPoints(laneData.lane_left);
  const right = geometry.mapPoints(laneData.lane_right);

  ctx.save();
  ctx.lineWidth = 6;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 15;

  [left, right].forEach((points) => {
    if (points.length < 2) {
      return;
    }

    ctx.beginPath();
    points.forEach((point, index) => {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });
    ctx.stroke();
  });

  ctx.restore();
}
