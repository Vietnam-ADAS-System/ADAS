export function drawLaneCenter(ctx, geometry, laneData) {
  if (!geometry || !laneData?.lane_center) {
    return;
  }

  const points = geometry.mapPoints(laneData.lane_center);

  if (points.length < 2) {
    return;
  }

  ctx.save();
  ctx.lineWidth = 2;
  ctx.setLineDash([10, 12]);
  ctx.strokeStyle = "rgba(235, 245, 255, 0.88)";
  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.stroke();
  ctx.restore();
}
