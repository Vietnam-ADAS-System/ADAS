# Báo cáo tổng hợp - Hệ thống ADAS

**Ngày cập nhật:** 2026-07-06
**Phạm vi:** Toàn bộ hệ thống ADAS - Từ AI Models đến Dashboard
**Tiến độ:** ~85-90%

---

## 1. Tổng quan hệ thống

### 1.1 Kiến trúc

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Camera/Video  │ -> │  Python AI      │ -> │  Node.js        │ -> │  React          │
│   Input         │    │  Backend        │    │  Server         │    │  Dashboard      │
│                 │    │                 │    │                 │    │                 │
│ - Webcam        │    │ - Vehicle Det.  │    │ - WebSocket     │    │ - Camera View   │
│ - Video File    │    │ - Lane Det.     │    │   Broadcast     │    │ - Lane Layer    │
│ - Image         │    │ - Traffic Sign  │    │ - HTTP API      │    │ - BBox Layer    │
└─────────────────┘    │ - Fusion        │    │ - Data Relay    │    │ - Sign Layer    │
                       │ - ADAS          │    └─────────────────┘    │ - Warning Panel │
                       └─────────────────┘                         └─────────────────┘
```

### 1.2 WebSocket Streams

| Stream | Dữ liệu | Tần suất |
|--------|---------|----------|
| `/ws/video` | Frame video (base64) | 30 fps |
| `/ws/lane` | Lane boundaries, center, status | Theo frame |
| `/ws/traffic-sign` | Traffic sign boxes, labels | Theo frame |
| `/ws/warning` | ADAS warnings | Theo frame |
| `/ws/vehicle` | Vehicle bounding boxes | Theo frame |
| `/ws/pedestrian` | Pedestrian bounding boxes | Theo frame |

---

## 2. Yêu cầu hệ thống

### 2.1 Phần cứng
- CPU: Intel Core i5 / AMD Ryzen 5 trở lên
- RAM: 8GB trở lên (16GB khuyến nghị)
- GPU: NVIDIA GPU với CUDA (tùy chọn)
- **Webcam hoặc video input** (không bắt buộc - xem 2.4)

### 2.2 Phần mềm
- Python 3.9+
- Node.js 18+
- npm 8+

### 2.3 Cách clone và chạy (Người mới)

```bash
# 1. Clone project
git clone <repo-url>
cd ADAS

# 2. Cài Python dependencies
cd backend/ai-service
pip install -r requirements.txt

# 3. Cài Node.js dependencies
cd ../node-server && npm install
cd ../../frontend && npm install

# 4. Chạy hệ thống (3 terminal)

# Terminal 1: Node.js Server
cd backend/node-server
node server.js

# Terminal 2: AI Backend (với webcam)
cd backend/ai-service
python run_unified.py --webcam --fps 15

# Terminal 3: Frontend
cd frontend
npm run dev
```

**Mở trình duyệt:** http://localhost:5173

### 2.4 Chạy không cần webcam?

**CÓ.** Hệ thống hỗ trợ 3 chế độ:

| Chế độ | Lệnh | Mô tả |
|---------|------|--------|
| Webcam | `--webcam` | Sử dụng webcam của máy |
| Video File | `--video path/to/video.mp4` | Sử dụng file video |
| Mock Mode | (không chạy AI backend) | Dashboard hiển thị demo data |

**Nếu máy không có webcam hoặc muốn demo nhanh:**
- Chỉ cần chạy Node.js server và Frontend
- Dashboard sẽ tự động chuyển sang **Mock Mode** với demo data
- Hoặc dùng video file: `python run_unified.py --video ./test_video.mp4`

---

## 3. Tiến độ theo ngày

### Ngày 02/07 - Tracking (DeepSORT)
| Module | File | Status |
|--------|------|--------|
| DeepSORT Tracker | `tracking/deepsort_tracker.py` | ✅ Hoàn thành |

### Ngày 03/07 - Fusion
| Module | File | Status |
|--------|------|--------|
| Vehicle-Lane Fusion | `fusion/vehicle_lane_fusion.py` | ✅ Hoàn thành |
| Traffic Sign Fusion | `fusion/traffic_sign_fusion.py` | ✅ Hoàn thành |
| Scene Understanding | `fusion/scene_understanding.py` | ✅ Hoàn thành |
| Decision Engine | `fusion/decision_engine.py` | ✅ Hoàn thành |

### Ngày 04/07 - Lane Departure Warning
| Module | File | Status |
|--------|------|--------|
| Lane Center | `adas/lane_departure/lane_center.py` | ✅ Hoàn thành |
| Offset Service | `adas/lane_departure/offset_service.py` | ✅ Hoàn thành |
| Warning Engine | `adas/lane_departure/warning_engine.py` | ✅ Hoàn thành |
| Dashboard Sender | `adas/lane_departure/dashboard_sender.py` | ✅ Hoàn thành |

### Ngày 05/07 - Traffic Sign Warning
| Module | File | Status |
|--------|------|--------|
| Sign Reader | `adas/traffic_sign/sign_reader.py` | ✅ Hoàn thành |
| Speed Limit Service | `adas/traffic_sign/speed_limit_service.py` | ✅ Hoàn thành |
| Warning Manager | `adas/traffic_sign/warning_manager.py` | ✅ Hoàn thành |
| Priority Manager | `adas/traffic_sign/priority_manager.py` | ✅ Hoàn thành |
| Stop/No Entry | `adas/stop_warning.py`, `adas/no_entry_warning.py` | ✅ Hoàn thành |

### Ngày 06/07 - Dashboard Realtime
| Module | Components | Status |
|--------|------------|--------|
| TV1 - Camera | 5 files | ✅ Hoàn thành |
| TV2 - Vehicle/Pedestrian BBox | 2 files | ✅ Hoàn thành |
| TV3 - Lane | 8 files | ✅ Hoàn thành |
| TV4 - Traffic Sign | 7 files | ✅ Hoàn thành |
| TV5 - Warning Panel | 7 files | ✅ Hoàn thành |
| Node.js Server | `server.js` | ✅ Hoàn thành |
| Realtime Server | `realtime_server.py` | ✅ Hoàn thành |
| Startup Scripts | `start-all.sh/bat` | ✅ Hoàn thành |

### Ngày 07/07 - Evaluation (CẦN HOÀN THÀNH)
| Module | Status |
|--------|--------|
| Detection Metrics | ⚠️ Có kết quả, cần viết report |
| Segmentation Metrics | ⚠️ Có confusion matrix, cần viết report |
| Tracking FPS | ⚠️ Chưa đo |
| System Test | ⚠️ Chưa test |
| Benchmark Report | ❌ Chưa có |

---

## 4. Cấu trúc Dashboard

### 4.1 Entry Point
- `frontend/src/pages/Dashboard.jsx` - Component chính của Dashboard
- `frontend/src/App.jsx` - React app entry
- `frontend/src/main.jsx` - React main entry

### 4.2 Module Camera (5 components)

| File | Chức năng |
|------|-----------|
| `CameraView.jsx` | Component hiển thị camera/video chính |
| `CameraCanvas.jsx` | Canvas vẽ annotation (bbox, lane, signs) |
| `CameraLoading.jsx` | Trạng thái loading khi kết nối |
| `CameraStatus.jsx` | Thông tin trạng thái kết nối |
| `CameraHeader.jsx` | Header cho camera view |

### 4.3 Module Lane (8 components)

| File | Chức năng |
|------|-----------|
| `LaneLayer.jsx` | Layer vẽ làn đường tổng hợp |
| `LaneStatus.jsx` | Hiển thị trạng thái làn |
| `LaneCenter.jsx` | Đường center làn đường |
| `LaneBoundary.jsx` | Đường boundary trái/phải |
| `LaneDepartureAlert.jsx` | Alert khi xe lệch làn |
| `OffsetIndicator.jsx` | Chỉ offset xe so với center |
| `SafeZone.jsx` | Vùng an toàn trong làn |
| `VehiclePosition.jsx` | Vị trí xe trong làn đường |

### 4.4 Module Traffic Sign (7 components)

| File | Chức năng |
|------|-----------|
| `TrafficSignLayer.jsx` | Layer tổng hợp biển báo |
| `TrafficSignBox.jsx` | Bounding box biển báo |
| `TrafficSignIcon.jsx` | Icon biển báo (STOP, SPEED, etc.) |
| `TrafficSignLabel.jsx` | Nhãn tên biển báo |
| `TrafficSignConfidence.jsx` | Hiển thị confidence score |
| `TrafficSignWarning.jsx` | Warning khi phát hiện biển báo |
| `TrafficSignRule.jsx` | Luật từ biển báo |

### 4.5 Module Warning (7 components)

| File | Chức năng |
|------|-----------|
| `WarningPanel.jsx` | Panel chính hiển thị warnings |
| `WarningBanner.jsx` | Banner cảnh báo nổi bật |
| `WarningPriority.jsx` | Mức ưu tiên (CRITICAL/HIGH/MEDIUM/LOW) |
| `WarningHistory.jsx` | Lịch sử cảnh báo |
| `LaneWarningCard.jsx` | Card cảnh báo lệch làn |
| `SystemStatusCard.jsx` | Card trạng thái hệ thống |
| `TrafficSignWarningCard.jsx` | Card cảnh báo biển báo |

### 4.6 Module Vehicle & Pedestrian

| File | Chức năng |
|------|-----------|
| `VehicleLayer.jsx` | Layer vẽ bounding box xe |
| `PedestrianLayer.jsx` | Layer vẽ bounding box người đi bộ |

---

## 5. Backend Services

### 5.1 Node.js Server
**File:** `backend/node-server/server.js`

Chức năng:
- WebSocket server trên port 3000
- HTTP API endpoint `/api/ai/frame` nhận AI data từ Python
- Broadcast data qua WebSocket streams
- Tự động chuyển mode mock → ai khi nhận data

### 5.2 Python Realtime Server
**File:** `backend/ai-service/realtime_server.py`

Chức năng:
- Xử lý video frame (webcam/video file)
- Chạy inference: vehicle, lane, traffic sign
- Gửi kết quả đến Node.js server qua HTTP POST
- FPS tracking và logging

### 5.3 Unified Runner
**File:** `backend/ai-service/run_unified.py`

Chức năng:
- Khởi động Node.js server trong thread riêng
- Chạy AI pipeline (detection → fusion → ADAS)
- Gửi kết quả đến Dashboard
- Hỗ trợ webcam, video file, image

---

## 6. Tính năng Dashboard

### 6.1 Camera View
- Hiển thị video frame theo thời gian thực
- Connection status indicator
- FPS counter
- Resolution display

### 6.2 Lane Visualization
- Vẽ lane boundaries (đường trái/phải)
- Vẽ đường center
- Hiển thị Safe Zone
- Offset indicator (khoảng cách xe đến center)

### 6.3 Vehicle/Pedestrian Detection
- Bounding box cho xe (màu xanh dương)
- Bounding box cho người đi bộ (màu xanh lá)
- Confidence score
- Class label

### 6.4 Traffic Sign Detection
- Bounding box biển báo
- Icon biển báo (STOP, SPEED LIMIT, NO ENTRY, etc.)
- Label tên biển báo
- Confidence score

### 6.5 Warning System
- Warning Banner nổi bật
- Warning Panel với lịch sử
- Priority levels:
  - 🔴 CRITICAL - Dừng ngay lập tức
  - 🟠 HIGH - Cảnh báo cao
  - 🟡 MEDIUM - Cảnh báo trung bình
  - ⚪ LOW - Thông tin
- System Status Card

---

## 7. Tổng kết tiến độ

| Module | Hoàn thành |
|--------|------------|
| AI Models (Vehicle, Lane, Traffic Sign, Pedestrian) | 95% |
| Tracking (DeepSORT) | 90% |
| Fusion | 90% |
| Lane Departure Warning | 95% |
| Traffic Sign Warning | 95% |
| Dashboard Frontend (TV1-TV5) | 95% |
| Backend Server (Node.js + Python) | 95% |
| **Evaluation** | **30%** |

### **OVERALL: ~85-90%**

---

## 8. Cần hoàn thành ngày 07/07

1. **Viết Evaluation Report**
   - Detection metrics (Precision, Recall, mAP)
   - Segmentation IoU
   - Tracking FPS
   - System latency test

2. **Benchmark Script**
   - Tạo `evaluation/benchmark.py`
   - Chạy benchmark tự động

3. **Demo Video**
   - Chạy demo cuối cùng
   - Record video clip

---

## 9. Vấn đề cần lưu ý

- FPS phụ thuộc vào hardware và độ phức tạp scene
- WebSocket latency cần test trên mạng thực
- Cần có video/ảnh test chất lượng tốt để demo
- **Mock mode cho phép demo không cần AI backend** - không bắt buộc phải có webcam
