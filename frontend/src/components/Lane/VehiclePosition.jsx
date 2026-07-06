export function drawVehiclePosition(ctx, geometry, laneData) {
  if (!geometry || !laneData?.vehicle_center) {
    return;
  }

  const point = geometry.mapPoint(laneData.vehicle_center);

  ctx.save();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.92)";
  ctx.fillStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(point.x, point.y, 7, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(point.x, point.y - 34);
  ctx.lineTo(point.x, point.y + 34);
  ctx.stroke();
  ctx.font = "600 12px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Tâm xe", point.x, point.y - 42);
  ctx.restore();
}
