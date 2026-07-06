import { useState, useEffect, useCallback } from "react";

const INITIAL_STATE = {
  offsetX: 0,      // Offset ngang từ vị trí giữa làn (-1 đến 1)
  speed: 0,        // Tốc độ hiện tại
  lane: 2,         // Làn hiện tại (0-3): 0,1 = ngược chiều, 2,3 = đúng chiều
  accelerating: false,
  braking: false,
};

const KEYS = {
  ArrowUp: "accelerate",
  ArrowDown: "brake",
  ArrowLeft: "left",
  ArrowRight: "right",
  w: "accelerate",
  s: "brake",
  a: "left",
  d: "right",
  q: "laneLeft",
  e: "laneRight",
};

const CONFIG = {
  maxOffset: 0.4,       // Tối đa lệch 40% làn
  offsetSpeed: 0.015,   // Tốc độ di chuyển ngang
  maxSpeed: 120,
  acceleration: 0.8,
  deceleration: 0.3,
  brakeForce: 1.5,
};

export function useVehicleControl() {
  const [vehicleState, setVehicleState] = useState(INITIAL_STATE);
  const [keysPressed, setKeysPressed] = useState(new Set());

  const handleKeyDown = useCallback((e) => {
    const action = KEYS[e.key];
    if (action) {
      e.preventDefault();
      setKeysPressed(prev => new Set([...prev, action]));
    }
  }, []);

  const handleKeyUp = useCallback((e) => {
    const action = KEYS[e.key];
    if (action) {
      e.preventDefault();
      setKeysPressed(prev => {
        const next = new Set(prev);
        next.delete(action);
        return next;
      });
    }
  }, []);

  // Reset keys when window loses focus
  const handleBlur = useCallback(() => {
    setKeysPressed(new Set());
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    window.addEventListener("blur", handleBlur);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      window.removeEventListener("blur", handleBlur);
    };
  }, [handleKeyDown, handleKeyUp, handleBlur]);

  // Update vehicle state based on keys
  useEffect(() => {
    const interval = setInterval(() => {
      setVehicleState(prev => {
        let { offsetX, speed, lane } = prev;
        const { accelerating, braking, left, right, laneLeft, laneRight } = {
          accelerating: keysPressed.has("accelerate"),
          braking: keysPressed.has("brake"),
          left: keysPressed.has("left"),
          right: keysPressed.has("right"),
          laneLeft: keysPressed.has("laneLeft"),
          laneRight: keysPressed.has("laneRight"),
        };

        // Speed control
        if (accelerating) {
          speed = Math.min(CONFIG.maxSpeed, speed + CONFIG.acceleration);
        } else if (braking) {
          speed = Math.max(0, speed - CONFIG.brakeForce);
        } else {
          speed = Math.max(0, speed - CONFIG.deceleration);
        }

        // Lateral movement within lane
        if (left) {
          offsetX = Math.max(-CONFIG.maxOffset, offsetX - CONFIG.offsetSpeed);
        }
        if (right) {
          offsetX = Math.min(CONFIG.maxOffset, offsetX + CONFIG.offsetSpeed);
        }

        // Lane switching (Q/E keys)
        if (laneLeft) {
          lane = Math.max(0, lane - 1);
          offsetX = 0; // Reset offset when changing lanes
        }
        if (laneRight) {
          lane = Math.min(3, lane + 1);
          offsetX = 0;
        }

        // Calculate lane status based on offset and direction
        const isOppositeDirection = lane < 2;
        const isLeavingLane = Math.abs(offsetX) > 0.45;
        const isNearBoundary = Math.abs(offsetX) > 0.35;

        // Only warn about lane departure when:
        // 1. In opposite direction lane (lane 0-1), OR
        // 2. Actually leaving current lane (>45% offset)
        const isLaneDeparture = isOppositeDirection || isLeavingLane;
        const laneStatus = isLaneDeparture ? "LANE_DEPARTURE" : isNearBoundary ? "NEAR_BOUNDARY" : "SAFE";

        return { offsetX, speed, lane, laneStatus, accelerating, braking };
      });
    }, 16); // ~60fps

    return () => clearInterval(interval);
  }, [keysPressed]);

  return vehicleState;
}
