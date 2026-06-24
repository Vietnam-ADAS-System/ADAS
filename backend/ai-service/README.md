# Python AI Service

FastAPI-based AI service for processing video streams and performing:
- Object Detection (YOLO)
- Lane Segmentation (DeepLabV3+)
- Traffic Sign Detection
- Object Tracking (DeepSORT)
- ADAS Decision Logic

## Components

### Preprocessing (CVIP)
- Color space conversions (RGB → HSV, Gray, LAB)
- Histogram Equalization & CLAHE
- Filtering (Gaussian, Median, Bilateral)
- Data Augmentation

### Traditional Computer Vision
- Edge Detection (Sobel, Canny, Laplacian)
- Lane Detection (ROI, Hough Transform, Lane Tracking)

### AI Models / Deep Learning
- Vehicle Detection (YOLOv11)
- Traffic Sign Detection (YOLOv11)
- Lane Segmentation (DeepLabV3+)

### System Components
- Object Tracking (YOLO + DeepSORT)
- Result Fusion
- ADAS Decision Logic
- Model Evaluation
- REST API

## Installation

```bash
pip install -r requirements.txt
python main.py
```
