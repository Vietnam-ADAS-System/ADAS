# Tổng quan Dự án ADAS - Hệ thống Hỗ trợ Lái xe Nâng cao

**Ngày cập nhật:** 2026-07-06
**Phiên bản:** 1.0
**Tiến độ:** ~90%

---

## 1. Giới thiệu

### 1.1 Tổng quan

Hệ thống **Vietnam Advanced Driver Assistance System (ADAS)** là một dự án nghiên cứu và phát triển hệ thống hỗ trợ lái xe thông minh, được thiết kế và triển khai cho điều kiện đường phố Việt Nam.

### 1.2 Mục tiêu

- Phát hiện và cảnh báo xe lệch làn đường
- Nhận dạng và cảnh báo biển báo giao thông
- Phát hiện phương tiện và người đi bộ
- Cung cấp cảnh báo thời gian thực qua Dashboard

---

## 2. Kiến trúc hệ thống

### 2.1 Sơ đồ tổng quan

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Camera/Video  │ ──> │  Python AI      │ ──> │  Node.js        │ ──> │  React          │
│   Input         │     │  Backend        │     │  Server         │     │  Dashboard      │
│                 │     │                 │     │                 │     │                 │
│ - Webcam        │     │ - Vehicle Det.  │     │ - WebSocket     │     │ - Camera View   │
│ - Video File    │     │ - Lane Det.     │     │   Broadcast     │     │ - Lane Layer    │
│ - Image         │     │ - Traffic Sign  │     │ - HTTP API      │     │ - BBox Layer    │
└─────────────────┘     │ - Fusion       │     │ - Data Relay    │     │ - Sign Layer    │
                        │ - ADAS         │     └─────────────────┘     │ - Warning Panel │
                        └─────────────────┘                           └─────────────────┘
```

### 2.2 Luồng dữ liệu

| Bước | Thành phần | Mô tả |
|------|------------|-------|
| 1 | Camera/Video Input | Nhận dữ liệu từ webcam, file video, hoặc ảnh |
| 2 | Python AI Service | Xử lý AI: Detection, Segmentation, Tracking |
| 3 | Fusion Engine | Tổng hợp và chuẩn hóa dữ liệu từ các module AI |
| 4 | ADAS Decision Engine | Đưa ra quyết định cảnh báo |
| 5 | Node.js Server | WebSocket server truyền dữ liệu thời gian thực |
| 6 | React Dashboard | Hiển thị kết quả và cảnh báo |

---

## 3. Công nghệ sử dụng

### 3.1 Frontend

| Công nghệ | Phiên bản | Vai trò |
|-----------|-----------|---------|
| React.js | 18+ | Giao diện Dashboard |
| HTML5/CSS3 | - | Layout và styling |
| Canvas API | - | Vẽ annotation trên video |

### 3.2 Backend

| Công nghệ | Phiên bản | Vai trò |
|-----------|-----------|---------|
| Node.js | 18+ | WebSocket server, HTTP API |
| Python | 3.9+ | AI processing |
| FastAPI | 0.115+ | REST API |
| WebSocket | - | Real-time data streaming |

### 3.3 AI/ML

| Công nghệ | Vai trò |
|-----------|---------|
| YOLOv11 | Object Detection (Vehicle, Pedestrian, Traffic Sign) |
| YOLOv11-seg | Lane Segmentation |
| DeepSORT | Object Tracking |
| OpenCV | Traditional Computer Vision |
| PyTorch | Deep Learning Framework |

### 3.4 Models sử dụng

| Model | File | Mục đích |
|-------|------|----------|
| Pedestrian | `best.pt` | Phát hiện người đi bộ |
| Vehicle | `best.pt` | Phát hiện ô tô, xe máy |
| Lane Detection | `best.pt` | Phát hiện làn đường (detection) |
| Lane Segmentation | `best.pt` | Phân vùng làn đường (segmentation) |
| Traffic Sign | `best.pt` | Nhận dạng biển báo giao thông |

---

## 4. Các module chính

### 4.1 Module AI Detection

**Vị trí:** `backend/ai-service/ai_models/`

#### Vehicle Detection
- **Mục đích:** Phát hiện ô tô, xe máy
- **Model:** YOLOv11
- **Classes:** Car, Motorcycle
- **Output:** Bounding boxes, confidence scores

#### Pedestrian Detection
- **Mục đích:** Phát hiện người đi bộ
- **Model:** YOLOv11
- **Classes:** Person
- **Output:** Bounding boxes, confidence scores

#### Traffic Sign Detection
- **Mục đích:** Nhận dạng biển báo giao thông
- **Model:** YOLOv11
- **Classes:** 52 loại biển báo
- **Output:** Bounding boxes, class labels, confidence scores

### 4.2 Module Lane Detection & Segmentation

**Vị trí:** `backend/ai-service/ai_models/lane_detection/`, `lane_segmentation/`

- **Lane Detection:** Phát hiện vạch kẻ làn đường
- **Lane Segmentation:** Phân vùng pixel-level của làn đường
- **Output:** Lane masks, lane boundaries (left/right), lane center

### 4.3 Module Tracking

**Vị trí:** `backend/ai-service/tracking/`

- **Thuật toán:** DeepSORT với IoU fallback
- **Mục đích:** Theo dõi đối tượng qua các frame
- **Output:** Track IDs, trajectory

### 4.4 Module Fusion

**Vị trí:** `backend/ai-service/fusion/`

| File | Chức năng |
|------|-----------|
| `vehicle_lane_fusion.py` | Kết hợp vehicle detection với lane geometry |
| `traffic_sign_fusion.py` | Xử lý traffic sign detections |
| `tracking_fusion.py` | Tích hợp tracking data |
| `scene_understanding.py` | Hiểu ngữ cảnh cảnh |
| `decision_engine.py` | Quyết định ADAS |
| `data_models.py` | Data models chuẩn hóa |

### 4.5 Module ADAS Warning

**Vị trí:** `backend/ai-service/adas/`

#### Lane Departure Warning
- Tính offset giữa xe và làn đường
- Phân loại: SAFE, NEAR_BOUNDARY, LANE_DEPARTURE
- Cảnh báo khi xe lệch làn

#### Traffic Sign Warning
- **TV1:** Đọc kết quả detection từ YOLO
- **TV2:** Rule Engine phân tích biển báo
- **TV3:** Quản lý trạng thái Speed Limit
- **TV4:** Decision Engine đưa ra cảnh báo
- **TV5:** Warning Manager quản lý cảnh báo

---

## 5. Cấu trúc thư mục

```
ADAS/
├── frontend/                    # React Dashboard
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── Camera/          # Camera view components
│   │   │   ├── Lane/            # Lane visualization
│   │   │   ├── TrafficSign/     # Traffic sign display
│   │   │   └── Warning/        # Warning panel
│   │   └── pages/               # Page components
│   └── package.json
│
├── backend/
│   ├── ai-service/              # Python AI Service
│   │   ├── adas/                # ADAS logic
│   │   │   ├── lane_departure/  # Lane departure warning
│   │   │   └── traffic_sign/    # Traffic sign warning
│   │   ├── ai_models/           # AI models
│   │   │   ├── vehicle_detection/
│   │   │   ├── pedestrian_detection/
│   │   │   ├── lane_detection/
│   │   │   ├── lane_segmentation/
│   │   │   └── traffic_sign_detection/
│   │   ├── fusion/              # Fusion engine
│   │   ├── tracking/            # DeepSORT tracking
│   │   ├── preprocessing/       # Image preprocessing
│   │   ├── realtime_server.py   # WebSocket server
│   │   └── run_unified.py       # Unified runner
│   │
│   └── node-server/             # Node.js server
│       └── server.js            # WebSocket & HTTP API
│
├── datasets/                    # Datasets
├── outputs/                     # Output results
├── docs/                        # Documentation
│   ├── report/                  # Report documents
│   └── diagrams/                # Architecture diagrams
│
├── main.py                      # Streamlit demo
└── README.md                    # Project readme
```

---

## 6. Kích thước Input/Output

### 6.1 Image Resize Configuration

| Module | Kích thước | Ghi chú |
|--------|-------------|---------|
| Vehicle/Pedestrian | 640 x 480 | Default preprocessing |
| Lane Segmentation | 640 x 640 | YOLO inference size |
| Traffic Sign | 960 x 960 | Giữ nguyên domain train |

### 6.2 WebSocket Streams

| Stream | Dữ liệu | Tần suất |
|--------|----------|----------|
| `/ws/video` | Frame video (base64) | 30 fps |
| `/ws/lane` | Lane boundaries, center, status | Theo frame |
| `/ws/traffic-sign` | Traffic sign boxes, labels | Theo frame |
| `/ws/warning` | ADAS warnings | Theo frame |
| `/ws/vehicle` | Vehicle bounding boxes | Theo frame |
| `/ws/pedestrian` | Pedestrian bounding boxes | Theo frame |

---

## 7. Dashboard

### 7.1 Các thành phần Dashboard (TV1-TV5)

| TV | Module | Components | Chức năng |
|----|--------|------------|------------|
| TV1 | Camera | 5 files | Hiển thị video frame |
| TV2 | Vehicle/Pedestrian | 2 files | Bounding box layers |
| TV3 | Lane | 8 files | Lane visualization |
| TV4 | Traffic Sign | 7 files | Sign detection display |
| TV5 | Warning | 7 files | Warning panel |

### 7.2 Warning Priority Levels

| Mức độ | Màu | Ký hiệu | Biểu tượng |
|--------|------|---------|-------------|
| CRITICAL | Đỏ | 🔴 | Nguy hiểm cực cao |
| HIGH | Đỏ | 🔴 | Nguy hiểm cao |
| MEDIUM | Vàng | 🟡 | Cảnh báo trung bình |
| LOW | Xanh dương | 🔵 | Thông tin |

---

## 8. Tiến độ dự án

### 8.1 Timeline

```
Ngày 02/07 - Tracking (DeepSORT)     ✅ Hoàn thành
Ngày 03/07 - Fusion                  ✅ Hoàn thành
Ngày 04/07 - Lane Departure Warning   ✅ Hoàn thành
Ngày 05/07 - Traffic Sign Warning    ✅ Hoàn thành
Ngày 06/07 - Dashboard Realtime      ✅ Hoàn thành
Ngày 07/07 - Evaluation              ⚠️ Đang thực hiện
```

### 8.2 Tiến độ chi tiết theo module

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

### **OVERALL: ~90%**

---

## 9. Yêu cầu hệ thống

### 9.1 Phần cứng

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
|------------|-------------------|--------------|
| CPU | Intel Core i5 / AMD Ryzen 5 | Intel Core i7 / AMD Ryzen 7 |
| RAM | 8GB | 16GB |
| GPU | Không bắt buộc | NVIDIA GPU với CUDA |
| Storage | 10GB | 20GB |

### 9.2 Phần mềm

| Phần mềm | Phiên bản |
|----------|-----------|
| Python | 3.9+ |
| Node.js | 18+ |
| npm | 8+ |

### 9.3 Python Packages

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
python-dotenv>=1.0.1
ultralytics>=8.3.0
opencv-python>=4.10.0
numpy>=1.24.0
streamlit>=1.37.0
deep-sort-realtime>=1.3.0
```

---

## 10. Cách chạy hệ thống

### 10.1 Clone và Setup

```bash
# Clone project
git clone <repo-url>
cd ADAS

# Cài Python dependencies
cd backend/ai-service
pip install -r requirements.txt

# Cài Node.js dependencies
cd ../node-server && npm install
cd ../../frontend && npm install
```

### 10.2 Chạy đầy đủ (3 terminal)

```bash
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

### 10.3 Chạy chỉ Streamlit Demo

```bash
streamlit run main.py
```

### 10.4 Các chế độ Input

| Chế độ | Lệnh | Mô tả |
|--------|------|--------|
| Webcam | `--webcam` | Sử dụng webcam của máy |
| Video File | `--video path/to/video.mp4` | Sử dụng file video |
| Demo Mode | `--no-ai` | Dashboard với demo data |

---

## 11. Performance Metrics

| Tiêu chí | Mục tiêu | Ghi chú |
|-----------|-----------|---------|
| FPS | 24+ | Real-time processing |
| Detection mAP50 | >80% | Object detection accuracy |
| Segmentation mIoU | >75% | Lane segmentation accuracy |
| Latency | <100ms | Per frame processing |

---

## 12. Công việc cần hoàn thành

### Ngày 07/07 - Evaluation

- [ ] Viết Evaluation Report
  - [ ] Detection metrics (Precision, Recall, mAP)
  - [ ] Segmentation IoU
  - [ ] Tracking FPS
  - [ ] System latency test

- [ ] Benchmark Script
  - [ ] Tạo `evaluation/benchmark.py`
  - [ ] Chạy benchmark tự động

- [ ] Demo Video
  - [ ] Chạy demo cuối cùng
  - [ ] Record video clip

---

## 13. Ghi chú quan trọng

1. **FPS** phụ thuộc vào hardware và độ phức tạp scene
2. **WebSocket latency** cần test trên mạng thực
3. **Mock mode** cho phép demo không cần AI backend
4. **Không commit** file `.env`, model, dataset và output lên Git

---

## 14. Liên hệ

**Vietnam ADAS System Development Team**

---

## 15. Tài liệu tham khảo

- `docs/report/BAO_CAO_TONG_HOP_06-07.md` - Báo cáo chi tiết
- `docs/Phát hiện và cảnh báo xe lệch làn.md` - Tài liệu LDW
- `docs/Traffic Sign Warning.md` - Tài liệu Traffic Sign Warning
- `docs/project-state.md` - Trạng thái dự án

---

*Document created: 2026-07-06*
*Last updated: 2026-07-06*
