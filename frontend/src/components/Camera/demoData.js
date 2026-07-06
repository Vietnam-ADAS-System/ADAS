// Shared state for demo mode - provides fake detections for overlay rendering
import { useEffect, useState, useRef } from "react";

let demoData = {
  vehicles: [],
  pedestrians: [],
  lastUpdate: 0,
};

let frameCallback = null;
let frameId = 0;

function generateDemoData() {
  const t = frameId / 30;
  
  // Car - moving toward camera
  const carProgress = (frameId / 120) % 1;
  const carScale = 0.3 + carProgress * 0.8;
  const carX = 480;
  const carY = 250 + (1 - carProgress) * 200;
  const carW = 960 * 0.14 * carScale;
  const carH = 540 * 0.1 * carScale;
  
  // Truck - moving sideways
  const truckProgress = (frameId / 80) % 1;
  const truckX = 200 + 560 * truckProgress;
  const truckY = 350;
  const truckW = 960 * 0.1;
  const truckH = 540 * 0.12;
  
  // Motorcycle - oscillating
  const motoProgress = (frameId / 40) % 1;
  const motoX = 850;
  const motoY = 320 + Math.sin(motoProgress * Math.PI * 2) * 40;
  const motoW = 50;
  const motoH = 35;
  
  // Person - crossing road
  const personProgress = (frameId / 100) % 1;
  const personX = 250 + 460 * personProgress;
  const personY = 420;
  const personH = 35;

  demoData = {
    vehicles: [
      {
        class_name: "car",
        bbox: [carX - carW / 2, carY, carX + carW / 2, carY + carH],
        confidence: 0.93,
        track_id: 1,
      },
      {
        class_name: "truck",
        bbox: [truckX - truckW / 2, truckY, truckX + truckW / 2, truckY + truckH],
        confidence: 0.88,
        track_id: 2,
      },
      {
        class_name: "motorcycle",
        bbox: [motoX - motoW / 2, motoY, motoX + motoW / 2, motoY + motoH],
        confidence: 0.85,
        track_id: 3,
      },
    ],
    pedestrians: [
      {
        class_name: "person",
        bbox: [personX - 12, personY - 12, personX + 12, personY + personH + 4],
        confidence: 0.91,
        track_id: 4,
      },
    ],
    lastUpdate: Date.now(),
  };

  frameCallback?.(demoData);
}

let animationId = null;
let running = false;

function startDemoLoop() {
  if (running) return;
  running = true;
  
  function tick() {
    if (!running) return;
    frameId++;
    generateDemoData();
    animationId = requestAnimationFrame(tick);
  }
  
  animationId = requestAnimationFrame(tick);
}

function stopDemoLoop() {
  running = false;
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
}

export function onDemoFrame(callback) {
  frameCallback = callback;
  startDemoLoop();
  return () => {
    frameCallback = null;
    stopDemoLoop();
  };
}

export function useDemoDetections() {
  const [detections, setDetections] = useState({ vehicles: [], pedestrians: [] });
  
  useEffect(() => {
    return onDemoFrame((data) => {
      setDetections({ vehicles: data.vehicles, pedestrians: data.pedestrians });
    });
  }, []);
  
  return detections;
}

export function getDemoData() {
  return demoData;
}
