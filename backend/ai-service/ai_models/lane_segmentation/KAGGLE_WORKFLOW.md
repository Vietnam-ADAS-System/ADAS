# Hướng dẫn Workflow: Kaggle Training + Local Project

## Tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL PROJECT                            │
│  ADAS/backend/ai-service/ai_models/lane_segmentation/            │
│                                                                  │
│  ├── segmentation/weights/best.pt     ← Model Segmentation    │
│  ├── detection/weights/best (1).pt    ← Model Detection        │
│  ├── kaggle/                          ← Notebooks              │
│  └── outputs/                         ← Logs, metrics          │
└─────────────────────────────────────────────────────────────────┘
              ↑                       ↓
              │    Kaggle Training    │
              │   (Train ở đây)      │
              │         ↓            │
         Download weights      Upload notebook
              │                   ↓   │
              └───────────────────────┘
```

---

## Bước 1: Chuẩn bị Dataset

### Upload lên Kaggle (Khuyến nghị)

1. **Download dataset về local**
```bash
mkdir -p backend/ai-service/ai_models/lane_segmentation/datasets
cd backend/ai-service/ai_models/lane_segmentation/datasets

# Download VIA Lane Segmentation Dataset
# Link: https://github.com/makerhanoi/via-dataset/releases/tag/v1.0
```

2. **Upload lên Kaggle**
- Vào https://www.kaggle.com/datasets
- Create New Dataset
- Upload folder đã giải nén

---

## Bước 2: Train trên Kaggle

1. Import notebook từ folder `kaggle/` vào Kaggle
2. Update dataset path trong notebook
3. Chạy training
4. Model tự save vào `/kaggle/working/`

---

## Bước 3: Download Kết quả về Local

### Kaggle Output Folder Structure
```
/kaggle/working/
├── segmentation_results/
│   └── weights/
│       └── best.pt              ← Segmentation weights
├── detection_results/
│   └── weights/
│       └── best (1).pt         ← Detection weights
└── test_results.png            ← Sample predictions
```

### Cách download

**Cách 1: Manual (Qua giao diện Kaggle)**
1. Vào tab "Output" của notebook
2. Click vào file cần download
3. Lưu về local

**Cách 2: Dùng Kaggle API**
```bash
kaggle kernels output <username>/<notebook-name> -p ./outputs
```

---

## Bước 4: Tổ chức Local Project

### Copy weights về local
```bash
cd backend/ai-service/ai_models/lane_segmentation/

# Segmentation
cp ~/Downloads/best.pt segmentation/weights/

# Detection
cp ~/Downloads/best\ \(1\).pt detection/weights/
```

### Final Local Structure
```
lane_segmentation/
├── segmentation/
│   ├── predict.py
│   ├── lane_yolo.yaml
│   └── weights/
│       └── best.pt              ← Trained weights
├── detection/
│   ├── detector.py
│   ├── lane_det.yaml
│   └── weights/
│       └── best (1).pt          ← Trained weights
├── kaggle/
├── datasets/
├── input/
├── output/
├── app.py                       # Gradio comparison app
└── requirements.txt
```

---

## Bước 5: Chạy Inference Local

### Segmentation
```bash
python segmentation/predict.py \
    --weights segmentation/weights/best.pt \
    --source input/anh2.png \
    --output output/result.png
```

### Detection
```bash
python detection/detector.py \
    --weights "detection/weights/best (1).pt" \
    --source input/anh2.png \
    --output output/result.png
```

### Gradio App
```bash
cd backend/ai-service/ai_models/lane_segmentation
python app.py
```

---

## Lưu ý

1. **Không commit weights lên Git** - File quá lớn (đã có trong .gitignore)

2. **Dataset có thể lưu local** nếu có đủ storage

3. **Training logs** nên lưu lại cho báo cáo
