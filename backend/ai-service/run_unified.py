#!/usr/bin/env python3
"""
ADAS Unified Backend - Chạy tất cả trong một process
Python AI Service + Node WebSocket Server

Cách dùng:
    python run_unified.py                      # Chạy tất cả
    python run_unified.py --no-ai              # Chỉ chạy Node server (demo mode)
    python run_unified.py --video path/to/video # Xử lý video với AI
    python run_unified.py --webcam             # Xử lý webcam với AI
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_ROOT = REPO_ROOT / "backend" / "ai-service"
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

AI_ENABLED = True
cap = None
frame_id = 0
models = {}
tracker = None
fusion_engine = None
adas_engine = None
frame_interval = 1.0 / 30  # 30 FPS for smoother display


def load_ai_models():
    """Load all AI models"""
    global models, tracker, fusion_engine, adas_engine
    
    logger.info("Loading AI models...")
    
    try:
        from fusion import FusionEngine
        from adas.decision_engine import ADASDecisionEngine
        fusion_engine = FusionEngine()
        adas_engine = ADASDecisionEngine()
        logger.info("✓ Fusion and ADAS engines loaded")
    except Exception as e:
        logger.warning(f"Fusion/ADAS load failed: {e}")
    
    try:
        from tracking.deepsort_tracker import ObjectTracker, TrackerConfig
        tracker = ObjectTracker(TrackerConfig(max_age=30, n_init=3))
        logger.info("✓ DeepSORT Tracker loaded")
    except Exception as e:
        logger.warning(f"Tracker load failed: {e}")
        try:
            from tracking.deepsort_tracker import ObjectTracker, TrackerConfig
            tracker = ObjectTracker(TrackerConfig(max_age=15, n_init=2))
        except:
            tracker = None
    
    model_paths = {
        "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "weights" / "best.pt",
        "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "weights" / "best.pt",
        "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "weights" / "best.pt",
        "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "weights" / "best.pt",
        "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes" / "weights" / "best.pt",
    }
    
    try:
        from ai_models.pedestrian_detection.detector import PedestrianDetector
        if model_paths["pedestrian"].exists():
            models["pedestrian"] = PedestrianDetector(
                model_name=str(model_paths["pedestrian"]),
                conf_threshold=0.5,
                enable_preprocessing=True,
            )
            logger.info("✓ Pedestrian Detector loaded")
    except Exception as e:
        logger.warning(f"Pedestrian detector failed: {e}")
    
    try:
        from ai_models.vehicle_detection.vehicle_detector import VehicleObjectDetector, VehicleDetectorConfig
        if model_paths["vehicle"].exists():
            models["vehicle"] = VehicleObjectDetector(
                VehicleDetectorConfig(
                    model_path=str(model_paths["vehicle"]),
                    use_preprocessing=True,
                )
            )
            logger.info("✓ Vehicle Detector loaded")
    except Exception as e:
        logger.warning(f"Vehicle detector failed: {e}")
    
    try:
        from ai_models.lane_detection.detector import LaneDetector
        if model_paths["lane_detection"].exists():
            models["lane"] = LaneDetector(
                str(model_paths["lane_detection"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Lane Detector loaded")
    except Exception as e:
        logger.warning(f"Lane detector failed: {e}")
    
    try:
        from ai_models.lane_segmentation.predict import LaneSegmenter
        if model_paths["lane_segmentation"].exists():
            models["lane_seg"] = LaneSegmenter(
                str(model_paths["lane_segmentation"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Lane Segmenter loaded")
    except Exception as e:
        logger.warning(f"Lane segmentation failed: {e}")
    
    try:
        from ai_models.traffic_sign_detection.predict import TrafficSignDetector
        if model_paths["traffic_sign"].exists():
            models["traffic_sign"] = TrafficSignDetector(
                str(model_paths["traffic_sign"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Traffic Sign Detector loaded")
    except Exception as e:
        logger.warning(f"Traffic sign detector failed: {e}")
    
    logger.info(f"Models loaded: {list(models.keys())}")


def process_frame_ai(frame):
    """Process frame with AI models"""
    global frame_id, models, tracker, fusion_engine, adas_engine
    
    h, w = frame.shape[:2]
    frame_size = (w, h)
    frame_id += 1
    
    result = {
        "frame_id": frame_id,
        "timestamp": time.time(),
        "width": w,
        "height": h,
    }
    
    pedestrian_dets = []
    if "pedestrian" in models:
        try:
            pedestrian_dets = models["pedestrian"].detect(frame)
        except Exception as e:
            logger.debug(f"Pedestrian error: {e}")
    
    vehicle_result = {}
    if "vehicle" in models:
        try:
            vehicle_result = models["vehicle"].detect_frame(frame)
        except Exception as e:
            logger.debug(f"Vehicle error: {e}")
    
    lane_detections = []
    if "lane" in models:
        try:
            lane_detections = models["lane"].get_detections(frame)
        except Exception as e:
            logger.debug(f"Lane error: {e}")
    
    lane_mask = None
    if "lane_seg" in models:
        try:
            lane_mask = models["lane_seg"].get_lane_mask(frame)
        except Exception as e:
            logger.debug(f"Segmentation error: {e}")
    
    traffic_sign_dets = []
    if "traffic_sign" in models:
        try:
            _, traffic_sign_dets = models["traffic_sign"].detect_with_detections(frame)
        except Exception as e:
            logger.debug(f"Traffic sign error: {e}")
    
    tracks = []
    if tracker:
        try:
            tracks = tracker.update(
                vehicle_detections=vehicle_result,
                pedestrian_detections=pedestrian_dets,
                frame=frame,
            )
            result["tracking"] = [t.to_dict() for t in tracks]
        except Exception as e:
            logger.debug(f"Tracking error: {e}")
    
    scene_context = {}
    if fusion_engine:
        try:
            scene_context = fusion_engine.build_scene_context(
                frame_index=frame_id,
                vehicle_detections=vehicle_result,
                lane_detection={"detections": lane_detections, "mask": lane_mask},
                traffic_sign_detections=traffic_sign_dets,
                tracking=result.get("tracking", []),
                pedestrian_detections=pedestrian_dets,
                fps=15,
            )
            scene_context = scene_context.to_dict() if hasattr(scene_context, "to_dict") else {}
        except Exception as e:
            logger.debug(f"Fusion error: {e}")
    
    adas_output = {}
    if adas_engine:
        try:
            adas_output = adas_engine.evaluate(scene_context, frame_size=frame_size)
            adas_output = adas_output.to_dict() if hasattr(adas_output, "to_dict") else {}
        except Exception as e:
            logger.debug(f"ADAS error: {e}")
    
    vehicles = vehicle_result.get("detections", []) if isinstance(vehicle_result, dict) else []
    
    result["pedestrians"] = pedestrian_dets
    result["vehicles"] = vehicles
    result["traffic_signs"] = traffic_sign_dets
    result["scene_context"] = scene_context
    result["adas_output"] = adas_output
    
    return result


def frame_to_base64(frame):
    """Convert frame to base64 JPEG"""
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])  # Lower quality = faster transmission
    return base64.b64encode(buffer).decode("utf-8")


def send_ai_data_to_node(result, annotated_frame_b64=None, node_url="http://127.0.0.1:3000"):
    """Gửi AI data đến Node.js server để hiển thị trên Dashboard"""
    try:
        payload = {
            "frame_id": result["frame_id"],
            "width": result["width"],
            "height": result["height"],
            "timestamp": result["timestamp"],
            "lane": extract_lane_data(result),
            "traffic_signs": result.get("traffic_signs", []),
            "pedestrians": result.get("pedestrians", []),
            "vehicles": result.get("vehicles", []),
        }

        if annotated_frame_b64:
            payload["annotated_frame"] = f"data:image/jpeg;base64,{annotated_frame_b64}"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{node_url}/api/ai/frame",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=0.5):
            pass

    except urllib.error.URLError:
        pass  # Node server chưa chạy, bỏ qua
    except Exception:
        pass


def extract_lane_data(result):
    """Extract lane data từ result"""
    lane = result.get("scene_context", {}).get("lane", {})
    lane_left = lane.get("lane_left", [])
    lane_right = lane.get("lane_right", [])

    lane_width = 0
    if len(lane_left) >= 2 and len(lane_right) >= 2:
        lane_width = abs(lane_right[-1][0] - lane_left[-1][0])

    vehicle_center = lane.get("vehicle_center", [result["width"] / 2, result["height"] * 0.88])
    lane_center_x = (lane_left[0][0] + lane_right[0][0]) / 2 if len(lane_left) > 0 and len(lane_right) > 0 else result["width"] / 2
    offset = vehicle_center[0] - lane_center_x
    normalized_offset = offset / (lane_width / 2) if lane_width > 0 else 0
    direction = "LEFT" if offset < -10 else "RIGHT" if offset > 10 else "CENTER"
    adas_output = result.get("adas_output", {})
    lane_departure = adas_output.get("lane_departure", False)
    lane_status = "LANE_DEPARTURE" if lane_departure or abs(normalized_offset) > 0.72 else "NEAR_BOUNDARY" if abs(normalized_offset) > 0.48 else "SAFE"

    return {
        "lane_left": lane_left,
        "lane_right": lane_right,
        "lane_center": lane.get("lane_center", []),
        "lane_width": int(lane_width),
        "vehicle_center": [int(c) for c in vehicle_center],
        "offset": int(offset),
        "normalized_offset": round(normalized_offset, 3),
        "direction": direction,
        "lane_status": lane_status,
        "warning": lane_status == "LANE_DEPARTURE",
    }


def run_node_server():
    """Run Node.js WebSocket server"""
    import subprocess
    import signal
    
    node_script = REPO_ROOT / "backend" / "node-server" / "server.js"
    
    if not node_script.exists():
        logger.error(f"Node server not found: {node_script}")
        return
    
    logger.info("Starting Node.js WebSocket server...")
    proc = subprocess.Popen(
        ["node", str(node_script)],
        cwd=str(node_script.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    # Don't register signal handlers in daemon thread - let main thread handle them
    # Just stream output from subprocess
    for line in proc.stdout:
        try:
            print(line.decode().rstrip())
        except:
            pass


def run_demo_loop():
    """Run demo loop without AI"""
    global frame_id, cap
    
    logger.info("Running demo mode (no AI)...")
    
    width = 960
    height = 540
    
    while True:
        frame_id += 1
        time.sleep(1.0 / 15)


def main():
    global AI_ENABLED, cap, frame_interval
    
    parser = argparse.ArgumentParser(description="ADAS Unified Backend")
    parser.add_argument("--video", "-v", type=str, help="Path to video file")
    parser.add_argument("--webcam", "-w", action="store_true", help="Use webcam")
    parser.add_argument("--no-ai", action="store_true", help="Run without AI (demo mode)")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    args = parser.parse_args()
    
    AI_ENABLED = not args.no_ai
    frame_interval = 1.0 / args.fps
    
    if not AI_ENABLED:
        logger.info("Running in DEMO mode (no AI processing)")
        run_demo_loop()
        return
    
    logger.info("Loading AI models...")
    load_ai_models()
    
    if args.webcam:
        cap = cv2.VideoCapture(0)
    elif args.video:
        cap = cv2.VideoCapture(args.video)
    else:
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Cannot open video source")
        return
    
    logger.info("Starting Node.js WebSocket server...")
    node_thread = threading.Thread(target=run_node_server, daemon=True)
    node_thread.start()
    
    time.sleep(2)
    
    logger.info("Starting AI processing loop...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if args.video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            
            process_start = time.time()
            result = process_frame_ai(frame)
            process_time = time.time() - process_start
            
            if frame_id % 30 == 0:
                logger.info(f"Frame {frame_id} | AI: {process_time*1000:.1f}ms | Det: P={len(result['pedestrians'])} V={len(result['vehicles'])} T={len(result['traffic_signs'])}")

            # Gửi AI data đến Dashboard qua Node server
            annotated_b64 = frame_to_base64(frame)
            send_ai_data_to_node(result, annotated_b64)

            elapsed = time.time() - process_start
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if cap:
            cap.release()


if __name__ == "__main__":
    main()
