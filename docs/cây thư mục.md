# 📁 ADAS Project Structure - Cấu Trúc Dự Án (CẬP NHẬT 2026-07-10)

```
ADAS/
│
├── 🎯 MAIN ENTRY POINTS
│   ├── 📄 main.py                      # Streamlit Dashboard (Giao diện chính)
│   ├── 📄 test_gpu_support.py         # Kiểm tra GPU acceleration
│   ├── 📄 GPU_ACCELERATION.md         # Hướng dẫn GPU setup
│   └── 📄 README.md                   # Giới thiệu dự án
│
├── 🎥 PRE-TRAINED MODELS
│   ├── yolo11n.pt                     # YOLO 11 Nano (2.6MB - lightweight)
│   └── yolo26x.pt                     # YOLO 26 X-large (262MB - accurate)
│
│
├── 📂 BACKEND - AI/ML SERVICE
│   └── ai-service/
│       ├── 📄 gpu_utils.py            # ⭐ GPU detection & auto-fallback
│       ├── 📄 requirements.txt        # Python dependencies
│       │
│       ├── 📂 PREPROCESSING (Tiền xử lý ảnh)
│       │   ├── image_processor.py
│       │   ├── color_space/
│       │   ├── enhancement/
│       │   ├── filtering/
│       │   └── utils/
│       │
│       ├── 📂 AI MODELS (YOLOv11 + DeepLab)
│       │   ├── vehicle_detection/
│       │   ├── pedestrian_detection/
│       │   ├── lane_detection/
│       │   ├── lane_segmentation/
│       │   ├── traffic_sign_detection/
│       │   └── evaluation/
│       │
│       ├── 📂 TRADITIONAL CV (Edge/Hough)
│       │   ├── edge_detection/
│       │   └── lane_detection/
│       │
│       ├── 📂 FUSION ENGINE (Scene Understanding)
│       │   ├── scene_understanding.py
│       │   ├── tracking_fusion.py
│       │   └── vehicle_lane_fusion.py
│       │
│       ├── 📂 TRACKING (DeepSORT)
│       │   └── deepsort_tracker.py
│       │
│       └── 📂 ADAS DECISION (Warnings & Alerts)
│           ├── decision_engine.py
│           ├── warning_manager.py
│           ├── lane_departure/       (20+ files)
│           ├── traffic_sign/
│           ├── stop_warning.py
│           ├── no_entry_warning.py
│           └── speed_limit.py
│
│
├── 📂 FRONTEND (React - Optional)
│   ├── src/pages/
│   ├── src/components/
│   └── src/services/
│
│
├── 📂 DOCUMENTATION
│   ├── 📄 cây thư mục.md           # File này
│   ├── 📄 cây thư mục_updated.md   # Detailed structure
│   ├── 📄 PROJECT_OVERVIEW.md      # ⭐ Summary (200+ lines)
│   ├── 📄 GPU_ACCELERATION.md
│   ├── 📄 Phát hiện và cảnh báo xe lệch làn.md
│   ├── 📄 Traffic Sign Warning.md
│   ├── diagrams/
│   ├── proposal/
│   ├── references/
│   └── report/
│
│
├── 📂 NOTEBOOKS (Jupyter)
│   └── README.md
│
│
├── 📂 OUTPUTS
│   ├── predictions/
│   ├── reports/
│   ├── screenshots/
│   └── videos/
│
│
└── 📂 OTHER
    ├── .env.example
    ├── .git/
    └── __pycache__/
```

---

## 🎯 **5 Thành Phần Chính**

### **1️⃣ PREPROCESSING** → Tiền xử lý ảnh
- RGB→HSV/Gray/LAB, CLAHE, Gaussian/Median/Bilateral filters

### **2️⃣ AI MODELS** → Phát hiện objects (GPU 5-8x)
- YOLOv11: Vehicle, Pedestrian, Traffic Sign
- DeepLabV3+: Lane Segmentation

### **3️⃣ TRADITIONAL CV** → Edge/Hough detection
- Canny, Sobel, Hough Transform

### **4️⃣ FUSION ENGINE** → Kết hợp dữ liệu
- Scene Understanding, Tracking, Relationship Detection

### **5️⃣ DECISION ENGINE** → Ra quyết định & Cảnh báo
- Lane Departure, Traffic Sign, Speed Limit, Traffic Rules

---

## ⚡ **GPU ACCELERATION (NEW)**

```bash
# Auto-detect GPU
python -m streamlit run main.py

# Force GPU
$env:AI_DEVICE="gpu"; python -m streamlit run main.py

# Force CPU
$env:AI_DEVICE="cpu"; python -m streamlit run main.py
```

**Performance**: ✅ 5-8x faster | ✅ Auto-detect | ✅ CPU fallback

---

## 📖 **Xem Thêm**

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Tóm tắt chi tiết 200+ dòng
- [GPU_ACCELERATION.md](../GPU_ACCELERATION.md) - GPU setup guide
- [cây thư mục_updated.md](cây%20thư%20mục_updated.md) - Full detailed structure

---

**✅ Updated**: 2026-07-10 | **🚀 GPU**: Auto-detected | **⚡ Speed**: 5-7x faster