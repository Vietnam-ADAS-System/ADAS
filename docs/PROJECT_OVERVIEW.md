# ADAS Project Overview

Cập nhật theo trạng thái workspace hiện tại tại `D:\xlyanh2\ADAS`.

## 1. Mục tiêu dự án

ADAS là demo hệ thống hỗ trợ lái xe, tập trung vào xử lý ảnh/video từ camera hoặc file video để:
- Phát hiện xe và người đi bộ.
- Phát hiện làn đường và phân đoạn làn đường.
- Phát hiện biển báo giao thông.
- Theo dõi đối tượng qua nhiều frame.
- Hợp nhất kết quả detector thành `SceneContext`.
- Sinh cảnh báo ADAS như lệch làn, biển báo, tốc độ, cấm vào và luật giao thông.
- Hiển thị kết quả trực quan bằng Streamlit.

## 2. Trạng thái thực tế của repository

Phần đang có code xử lý chính:
- `main.py`: Streamlit app cho ảnh, video và webcam.
- `backend/ai-service/`: Python AI service, gồm model wrapper, preprocessing, fusion, tracking và ADAS rules.
- `backend/ai-service/ai_models/`: detector, trainer, weights và artifact đánh giá.
- `backend/ai-service/adas/`: decision engine, lane departure, traffic sign warning.
- `backend/ai-service/fusion/`: chuẩn hóa và hợp nhất kết quả nhận diện.
- `backend/ai-service/tracking/`: DeepSORT/fallback tracking.
- `outputs/videos/`: video kết quả đã xuất từ app.

Phần đang là scaffold hoặc tài liệu:
- `frontend/`: hiện chỉ có README và placeholder, chưa có React source thật.
- `backend/node-server/`: hiện chỉ có README và placeholder, chưa có route/controller/service thật.
- Một số thư mục docs/output/traditional CV chỉ có `.gitkeep`, đã loại khỏi cây thư mục cập nhật.

## 3. Kiến trúc tổng quan

```text
Input ảnh/video/webcam
        |
        v
Streamlit app: main.py
        |
        |-- file upload / camera input
        |-- chọn module chạy
        |-- bật/tắt preprocessing
        |-- preview frame realtime
        v
AI service modules
        |
        |-- preprocessing/
        |-- ai_models/
        |   |-- vehicle_detection
        |   |-- pedestrian_detection
        |   |-- lane_detection
        |   |-- lane_segmentation
        |   `-- traffic_sign_detection
        |-- tracking/
        |-- fusion/
        `-- adas/
        |
        v
Kết quả
        |
        |-- frame/video đã annotate
        |-- counts theo module
        |-- SceneContext
        |-- ADASOutput
        `-- cảnh báo hiển thị trên giao diện
```

## 4. Ứng dụng Streamlit chính

File: `main.py`

Chức năng hiện có:
- Chế độ ảnh: upload `jpg/jpeg/png/bmp/webp`, xử lý detection, hiển thị ảnh kết quả và tải ảnh.
- Chế độ video: upload `mp4/avi/mov/mkv`, xử lý từng frame, hiển thị preview realtime, xuất video kết quả và tải video.
- Chế độ webcam: dùng `st.camera_input` để chụp ảnh từ trình duyệt.
- Sidebar chọn module:
  - Pedestrian
  - Vehicle
  - Lane Detection
  - Lane Segmentation
  - Traffic Sign
- Sidebar bật/tắt preprocessing.
- Hiển thị `Scene Context / ADAS Output` để debug kết quả fusion và warning.
- Video output được xử lý để trình duyệt có thể phát trực tiếp bằng MIME phù hợp (`video/mp4` hoặc `video/webm`).

## 5. AI service

Thư mục: `backend/ai-service/`

File gốc:
- `gpu_utils.py`: kiểm tra CUDA, chọn GPU/CPU, log thiết bị inference.
- `requirements.txt`: dependency Python chính.

Dependency chính hiện có:
```text
fastapi
uvicorn[standard]
python-multipart
python-dotenv
ultralytics
opencv-python
numpy
streamlit
deep-sort-realtime
```

## 6. Model và detector

Thư mục: `backend/ai-service/ai_models/`

### Vehicle Detection

Thư mục: `vehicle_detection/`

Thành phần:
- `vehicle_detector.py`: wrapper chính cho YOLO vehicle detection.
- `src/detector.py`: detector phụ/trừu tượng hóa detector.
- `train_vehicle_detector.py`: script train.
- `convert_bdd100k_to_yolo.py`: chuyển BDD100K sang YOLO format.
- `vehicle_detection.yaml`: cấu hình dataset/model.
- `weights/best.pt`, `weights/last.pt`: weights đã train.
- `evaluation/`: 22 artifact gồm `args.yaml`, `results.csv`, confusion matrix, curve và batch image.

### Pedestrian Detection

Thư mục: `pedestrian_detection/`

Thành phần:
- `detector.py`: detector người đi bộ.
- `train.py`: train YOLO pedestrian.
- `test_pedestrian_detector.py`: script test/pick image/draw output.
- `pedestrian_runs/`: artifact train/evaluate, gồm `detect/val`, `detect/val2`, `pedestrian/walking_v1`.
- `pedestrian_output/nhandiennguoidibo/`: 12 ảnh output đã detect.

### Lane Detection

Thư mục: `lane_detection/`

Thành phần:
- `detector.py`: `LaneDetector`, detect lane từ ảnh/video.
- `lane_det.yaml`: cấu hình dataset.
- `weights/best.pt`: weight lane detection.
- `README.md`: mô tả module.

### Lane Segmentation

Thư mục: `lane_segmentation/`

Thành phần:
- `predict.py`: `LaneSegmenter`, predict ảnh/video.
- `train.py`: train lane segmentation.
- `convert_via_to_yolo.py`: convert VIA dataset sang YOLO.
- `lane_yolo.yaml`: cấu hình dataset.
- `weights/best.pt`: weight segmentation.
- `KAGGLE_WORKFLOW.md`, `RE_TRAIN_GUIDE.md`, `README.md`, `requirements.txt`.

### Traffic Sign Detection

Thư mục: `traffic_sign_detection/`

Thành phần:
- `predict.py`: preprocess, infer traffic sign, xử lý frame/video.
- `train.py`: train traffic sign model.
- `data.yaml`: cấu hình dataset/classes.
- 12 ảnh mẫu đầu vào trong thư mục module.
- `inference_outputs/prediction_results/`: 14 ảnh inference đã xuất.
- `traffic_sign_runs/`: 24 artifact train/evaluate, gồm weights và biểu đồ.
- `traffic_sign_runs_new/traffic_sign_52classes/`: 23 artifact cho phiên bản 52 classes.

## 7. Preprocessing

Thư mục: `backend/ai-service/preprocessing/`

Thành phần:
- `image_processor.py`: entry point xử lý ảnh.
- `color_space/converter.py`: đổi RGB/HSV/Gray/LAB.
- `enhancement/equalizer.py`: CLAHE và histogram equalization.
- `filtering/filters.py`: Gaussian, Median, Bilateral.
- `utils/visualizer.py`: tiện ích hiển thị/so sánh preprocessing.

Vai trò:
- Chuẩn hóa input trước khi đưa vào detector.
- Giảm noise, tăng tương phản, resize và hỗ trợ debug trực quan.

## 8. Tracking

Thư mục: `backend/ai-service/tracking/`

Thành phần:
- `deepsort_tracker.py`: `Track`, `TrackerConfig`, `ObjectTracker`.
- `README.md`: mô tả cách dùng DeepSORT/fallback.

Vai trò:
- Gán ID ổn định cho vehicle/pedestrian qua nhiều frame.
- Có fallback IoU khi DeepSORT hoặc embedder không sẵn sàng.
- Cung cấp track output cho Fusion.

## 9. Fusion layer

Thư mục: `backend/ai-service/fusion/`

Thành phần:
- `data_models.py`: `BoundingBox`, `VehicleDetection`, `PedestrianDetection`, `LaneInfo`, `TrafficSign`, `TrackInfo`, `SceneContext`.
- `decision_engine.py`: `FusionEngine`, chuẩn hóa input và tạo context.
- `scene_understanding.py`: hiểu scene tổng hợp.
- `tracking_fusion.py`: liên kết detection với track.
- `traffic_sign_fusion.py`: chuẩn hóa biển báo thành traffic rule.
- `vehicle_lane_fusion.py`: xác định trạng thái xe so với làn.
- `utils.py`: bbox, IoU, lane bounds, parse speed limit, timestamp.
- `config.py`: cấu hình fusion.

Vai trò:
- Nhận output từ detector/lane/tracking/sign.
- Chuẩn hóa dữ liệu không đồng nhất.
- Trả về một `SceneContext` để ADAS decision engine đọc.

## 10. ADAS decision và cảnh báo

Thư mục: `backend/ai-service/adas/`

Thành phần cấp cao:
- `decision_engine.py`: `ADASDecisionEngine`.
- `warning_manager.py`: gom và ưu tiên warning.
- `data_models.py`: model dữ liệu ADAS output/warning.
- `dashboard_output.py`: format output cho dashboard.
- `stop_warning.py`, `no_entry_warning.py`, `speed_limit.py`, `traffic_rule.py`: rule cảnh báo cụ thể.

### Lane Departure

Thư mục: `adas/lane_departure/`

Thành phần chính:
- `lane_departure_service.py`: service xử lý lệch làn.
- `validator.py`, `frame_validator.py`, `vehicle_validator.py`, `lane_validator.py`, `tracking_validator.py`: validate input.
- `lane_center.py`, `lane_width.py`, `lane_offset.py`, `normalize_offset.py`: tính toán hình học làn.
- `lane_status.py`, `direction.py`, `lane_warning.py`, `warning_engine.py`: phân loại trạng thái và cảnh báo.
- `lane_visualizer.py`: vẽ overlay cảnh báo lên frame.
- `models.py`, `config.py`, `utils.py`, `dashboard_sender.py`.

### Traffic Sign Warning

Thư mục: `adas/traffic_sign/`

Thành phần chính:
- `sign_input_service.py`, `sign_reader.py`: chuẩn hóa input biển báo.
- `class_mapper.py`: mapping class từ detector.
- `confidence_filter.py`: lọc theo confidence.
- `bbox_parser.py`: chuẩn hóa bbox.
- `speed_rule_parser.py`, `speed_limit_service.py`, `speed_limit_manager.py`: xử lý speed limit.
- `warning_decision.py`, `warning_service.py`, `warning_manager.py`: sinh cảnh báo.
- `priority_manager.py`, `warning_queue.py`, `warning_history.py`, `warning_timer.py`: quản lý ưu tiên, queue, lịch sử và thời gian warning.
- `dashboard_sender.py`: gửi/format output cho dashboard.
- `traffic_sign_config.yaml`: cấu hình module.
- `test_traffic_sign.py`: test pipeline traffic sign.

## 11. Dữ liệu và artifact

Root weights:
- `yolo11n.pt`
- `yolo26x.pt`

Weights trong module:
- `vehicle_detection/weights/best.pt`
- `vehicle_detection/weights/last.pt`
- `lane_detection/weights/best.pt`
- `lane_segmentation/weights/best.pt`
- `traffic_sign_runs/weights/best.pt`
- `traffic_sign_runs/weights/last.pt`
- `traffic_sign_runs_new/traffic_sign_52classes/weights/best.pt`
- `traffic_sign_runs_new/traffic_sign_52classes/weights/last.pt`
- `pedestrian_runs/pedestrian/walking_v1/weights/best.pt`
- `pedestrian_runs/pedestrian/walking_v1/weights/last.pt`

Generated output hiện có:
- `outputs/videos/tmp3w1ne8g8_streamlit_annotated.mp4`
- `outputs/videos/tmpd2tj4_hl_streamlit_annotated.mp4`

Các thư mục `outputs/predictions/`, `outputs/reports/`, `outputs/screenshots/` hiện chỉ có placeholder nên không được tính là nội dung thật.

## 12. Frontend và Node server

`frontend/`:
- Hiện có `README.md`.
- Các nhánh `public/`, `src/assets/`, `src/components/`, `src/services/` chỉ có placeholder.
- Chưa có `package.json`, component React hoặc service API thật trong workspace hiện tại.

`backend/node-server/`:
- Hiện có `README.md`.
- Các nhánh `controllers/`, `middleware/`, `routes/`, `services/`, `uploads/` chỉ có placeholder.
- Chưa có `server.js` hoặc code Express thật trong workspace hiện tại.

Vì vậy, giao diện chạy được hiện tại là Streamlit trong `main.py`, không phải React dashboard.

## 13. Luồng xử lý video trong Streamlit

```text
Upload video
    |
    v
Lưu tạm file upload
    |
    v
cv2.VideoCapture đọc từng frame
    |
    v
process_image()
    |
    |-- preprocessing nếu bật
    |-- vehicle detection
    |-- pedestrian detection
    |-- lane detection
    |-- lane segmentation
    |-- traffic sign detection
    |-- tracking
    |-- fusion
    `-- ADAS warning
    |
    v
Vẽ annotation và warning lên frame
    |
    v
Ghi video output bằng codec trình duyệt phát được
    |
    v
st.video hiển thị inline + download_button
```

## 14. Cách chạy

Chạy Streamlit app:
```bash
python -m streamlit run main.py
```

Hoặc:
```bash
streamlit run main.py
```

Kiểm tra GPU support:
```bash
python test_gpu_support.py
```

Cài dependency Python chính:
```bash
cd backend/ai-service
pip install -r requirements.txt
```

## 15. Thống kê repository sau khi lọc placeholder

Sau khi bỏ `.git/`, `__pycache__/`, `.gitkeep` và file 0 byte:
- 281 file có nội dung.
- 47 thư mục có nội dung thật.
- Tổng dung lượng khoảng 353.7 MB.

Theo phần mở rộng:
- `.jpg`: 91
- `.py`: 90
- `.png`: 40
- `.md`: 28
- `.pt`: 12
- `.yaml`: 10
- `.csv`: 3
- `.mp4`: 2
- `.txt`: 2
- `.example`: 1
- `.gitattributes`: 1
- `.gitignore`: 1

## 16. Những phần không đưa vào overview/cây vì rỗng

- `docs/Dashboard Realtime.md` vì file 0 byte.
- `backend/ai-service/evaluation/`.
- `backend/ai-service/traditional_cv/edge_detection/`.
- `backend/ai-service/traditional_cv/lane_detection/`.
- `backend/node-server/controllers/`, `middleware/`, `routes/`, `services/`, `uploads/`.
- `frontend/public/`, `frontend/src/assets/`, `frontend/src/components/`, `frontend/src/services/`.
- `docs/diagrams/`, `docs/proposal/`, `docs/references/`, `docs/slides/`.
- `outputs/predictions/`, `outputs/reports/`, `outputs/screenshots/`.
- Các `__init__.py` 0 byte và toàn bộ `__pycache__/`.

## 17. Tài liệu liên quan

- `README.md`: hướng dẫn tổng quan ở root.
- `GPU_ACCELERATION.md`: hướng dẫn GPU/CUDA.
- `docs/cây thư mục_updated.md`: cây thư mục cập nhật.
- `docs/Phát hiện và cảnh báo xe lệch làn.md`: mô tả lane departure.
- `docs/Traffic Sign Warning.md`: mô tả traffic sign warning.
- `docs/project-state.md`: trạng thái phát triển.
- `docs/report/BAO_CAO_TONG_HOP.md`: báo cáo tổng hợp.

## 18. Kết luận trạng thái

Dự án hiện là demo ADAS chạy được qua Streamlit, với trọng tâm là Python AI pipeline. Các phần model, preprocessing, tracking, fusion và ADAS warning đã có source thực tế. React frontend và Node server hiện mới ở mức scaffold/tài liệu, nên không nên mô tả như module đã triển khai đầy đủ.

Last updated: 2026-07-10.
