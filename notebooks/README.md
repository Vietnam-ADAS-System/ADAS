# Jupyter Notebooks

Research and experimentation notebooks:

- `data_analysis.ipynb` - Data analysis and visualization
- `yolo_experiment.ipynb` - YOLO model experiments
- `deeplab_experiment.ipynb` - DeepLab segmentation experiments
- `lane_detection_training.ipynb` - Lane detection training (legacy version)
- **`lane_detection_train.ipynb`** - ⭐ **Lane detection training chạy trên Google Colab** (mới nhất):
  - Dataset: `veetinator/Road_Line_Marking_Dataset (RLMD)` từ Hugging Face — 2137 ảnh, **25 lớp** vạch kẻ đường phù hợp Việt Nam
  - Model: YOLOv11-seg (Ultralytics)
  - **Mount Google Drive** và cache toàn bộ dataset + weights → không mất khi Colab disconnect
  - 41 cells: download → convert mask PNG → YOLO seg format → split 80/20 → train → đánh giá chi tiết (mAP50, mAP50-95, precision/recall per class) → export ONNX/TorchScript → test trên ảnh Việt Nam → tuỳ chọn push lên Hugging Face Hub
  - File `build_notebook.py` là script phát sinh notebook (có thể chỉnh sửa & regenerate)
