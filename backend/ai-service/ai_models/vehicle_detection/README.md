# Vehicle Object Detection

Module nay chi phu trach chuc nang duoc giao:

- xe hoi: `car`
- xe may: `motorcycle`
- nguoi di bo: `person`

Khong xu ly lane segmentation, traffic sign, tracking hay ADAS warning.

## Lua chon model

Mac dinh dung `yolo26x.pt` de uu tien do chinh xac. Theo tai lieu Ultralytics,
YOLO26 detect models duoc pretrained tren COCO va ban `x` co mAP cao nhat trong
nhom pretrained. Neu bai yeu cau dung YOLO11, doi:

```env
YOLO_VEHICLE_MODEL_PATH=yolo11x.pt
```

Mac dinh `VEHICLE_DETECTION_END2END=false` de uu tien accuracy cua YOLO26
one-to-many head/NMS. Doi thanh `true` neu can uu tien toc do va export don gian hon.

Do chinh xac cao nhat cho duong Viet Nam nen lay tu model fine-tune tren BDD100K
hoac dataset noi bo, sau do cau hinh:

```env
YOLO_VEHICLE_MODEL_PATH=backend/ai-service/ai_models/detection/weights/best.pt
```

## Chay inference anh

Tu thu muc `backend/ai-service`:

```bash
pip install -r requirements.txt
python main.py
```

API:

```bash
curl -X POST "http://127.0.0.1:8000/detect/vehicles" \
  -F "file=@path/to/test.jpg"
```

Tra ve JSON gom bounding box, class, confidence va thoi gian inference.

Anh da ve bounding box:

```bash
curl -X POST "http://127.0.0.1:8000/detect/vehicles/annotated" \
  -F "file=@path/to/test.jpg" \
  --output annotated.jpg
```

## Fine-tune voi BDD100K

1. Tai BDD100K detection dataset, co thu muc `images/100k` va labels detection.
2. Convert label sang YOLO, chi giu 3 class duoc giao:

```bash
python ai_models/detection/convert_bdd100k_to_yolo.py \
  --bdd-root D:/datasets/bdd100k \
  --copy-images
```

3. Train:

```bash
python ai_models/detection/train_vehicle_detector.py \
  --data ai_models/detection/vehicle_detection.yaml \
  --model yolo26x.pt \
  --epochs 100 \
  --imgsz 960 \
  --device 0
```

Neu can YOLO11:

```bash
python ai_models/detection/train_vehicle_detector.py --model yolo11x.pt
```
