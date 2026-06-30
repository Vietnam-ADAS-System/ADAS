# Cấu hình train lại model với các tham số tối ưu hơn
# Chạy trên Kaggle

# 1. Cấu hình giảm conf threshold khi inference
results = model.train(
    data='/kaggle/working/dataset.yaml',
    epochs=150,           # Tăng epochs lên 150
    imgsz=640,
    batch=16,
    device=selected_device,
    project='/kaggle/working/yolo_lane_seg_v2',
    name='train_run',
    # Tăng cường augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.5,
    degrees=10.0,          # Tăng rotation
    translate=0.2,
    scale=0.5,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.15,            # Thêm mixup
    # Early stopping patience
    patience=50,
)

# 2. Test với conf thấp hơn khi inference
results = model.predict(
    source='/path/to/test/image.jpg',
    conf=0.05,             # Dùng conf thấp hơn
    iou=0.5,
    imgsz=640
)
