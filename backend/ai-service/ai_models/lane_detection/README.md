# Lane Detection Module

Module nhận diện vạch kẻ đường (detection) cho hệ thống ADAS.

## Cấu trúc

```
lane_detection/
├── detector.py             # Inference script
├── lane_det.yaml          # Dataset config
└── weights/
    └── best (1).pt        # Trained weights
```

## Classes (11 loại)

| ID | Tên | Mô tả |
|----|-----|--------|
| 0 | broken_and_solid_lines_white_lane | Vạch đứt nối + liền trắng |
| 1 | broken_and_solid_lines_yellow_lane | Vạch đứt nối + liền vàng |
| 2 | broken_line_white_lane | Vạch đứt trắng |
| 3 | broken_line_yellow_lane | Vạch đứt vàng |
| 4 | double_solid_line_white_lane | Vạch đôi liền trắng |
| 5 | double_solid_line_yellow_lane | Vạch đôi liền vàng |
| 6 | left_turn | Rẽ trái |
| 7 | right_turn | Rẽ phải |
| 8 | solid_line_white_lane | Vạch liền trắng |
| 9 | solid_line_yellow_lane | Vạch liền vàng |
| 10 | straight_way | Đường thẳng |

## Sử dụng

```python
from detector import LaneDetector

# Khởi tạo
detector = LaneDetector("weights/best (1).pt", conf=0.25)

# Detect trên ảnh
img = cv2.imread("test.jpg")
result = detector.visualize(img)

# Lấy danh sách detections
detections = detector.get_detections(img)
for det in detections:
    print(f"{det['class_name']}: {det['conf']:.2f}")
```

## Chạy command line

```bash
cd backend/ai-service/ai_models/lane_detection
python detector.py \
    --weights weights/best\ \(1\).pt \
    --source ../outputs/lane_segmentation/test_samples/anh2.png \
    --output ../outputs/lane_detection/result.png \
    --conf 0.25
```

## Output

Kết quả được lưu tại `../../outputs/lane_detection/`
