# Vietnam Advanced Driver Assistance System (ADAS)

A comprehensive Advanced Driver Assistance System designed and implemented for Vietnamese roads.

## Project Overview

This project implements an intelligent system that combines:
- **Computer Vision** for real-time object and lane detection
- **Deep Learning** for robust vehicle, traffic sign, and lane segmentation
- **Real-time Processing** with object tracking
- **ADAS Logic** for intelligent warnings and alerts

## System Architecture

```
Frontend (React)
     ↓
Node.js Backend Server
     ↓
Python AI Service (FastAPI)
     ├── Preprocessing (CVIP)
     ├── Traditional CV (Edge & Lane Detection)
     ├── AI Models (YOLO, DeepLab)
     ├── Tracking (DeepSORT)
     ├── Fusion Module
     └── ADAS Decision Logic
```

## Key Features

### 1. Vehicle Object Detection
- Detects only the assigned classes: Cars, Motorcycles, Persons/Pedestrians
- Uses Ultralytics YOLO detection models, configurable by `YOLO_VEHICLE_MODEL_PATH`
- Dedicated code: `backend/ai-service/ai_models/detection/`

### 2. Lane Detection & Segmentation
- DeepLabV3+ for semantic lane segmentation
- Traditional CV methods (Hough Transform, Edge Detection)
- Lane departure warnings

### 3. Traffic Sign Recognition
- YOLOv11-based traffic sign detection
- Recognizes: Stop signs, No Entry, Speed limits, Turn arrows

### 4. Object Tracking
- Unique ID assignment using DeepSORT
- Vehicle trajectory tracking

### 5. ADAS Warnings
- Lane departure alerts
- Traffic sign warnings
- Speed limit notifications

## Directory Structure

See [docs/cây thư mục.md](docs/cây%20thư%20mục.md) for detailed structure.

### Quick Overview
- `frontend/` - React.js UI application
- `backend/node-server/` - Express.js API server
- `backend/ai-service/` - Python FastAPI AI service
- `datasets/` - Training datasets
- `outputs/` - System outputs and results
- `docs/` - Documentation and reports
- `notebooks/` - Research and experiment notebooks

## Getting Started

### Prerequisites
- Node.js 14+ (for frontend and backend)
- Python 3.8+ (for AI service)
- CUDA 11.0+ (recommended for GPU acceleration)

### Team Setup Notes

Không commit file `.env`, model, dataset và output chạy thử lên Git.

Tạo file cấu hình local:
```bash
cp .env.example .env
```

Nếu team dùng chung cấu hình mặc định thì không cần sửa thêm. Nếu chạy khác port hoặc khác đường dẫn model/dataset thì sửa trong `.env`.

Các file lớn cần tải riêng:
- Model YOLO: đặt `yolo11n.pt` và `yolo11n-seg.pt` ở thư mục gốc project.
- Dataset: tải và giải nén vào `datasets/`.
- Video/ảnh test: đặt vào `datasets/vietnam_test_videos/` hoặc thư mục dataset tương ứng.

Link dữ liệu/model của team:
- Model: `<dán link ở đây>`
- Dataset: `<dán link ở đây>`

### Installation

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### Backend - Node Server
```bash
cd backend/node-server
npm install
npm start
```

#### Backend - AI Service
```bash
cd backend/ai-service
pip install -r requirements.txt
python main.py
```

#### Object Detection - xe hoi, xe may, nguoi di bo
```bash
cd backend/ai-service
python main.py
```

Detect image:
```bash
curl -X POST "http://127.0.0.1:8000/detect/vehicles" -F "file=@path/to/test.jpg"
```

Annotated image:
```bash
curl -X POST "http://127.0.0.1:8000/detect/vehicles/annotated" -F "file=@path/to/test.jpg" --output annotated.jpg
```

For highest accuracy, fine-tune with BDD100K or your team's Vietnamese road dataset, then set:
```env
YOLO_VEHICLE_MODEL_PATH=backend/ai-service/ai_models/detection/weights/best.pt
```

## Project Workflow

1. **Frontend** captures or uploads video
2. **Node.js Server** handles API requests
3. **Python AI Service** processes video frames with:
   - Object detection
   - Lane segmentation
   - Traffic sign recognition
4. **System** fuses results and generates warnings
5. **Frontend** displays results and alerts to driver

## Performance Metrics

- **FPS**: Target 24+ FPS for real-time processing
- **Detection mAP50**: Target >80%
- **Segmentation mIoU**: Target >75%
- **Latency**: <100ms per frame

## Technologies Used

### Frontend
- React.js
- HTML5/CSS3
- Canvas for video rendering

### Backend
- Node.js + Express.js
- Python 3.8+
- FastAPI

### AI/ML
- YOLOv11 (Object Detection)
- DeepLabV3+ (Semantic Segmentation)
- OpenCV (Traditional Computer Vision)
- PyTorch (Deep Learning Framework)
- DeepSORT (Object Tracking)

## Evaluation

Model evaluation metrics are computed in:
- `backend/ai-service/evaluation/`

Results include:
- Detection: Precision, Recall, mAP50, mAP50-95
- Segmentation: IoU, mIoU, Pixel Accuracy
- System: FPS, Latency

## Team

Vietnam ADAS System Development Team

## License

[License Information]

## References

See [docs/references/](docs/references/) for research papers and technical references.

## Contact

For questions or contributions, please reach out to the development team.

---

## Quy tắc làm việc

### Phạm vi được phép

- Được phép đọc và phân tích code hiện có
- Được phép tạo file mới trong thư mục được chỉ định
- Được phép viết code theo template đã có trong project
- Được phép cập nhật tài liệu (docs/) khi được yêu cầu

### Ràng buộc AI

- **Không được tự suy đoán** khi thiếu dữ liệu hoặc thông tin
- **Không được sửa file** ngoài phạm vi yêu cầu
- **Không được thay đổi** cấu trúc database/project nếu chưa được chỉ định
- **Không được tạo code mẫu giả lập** khi dự án đã có code thực tế
- **Luôn ưu tiên code hiện có** trước khi đề xuất viết lại
- **Phải hỏi lại** nếu yêu cầu không rõ ràng hoặc nằm ngoài phạm vi

### Quy tắc phản hồi

- Trả lời **ngắn gọn**, đi thẳng vào vấn đề
- **Giải thích trước** khi thực hiện thay đổi code
- Khi có nhiều cách làm, **đề xuất và hỏi** người dùng chọn
- Nếu không chắc chắn, **hỏi lại** thay vì đoán

---

**Note**: This is a research and development project. Always follow local traffic laws and regulations when using this system.
