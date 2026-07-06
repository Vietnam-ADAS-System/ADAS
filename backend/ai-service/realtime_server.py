#!/usr/bin/env python3
"""
ADAS Realtime Processing Server
Xử lý video/camera theo thời gian thực với AI models
Output qua WebSocket cho Dashboard
"""

import argparse
import asyncio
import base64
import json
import logging
import sys
import time
import urllib.request
import urllib.error
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import websockets
from websockets.asyncio.server import serve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_ROOT = REPO_ROOT / "backend" / "ai-service"
if str(AI_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_ROOT))

import importlib.util


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WEIGHTS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "weights" / "best.pt",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "weights" / "best.pt",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "weights" / "best.pt",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "weights" / "best.pt",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes" / "weights" / "best.pt",
}

FRONTEND_DIR = REPO_ROOT / "frontend" / "dist"


class ADASRealtimeServer:
    def __init__(self, video_path=None, use_webcam=False, port=8765, fps=15, node_server_url="http://127.0.0.1:3000"):
        self.video_path = video_path
        self.use_webcam = use_webcam
        self.port = port
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.node_server_url = node_server_url
        self.send_to_node = True  # Gửi AI data đến Node server

        self.cap = None
        self.frame_id = 0
        self.running = False

        self.models = {}
        self.tracker = None
        self.fusion_engine = None
        self.adas_engine = None

        self.clients = set()

    def load_models(self):
        """Load all AI models"""
        logger.info("Loading AI models...")
        
        from fusion import FusionEngine
        from adas.decision_engine import ADASDecisionEngine
        
        self.fusion_engine = FusionEngine()
        self.adas_engine = ADASDecisionEngine()
        
        try:
            from tracking.deepsort_tracker import ObjectTracker, TrackerConfig
            self.tracker = ObjectTracker(TrackerConfig(max_age=30, n_init=3))
            logger.info("✓ DeepSORT Tracker loaded")
        except Exception as e:
            logger.warning(f"DeepSORT not available: {e}")
            from tracking.deepsort_tracker import ObjectTracker, TrackerConfig
            self.tracker = ObjectTracker(TrackerConfig(max_age=15, n_init=2))
        
        try:
            from ai_models.pedestrian_detection.detector import PedestrianDetector
            self.models["pedestrian"] = PedestrianDetector(
                model_name=str(WEIGHTS["pedestrian"]),
                conf_threshold=0.5,
                enable_preprocessing=True,
            )
            logger.info("✓ Pedestrian Detector loaded")
        except Exception as e:
            logger.warning(f"Pedestrian detector failed: {e}")
        
        try:
            from ai_models.vehicle_detection.vehicle_detector import VehicleObjectDetector, VehicleDetectorConfig
            self.models["vehicle"] = VehicleObjectDetector(
                VehicleDetectorConfig(
                    model_path=str(WEIGHTS["vehicle"]),
                    use_preprocessing=True,
                )
            )
            logger.info("✓ Vehicle Detector loaded")
        except Exception as e:
            logger.warning(f"Vehicle detector failed: {e}")
        
        try:
            from ai_models.lane_detection.detector import LaneDetector
            self.models["lane"] = LaneDetector(
                str(WEIGHTS["lane_detection"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Lane Detector loaded")
        except Exception as e:
            logger.warning(f"Lane detector failed: {e}")
        
        try:
            from ai_models.lane_segmentation.predict import LaneSegmenter
            self.models["lane_seg"] = LaneSegmenter(
                str(WEIGHTS["lane_segmentation"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Lane Segmenter loaded")
        except Exception as e:
            logger.warning(f"Lane segmentation failed: {e}")
        
        try:
            from ai_models.traffic_sign_detection.predict import TrafficSignDetector
            self.models["traffic_sign"] = TrafficSignDetector(
                str(WEIGHTS["traffic_sign"]),
                enable_preprocessing=True,
            )
            logger.info("✓ Traffic Sign Detector loaded")
        except Exception as e:
            logger.warning(f"Traffic sign detector failed: {e}")
        
        logger.info(f"Models loaded: {list(self.models.keys())}")

    def init_capture(self):
        """Initialize video capture"""
        if self.use_webcam:
            self.cap = cv2.VideoCapture(0)
            logger.info("Using webcam (0)")
        elif self.video_path:
            self.cap = cv2.VideoCapture(str(self.video_path))
            logger.info(f"Using video: {self.video_path}")
        else:
            self.cap = cv2.VideoCapture(0)
            logger.info("No input specified, using webcam")
        
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open video source")

    def process_frame(self, frame):
        """Process single frame with all AI models"""
        h, w = frame.shape[:2]
        frame_size = (w, h)
        
        result = {
            "frame_id": self.frame_id,
            "timestamp": time.time(),
            "width": w,
            "height": h,
        }
        
        pedestrian_dets = []
        if "pedestrian" in self.models:
            try:
                pedestrian_dets = self.models["pedestrian"].detect(frame)
            except Exception as e:
                logger.debug(f"Pedestrian detection error: {e}")
        
        vehicle_result = {}
        if "vehicle" in self.models:
            try:
                vehicle_result = self.models["vehicle"].detect_frame(frame)
            except Exception as e:
                logger.debug(f"Vehicle detection error: {e}")
        
        lane_detections = []
        if "lane" in self.models:
            try:
                lane_detections = self.models["lane"].get_detections(frame)
            except Exception as e:
                logger.debug(f"Lane detection error: {e}")
        
        lane_mask = None
        if "lane_seg" in self.models:
            try:
                lane_mask = self.models["lane_seg"].get_lane_mask(frame)
            except Exception as e:
                logger.debug(f"Lane segmentation error: {e}")
        
        traffic_sign_dets = []
        if "traffic_sign" in self.models:
            try:
                _, traffic_sign_dets = self.models["traffic_sign"].detect_with_detections(frame)
            except Exception as e:
                logger.debug(f"Traffic sign detection error: {e}")
        
        if self.tracker:
            try:
                tracks = self.tracker.update(
                    vehicle_detections=vehicle_result,
                    pedestrian_detections=pedestrian_dets,
                    frame=frame,
                )
                result["tracking"] = [t.to_dict() for t in tracks]
            except Exception as e:
                logger.debug(f"Tracking error: {e}")
        
        scene_context = self.fusion_engine.build_scene_context(
            frame_index=self.frame_id,
            vehicle_detections=vehicle_result,
            lane_detection={"detections": lane_detections, "mask": lane_mask},
            traffic_sign_detections=traffic_sign_dets,
            tracking=result.get("tracking", []),
            pedestrian_detections=pedestrian_dets,
            fps=self.fps,
        )
        
        adas_output = self.adas_engine.evaluate(scene_context, frame_size=frame_size)
        
        result["pedestrians"] = pedestrian_dets
        result["vehicles"] = vehicle_result.get("detections", []) if isinstance(vehicle_result, dict) else []
        result["lane"] = {
            "detections": lane_detections,
            "mask": lane_mask.tolist() if lane_mask is not None and hasattr(lane_mask, "tolist") else None,
        }
        result["traffic_signs"] = traffic_sign_dets
        result["scene_context"] = scene_context.to_dict() if hasattr(scene_context, "to_dict") else {}
        result["adas_output"] = adas_output.to_dict() if hasattr(adas_output, "to_dict") else {}
        
        return result

    def frame_to_base64(self, frame):
        """Convert frame to base64 JPEG"""
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buffer).decode("utf-8")

    def build_ws_payload(self, frame, process_result):
        """Build WebSocket payload with annotated frame"""
        frame_b64 = self.frame_to_base64(frame)
        
        return {
            "frame_id": process_result["frame_id"],
            "frame": f"data:image/jpeg;base64,{frame_b64}",
            "fps": self.fps,
            "width": process_result["width"],
            "height": process_result["height"],
            "timestamp": process_result["timestamp"],
            "source": "ai_realtime",
        }

    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}, total: {len(self.clients)}")
        try:
            async for message in websocket:
                if message == "ping":
                    await websocket.send("pong")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected, remaining: {len(self.clients)}")

    def send_ai_data_to_node(self, result, annotated_frame_b64=None):
        """Gửi AI data đến Node.js server"""
        if not self.send_to_node:
            return

        try:
            payload = {
                "frame_id": result["frame_id"],
                "width": result["width"],
                "height": result["height"],
                "timestamp": result["timestamp"],
                "lane": self._extract_lane_data(result),
                "traffic_signs": result["traffic_signs"],
                "pedestrians": result["pedestrians"],
                "vehicles": result["vehicles"],
            }

            if annotated_frame_b64:
                payload["annotated_frame"] = f"data:image/jpeg;base64,{annotated_frame_b64}"

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.node_server_url}/api/ai/frame",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=1) as response:
                pass  # Chỉ cần gửi, không cần đọc response

        except urllib.error.URLError as e:
            logger.debug(f"Node server not available: {e}")
        except Exception as e:
            logger.debug(f"Error sending to Node: {e}")

    def _extract_lane_data(self, result):
        """Extract lane data for broadcast"""
        lane = result.get("lane", {})
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
        lane_status = "LANE_DEPARTURE" if abs(normalized_offset) > 0.72 else "NEAR_BOUNDARY" if abs(normalized_offset) > 0.48 else "SAFE"

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

    async def broadcast(self, payload):
        """Broadcast to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(payload)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        
        for client in disconnected:
            self.clients.discard(client)

    async def run(self):
        """Main processing loop"""
        self.load_models()
        self.init_capture()
        self.running = True
        
        logger.info(f"Starting ADAS Realtime Server on port {self.port}")
        
        async with serve(self.handle_client, "0.0.0.0", self.port):
            logger.info(f"WebSocket server running on ws://0.0.0.0:{self.port}")
            
            last_frame_time = time.time()
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    if self.use_webcam or not self.video_path:
                        logger.error("Failed to read frame")
                        break
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                process_start = time.time()
                result = self.process_frame(frame)
                process_time = time.time() - process_start
                
                frame_payload = self.build_ws_payload(frame, result)
                await self.broadcast(frame_payload)
                
                lane_payload = {
                    "frame_id": result["frame_id"],
                    **self._extract_lane_data(result),
                }
                await self.broadcast({"type": "lane", **lane_payload})
                
                pedestrian_payload = {
                    "frame_id": result["frame_id"],
                    "detections": result["pedestrians"],
                    "count": len(result["pedestrians"]),
                }
                await self.broadcast({"type": "pedestrian", **pedestrian_payload})
                
                vehicle_payload = {
                    "frame_id": result["frame_id"],
                    "detections": result["vehicles"],
                    "count": len(result["vehicles"]),
                }
                await self.broadcast({"type": "vehicle", **vehicle_payload})
                
                traffic_payload = {
                    "frame_id": result["frame_id"],
                    "signs": result["traffic_signs"],
                    "count": len(result["traffic_signs"]),
                }
                await self.broadcast({"type": "traffic_sign", **traffic_payload})
                
                warning_payload = {
                    "frame_id": result["frame_id"],
                    **result["adas_output"],
                }
                await self.broadcast({"type": "warning", **warning_payload})

                # Gửi AI data đến Node server cho Dashboard
                annotated_frame_b64 = self.frame_to_base64(frame) if self.send_to_node else None
                self.send_ai_data_to_node(result, annotated_frame_b64)

                self.frame_id += 1
                
                elapsed = time.time() - last_frame_time
                if elapsed < self.frame_interval:
                    await asyncio.sleep(self.frame_interval - elapsed)
                last_frame_time = time.time()
                
                if self.frame_id % 30 == 0:
                    logger.info(f"Frame {self.frame_id} | Process: {process_time*1000:.1f}ms | Clients: {len(self.clients)}")

    def _extract_lane_data(self, result):
        """Extract lane data from processing result"""
        lane_info = result.get("lane", {})
        scene = result.get("scene_context", {})
        
        lane_left = []
        lane_right = []
        lane_center = []
        lane_status = "SAFE"
        
        if "lane_center" in scene:
            lc = scene["lane_center"]
            if isinstance(lc, dict):
                lane_left = lc.get("left", [])
                lane_right = lc.get("right", [])
                lane_center = lc.get("center", [])
        
        if "lane_status" in scene:
            lane_status = scene["lane_status"]
        elif "lane_departure" in result.get("adas_output", {}):
            if result["adas_output"]["lane_departure"]:
                lane_status = "LANE_DEPARTURE"
        
        return {
            "lane_left": lane_left,
            "lane_right": lane_right,
            "lane_center": lane_center,
            "lane_status": lane_status,
            "vehicle_center": scene.get("vehicle_center", []),
        }

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        logger.info("Server stopped")


def main():
    parser = argparse.ArgumentParser(description="ADAS Realtime Processing Server")
    parser.add_argument("--video", "-v", type=str, help="Path to video file")
    parser.add_argument("--webcam", "-w", action="store_true", help="Use webcam")
    parser.add_argument("--port", "-p", type=int, default=8765, help="WebSocket port")
    parser.add_argument("--fps", "-f", type=int, default=15, help="Target FPS")
    parser.add_argument("--node-url", type=str, default="http://127.0.0.1:3000", help="Node.js server URL")
    parser.add_argument("--no-node", action="store_true", help="Disable sending to Node server")
    args = parser.parse_args()

    server = ADASRealtimeServer(
        video_path=args.video,
        use_webcam=args.webcam,
        port=args.port,
        fps=args.fps,
        node_server_url=args.node_url,
    )
    server.send_to_node = not args.no_node

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop()


if __name__ == "__main__":
    main()
