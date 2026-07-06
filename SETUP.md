# ADAS - Hệ thống Hỗ trợ Lái xe An toàn

## Tổng quan

Hệ thống ADAS (Advanced Driver Assistance System) với các tính năng:
- **Phát hiện làn đường** - Lane Detection
- **Nhận diện biển báo giao thông** - Traffic Sign Recognition
- **Phát hiện phương tiện** - Vehicle Detection
- **Phát hiện người đi bộ** - Pedestrian Detection
- **Cảnh báo lệch làn** - Lane Departure Warning

## Yêu cầu hệ thống

### Phần cứng
- CPU: Intel Core i5 / AMD Ryzen 5 trở lên
- RAM: 8GB trở lên (16GB khuyến nghị)
- GPU: NVIDIA GPU với CUDA (tùy chọn, tăng tốc AI)
- Webcam hoặc video input

### Phần mềm
- Python 3.9+
- Node.js 18+
- npm 8+

## Cài đặt

### 1. Clone project
```bash
git clone <repo-url>
cd ADAS
```

### 2. Cài đặt Python dependencies
```bash
cd backend/ai-service

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

### 3. Cài đặt Node.js dependencies
```bash
# Backend Node server
cd backend/node-server
npm install

# Frontend
cd ../../frontend
npm install
```

## Chạy hệ thống

### Cách 1: Script tự động (Khuyến nghị)

**Windows:**
```bash
scripts\start-all.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start-all.sh
bash scripts/start-all.sh
```

### Cách 2: Chạy thủ công từng phần

#### Terminal 1: Node.js Backend
```bash
cd backend/node-server
node server.js
```
Server chạy tại: http://localhost:3000

#### Terminal 2: AI Backend (Python)
```bash
cd backend/ai-service

# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Với webcam
python run_unified.py --webcam --fps 15

# Với video file
python run_unified.py --video ./test_videos/traffic.mp4
```

#### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

Mở trình duyệt: http://localhost:5173

## Cấu trúc project

```
ADAS/
├── backend/
│   ├── ai-service/           # AI models (Python)
│   │   ├── ai_models/        # YOLO models
│   │   ├── fusion.py         # Fusion engine
│   │   ├── adas/             # ADAS decision engine
│   │   ├── tracking/         # DeepSORT tracker
│   │   └── realtime_server.py # WebSocket AI server
│   └── node-server/          # Node.js backend
│       ├── server.js         # Main WebSocket server
│       └── ...
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── services/         # WebSocket services
│   │   └── pages/           # Pages
│   └── ...
└── scripts/                   # Helper scripts
    ├── start-all.sh          # Linux/Mac launcher
    └── start-all.bat         # Windows launcher
```

## API Endpoints

### Node.js Backend (port 3000)

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/health` | GET | Health check |
| `/api/ai/frame` | POST | Nhận AI data từ Python |
| `/api/mode` | POST | Chuyển đổi mode (ai/mock) |
| `/api/realtime/snapshot` | GET | Lấy frame hiện tại |
| `/ws/video` | WebSocket | Video stream |
| `/ws/lane` | WebSocket | Lane data stream |
| `/ws/traffic-sign` | WebSocket | Traffic sign stream |
| `/ws/warning` | WebSocket | Warning stream |

### AI Backend (port 8765)

WebSocket server nhận kết nối từ clients và broadcast kết quả AI.

## Troubleshooting

### Lỗi "Port already in use"
```bash
# Tìm và kill process sử dụng port
# Windows:
netstat -ano | findstr :3000
taskkill /PID <pid> /F

# Linux/Mac:
lsof -i :3000
kill -9 <pid>
```

### Lỗi Python import
```bash
cd backend/ai-service
pip install ultralytics opencv-python numpy
```

### Lỗi npm install
```bash
npm cache clean --force
npm install
```

### Webcam không hoạt động
- Kiểm tra webcam đã được kết nối
- Thử chỉ định device: `python run_unified.py --webcam --device 0`

## Phát triển

### Thêm model mới
1. Thêm model vào thư mục `ai_models/`
2. Cập nhật `fusion.py` để tích hợp
3. Cập nhật `realtime_server.py` để broadcast kết quả

### Sửa UI
1. Chỉnh sửa components trong `frontend/src/components/`
2. Styles trong `frontend/src/styles.css`
3. Rebuild: `npm run build`

## License

MIT License
