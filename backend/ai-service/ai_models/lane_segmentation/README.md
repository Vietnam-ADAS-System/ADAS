# Lane Segmentation Module

Module phân vùng làn đường (segmentation) cho hệ thống ADAS.

## Cấu trúc

```
lane_segmentation/
├── predict.py               # Inference script
├── train.py                 # Training script
├── lane_yolo.yaml           # Dataset config
├── convert_via_to_yolo.py   # Convert annotation tool
│
├── weights/
│   └── best.pt              # Trained weights
│
└── datasets/                # Dataset storage
```

## Classes

| ID | Tên | Mô tả |
|----|-----|--------|
| 0 | lane_line | Vạch kẻ đường |
| 1 | road | Mặt đường |

## Sử dụng

```python
from predict import LaneSegmenter

# Khởi tạo
segmenter = LaneSegmenter("weights/best.pt", conf=0.15)

# Phân đoạn trên ảnh
img = cv2.imread("test.jpg")
mask = segmenter.get_lane_mask(img, class_id=1)  # road
vis = segmenter.visualize(img)
```

## Chạy command line

```bash
cd backend/ai-service/ai_models/lane_segmentation
python predict.py \
    --weights weights/best.pt \
    --source ../outputs/lane_segmentation/test_samples/anh2.png \
    --output ../outputs/lane_segmentation/result.png \
    --conf 0.15
```

## Training

### Trên local
```bash
python train.py --data lane_yolo.yaml --epochs 50 --imgsz 640
```

### Trên Kaggle
Xem `KAGGLE_WORKFLOW.md` để biết thêm chi tiết.

## Output

Kết quả được lưu tại `../../outputs/lane_segmentation/`:
- `test_samples/` - Ảnh/video test
- `compare/` - So sánh các model
- `traditional_result*.png` - Kết quả traditional CV

## Hướng dẫn

- `KAGGLE_WORKFLOW.md` - Hướng dẫn train trên Kaggle
- `RE_TRAIN_GUIDE.md` - Hướng dẫn retrain model
