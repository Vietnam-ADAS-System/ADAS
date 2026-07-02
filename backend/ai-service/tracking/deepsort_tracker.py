"""
DeepSORT-based Object Tracker for ADAS
Theo dõi xe, người đi bộ qua nhiều frame, gán ID ổn định
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """
    Đại diện cho một track (dối tượng đã xác nhận theo dõi)
    
    Attributes:
        track_id: ID duy nhất của track (ổn định qua các frame)
        class_name: Loại đối tượng ("vehicle", "pedestrian")
        bbox: Bounding box hiện tại [x1, y1, x2, y2]
        confidence: Độ tin cậy của detection hiện tại
        frame_count: Số frame track này đã xuất hiện
        time_since_update: Số frame kể từ lần cuối update bbox
    """
    track_id: int
    class_name: str
    bbox: List[float]
    confidence: float
    frame_count: int = 1
    time_since_update: int = 0
    
    def to_dict(self) -> Dict:
        """Chuyển track thành dict format (for JSON/API)"""
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "bbox": {
                "x1": round(self.bbox[0], 2),
                "y1": round(self.bbox[1], 2),
                "x2": round(self.bbox[2], 2),
                "y2": round(self.bbox[3], 2),
                "width": round(self.bbox[2] - self.bbox[0], 2),
                "height": round(self.bbox[3] - self.bbox[1], 2),
            },
            "confidence": round(self.confidence, 4),
            "frame_count": self.frame_count,
            "time_since_update": self.time_since_update,
        }


@dataclass
class TrackerConfig:
    """Cấu hình cho ObjectTracker"""
    # DeepSORT parameters
    max_age: int = 30  # Số frame giữ track khi mất detection
    n_init: int = 3    # Số frame liên tiếp cần detect để confirm track mới
    max_cosine_distance: float = 0.5  # Ngưỡng matching appearance
    
    # Tracker behavior
    use_separate_trackers: bool = True  # Dùng tracker riêng cho vehicle và pedestrian
    min_confidence: float = 0.3  # Ngưỡng confidence tối thiểu để track
    embedder_gpu: bool = False  # Sử dụng GPU cho embedder (False = CPU)


class ObjectTracker:
    """
    DeepSORT-based tracker cho đối tượng phát hiện (xe, người)
    
    Cách dùng:
        config = TrackerConfig(max_age=30, n_init=3)
        tracker = ObjectTracker(config=config)
        
        # Trong vòng lặp xử lý video:
        for frame in video_frames:
            vehicle_dets = vehicle_detector.detect_frame(frame)
            pedestrian_dets = pedestrian_detector.detect(frame)
            
            # Gọi tracker
            tracks = tracker.update(
                vehicle_detections=vehicle_dets,
                pedestrian_detections=pedestrian_dets,
                frame=frame
            )
            
            # Sử dụng tracks để vẽ hoặc xử lý tiếp
            for track in tracks:
                print(f"ID {track.track_id}: {track.class_name} @ {track.bbox}")
    """
    
    def __init__(self, config: Optional[TrackerConfig] = None):
        """
        Khởi tạo tracker
        
        Args:
            config: Cấu hình cho tracker (TrackerConfig instance)
        """
        self.config = config or TrackerConfig()
        self._next_id = 1
        self._active_tracks: Dict[int, Track] = {}  # track_id -> Track
        self._frame_count = 0
        self._use_deepsort = True
        self.DeepSort = None
        self.vehicle_tracker = None
        self.pedestrian_tracker = None
        self.tracker = None
        
        # Defer DeepSORT import until first update() call (lazy loading)
        # This avoids hanging on embedder download during initialization
        logger.info("✓ ObjectTracker initialized (DeepSORT will load on first update)")
    
    def _init_deepsort_if_needed(self):
        """Lazy-init DeepSORT on first use"""
        if self.DeepSort is not None or not self._use_deepsort:
            return  # Already initialized or disabled
        
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            self.DeepSort = DeepSort
            logger.info("DeepSORT available - will use appearance-based matching")
            
            # Initialize trackers
            if self.config.use_separate_trackers:
                self.vehicle_tracker = DeepSort(
                    max_age=self.config.max_age,
                    n_init=self.config.n_init,
                    max_cosine_distance=self.config.max_cosine_distance,
                    embedder='mobilenet',
                    half=True,
                    bgr=True,
                    embedder_gpu=self.config.embedder_gpu,
                )
                self.pedestrian_tracker = DeepSort(
                    max_age=self.config.max_age,
                    n_init=self.config.n_init,
                    max_cosine_distance=self.config.max_cosine_distance,
                    embedder='mobilenet',
                    half=True,
                    bgr=True,
                    embedder_gpu=self.config.embedder_gpu,
                )
                logger.info("✓ Separate vehicle & pedestrian trackers initialized")
            else:
                self.tracker = DeepSort(
                    max_age=self.config.max_age,
                    n_init=self.config.n_init,
                    max_cosine_distance=self.config.max_cosine_distance,
                    embedder='mobilenet',
                    half=True,
                    bgr=True,
                    embedder_gpu=self.config.embedder_gpu,
                )
                logger.info("✓ Combined tracker (vehicle + pedestrian) initialized")
        
        except Exception as e:
            logger.warning(f"DeepSORT init failed: {e}")
            logger.warning("Falling back to IoU-based matching (no appearance features)")
            self._use_deepsort = False
    
    def update(
        self,
        vehicle_detections: Optional[Dict] = None,
        pedestrian_detections: Optional[List[Dict]] = None,
        frame: Optional[np.ndarray] = None,
    ) -> List[Track]:
        """
        Cập nhật tracker với detections từ frame hiện tại
        
        Args:
            vehicle_detections: Output từ VehicleObjectDetector.detect_frame()
                Format: {"detections": [...], ...}
            pedestrian_detections: Output từ PedestrianDetector.detect()
                Format: [...]
            frame: Frame ảnh gốc (BGR, numpy array) - dùng để extract feature (optional)
        
        Returns:
            List[Track]: Danh sách các track đã được xác nhận (có ID ổn định)
        
        Note:
            - Hàm này có thể được gọi với chỉ vehicle hoặc chỉ pedestrian detections
            - Nếu frame là None, tracker sẽ dùng IoU matching thay vì appearance matching
            - Output là List[Track] - mỗi track có track_id, class_name, bbox, confidence
        """
        # Lazy-init DeepSORT on first call
        if self._frame_count == 0 and self._use_deepsort:
            self._init_deepsort_if_needed()
        
        self._frame_count += 1
        all_tracks = []
        
        # Xử lý vehicle detections
        if vehicle_detections is not None:
            vehicle_tracks = self._process_detections(
                detections=vehicle_detections.get("detections", []),
                class_name="vehicle",
                frame=frame,
                is_vehicle=True,
            )
            all_tracks.extend(vehicle_tracks)
        
        # Xử lý pedestrian detections
        if pedestrian_detections is not None:
            pedestrian_tracks = self._process_detections(
                detections=pedestrian_detections,
                class_name="pedestrian",
                frame=frame,
                is_vehicle=False,
            )
            all_tracks.extend(pedestrian_tracks)
        
        # Cập nhật time_since_update cho các track không được update
        for track_id, track in list(self._active_tracks.items()):
            if track_id not in [t.track_id for t in all_tracks]:
                track.time_since_update += 1
                # Xoá track nếu quá lâu không update (đã rời khỏi frame)
                if track.time_since_update > self.config.max_age:
                    del self._active_tracks[track_id]
        
        # Cập nhật active tracks dict
        for track in all_tracks:
            self._active_tracks[track.track_id] = track
        
        return all_tracks
    
    def _process_detections(
        self,
        detections: List[Dict],
        class_name: str,
        frame: Optional[np.ndarray] = None,
        is_vehicle: bool = True,
    ) -> List[Track]:
        """
        Xử lý detections (vehicle hoặc pedestrian) thông qua DeepSORT hoặc IoU matching
        
        Args:
            detections: Danh sách detections từ detector
            class_name: "vehicle" hoặc "pedestrian"
            frame: Frame ảnh (dùng cho feature extraction)
            is_vehicle: True nếu là vehicle detection, False nếu pedestrian
        
        Returns:
            List[Track] của frame hiện tại
        """
        if not detections:
            return []
        
        # Normalize detections thành format [x1, y1, x2, y2, confidence]
        detections_list = self._normalize_detections(detections, is_vehicle)
        
        # Lọc theo min_confidence
        detections_list = [
            d for d in detections_list
            if d[4] >= self.config.min_confidence
        ]
        
        if not detections_list:
            return []
        
        result_tracks = []
        
        if self._use_deepsort:
            # Sử dụng DeepSORT
            # Chọn tracker (vehicle hoặc pedestrian)
            if self.config.use_separate_trackers:
                tracker = self.vehicle_tracker if is_vehicle else self.pedestrian_tracker
            else:
                tracker = self.tracker
            
            # Chuyển thành numpy array (format DeepSORT: [x1, y1, x2, y2, conf])
            detections_array = np.array(detections_list)
            
            # Update DeepSORT tracker
            try:
                tracks = tracker.update_tracks(
                    detections_array,
                    frame=frame,
                )
                
                # Convert DeepSORT tracks to our Track format
                for deep_sort_track in tracks:
                    # deep_sort_track có thuộc tính: track_id, to_xyxy() -> bbox
                    if not deep_sort_track.is_confirmed():
                        continue  # Chỉ lấy confirmed tracks
                    
                    bbox = deep_sort_track.to_xyxy()
                    # Tìm detection gốc để lấy confidence
                    conf = self._find_detection_confidence(bbox, detections_list)
                    
                    track = Track(
                        track_id=deep_sort_track.track_id,
                        class_name=class_name,
                        bbox=bbox,
                        confidence=conf,
                        frame_count=deep_sort_track.hits,
                        time_since_update=deep_sort_track.time_since_update,
                    )
                    result_tracks.append(track)
            
            except Exception as e:
                logger.debug(f"DeepSORT update failed, falling back to IoU matching: {e}")
                # Fallback: IoU matching
                result_tracks = self._iou_matching(detections_list, class_name)
        
        else:
            # Fallback: IoU-based matching (không có DeepSORT)
            result_tracks = self._iou_matching(detections_list, class_name)
        
        return result_tracks
    
    def _normalize_detections(
        self, detections: List[Dict], is_vehicle: bool
    ) -> List[List[float]]:
        """
        Normalize detections từ vehicle/pedestrian detector thành format DeepSORT
        Format output: [[x1, y1, x2, y2, confidence], ...]
        
        Args:
            detections: Detections từ detector
            is_vehicle: True nếu từ vehicle detector, False nếu pedestrian
        
        Returns:
            List của [x1, y1, x2, y2, confidence]
        """
        normalized = []
        
        for det in detections:
            try:
                if is_vehicle:
                    # Vehicle detector format: {"bbox": {"x1", "y1", "x2", "y2", ...}, "confidence": ...}
                    bbox = det.get("bbox", {})
                    x1 = float(bbox.get("x1", 0))
                    y1 = float(bbox.get("y1", 0))
                    x2 = float(bbox.get("x2", 0))
                    y2 = float(bbox.get("y2", 0))
                    conf = float(det.get("confidence", 0.0))
                else:
                    # Pedestrian detector format: {"x1", "y1", "x2", "y2", "confidence", ...}
                    x1 = float(det.get("x1", 0))
                    y1 = float(det.get("y1", 0))
                    x2 = float(det.get("x2", 0))
                    y2 = float(det.get("y2", 0))
                    conf = float(det.get("confidence", 0.0))
                
                # Validate bbox
                if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                    logger.debug(f"Skipping invalid bbox: {[x1, y1, x2, y2]}")
                    continue
                
                normalized.append([x1, y1, x2, y2, conf])
            
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Error normalizing detection {det}: {e}")
                continue
        
        return normalized
    
    def _find_detection_confidence(
        self, bbox: List[float], detections_list: List[List[float]]
    ) -> float:
        """
        Tìm confidence của detection gốc dựa vào bbox
        
        Args:
            bbox: [x1, y1, x2, y2] từ DeepSORT track
            detections_list: [[x1, y1, x2, y2, conf], ...] từ detector
        
        Returns:
            Confidence score, default 0.0 nếu không tìm thấy
        """
        threshold = 50  # IoU threshold để match
        for det in detections_list:
            if self._bbox_iou(bbox, det[:4]) > 0.5:
                return det[4]
        return 0.0
    
    @staticmethod
    def _bbox_iou(box1: List[float], box2: List[float]) -> float:
        """Tính IoU (Intersection over Union) giữa 2 bbox"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Intersection
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Union
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        if union_area <= 0:
            return 0.0
        
        return inter_area / union_area
    
    def _iou_matching(
        self, detections_list: List[List[float]], class_name: str
    ) -> List[Track]:
        """
        IoU-based matching fallback khi DeepSORT không available
        Đơn giản: match detection với existing track dựa vào IoU
        
        Args:
            detections_list: [[x1, y1, x2, y2, conf], ...]
            class_name: "vehicle" hoặc "pedestrian"
        
        Returns:
            List[Track]
        """
        iou_threshold = 0.3  # Ngưỡng IoU để match
        matched_tracks = set()
        result_tracks = []
        
        # Cập nhật existing tracks
        for detection in detections_list:
            det_box = detection[:4]
            det_conf = detection[4]
            
            # Tìm best match trong active tracks
            best_track_id = None
            best_iou = 0
            
            for track_id, track in self._active_tracks.items():
                if track.class_name != class_name:
                    continue  # Chỉ match cùng class
                
                iou = self._bbox_iou(det_box, track.bbox)
                if iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Update existing track
                track = self._active_tracks[best_track_id]
                track.bbox = det_box
                track.confidence = det_conf
                track.frame_count += 1
                track.time_since_update = 0
                result_tracks.append(track)
                matched_tracks.add(best_track_id)
            else:
                # Create new track
                new_track_id = self._next_id
                self._next_id += 1
                
                new_track = Track(
                    track_id=new_track_id,
                    class_name=class_name,
                    bbox=det_box,
                    confidence=det_conf,
                    frame_count=1,
                    time_since_update=0,
                )
                result_tracks.append(new_track)
                self._active_tracks[new_track_id] = new_track
                matched_tracks.add(new_track_id)
        
        return result_tracks
    
    def get_active_tracks(self) -> List[Track]:
        """Trả về danh sách toàn bộ active tracks hiện tại"""
        return list(self._active_tracks.values())
    
    def reset(self):
        """Reset tracker - xoá toàn bộ active tracks"""
        self._active_tracks.clear()
        self._next_id = 1
        self._frame_count = 0
    
    def get_stats(self) -> Dict:
        """Lấy thống kê tracker"""
        return {
            "frame_count": self._frame_count,
            "active_track_count": len(self._active_tracks),
            "total_track_count": self._next_id - 1,
        }
