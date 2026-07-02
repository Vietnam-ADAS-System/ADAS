# Cây thư mục ADAS mới

```text
ADAS/
├── main.py
├── README.md
├── yolo11n.pt
├── yolo26x.pt
├── backend/
│   ├── ai-service/
│   │   ├── requirements.txt
│   │   ├── adas/
│   │   ├── ai_models/
│   │   │   ├── __init__.py
│   │   │   ├── lane_detection/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detector.py
│   │   │   │   ├── lane_det.yaml
│   │   │   │   ├── README.md
│   │   │   │   └── weights/
│   │   │   │       └── best.pt
│   │   │   ├── lane_segmentation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── convert_via_to_yolo.py
│   │   │   │   ├── KAGGLE_WORKFLOW.md
│   │   │   │   ├── predict.py
│   │   │   │   ├── README.md
│   │   │   │   ├── requirements.txt
│   │   │   │   ├── train.py
│   │   │   │   └── weights/
│   │   │   │       └── best.pt
│   │   │   ├── pedestrian_detection/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detector.py
│   │   │   │   ├── test_pedestrian_detector.py
│   │   │   │   ├── train.py
│   │   │   │   └── pedestrian_output/
│   │   │   ├── traffic_sign_detection/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data.yaml
│   │   │   │   ├── predict.py
│   │   │   │   ├── train.py
│   │   │   │   └── inference_outputs/
│   │   │   └── vehicle_detection/
│   │   │       ├── __init__.py
│   │   │       ├── convert_bdd100k_to_yolo.py
│   │   │       ├── README.md
│   │   │       ├── train_vehicle_detector.py
│   │   │       ├── vehicle_detection.yaml
│   │   │       ├── vehicle_detector.py
│   │   │       ├── evaluation/
│   │   │       └── weights/
│   │   ├── evaluation/
│   │   ├── fusion/
│   │   ├── preprocessing/
│   │   │   ├── __init__.py
│   │   │   ├── image_processor.py
│   │   │   ├── color_space/
│   │   │   │   ├── __init__.py
│   │   │   │   └── converter.py
│   │   │   ├── enhancement/
│   │   │   │   ├── __init__.py
│   │   │   │   └── equalizer.py
│   │   │   ├── filtering/
│   │   │   │   ├── __init__.py
│   │   │   │   └── filters.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── visualizer.py
│   │   └── tracking/
│   │       ├── __init__.py
│   │       ├── deepsort_tracker.py
│   │       └── README.md
│   └── node-server/
│       ├── README.md
│       ├── controllers/
│       ├── middleware/
│       ├── routes/
│       ├── services/
│       └── uploads/
├── frontend/
│   ├── README.md
│   ├── public/
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── services/
├── docs/
│   ├── README.md
│   ├── cây thư mục.md
│   ├── diagrams/
│   ├── proposal/
│   ├── references/
│   ├── report/
│   │   └── BAO_CAO_TONG_HOP.md
│   └── slides/
├── File .MD/
│   ├── PREPROCESSING_INTEGRATION_PLAN.md
│   └── PROMPT_TAO_MAIN_PY.md
├── notebooks/
│   └── README.md
├── outputs/
│   ├── README.md
│   ├── predictions/
│   ├── reports/
│   ├── screenshots/
│   └── videos/
```
