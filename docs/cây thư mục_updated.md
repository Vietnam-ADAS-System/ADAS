# ADAS - Cây thư mục cập nhật

Cập nhật theo workspace hiện tại tại `D:\xlyanh2\ADAS`.

Quy ước lọc cây thư mục:
- Không liệt kê `.git/`, `__pycache__/`, file `.pyc`.
- Không liệt kê `.gitkeep`, file 0 byte và thư mục chỉ chứa placeholder.
- Các thư mục artifact có nhiều ảnh/plot/weights được ghi kèm số lượng để tài liệu vẫn đầy đủ nhưng không quá nhiễu.

```text
ADAS/
|-- .env.example                         # Mẫu biến môi trường
|-- .gitattributes
|-- .gitignore
|-- GPU_ACCELERATION.md                   # Hướng dẫn GPU/CUDA
|-- README.md                             # README chính
|-- main.py                               # Streamlit demo ảnh/video/webcam
|-- test_gpu_support.py                   # Kiểm tra GPU và môi trường inference
|-- yolo11n.pt                            # YOLO weight nhẹ ở root
|-- yolo26x.pt                            # YOLO weight lớn ở root
|
|-- backend/
|   |-- ai-service/
|   |   |-- gpu_utils.py                  # Auto-detect CUDA/CPU fallback
|   |   |-- requirements.txt              # Dependency Python chính
|   |   |
|   |   |-- adas/                         # Rule/decision layer cho ADAS
|   |   |   |-- __init__.py
|   |   |   |-- config.py
|   |   |   |-- dashboard_output.py
|   |   |   |-- data_models.py
|   |   |   |-- decision_engine.py
|   |   |   |-- no_entry_warning.py
|   |   |   |-- speed_limit.py
|   |   |   |-- stop_warning.py
|   |   |   |-- traffic_rule.py
|   |   |   |-- utils.py
|   |   |   |-- warning_manager.py
|   |   |   |
|   |   |   |-- lane_departure/            # Cảnh báo lệch làn
|   |   |   |   |-- __init__.py
|   |   |   |   |-- config.py
|   |   |   |   |-- dashboard_sender.py
|   |   |   |   |-- direction.py
|   |   |   |   |-- frame_validator.py
|   |   |   |   |-- lane_center.py
|   |   |   |   |-- lane_departure_service.py
|   |   |   |   |-- lane_offset.py
|   |   |   |   |-- lane_status.py
|   |   |   |   |-- lane_validator.py
|   |   |   |   |-- lane_visualizer.py
|   |   |   |   |-- lane_warning.py
|   |   |   |   |-- lane_width.py
|   |   |   |   |-- models.py
|   |   |   |   |-- normalize_offset.py
|   |   |   |   |-- offset_model.py
|   |   |   |   |-- offset_service.py
|   |   |   |   |-- tracking_validator.py
|   |   |   |   |-- utils.py
|   |   |   |   |-- validator.py
|   |   |   |   |-- vehicle_center.py
|   |   |   |   |-- vehicle_validator.py
|   |   |   |   `-- warning_engine.py
|   |   |   |
|   |   |   `-- traffic_sign/              # Chuẩn hóa biển báo và sinh cảnh báo
|   |   |       |-- __init__.py
|   |   |       |-- bbox_parser.py
|   |   |       |-- class_mapper.py
|   |   |       |-- confidence_filter.py
|   |   |       |-- config.py
|   |   |       |-- dashboard_sender.py
|   |   |       |-- example_pipeline.py
|   |   |       |-- models.py
|   |   |       |-- priority_manager.py
|   |   |       |-- README.md
|   |   |       |-- sign_input_service.py
|   |   |       |-- sign_reader.py
|   |   |       |-- speed_limit_manager.py
|   |   |       |-- speed_limit_service.py
|   |   |       |-- speed_rule_parser.py
|   |   |       |-- test_traffic_sign.py
|   |   |       |-- traffic_sign_config.yaml
|   |   |       |-- warning_decision.py
|   |   |       |-- warning_history.py
|   |   |       |-- warning_manager.py
|   |   |       |-- warning_queue.py
|   |   |       |-- warning_service.py
|   |   |       `-- warning_timer.py
|   |   |
|   |   |-- ai_models/                     # Detector, trainer, weights, artifact
|   |   |   |-- vehicle_detection/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- convert_bdd100k_to_yolo.py
|   |   |   |   |-- README.md
|   |   |   |   |-- train_vehicle_detector.py
|   |   |   |   |-- vehicle_detection.yaml
|   |   |   |   |-- vehicle_detector.py
|   |   |   |   |-- src/
|   |   |   |   |   |-- __init__.py
|   |   |   |   |   `-- detector.py
|   |   |   |   |-- weights/
|   |   |   |   |   |-- best.pt
|   |   |   |   |   `-- last.pt
|   |   |   |   `-- evaluation/             # 22 file: args/results/plots/batch images
|   |   |   |
|   |   |   |-- pedestrian_detection/
|   |   |   |   |-- detector.py
|   |   |   |   |-- test_pedestrian_detector.py
|   |   |   |   |-- train.py
|   |   |   |   |-- pedestrian_output/
|   |   |   |   |   `-- nhandiennguoidibo/   # 12 ảnh kết quả phát hiện người đi bộ
|   |   |   |   `-- pedestrian_runs/
|   |   |   |       |-- detect/
|   |   |   |       |   |-- val/              # 8 file evaluation
|   |   |   |       |   `-- val2/             # 8 file evaluation
|   |   |   |       `-- pedestrian/
|   |   |   |           `-- walking_v1/      # 22 file, gồm weights/best.pt và last.pt
|   |   |   |
|   |   |   |-- lane_detection/
|   |   |   |   |-- detector.py
|   |   |   |   |-- lane_det.yaml
|   |   |   |   |-- README.md
|   |   |   |   `-- weights/
|   |   |   |       `-- best.pt
|   |   |   |
|   |   |   |-- lane_segmentation/
|   |   |   |   |-- convert_via_to_yolo.py
|   |   |   |   |-- KAGGLE_WORKFLOW.md
|   |   |   |   |-- lane_yolo.yaml
|   |   |   |   |-- predict.py
|   |   |   |   |-- RE_TRAIN_GUIDE.md
|   |   |   |   |-- README.md
|   |   |   |   |-- requirements.txt
|   |   |   |   |-- train.py
|   |   |   |   `-- weights/
|   |   |   |       `-- best.pt
|   |   |   |
|   |   |   `-- traffic_sign_detection/
|   |   |       |-- train.py
|   |   |       |-- predict.py
|   |   |       |-- data.yaml
|   |   |       |-- 2583453-c14c6c115268fad9f7013a267f3dbe06.jpg
|   |   |       |-- 3e58805fce2d6bc584f0cfbcdac8a07f.jpg
|   |   |       |-- 80.jpg
|   |   |       |-- bien-bao-1.jpg
|   |   |       |-- bien-giao-nhau-voi-duong-khong-uu-tien-antbook.vn-4.jpg
|   |   |       |-- cấm đi ngược chiều .jpg
|   |   |       |-- cấm quay đầu.jpg
|   |   |       |-- giao đi bộ và biển 60.jpg
|   |   |       |-- OIP.jpg
|   |   |       |-- quay đàu.jpg
|   |   |       |-- test.jpg
|   |   |       |-- VP Gửi .jpg
|   |   |       |-- inference_outputs/
|   |   |       |   `-- prediction_results/  # 14 ảnh inference đã xuất
|   |   |       |-- traffic_sign_runs/       # 24 file: weights, args, results, plots, batches
|   |   |       `-- traffic_sign_runs_new/
|   |   |           `-- traffic_sign_52classes/ # 23 file: weights, args, plots, batches
|   |   |
|   |   |-- preprocessing/                 # Tiền xử lý ảnh dùng chung
|   |   |   |-- __init__.py
|   |   |   |-- image_processor.py
|   |   |   |-- color_space/
|   |   |   |   `-- converter.py
|   |   |   |-- enhancement/
|   |   |   |   `-- equalizer.py
|   |   |   |-- filtering/
|   |   |   |   `-- filters.py
|   |   |   `-- utils/
|   |   |       `-- visualizer.py
|   |   |
|   |   |-- fusion/                        # Hợp nhất detection/lane/sign/tracking
|   |   |   |-- __init__.py
|   |   |   |-- config.py
|   |   |   |-- data_models.py
|   |   |   |-- decision_engine.py
|   |   |   |-- README.md
|   |   |   |-- scene_understanding.py
|   |   |   |-- tracking_fusion.py
|   |   |   |-- traffic_sign_fusion.py
|   |   |   |-- utils.py
|   |   |   `-- vehicle_lane_fusion.py
|   |   |
|   |   `-- tracking/
|   |       |-- __init__.py
|   |       |-- deepsort_tracker.py
|   |       `-- README.md
|   |
|   `-- node-server/
|       `-- README.md                     # Tài liệu scaffold Node/Express; code route/controller chưa có
|
|-- docs/
|   |-- cây thư mục mới.md
|   |-- cây thư mục.md
|   |-- cây thư mục_updated.md             # File này
|   |-- file.md
|   |-- phan1.md
|   |-- Phát hiện và cảnh báo xe lệch làn.md
|   |-- phương pháp nghiên cứu.md
|   |-- project-state.md
|   |-- PROJECT_OVERVIEW.md
|   |-- README.md
|   |-- task-template.md
|   |-- Traffic Sign Warning.md
|   `-- report/
|       `-- BAO_CAO_TONG_HOP.md
|
|-- File .MD/
|   `-- PROMPT_TAO_MAIN_PY.md
|
|-- frontend/
|   `-- README.md                         # Scaffold React; source hiện chỉ có placeholder
|
|-- notebooks/
|   `-- README.md
|
`-- outputs/
    |-- README.md
    `-- videos/
        |-- tmp3w1ne8g8_streamlit_annotated.mp4
        `-- tmpd2tj4_hl_streamlit_annotated.mp4
```

## Thống kê hiện tại

- 281 file có nội dung sau khi bỏ `.git/`, `__pycache__/`, `.gitkeep` và file 0 byte.
- 47 thư mục có nội dung thật.
- Tổng dung lượng file được tính trong cây: khoảng 353.7 MB.
- Theo phần mở rộng:
  - `.jpg`: 91 file
  - `.py`: 90 file
  - `.png`: 40 file
  - `.md`: 28 file
  - `.pt`: 12 file
  - `.yaml`: 10 file
  - `.csv`: 3 file
  - `.mp4`: 2 file
  - `.txt`: 2 file
  - `.example`, `.gitattributes`, `.gitignore`: mỗi loại 1 file

## Các phần đã loại khỏi cây vì rỗng hoặc chỉ là placeholder

- `backend/ai-service/evaluation/`
- `backend/ai-service/traditional_cv/edge_detection/`
- `backend/ai-service/traditional_cv/lane_detection/`
- `backend/node-server/controllers/`, `middleware/`, `routes/`, `services/`, `uploads/`
- `docs/diagrams/`, `proposal/`, `references/`, `slides/`
- `docs/Dashboard Realtime.md` vì file 0 byte
- `frontend/public/`, `frontend/src/assets/`, `frontend/src/components/`, `frontend/src/services/`
- `outputs/predictions/`, `outputs/reports/`, `outputs/screenshots/`
- Các file `__init__.py` 0 byte và toàn bộ `__pycache__/`

## Nhận xét trạng thái

- Ứng dụng chạy chính hiện là `main.py` bằng Streamlit.
- `backend/ai-service/` là phần có code xử lý thực tế: model, preprocessing, fusion, tracking và ADAS warning.
- `frontend/` và `backend/node-server/` hiện là scaffold/tài liệu, chưa có source triển khai ngoài README và placeholder.
- `outputs/videos/` đang có video kết quả đã sinh từ app; các thư mục output khác hiện chưa có nội dung thật.
