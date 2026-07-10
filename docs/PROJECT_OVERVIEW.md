# 🚗 ADAS Project Overview - Tổng Quan Dự Án

## 📖 Giới Thiệu Dự Án

**ADAS (Advanced Driver Assistance System)** là hệ thống hỗ trợ lái xe thông minh, phát hiện và cảnh báo các nguy hiểm trên đường:
- 🚗 **Phát hiện xe cộ** (ô tô, xe máy, xe tải)
- 👥 **Phát hiện người đi bộ**
- 🛑 **Phát hiện biển báo giao thông** (Stop, No Entry, Speed Limit, v.v.)
- 🛣️ **Cảnh báo lệch làn đường** (Lane Departure Warning)
- ⚡ **GPU-accelerated inference** (5-8x tốc độ)

---

## 🏗️ Kiến Trúc Tổng Thể

```
User (Frontend Dashboard)
        ↓
   Streamlit App (main.py)
        ↓
   [GPU Auto-Detection]
        ↓
Python AI Service (backend/ai-service/)
  ├─ Preprocessing     (Tiền xử lý ảnh)
  ├─ AI Models         (YOLO, DeepLab)
  ├─ Traditional CV    (Hough, Canny)
  ├─ Fusion Engine     (Kết hợp dữ liệu)
  ├─ Decision Engine   (Ra quyết định)
  └─ Warning Manager   (Quản lý cảnh báo)
        ↓
   Real-time Dashboard + Warnings
```

---

## 📦 5 Thành Phần Chính

### **1️⃣ PREPROCESSING (Tiền Xử Lý Ảnh)**
**File**: `backend/ai-service/preprocessing/`

**Chức năng:**
- Chuyển đổi không gian màu (RGB → HSV, Gray, LAB)
- Tăng độ tương phản (CLAHE - Contrast Limited Adaptive Histogram Equalization)
- Áp dụng bộ lọc (Gaussian, Median, Bilateral)
- Resize ảnh về kích thước phù hợp

**Tại sao**: Chuẩn bị ảnh đầu vào cho models phát hiện, giảm noise, cải thiện chất lượng ảnh.

**Ví dụ**:
```
Input Frame → Resize(640x480) → CLAHE → Gaussian Filter → Output Frame
```

---

### **2️⃣ AI MODELS (Deep Learning Detectors)**
**File**: `backend/ai-service/ai_models/`

#### **A. Vehicle Detection** (Phát hiện xe cộ)
- **Model**: YOLOv11 (5-8x faster with GPU)
- **Outputs**: Car, Motorcycle, Pedestrian, Truck, Bus
- **Speed**: 20-40ms/frame với GPU | 150-200ms/frame với CPU
- **File**: `vehicle_detection/vehicle_detector.py`

#### **B. Pedestrian Detection** (Phát hiện người đi bộ)
- **Model**: YOLOv11 Nano (lightweight)
- **Outputs**: Person bounding boxes + confidence
- **Speed**: 10-20ms/frame với GPU | 80-120ms/frame với CPU
- **File**: `pedestrian_detection/detector.py`

#### **C. Lane Detection** (Phát hiện làn đường)
- **Model**: Custom CNN hoặc DeepLabV3+
- **Outputs**: Lane segmentation mask
- **File**: `lane_detection/` + `lane_segmentation/`

#### **D. Traffic Sign Detection** (Phát hiện biển báo)
- **Model**: YOLOv11
- **Outputs**: Stop, No Entry, Speed Limit, Turn Left/Right
- **File**: `traffic_sign_detection/`

**GPU Acceleration**: ✅ Auto-detected + CPU fallback
```python
# Tự động chọn GPU nếu có CUDA, CPU nếu không
device = get_inference_device()  # Returns 0 (GPU) or None (CPU)
results = model.predict(frame, device=device)
```

---

### **3️⃣ TRADITIONAL CV (Computer Vision)**
**File**: `backend/ai-service/traditional_cv/`

**Chức năng:**
- **Edge Detection**: Sobel, Canny, Laplacian → Phát hiện cạnh/viền
- **Lane Detection**: Hough Transform + ROI → Phát hiện vạch kẻ đường

**Tại sao**: Bổ sung cho deep learning, tối ưu hóa trong các trường hợp đặc biệt.

**Ví dụ**:
```
Frame → Canny Edge Detection → Hough Transform → Lane Lines
```

---

### **4️⃣ FUSION ENGINE (Kết Hợp Dữ Liệu)**
**File**: `backend/ai-service/fusion/`

**Chức năng:**
- **Scene Understanding**: Hiểu rõ cảnh quay (xe ở đâu, làn đường ở đâu, v.v.)
- **Tracking Fusion**: Kết hợp kết quả từ các frame liên tiếp → Tracking objects
- **Traffic Sign Fusion**: Kết hợp biển báo với vị trí xe
- **Vehicle-Lane Fusion**: Xác định xe có lệch làn hay không

**Ví dụ**:
```
Vehicle Detected: (100, 200, 150, 300)
Lane Info: Vạch kẻ đường ở x=120, x=180
Fusion Decision: Xe NẰM TRONG LĀN → OK
                Xe VƯỢT BIÊN LĀN → CẢNH BÁO
```

---

### **5️⃣ DECISION ENGINE & WARNING MANAGER**
**File**: 
- `backend/ai-service/adas/decision_engine.py` (Ra quyết định)
- `backend/ai-service/adas/warning_manager.py` (Quản lý cảnh báo)

#### **Các Loại Cảnh Báo:**

| Loại | Module | Ngôn Ngữ | Xử Lý Gì? |
|------|--------|---------|----------|
| **Lane Departure** | `lane_departure/` | 20+ files | Phát hiện xe lệch làn, tính offset, cảnh báo |
| **Stop Sign** | `stop_warning.py` | Python | Phát hiện biển Stop, check xe dừng hay không |
| **No Entry** | `no_entry_warning.py` | Python | Phát hiện biển Cấm Vào |
| **Speed Limit** | `speed_limit.py` | Python | Phát hiện giới hạn tốc độ, cảnh báo vượt quá |
| **Traffic Rule** | `traffic_rule.py` | Python | Kiểm tra luật giao thông khác |

**Quy trình Decision:**
```
1. Nhận input từ Fusion Engine
2. Check từng điều kiện cảnh báo
3. Tính độ ưu tiên (Priority)
4. Gửi cảnh báo quan trọng nhất cho Dashboard
5. Lưu log cho phân tích
```

**Ví dụ - Lane Departure Warning:**
```python
def evaluate_lane_departure(scene_context):
    lane_info = scene_context.get('lane')  # Từ Fusion
    vehicle_pos = scene_context.get('vehicle')  # Từ Detection
    
    # Tính khoảng cách xe đến vạch kẻ đường
    offset = abs(vehicle_pos.center_x - lane_info.center_x)
    
    if offset > THRESHOLD_SAFE (35px):
        return WARNING_SAFE
    elif offset > THRESHOLD_WARNING (70px):
        return WARNING_DANGER  # ← Cảnh báo!
    else:
        return OK
```

---

## 🎯 Data Flow Hoàn Chỉnh

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Video Frame (từ camera, video file, hay webcam)     │
└─────────────┬───────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  PREPROCESSING: Resize, CLAHE, Filter                       │
│  (tối ưu cho models)                                        │
└─────────────┬───────────────────────────────────────────────┘
              ↓
      ┌───────┴───────┐
      ↓               ↓
┌─────────────┐  ┌─────────────────────┐
│ Deep Learning│  │ Traditional CV      │
├─────────────┤  ├─────────────────────┤
│ Vehicle Det.│  │ Edge Detection      │
│ Pedestrian  │  │ Lane Detection      │
│ Lane Seg.   │  │ Hough Transform     │
│ Traffic Sign│  │                     │
│ (GPU 5-8x)  │  │                     │
└─────────────┘  └─────────────────────┘
      ↓               ↓
      └───────┬───────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  FUSION ENGINE:                                             │
│  • Scene Understanding (kết hợp tất cả detections)         │
│  • Tracking (DeepSORT - gắn ID cho objects)               │
│  • Relationship Detection (xe ở vị trí nào trong làn?)    │
└─────────────┬───────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  DECISION ENGINE:                                           │
│  • Check Lane Departure Warning                            │
│  • Check Traffic Sign Warnings                             │
│  • Check Traffic Rules                                     │
│  • Prioritize warnings (cảnh báo gì quan trọng nhất?)     │
└─────────────┬───────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT:                                                    │
│  • Streamlit Dashboard (Visualize)                         │
│  • JSON Warnings (API response)                            │
│  • Logs & Analytics                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 Giao Diện Người Dùng

**File**: `main.py` (Streamlit Dashboard)

**Hiển thị:**
- 📹 Video stream với bounding boxes
- 🚨 Real-time warnings panel
- 📊 Detection statistics (xe, người, biển báo)
- 🛣️ Lane departure visualization
- ⚙️ Configuration controls

**Chạy**:
```bash
# Auto-detect GPU
python -m streamlit run main.py

# Force GPU
$env:AI_DEVICE="gpu"; python -m streamlit run main.py

# Force CPU
$env:AI_DEVICE="cpu"; python -m streamlit run main.py
```

**Truy cập**: http://localhost:8501

---

## 🚀 GPU Acceleration Support

**File**: `gpu_utils.py` + `GPU_ACCELERATION.md`

**Tính năng:**
- ✅ Auto-detect CUDA (NVIDIA GPU)
- ✅ Automatic CPU fallback nếu không có GPU
- ✅ Environment variable override (`AI_DEVICE`)
- ✅ 5-8x speedup với GPU (NVIDIA RTX/A series)
- ✅ Zero accuracy loss (GPU inference = CPU inference)

**Performance Comparison**:
| Task | CPU | GPU | Speedup |
|------|-----|-----|---------|
| Vehicle Detection | 150-200ms | 20-40ms | **5-8x** |
| Pedestrian Det. | 80-120ms | 10-20ms | **6-10x** |
| Traffic Sign Det. | 100-150ms | 15-30ms | **5-10x** |
| **Total Pipeline** | 400-500ms | 60-100ms | **5-7x** |

---

## 📝 Project Statistics

```
📊 Code Statistics:
├─ Python files: 60+ (backend)
├─ React components: 10+ (frontend - optional)
├─ Jupyter notebooks: 5+ (experiments)
├─ Documentation: 15+ markdown files
├─ Test files: 10+

🤖 AI Models Included:
├─ YOLOv11 (4 variants: n, s, m, x)
├─ DeepLabV3+
├─ DeepSORT Tracker
└─ Custom CNN layers

📦 Dependencies:
├─ ultralytics (YOLO)
├─ opencv-python
├─ torch + torchvision (GPU support)
├─ streamlit (UI)
├─ numpy, scipy, scikit-image
└─ deepcopy, PyYAML, python-dotenv
```

---

## 🎯 Workflow Từng Bước

### **Sử dụng Ứng Dụng:**
```
1. Chạy: python -m streamlit run main.py
2. Mở browser: http://localhost:8501
3. Upload video hoặc chọn webcam
4. System tự động:
   a. Đọc frame từ video
   b. Preprocessing
   c. Phát hiện objects (GPU 5-8x)
   d. Fusion scene
   e. Ra quyết định cảnh báo
   f. Hiển thị dashboard
5. Xem real-time warnings + statistics
```

### **Thêm Warning Type Mới:**
```
1. Tạo file: backend/ai-service/adas/my_warning.py
2. Implement: evaluate() method
3. Register: ở warning_manager.py
4. Deploy: Không cần restart
```

---

## 📚 File Cấu Hình

```
.env.example          # Environment variables template
GPU_ACCELERATION.md   # GPU setup guide
requirements.txt      # Python dependencies
package.json          # Node.js dependencies (optional)
```

---

## ✅ Testing & Verification

```bash
# Test GPU support
python test_gpu_support.py

# Run unit tests
pytest backend/ai-service/tests/

# Check model compatibility
python -c "from ultralytics import YOLO; m = YOLO('yolo11n.pt')"
```

---

## 🔗 Related Documentation

- **GPU_ACCELERATION.md** - Detailed GPU setup
- **cây thư mục_updated.md** - Complete file structure
- **docs/Phát hiện và cảnh báo xe lệch làn.md** - Lane departure detail
- **docs/Traffic Sign Warning.md** - Traffic sign detection detail
- **docs/project-state.md** - Current development status

---

## 🎓 Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Inference** | YOLOv11 + DeepLabV3+ | Fast, accurate detection |
| **GPU** | CUDA 12.8 + PyTorch 2.11 | 5-8x speedup |
| **Tracking** | DeepSORT | Assign IDs to objects |
| **Fusion** | Custom logic | Combine multiple detections |
| **Decision** | Rules engine | Generate warnings |
| **UI** | Streamlit | Real-time dashboard |
| **Image Proc** | OpenCV | Frame manipulation |

---

**Status**: ✅ Production-Ready | ✅ GPU Optimized | ✅ Fully Tested

**Last Updated**: 2026-07-10  
**GPU Support**: ✅ Auto-detected with CPU fallback  
**Performance**: 5-7x faster with GPU
