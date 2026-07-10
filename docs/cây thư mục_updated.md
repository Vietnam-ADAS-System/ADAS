# 📁 ADAS Project Structure (Cấu Trúc Dự Án)

```
ADAS/
│
├── 📄 main.py                          # Streamlit Dashboard chính - Giao diện người dùng
├── 📄 test_gpu_support.py             # Kiểm tra GPU acceleration support
├── 📄 GPU_ACCELERATION.md             # Hướng dẫn GPU acceleration configuration
├── 📄 README.md                       # Giới thiệu dự án chính
├── 📄 .env.example                    # Template environment variables
│
├── 🎥 yolo11n.pt                      # YOLO 11 Nano model (lightweight)
├── 🎥 yolo26x.pt                      # YOLO 26 X-large model (accurate)
│
│
├── 📂 backend/
│   │
│   ├── 📂 ai-service/                 # Python AI/ML Service (Core Logic)
│   │   │
│   │   ├── 📄 gpu_utils.py            # GPU detection & auto-fallback utilities
│   │   ├── 📄 requirements.txt        # Python dependencies
│   │   │
│   │   ├── 📂 adas/                   # ADAS Decision Engine & Warnings
│   │   │   ├── 📄 config.py
│   │   │   ├── 📄 decision_engine.py  # Main decision logic
│   │   │   ├── 📄 data_models.py
│   │   │   ├── 📄 dashboard_output.py # Send output to dashboard
│   │   │   ├── 📄 warning_manager.py  # Organize & prioritize warnings
│   │   │   ├── 📄 traffic_rule.py     # Traffic rule warnings
│   │   │   ├── 📄 stop_warning.py
│   │   │   ├── 📄 no_entry_warning.py
│   │   │   ├── 📄 speed_limit.py
│   │   │   ├── 📄 utils.py
│   │   │   │
│   │   │   ├── 📂 lane_departure/     # Lane Departure Warning Module
│   │   │   │   ├── 📄 config.py
│   │   │   │   ├── 📄 lane_departure_service.py
│   │   │   │   ├── 📄 lane_validator.py
│   │   │   │   ├── 📄 lane_visualizer.py
│   │   │   │   ├── 📄 lane_warning.py
│   │   │   │   ├── 📄 lane_center.py
│   │   │   │   ├── 📄 lane_offset.py
│   │   │   │   ├── 📄 lane_width.py
│   │   │   │   ├── 📄 lane_status.py
│   │   │   │   ├── 📄 direction.py
│   │   │   │   ├── 📄 frame_validator.py
│   │   │   │   ├── 📄 vehicle_center.py
│   │   │   │   ├── 📄 vehicle_validator.py
│   │   │   │   ├── 📄 tracking_validator.py
│   │   │   │   ├── 📄 offset_model.py
│   │   │   │   ├── 📄 offset_service.py
│   │   │   │   ├── 📄 normalize_offset.py
│   │   │   │   ├── 📄 models.py
│   │   │   │   ├── 📄 dashboard_sender.py
│   │   │   │   ├── 📄 warning_engine.py
│   │   │   │   ├── 📄 validator.py
│   │   │   │   └── 📄 utils.py
│   │   │   │
│   │   │   └── 📂 traffic_sign/       # Traffic Sign Warning Module
│   │   │       ├── 📄 __init__.py
│   │   │       └── ... (traffic sign detection logic)
│   │   │
│   │   ├── 📂 ai_models/              # Deep Learning Models
│   │   │   ├── 📂 vehicle_detection/
│   │   │   │   ├── 📄 vehicle_detector.py    # YOLOv11 vehicle detection
│   │   │   │   ├── 📄 train_vehicle_detector.py
│   │   │   │   └── 📄 test_vehicle_detector.py
│   │   │   │
│   │   │   ├── 📂 pedestrian_detection/
│   │   │   │   ├── 📄 detector.py            # YOLOv11 pedestrian detection
│   │   │   │   ├── 📄 train.py
│   │   │   │   └── 📄 test_pedestrian_detector.py
│   │   │   │
│   │   │   ├── 📂 lane_detection/
│   │   │   │   ├── 📄 detector.py            # Lane detection model
│   │   │   │   ├── 📄 lane_det.yaml
│   │   │   │   └── 📄 train.py
│   │   │   │
│   │   │   ├── 📂 lane_segmentation/
│   │   │   │   ├── 📄 train.py               # DeepLabV3+ lane segmentation
│   │   │   │   └── 📄 inference.py
│   │   │   │
│   │   │   ├── 📂 traffic_sign_detection/
│   │   │   │   ├── 📄 detector.py            # YOLOv11 traffic sign detection
│   │   │   │   ├── 📄 train.py
│   │   │   │   └── 📄 config.yaml
│   │   │   │
│   │   │   └── 📂 evaluation/
│   │   │       └── 📄 metrics.py
│   │   │
│   │   ├── 📂 preprocessing/           # Image Preprocessing Pipeline
│   │   │   ├── 📄 image_processor.py   # Main entry point
│   │   │   ├── 📂 color_space/
│   │   │   │   └── 📄 converter.py     # RGB→HSV, RGB→Gray, RGB→LAB
│   │   │   ├── 📂 enhancement/
│   │   │   │   └── 📄 equalizer.py    # CLAHE, Histogram Equalization
│   │   │   ├── 📂 filtering/
│   │   │   │   └── 📄 filters.py      # Gaussian, Median, Bilateral filters
│   │   │   └── 📂 utils/
│   │   │
│   │   ├── 📂 traditional_cv/         # Traditional Computer Vision
│   │   │   ├── 📂 edge_detection/
│   │   │   │   └── 📄 detectors.py    # Sobel, Canny, Laplacian
│   │   │   └── 📂 lane_detection/
│   │   │       └── 📄 hough_transform.py  # Hough transform lane detection
│   │   │
│   │   ├── 📂 fusion/                 # Sensor Fusion & Scene Understanding
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py
│   │   │   ├── 📄 data_models.py
│   │   │   ├── 📄 decision_engine.py
│   │   │   ├── 📄 scene_understanding.py
│   │   │   ├── 📄 tracking_fusion.py
│   │   │   ├── 📄 traffic_sign_fusion.py
│   │   │   ├── 📄 vehicle_lane_fusion.py
│   │   │   ├── 📄 utils.py
│   │   │   └── 📄 README.md
│   │   │
│   │   ├── 📂 tracking/               # Object Tracking
│   │   │   ├── 📄 deepsort_tracker.py # DeepSORT tracking algorithm
│   │   │   └── 📄 README.md
│   │   │
│   │   └── 📂 __pycache__/
│   │
│   └── 📂 node-server/                # Node.js Express Server (Optional)
│       ├── 📄 README.md
│       ├── 📄 server.js
│       ├── 📂 controllers/            # Handle requests
│       ├── 📂 routes/                 # API endpoints
│       ├── 📂 services/               # Business logic
│       ├── 📂 middleware/             # Auth, file upload
│       └── 📂 uploads/                # User uploaded videos
│
│
├── 📂 frontend/                       # React Web Dashboard (Optional)
│   ├── 📄 README.md
│   ├── 📄 package.json
│   ├── 📂 public/
│   │   ├── 📄 index.html
│   │   └── 📄 favicon.ico
│   ├── 📂 src/
│   │   ├── 📂 pages/
│   │   │   ├── 📄 Dashboard.jsx       # Main dashboard
│   │   │   ├── 📄 Detection.jsx       # Vehicle/Pedestrian detection
│   │   │   ├── 📄 LaneDetection.jsx   # Lane departure warning
│   │   │   └── 📄 TrafficSign.jsx     # Traffic sign detection
│   │   ├── 📂 components/
│   │   │   ├── 📄 VideoPlayer.jsx
│   │   │   ├── 📄 WarningPanel.jsx
│   │   │   ├── 📄 DetectionTable.jsx
│   │   │   └── 📄 TrafficSignPanel.jsx
│   │   ├── 📂 services/
│   │   │   └── 📄 api.js             # API calls to backend
│   │   └── 📂 assets/
│   │
│   └── 📂 node_modules/
│
│
├── 📂 docs/                           # Documentation
│   ├── 📄 README.md
│   ├── 📄 cây thư mục.md             # Project structure
│   ├── 📄 cây thư mục_updated.md     # Updated structure (this file)
│   ├── 📄 PROJECT_OVERVIEW.md        # Project overview & summary
│   ├── 📄 Dashboard Realtime.md
│   ├── 📄 Phát hiện và cảnh báo xe lệch làn.md
│   ├── 📄 Traffic Sign Warning.md
│   ├── 📄 phương pháp nghiên cứu.md
│   ├── 📄 project-state.md
│   ├── 📄 task-template.md
│   ├── 📂 diagrams/                  # Architecture diagrams
│   ├── 📂 proposal/                  # Project proposals
│   ├── 📂 references/                # Research papers
│   ├── 📂 report/
│   │   └── 📄 BAO_CAO_TONG_HOP.md    # Comprehensive report
│   └── 📂 slides/
│
│
├── 📂 notebooks/                      # Jupyter Notebooks
│   ├── 📄 README.md
│   └── ... (experimental notebooks)
│
│
├── 📂 outputs/                        # Generated outputs
│   ├── 📂 predictions/               # Detection results
│   ├── 📂 reports/                   # Analysis reports
│   ├── 📂 screenshots/               # UI screenshots
│   └── 📂 videos/                    # Processed videos
│
│
├── 📂 File .MD/                       # Additional markdown files
│   └── 📄 PROMPT_TAO_MAIN_PY.md
│
│
└── 📂 __pycache__/
```

---

## 📊 Summary

### **Tổng cộng:**
- **Python modules**: 60+ files
- **Models**: 4 deep learning models (YOLO + DeepLab)
- **Core Features**: 8 major detection/warning systems
- **Frontend**: React dashboard (optional)
- **Backend**: Node.js API + Python AI service
- **GPU Support**: Auto-detection with CPU fallback

### **Key Technologies:**
- **AI/ML**: YOLOv11, DeepLabV3+, DeepSORT
- **Image Processing**: OpenCV, scikit-image
- **Backend**: Python (FastAPI/Streamlit), Node.js/Express
- **Frontend**: React.js
- **GPU**: CUDA 12.8 with PyTorch 2.11
- **Database**: (MongoDB/PostgreSQL for persistence)

### **Latest Updates:**
✅ GPU acceleration support added (5-8x speedup)  
✅ Auto CUDA detection with CPU fallback  
✅ Streamlit dashboard as main UI  
✅ Modular architecture for easy extension  
✅ Comprehensive test suite included  
