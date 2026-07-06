import { useEffect, useRef, useCallback, useState } from "react";
import { getSpriteConfig, preloadSprites } from "../../services/spriteManager.js";
import { getVehicleLabel, getTrafficSignLabel } from "../../services/labelMapping.js";

let spritesPreloading = false;
let spritesReady = false;

function startPreload() {
  if (typeof window === "undefined" || spritesPreloading) return;
  spritesPreloading = true;
  const loadNext = () => {
    if (spritesReady) return;
    preloadSprites().then(() => {
      spritesReady = true;
    });
  };
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(loadNext, { timeout: 1000 });
  } else {
    setTimeout(loadNext, 100);
  }
}
startPreload();

const DETECTION_COLORS = {
  car: { stroke: "#4fb8ff", fill: "rgba(79, 184, 255, 0.3)" },
  motorcycle: { stroke: "#ff9f43", fill: "rgba(255, 159, 67, 0.3)" },
  truck: { stroke: "#a855f7", fill: "rgba(168, 85, 247, 0.3)" },
  bus: { stroke: "#06b6d4", fill: "rgba(6, 182, 212, 0.3)" },
  vehicle: { stroke: "#4fb8ff", fill: "rgba(79, 184, 255, 0.3)" },
  person: { stroke: "#00ff88", fill: "rgba(0, 255, 136, 0.3)" },
  traffic_sign: { stroke: "#ffd700", fill: "rgba(255, 215, 0, 0.3)" },
  dangerous: { stroke: "#ff4f5f", fill: "rgba(255, 79, 95, 0.4)" },
};

const BUILDINGS = [
  { x: 0.02, w: 0.08, h: 0.18, color: "#3d5a80" },
  { x: 0.08, w: 0.12, h: 0.25, color: "#4a6fa5" },
  { x: 0.18, w: 0.10, h: 0.20, color: "#5c7a99" },
  { x: 0.26, w: 0.14, h: 0.30, color: "#2c4a6e" },
  { x: 0.38, w: 0.08, h: 0.15, color: "#4d6d8a" },
  { x: 0.44, w: 0.12, h: 0.22, color: "#3a5f7c" },
  { x: 0.62, w: 0.10, h: 0.17, color: "#4a6fa5" },
  { x: 0.70, w: 0.08, h: 0.24, color: "#3d5a80" },
  { x: 0.76, w: 0.12, h: 0.28, color: "#5c7a99" },
  { x: 0.86, w: 0.14, h: 0.20, color: "#2c4a6e" },
];

const TREES_LEFT = [
  { x: 0.05, y: 0.55, s: 0.8 },
  { x: 0.12, y: 0.58, s: 1.0 },
];
const TREES_RIGHT = [
  { x: 0.88, y: 0.56, s: 0.9 },
  { x: 0.95, y: 0.54, s: 0.8 },
];

function drawBuilding(ctx, x, y, w, h, color, horizon, height, width) {
  const bx = x * width;
  const bw = w * width;
  const by = horizon;
  const bh = h * height;

  ctx.fillStyle = color;
  ctx.fillRect(bx, by - bh, bw, bh);

  ctx.fillStyle = "rgba(255, 230, 150, 0.6)";
  const winSize = 6;
  const winGap = 12;
  for (let wy = by - bh + 15; wy < by - 10; wy += winGap) {
    for (let wx = bx + 8; wx < bx + bw - 8; wx += winGap) {
      ctx.fillRect(wx, wy, winSize, winSize);
    }
  }
}

function drawTree(ctx, x, y, size, horizon, height, width) {
  const tx = x * width;
  const ty = horizon + y * (height - horizon);

  ctx.fillStyle = "#5d4037";
  ctx.fillRect(tx - 4 * size, ty - 20 * size, 8 * size, 20 * size);

  ctx.fillStyle = "#2e7d32";
  ctx.beginPath();
  ctx.arc(tx, ty - 30 * size, 18 * size, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#388e3c";
  ctx.beginPath();
  ctx.arc(tx - 8 * size, ty - 20 * size, 14 * size, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(tx + 10 * size, ty - 22 * size, 12 * size, 0, Math.PI * 2);
  ctx.fill();
}

function renderScene(ctx, frameId, width, height, vehicleState = {}) {
  ctx.clearRect(0, 0, width, height);

  const horizon = height * 0.39;
  const roadTopWidth = width * 0.20;
  const roadBottomWidth = width * 0.95;
  const centerX = width / 2;
  const roadLeftTop = centerX - roadTopWidth / 2;
  const roadRightTop = centerX + roadTopWidth / 2;
  const roadLeftBottom = centerX - roadBottomWidth / 2;
  const roadRightBottom = centerX + roadBottomWidth / 2;

  const sky = ctx.createLinearGradient(0, 0, 0, horizon);
  sky.addColorStop(0, "#1a1a2e");
  sky.addColorStop(0.4, "#16213e");
  sky.addColorStop(1, "#0f3460");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, width, horizon);

  const cityGlow = ctx.createLinearGradient(0, horizon - 60, 0, horizon);
  cityGlow.addColorStop(0, "rgba(255, 150, 100, 0)");
  cityGlow.addColorStop(1, "rgba(255, 150, 100, 0.15)");
  ctx.fillStyle = cityGlow;
  ctx.fillRect(0, horizon - 60, width, 60);

  const t = frameId / 120;
  ctx.fillStyle = "rgba(255, 255, 200, 0.3)";
  ctx.beginPath();
  ctx.arc(width * 0.8 + Math.sin(t) * 20, horizon * 0.3, 15, 0, Math.PI * 2);
  ctx.fill();

  BUILDINGS.forEach(b => {
    drawBuilding(ctx, b.x, horizon, b.w, b.h, b.color, horizon, height, width);
  });

  const leftSidewalkTopWidth = 30;
  const leftSidewalkBottomWidth = 60;

  ctx.fillStyle = "#7d8a8a";
  ctx.beginPath();
  ctx.moveTo(roadLeftTop - leftSidewalkTopWidth, horizon);
  ctx.lineTo(roadLeftTop, horizon);
  ctx.lineTo(roadLeftBottom, height);
  ctx.lineTo(roadLeftBottom - leftSidewalkBottomWidth, height);
  ctx.closePath();
  ctx.fill();

  ctx.strokeStyle = "#9ca3af";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(roadLeftTop, horizon);
  ctx.lineTo(roadLeftBottom, height);
  ctx.stroke();

  const rightSidewalkTopWidth = 30;
  const rightSidewalkBottomWidth = 60;

  ctx.fillStyle = "#7d8a8a";
  ctx.beginPath();
  ctx.moveTo(roadRightTop, horizon);
  ctx.lineTo(roadRightTop + rightSidewalkTopWidth, horizon);
  ctx.lineTo(roadRightBottom + rightSidewalkBottomWidth, height);
  ctx.lineTo(roadRightBottom, height);
  ctx.closePath();
  ctx.fill();

  ctx.strokeStyle = "#9ca3af";
  ctx.beginPath();
  ctx.moveTo(roadRightTop, horizon);
  ctx.lineTo(roadRightBottom, height);
  ctx.stroke();

  ctx.fillStyle = "rgba(0,0,0,0.06)";
  for (let y = horizon + 20; y < height; y += 20) {
    const tParam = (y - horizon) / (height - horizon);
    const brickWidth = 15 + tParam * 10;
    const brickHeight = 6 + tParam * 4;
    const leftSX = roadLeftTop - leftSidewalkTopWidth + (roadLeftBottom - leftSidewalkBottomWidth - (roadLeftTop - leftSidewalkTopWidth)) * tParam;
    const rightSX = roadRightTop + rightSidewalkTopWidth + (roadRightBottom + rightSidewalkBottomWidth - (roadRightTop + rightSidewalkTopWidth)) * tParam;

    for (let x = leftSX + 5; x < roadLeftTop - 5; x += brickWidth + 3) {
      ctx.fillRect(x, y, brickWidth, brickHeight);
    }
    for (let x = roadRightTop + 5; x < rightSX - 5; x += brickWidth + 3) {
      ctx.fillRect(x, y, brickWidth, brickHeight);
    }
  }

  const sidewalkLeftWidth = roadLeftBottom - leftSidewalkBottomWidth;
  const sidewalkRightStart = roadRightBottom + rightSidewalkBottomWidth;
  const sidewalkRightWidth = width - sidewalkRightStart;

  ctx.beginPath();
  ctx.moveTo(roadLeftTop, horizon);
  ctx.lineTo(roadRightTop, horizon);
  ctx.lineTo(roadRightBottom, height);
  ctx.lineTo(roadLeftBottom, height);
  ctx.closePath();
  const road = ctx.createLinearGradient(0, horizon, 0, height);
  road.addColorStop(0, "#2a2a35");
  road.addColorStop(1, "#151520");
  ctx.fillStyle = road;
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.02)";
  for (let i = 0; i < 50; i++) {
    const rx = roadLeftBottom + Math.random() * (roadRightBottom - roadLeftBottom);
    const ry = horizon + Math.random() * (height - horizon);
    ctx.fillRect(rx, ry, 2, 2);
  }

  TREES_LEFT.forEach(tree => drawTree(ctx, tree.x, tree.y, tree.s, horizon, height, width));
  TREES_RIGHT.forEach(tree => drawTree(ctx, tree.x, tree.y, tree.s, horizon, height, width));

  const getLeftEdgeX = (yPos) => {
    const tVal = (yPos - horizon) / (height - horizon);
    return roadLeftTop + (roadLeftBottom - roadLeftTop) * tVal;
  };
  const getRightEdgeX = (yPos) => {
    const tVal = (yPos - horizon) / (height - horizon);
    return roadRightTop + (roadRightBottom - roadRightTop) * tVal;
  };
  const getCenterX = (yPos) => {
    const leftX = getLeftEdgeX(yPos);
    const rightX = getRightEdgeX(yPos);
    return (leftX + rightX) / 2;
  };

  const getLaneBoundaryX = (yPos, laneIndex) => {
    const leftEdge = getLeftEdgeX(yPos);
    const rightEdge = getRightEdgeX(yPos);
    const totalWidth = rightEdge - leftEdge;
    const laneWidth = totalWidth / 4;
    return leftEdge + laneWidth * laneIndex;
  };
  const getLaneCenterX = (yPos, laneIndex) => {
    return (getLaneBoundaryX(yPos, laneIndex) + getLaneBoundaryX(yPos, laneIndex + 1)) / 2;
  };

  const currentLane = Math.max(0, Math.min(3, Math.round(vehicleState?.lane || 2)));
  const isOppositeDirection = currentLane < 2;

  ctx.lineWidth = 4;
  ctx.strokeStyle = "#ffffff";
  ctx.setLineDash([]);

  ctx.beginPath();
  for (let y = horizon + 5; y < height; y += 2) {
    const x = getLeftEdgeX(y) + 8;
    if (y === horizon + 5) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.beginPath();
  for (let y = horizon + 5; y < height; y += 2) {
    const x = getRightEdgeX(y) - 8;
    if (y === horizon + 5) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  const dashOffset = -((frameId * (vehicleState?.speed || 60) / 30) % 35);

  ctx.lineWidth = 4;
  ctx.strokeStyle = "#f4d03f";
  ctx.setLineDash([20, 15]);
  ctx.lineDashOffset = dashOffset;
  ctx.beginPath();
  for (let y = horizon + 10; y < height; y += 2) {
    const x = getLaneBoundaryX(y, 2);
    if (y === horizon + 10) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.lineDashOffset = 0;

  ctx.lineWidth = 3;
  ctx.strokeStyle = "#ffffff";
  ctx.setLineDash([20, 15]);
  ctx.lineDashOffset = dashOffset;

  ctx.beginPath();
  for (let y = horizon + 10; y < height; y += 2) {
    const x = getLaneBoundaryX(y, 1);
    if (y === horizon + 10) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.beginPath();
  for (let y = horizon + 10; y < height; y += 2) {
    const x = getLaneBoundaryX(y, 3);
    if (y === horizon + 10) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.setLineDash([]);
  ctx.lineDashOffset = 0;

  const currentLaneLeftX = getLaneBoundaryX(horizon + 20, currentLane);
  const currentLaneRightX = getLaneBoundaryX(horizon + 20, currentLane + 1);
  const currentLaneLeftX2 = getLaneBoundaryX(height - 30, currentLane);
  const currentLaneRightX2 = getLaneBoundaryX(height - 30, currentLane + 1);

  const isWarning = isOppositeDirection;
  const laneFill = ctx.createLinearGradient(0, horizon, 0, height);
  if (isWarning) {
    laneFill.addColorStop(0, "rgba(231, 76, 60, 0.25)");
    laneFill.addColorStop(1, "rgba(231, 76, 60, 0.4)");
  } else {
    laneFill.addColorStop(0, "rgba(46, 204, 113, 0.15)");
    laneFill.addColorStop(1, "rgba(46, 204, 113, 0.35)");
  }
  ctx.fillStyle = laneFill;
  ctx.beginPath();
  ctx.moveTo(currentLaneLeftX, horizon + 20);
  ctx.lineTo(currentLaneRightX, horizon + 20);
  ctx.lineTo(currentLaneRightX2, height - 30);
  ctx.lineTo(currentLaneLeftX2, height - 30);
  ctx.closePath();
  ctx.fill();

  const myCarY = height - 60;
  const myCarW = width * 0.12;
  const myCarH = myCarW * 0.5;
  const lateralOffset = (vehicleState?.offsetX || 0) * (myCarW * 0.8);
  const myCarX = getLaneCenterX(myCarY, currentLane) + lateralOffset;

  ctx.fillStyle = "#2ecc71";
  ctx.beginPath();
  ctx.roundRect(myCarX - myCarW/2, myCarY - myCarH/2, myCarW, myCarH, 8);
  ctx.fill();
  ctx.fillStyle = "#27ae60";
  ctx.fillRect(myCarX - myCarW/3, myCarY - myCarH/3, myCarW*0.66, myCarH*0.25);
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(myCarX - myCarW/2 - 5, myCarY - myCarH/4, 8, myCarH/2);
  ctx.fillRect(myCarX + myCarW/2 - 3, myCarY - myCarH/4, 8, myCarH/2);
  ctx.fillStyle = "#2ecc71";
  ctx.font = "bold 11px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("XE CUA TOI", myCarX, myCarY + myCarH/2 + 15);
  ctx.textAlign = "left";

  const laneStatus = vehicleState?.laneStatus || "SAFE";
  const isLaneDeparture = laneStatus === "LANE_DEPARTURE";
  const isNearBoundary = laneStatus === "NEAR_BOUNDARY";

  if (isLaneDeparture) {
    ctx.fillStyle = isOppositeDirection ? "rgba(231, 76, 60, 0.9)" : "rgba(231, 76, 60, 0.8)";
    ctx.font = "bold 18px system-ui";
    ctx.textAlign = "center";
    const warnText = isOppositeDirection ? "NGUY HIEM! SAI LAN!" : "LECH LAN!";
    ctx.fillText(warnText, width / 2, height - 100);
    ctx.textAlign = "left";
  } else if (isNearBoundary) {
    ctx.fillStyle = "rgba(243, 156, 18, 0.7)";
    ctx.font = "bold 16px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("Gan vach lan", width / 2, height - 100);
    ctx.textAlign = "left";
  }

  const detections = [];

  const simLane = currentLane >= 2 ? 3 : 0;
  const oppSimLane = currentLane >= 2 ? 0 : 3;

  const carProgress = (frameId / 200) % 1;
  const carScale = 0.3 + carProgress * 0.7;
  const carX = getLaneCenterX(horizon + 100, simLane);
  const carY = horizon + 80 + (1 - carProgress) * 200;
  const carW = width * 0.10 * carScale;
  const carH = height * 0.07 * carScale;

  if (spritesReady) {
    const spriteConfig = getSpriteConfig("car", { x1: carX - carW/2, y1: carY, x2: carX + carW/2, y2: carY + carH });
    if (spriteConfig?.sprite?.img) {
      ctx.drawImage(spriteConfig.sprite.img, spriteConfig.drawX, spriteConfig.drawY, spriteConfig.drawWidth, spriteConfig.drawHeight);
    } else {
      drawVehicleShape(ctx, carX - carW/2, carY, carW, carH, "#3498db");
    }
  } else {
    drawVehicleShape(ctx, carX - carW/2, carY, carW, carH, "#3498db");
  }

  detections.push({
    class_name: "car",
    bbox: [carX - carW / 2 - 5, carY - 5, carX + carW / 2 + 5, carY + carH + 5],
    confidence: 0.93,
    track_id: 1,
  });

  const truckProgress = (frameId / 280) % 1;
  const truckScale = 0.35 + truckProgress * 0.65;
  const truckX = getLaneCenterX(horizon + 80, simLane);
  const truckY = horizon + 60 + (1 - truckProgress) * 240;
  const truckW = width * 0.11 * truckScale;
  const truckH = height * 0.10 * truckScale;

  drawVehicleShape(ctx, truckX - truckW/2, truckY, truckW, truckH, "#8e44ad");

  detections.push({
    class_name: "truck",
    bbox: [truckX - truckW / 2 - 5, truckY - 5, truckX + truckW / 2 + 5, truckY + truckH + 5],
    confidence: 0.88,
    track_id: 2,
  });

  const motoProgress = (frameId / 180) % 1;
  const motoScale = 0.3 + motoProgress * 0.7;
  const motoX = getLaneCenterX(horizon + 90, oppSimLane);
  const motoY = horizon + 70 + (1 - motoProgress) * 220;
  const motoW = 40 * motoScale;
  const motoH = 25 * motoScale;

  drawVehicleShape(ctx, motoX - motoW/2, motoY, motoW, motoH, "#e74c3c", true);

  detections.push({
    class_name: "motorcycle",
    bbox: [motoX - motoW / 2 - 3, motoY - 3, motoX + motoW / 2 + 3, motoY + motoH + 12],
    confidence: 0.85,
    track_id: 3,
    dangerous: true,
  });

  const personCycle = 300;
  const personProgress = (frameId % personCycle) / personCycle;
  const personOnLeftSidewalk = frameId % 2 === 0;

  const personScreenY = horizon + (1 - personProgress) * (height - horizon) * 0.8;
  const personScale = 1 - (1 - personProgress) * 0.7;

  let personX;
  if (personOnLeftSidewalk) {
    const tVal = (personScreenY - horizon) / (height - horizon);
    const leftEdgeX = roadLeftTop - leftSidewalkTopWidth + (roadLeftBottom - leftSidewalkBottomWidth - (roadLeftTop - leftSidewalkTopWidth)) * tVal;
    personX = leftEdgeX - 20 * personScale;
  } else {
    const tVal = (personScreenY - horizon) / (height - horizon);
    const rightEdgeX = roadRightTop + rightSidewalkTopWidth + (roadRightBottom + rightSidewalkBottomWidth - (roadRightTop + rightSidewalkTopWidth)) * tVal;
    personX = rightEdgeX + 20 * personScale;
  }

  const personH = 28 * personScale;

  if (personScale > 0.2) {
    ctx.fillStyle = "#e74c3c";
    ctx.fillRect(personX - 5 * personScale, personScreenY - personH * 0.3, 10 * personScale, personH * 0.6);
    ctx.fillStyle = "#fad390";
    ctx.beginPath();
    ctx.arc(personX, personScreenY - personH * 0.5, 5 * personScale, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#2d3436";
    ctx.fillRect(personX - 4 * personScale, personScreenY + personH * 0.3, 8 * personScale, personH * 0.5);
  }

  const personStepsOnRoad = Math.sin(frameId / 120) > 0.9 && personProgress > 0.7;
  if (personStepsOnRoad && personScale > 0.4) {
    const roadY = height * 0.85;
    const stepX = personOnLeftSidewalk ? roadLeftBottom + 30 : roadRightBottom - 30;

    ctx.fillStyle = "#ff4f5f";
    ctx.fillRect(stepX - 6, roadY, 12, personH);
    ctx.beginPath();
    ctx.arc(stepX, roadY - 4, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#ff4f5f";
    ctx.font = "bold 12px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("!", stepX, roadY - 20);
    ctx.textAlign = "left";

    detections.push({
      class_name: "person",
      bbox: [stepX - 10, roadY - 10, stepX + 10, roadY + personH + 4],
      confidence: 0.91,
      track_id: 4,
      dangerous: true,
    });
  } else {
    detections.push({
      class_name: "person",
      bbox: [personX - 8 * personScale, personScreenY - personH * 0.5, personX + 8 * personScale, personScreenY + personH * 0.5],
      confidence: 0.91,
      track_id: 4,
      dangerous: false,
    });
  }

  const signDetections = [];

  const getDepthScale = (y) => {
    const distFromHorizon = y - horizon;
    const totalDist = height - horizon;
    return Math.max(0.1, distFromHorizon / totalDist);
  };

  const centerVP = width / 2;
  const projectSign = (worldX, worldY, worldZ) => {
    const scaleVal = 1 - worldZ * 0.85;
    const screenYVal = horizon + (1 - worldZ) * (height - horizon) * 0.7;
    const screenXVal = worldX;
    const sizeVal = 40 * scaleVal;
    return { x: screenXVal, y: screenYVal, size: sizeVal };
  };

  const signConfigs = [
    { side: 'left', cycle: 450, offset: 0, type: 'speed', text: '60', color: '#c0392b', bg: '#f5f6fa' },
    { side: 'right', cycle: 500, offset: 100, type: 'no_entry' },
    { side: 'left', cycle: 550, offset: 200, type: 'stop' },
    { side: 'right', cycle: 480, offset: 300, type: 'speed', text: '80', color: '#c0392b', bg: '#f5f6fa' },
    { side: 'left', cycle: 600, offset: 400, type: 'yield' },
    { side: 'right', cycle: 520, offset: 500, type: 'pedestrian' },
  ];

  signConfigs.forEach((config, idx) => {
    const progress = ((frameId + config.offset) / config.cycle) % 1;
    if (progress < 0.02) return;

    const worldZ = 1 - progress;

    const screenY = horizon + (1 - worldZ) * (height - horizon) * 0.75;
    const scale = 1 - worldZ * 0.85;
    const size = 40 * scale;

    const tVal = (screenY - horizon) / (height - horizon);
    let screenX;
    if (config.side === 'left') {
      const leftEdgeX = roadLeftTop - leftSidewalkTopWidth + (roadLeftBottom - leftSidewalkBottomWidth - (roadLeftTop - leftSidewalkTopWidth)) * tVal;
      screenX = leftEdgeX - 25 * scale;
    } else {
      const rightEdgeX = roadRightTop + rightSidewalkTopWidth + (roadRightBottom + rightSidewalkBottomWidth - (roadRightTop + rightSidewalkTopWidth)) * tVal;
      screenX = rightEdgeX + 25 * scale;
    }

    const poleHeight = size * 0.8;
    ctx.fillStyle = "#c0c5ce";
    ctx.fillRect(screenX - 3, screenY + size * 0.3, 6, poleHeight);

    if (config.type === 'speed') {
      ctx.beginPath();
      ctx.arc(screenX, screenY, size / 2, 0, Math.PI * 2);
      ctx.fillStyle = config.bg;
      ctx.fill();
      ctx.lineWidth = 3 * (size / 50);
      ctx.strokeStyle = config.color;
      ctx.stroke();
      ctx.fillStyle = "#1c2833";
      ctx.font = `bold ${size * 0.35}px system-ui`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(config.text, screenX, screenY);
    } else if (config.type === 'no_entry') {
      ctx.beginPath();
      ctx.arc(screenX, screenY, size / 2, 0, Math.PI * 2);
      ctx.fillStyle = "#e74c3c";
      ctx.fill();
      ctx.lineWidth = 3 * (size / 50);
      ctx.strokeStyle = "#fff";
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(screenX - size * 0.3, screenY - size * 0.3);
      ctx.lineTo(screenX + size * 0.3, screenY + size * 0.3);
      ctx.lineWidth = 3 * (size / 50);
      ctx.strokeStyle = "#fff";
      ctx.stroke();
    } else if (config.type === 'stop') {
      ctx.beginPath();
      const r = size / 2;
      for (let i = 0; i < 8; i++) {
        const angle = (i * Math.PI / 4) - Math.PI / 8;
        const px = screenX + r * Math.cos(angle);
        const py = screenY + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fillStyle = "#c0392b";
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = `bold ${size * 0.22}px system-ui`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("STOP", screenX, screenY);
    } else if (config.type === 'yield') {
      ctx.beginPath();
      ctx.moveTo(screenX, screenY + size / 2);
      ctx.lineTo(screenX + size / 2, screenY - size / 3);
      ctx.lineTo(screenX - size / 2, screenY - size / 3);
      ctx.closePath();
      ctx.fillStyle = "#f1c40f";
      ctx.fill();
      ctx.strokeStyle = "#c0392b";
      ctx.lineWidth = 2 * (size / 50);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(screenX, screenY - size * 0.1, size * 0.08, 0, Math.PI * 2);
      ctx.fillStyle = "#c0392b";
      ctx.fill();
    } else if (config.type === 'pedestrian') {
      ctx.beginPath();
      ctx.arc(screenX, screenY, size / 2, 0, Math.PI * 2);
      ctx.fillStyle = "#3498db";
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = `bold ${size * 0.3}px Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("PED", screenX, screenY);
    }

    if (progress > 0.1) {
      signDetections.push({
        class_name: "traffic_sign",
        bbox: [screenX - size * 0.6, screenY - size * 0.6, screenX + size * 0.6, screenY + size * 1.4],
        confidence: 0.88 + Math.random() * 0.1,
        sign_type: config.type,
      });
    }
  });

  detections.push(...signDetections);

  ctx.fillStyle = "rgba(230, 50, 50, 0.9)";
  ctx.fillRect(14, 14, 140, 40);
  ctx.fillStyle = "#fff";
  ctx.font = "bold 14px system-ui";
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.fillText("MO PHONG", 24, 40);

  return detections;
}

function drawVehicleShape(ctx, x, y, w, h, color, isMotorcycle = false) {
  if (isMotorcycle) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, 4);
    ctx.fill();

    ctx.fillStyle = "#0a1015";
    ctx.beginPath();
    ctx.arc(x + w * 0.2, y + h + 2, h * 0.3, 0, Math.PI * 2);
    ctx.arc(x + w * 0.8, y + h + 2, h * 0.3, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, 6);
    ctx.fill();

    ctx.fillStyle = "rgba(50, 80, 120, 0.8)";
    ctx.fillRect(x + w * 0.2, y + 3, w * 0.5, h * 0.2);

    ctx.fillStyle = "#0a1015";
    ctx.fillRect(x - 2, y + h * 0.2, 4, h * 0.4);
    ctx.fillRect(x + w - 2, y + h * 0.2, 4, h * 0.4);
  }
}

function drawBboxes(ctx, detections, width, height) {
  for (const det of detections) {
    if (!det.bbox) continue;
    const [x1, y1, x2, y2] = det.bbox;
    const w = x2 - x1, h = y2 - y1;
    if (w <= 0 || h <= 0) continue;
    const className = det.class_name || "vehicle";

    let color;
    if (det.dangerous) {
      color = DETECTION_COLORS.dangerous;
    } else {
      color = DETECTION_COLORS[className] || DETECTION_COLORS.vehicle;
    }

    const conf = det.confidence || 0.9;

    ctx.strokeStyle = color.stroke;
    ctx.lineWidth = det.dangerous ? 3 : 2.5;
    ctx.fillStyle = color.fill;
    ctx.beginPath();
    ctx.roundRect(x1, y1, w, h, 4);
    ctx.fill();
    ctx.stroke();

    const label = det.sign_type
      ? `${getTrafficSignLabel(det.sign_type)} ${Math.round(conf * 100)}%`
      : `${getVehicleLabel(className)} ${Math.round(conf * 100)}%`;
    ctx.font = det.dangerous ? "bold 12px system-ui" : "bold 11px system-ui";
    ctx.textBaseline = "alphabetic";
    const tw = ctx.measureText(label).width;
    ctx.fillStyle = color.stroke;
    ctx.fillRect(x1, y1 - 18, tw + 10, 16);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, x1 + 5, y1 - 5);
  }
}

export default function SceneLayer({ viewport, frameId, vehicleState }) {
  const canvasRef = useRef(null);
  const lastFrameIdRef = useRef(-1);
  const resizeObserverRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const updateCanvasSize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;

      const rect = parent.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
    };

    updateCanvasSize();
    resizeObserverRef.current = new ResizeObserver(updateCanvasSize);
    resizeObserverRef.current.observe(canvas.parentElement);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || frameId === null || frameId === undefined) return;

    if (frameId === lastFrameIdRef.current) return;
    lastFrameIdRef.current = frameId;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const detections = renderScene(ctx, frameId, canvas.width, canvas.height, vehicleState);

    drawBboxes(ctx, detections, canvas.width, canvas.height);
  }, [frameId, vehicleState]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
    />
  );
}
