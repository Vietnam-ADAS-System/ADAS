ADAS-Vietnam/
│
├── frontend/
│   │
│   ├── public/
│   │   └── Chứa favicon, logo, file tĩnh.
│   │
│   ├── src/
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Detection.jsx
│   │   │   ├── LaneDetection.jsx
│   │   │   └── TrafficSign.jsx
│   │   │
│   │   │   => Các trang giao diện chính.
│   │   │
│   │   ├── components/
│   │   │
│   │   │   => Các component tái sử dụng:
│   │   │
│   │   │   - VideoPlayer
│   │   │   - WarningPanel
│   │   │   - DetectionTable
│   │   │   - TrafficSignPanel
│   │   │
│   │   ├── services/
│   │   │
│   │   │   => Gọi API từ NodeJS.
│   │   │
│   │   └── assets/
│   │
│   └── package.json
│
│
├── backend/
│   │
│   ├── node-server/
│   │   │
│   │   ├── routes/
│   │   │
│   │   │   => Định nghĩa API:
│   │   │
│   │   │   /upload-video
│   │   │   /detect
│   │   │   /segment
│   │   │   /warning
│   │   │
│   │   ├── controllers/
│   │   │
│   │   │   => Xử lý request từ frontend.
│   │   │
│   │   ├── services/
│   │   │
│   │   │   => Gọi sang Python AI Service.
│   │   │
│   │   ├── middleware/
│   │   │
│   │   │   => Upload file, xác thực,...
│   │   │
│   │   └── uploads/
│   │
│   │       => Video người dùng upload.
│   │
│   │
│   └── ai-service/
│       │
│       ├── preprocessing/
│       │
│       │   => PHẦN CVIP
│       │
│       │   Bao gồm:
│       │
│       │   - RGB → HSV
│       │   - RGB → Gray
│       │   - RGB → LAB
│       │   - Histogram Equalization
│       │   - CLAHE
│       │   - Gaussian Blur
│       │   - Median Filter
│       │   - Bilateral Filter
│       │   - Data Augmentation
│       │
│       │
│       ├── traditional_cv/
│       │
│       │   => PHẦN COMPUTER VISION
│       │
│       │
│       │   ├── edge_detection/
│       │   │
│       │   │   => Phát hiện biên
│       │   │
│       │   │   - Sobel
│       │   │   - Canny
│       │   │   - Laplacian
│       │   │
│       │   │
│       │   └── lane_detection/
│       │
│       │       => Phát hiện làn đường
│       │
│       │       - ROI
│       │       - Hough Transform
│       │       - Lane Tracking
│       │       - Lane Visualization
│       │
│       │
│       ├── ai_models/
│       │
│       │   => PHẦN AI / DEEP LEARNING
│       │
│       │
│       │   ├── detection/
│       │   │
│       │   │   => YOLOv11 Vehicle Detection
│       │   │
│       │   │   Nhận diện:
│       │   │
│       │   │   - Car
│       │   │   - Bus
│       │   │   - Truck
│       │   │   - Motorcycle
│       │   │   - Person
│       │   │
│       │   │
│       │   ├── traffic_sign_detection/
│       │   │
│       │   │   => YOLOv11 Traffic Sign Detection
│       │   │
│       │   │   Nhận diện:
│       │   │
│       │   │   - Stop
│       │   │   - No Entry
│       │   │   - Speed Limit
│       │   │   - Turn Left
│       │   │   - Turn Right
│       │   │
│       │   │
│       │   └── lane_segmentation/
│       │
│       │       => DeepLabV3+
│       │
│       │       Semantic Segmentation:
│       │
│       │       - Road
│       │       - Lane
│       │       - Background
│       │
│       │
│       ├── tracking/
│       │
│       │   => Theo dõi đối tượng
│       │
│       │   YOLO + DeepSORT
│       │
│       │   Mỗi xe sẽ có ID riêng:
│       │
│       │   Car #1
│       │   Car #2
│       │   Motorcycle #3
│       │
│       │
│       ├── fusion/
│       │
│       │   => KẾT HỢP KẾT QUẢ
│       │
│       │   Vehicle Detection
│       │          +
│       │   Lane Segmentation
│       │          +
│       │   Traffic Sign Detection
│       │
│       │
│       │   Đầu ra:
│       │
│       │   - Vị trí xe
│       │   - Vị trí làn đường
│       │   - Biển báo hiện tại
│       │
│       │
│       ├── adas/
│       │
│       │   => PHẦN QUYẾT ĐỊNH ADAS
│       │
│       │
│       │   Lane Departure Warning
│       │
│       │   Ví dụ:
│       │
│       │   Xe lệch làn
│       │   →
│       │   Cảnh báo
│       │
│       │
│       │   Traffic Sign Alert
│       │
│       │   Ví dụ:
│       │
│       │   STOP
│       │   →
│       │   Prepare To Stop
│       │
│       │   Speed Limit 40
│       │   →
│       │   Current Limit = 40
│       │
│       │
│       ├── evaluation/
│       │
│       │   => ĐÁNH GIÁ MÔ HÌNH
│       │
│       │   Detection:
│       │
│       │   - Precision
│       │   - Recall
│       │   - mAP50
│       │   - mAP50-95
│       │
│       │
│       │   Segmentation:
│       │
│       │   - IoU
│       │   - mIoU
│       │   - Pixel Accuracy
│       │
│       │
│       │   System:
│       │
│       │   - FPS
│       │   - Latency
│       │
│       │
│       └── api/
│
│           => FastAPI
│
│           Cung cấp API cho:
│
│           - Detection
│           - Segmentation
│           - Tracking
│           - ADAS Warning
│
│
├── datasets/
│
│   => Dataset huấn luyện
│
│   vehicle_detection/
│
│   traffic_sign/
│
│   lane_segmentation/
│
│   vietnam_test_videos/
│
│
├── outputs/
│
│   => Kết quả sinh ra
│
│   predictions/
│
│   videos/
│
│   screenshots/
│
│   reports/
│
│
├── docs/
│
│   => Tài liệu đồ án
│
│   proposal/
│
│   report/
│
│   slides/
│
│   diagrams/
│
│   references/
│
│
└── notebooks/
│
│   => Thử nghiệm và nghiên cứu
│
│   data_analysis.ipynb
│
│   yolo_experiment.ipynb
│
│   deeplab_experiment.ipynb