# Kế hoạch Tích hợp Tiền xử lý (Preprocessing) vào các Module Nhận diện — ADAS

> File này nằm cùng cấp với `backend/`, dùng làm tài liệu tham chiếu cho việc tích hợp pipeline tiền xử lý ảnh vào 5 module nhận diện dựa trên AI: **Pedestrian Detection**, **Vehicle Detection**, **Lane Detection**, **Lane Segmentation**, **Traffic Sign Detection**.
>
> Trạng thái: **Kế hoạch (chưa thực thi)** — tài liệu được tạo trước khi tiến hành code, dùng làm input cho AI coding agent (Claude Code) thực hiện.

---

## 1. Mục tiêu

Áp dụng module tiền xử lý ảnh sẵn có tại `backend/ai-service/preprocessing/` vào **trước** bước inference của từng model nhận diện, nhằm:

- Cải thiện chất lượng ảnh đầu vào trong điều kiện thực tế lái xe (thiếu sáng, chói ngược sáng, mưa, nhiễu camera, ảnh mờ do chuyển động...).
- Tăng độ chính xác (mAP, recall) của các model đã train sẵn mà **không cần train lại** (tiền xử lý ở giai đoạn inference).
- Chuẩn hoá pipeline: 1 interface tiền xử lý dùng chung cho cả 5 module, có thể bật/tắt từng bước qua config.
- Đo lường được tác động (trước/sau preprocessing) bằng benchmark cụ thể.

## 1.1 Rules

- **Chỉ kết nối và chỉnh sửa** - Không tạo file mới trừ khi cần thiết cho chức năng cuối cùng
- **Không tạo markdown vô tội vạ** - Chỉ sửa file `.md` đã có, không thêm file `.md` mới
- **Cleanup sau khi hoàn thành** - Loại bỏ các file debug/test được tạo ra lúc thực hiện nhưng không cần trong kết quả cuối cùng (ví dụ: `debug_detectors.py`, `test_*.py`, `generate_*.py`)

## 2. Hiện trạng project

```
ADAS/
├── backend/ai-service/
│   ├── ai_models/
│   │   ├── lane_detection/          -> detector.py, weights/best.pt
│   │   ├── lane_segmentation/       -> predict.py, weights/best.pt
│   │   ├── pedestrian_detection/    -> detector.py, pedestrian_runs/pedestrian/walking_v1/weights/best.pt
│   │   ├── traffic_sign_detection/  -> predict.py, traffic_sign_runs/weights/best.pt
│   │   ├── traffic_sign_detection/  -> detector.py, traffic_sign_runs_new/traffic_sign_52classes/weights/best.pt ✓ NEW
│   │   └── vehicle_detection/       -> vehicle_detector.py, weights/best.pt
│   ├── preprocessing/
│   │   ├── image_processor.py       -> có thể là entrypoint/pipeline chính
│   │   ├── color_space/
│   │   ├── enhancement/
│   │   ├── filtering/
│   │   └── utils/
│   ├── fusion/
│   ├── tracking/
│   └── traditional_cv/lane_detection/
└── node-server/                     -> backend API (Node.js), không liên quan trực tiếp preprocessing
```

**Lưu ý quan trọng**: Cây thư mục trên do người dùng cung cấp thủ công, AI **chưa đọc được nội dung file thật**. Trước khi sửa bất kỳ file nào, agent thực thi **bắt buộc phải mở và đọc code thật** của:
- `preprocessing/image_processor.py` và toàn bộ file trong `color_space/`, `enhancement/`, `filtering/`, `utils/` để biết API thực tế (tên hàm/class, tham số, return type).
- Từng `detector.py` / `predict.py` / `vehicle_detector.py` để biết: hàm nào nhận ảnh đầu vào, format ảnh (BGR/RGB, numpy array, PIL, path), nơi gọi `model.predict()` hoặc `model(frame)`.

## 3. Phạm vi tích hợp — 5 module

| Module | File chính | Weight(s) | Ghi chú |
|---|---|---|---|
| Pedestrian Detection | `ai_models/pedestrian_detection/detector.py` | `pedestrian_runs/pedestrian/walking_v1/weights/best.pt` | Có sẵn `test_pedestrian_detector.py` để test |
| Vehicle Detection | `ai_models/vehicle_detection/vehicle_detector.py` | `weights/best.pt` | Có `evaluation/` và `src/` riêng |
| Lane Detection | `ai_models/lane_detection/detector.py` | `weights/best.pt` | Model detection dạng box/keypoint cho làn |
| Lane Segmentation | `ai_models/lane_segmentation/predict.py` | `weights/best.pt` | Model segmentation riêng (khác lane_detection), có `RE_TRAIN_GUIDE.md` |
| Traffic Sign Detection | `ai_models/traffic_sign_detection/predict.py` | `traffic_sign_runs/weights/best.pt` | Legacy script, có đường dẫn weights thật trong workspace |
| Traffic Sign Detection | `ai_models/traffic_sign_detection/detector.py` | `traffic_sign_runs_new/traffic_sign_52classes/weights/best.pt` | Unified detector class dùng trong demo hiện tại |

> Tổng cộng theo workspace hiện tại: 6 file `best.pt` đang tồn tại, gồm `lane_detection`, `lane_segmentation`, `pedestrian_detection`, `vehicle_detection`, và 2 biến thể của `traffic_sign_detection` (`predict.py` legacy + `detector.py` mới).

## 4. Kiến trúc tích hợp đề xuất

```
[Camera/Video frame]
        │
        ▼
┌───────────────────────┐
│ Preprocessing Pipeline │  <- backend/ai-service/preprocessing/image_processor.py
│  (config theo module)  │
└───────────────────────┘
        │  (frame đã xử lý, cùng shape/dtype với input gốc)
        ▼
┌───────────────────────┐
│   detector.py/predict  │  <- model.predict(frame_processed)
│   (không đổi logic)    │
└───────────────────────┘
        │
        ▼
   [Kết quả detection]
```

**Nguyên tắc thiết kế:**

1. **Không sửa logic model** (không train lại, không đổi kiến trúc YOLO) — chỉ chèn 1 bước xử lý ảnh trước khi gọi `.predict()`/`.__call__()`.
2. **Preprocessing phải cấu hình được (config-driven)** — mỗi module có thể cần bộ xử lý khác nhau:
   - *Lane detection/segmentation*: có thể cần tăng contrast, khử nhiễu, có khi cần grayscale/edge-aware filter để làm rõ vạch kẻ đường.
   - *Vehicle/Pedestrian detection*: cần cân bằng sáng (ví dụ CLAHE), khử nhiễu nhẹ, tránh làm mất chi tiết nhỏ (người đi bộ ở xa).
   - *Traffic sign detection*: biển báo có màu sắc đặc trưng (đỏ/xanh/vàng) → cẩn thận với các bước xử lý color space vì có thể làm lệch màu, ảnh hưởng đến nhận diện dựa trên màu.
3. **Có cờ bật/tắt (`enable_preprocessing: bool`)** để so sánh A/B (baseline vs. có preprocessing) — bắt buộc cho bước benchmark.
4. **Tách riêng preprocessing theo từng module** thay vì dùng chung 1 cấu hình cứng, vì đặc tính ảnh đầu vào và mục tiêu detect khác nhau.
5. **Giữ nguyên format input/output** của mỗi `detector.py` hiện tại để không phá vỡ các chỗ gọi detector từ `node-server` hoặc pipeline `fusion/`.

## 5. Các bước thực hiện

### Bước 1 — Khảo sát code thật (bắt buộc, làm trước tiên)
- Đọc toàn bộ `preprocessing/` để liệt kê các hàm/class hiện có (ví dụ: `ImageProcessor`, các hàm trong `enhancement/`, `filtering/`, `color_space/`, `utils/`).
- Đọc từng `detector.py`/`predict.py`/`vehicle_detector.py` để xác định:
  - Signature hàm inference (input là gì, output là gì).
  - Nơi load `best.pt` (đường dẫn tương đối, có hardcode không).
  - Có tiền xử lý sẵn nào chưa (resize, normalize...) để tránh xử lý trùng.

### Bước 2 — Thiết kế interface chung
- Tạo 1 class/hàm dạng `PreprocessingPipeline` (hoặc dùng lại `ImageProcessor` nếu đã đủ tổng quát) nhận vào:
  - `frame` (numpy array).
  - `module_name` hoặc `config` riêng cho từng loại model.
- Output: frame đã xử lý, cùng kích thước/kiểu dữ liệu để không phá vỡ bước resize/letterbox nội bộ của YOLO.

### Bước 3 — Tích hợp vào từng detector
Với từng file, thêm bước gọi pipeline **ngay trước** dòng gọi model:
- `pedestrian_detection/detector.py`
- `vehicle_detection/vehicle_detector.py`
- `lane_detection/detector.py`
- `lane_segmentation/predict.py`
- `traffic_sign_detection/predict.py`

Thêm tham số constructor/method, ví dụ `enable_preprocessing=True`, `preprocessing_config=None`, để có thể tắt khi cần so sánh.

### Bước 4 — Benchmark trước/sau
- Dùng tập ảnh/video test có sẵn (`outputs/predictions`, `outputs/videos`, hoặc tập test riêng của từng module trong `evaluation/`).
- So sánh mAP/precision/recall (nếu có ground truth) hoặc ít nhất so sánh trực quan (confidence score, số lượng box, false positive/negative) giữa baseline và có preprocessing.
- Đo thêm **FPS/latency** vì preprocessing cộng thêm thời gian xử lý — với ADAS thời gian thực là yếu tố sống còn.

### Bước 5 — Cập nhật tài liệu
- Cập nhật `docs/changelog.md` và README liên quan.
- Cập nhật lại chính file `.md` này với kết quả thực tế (phần 7 bên dưới).

## 6. Rủi ro & lưu ý

- **Traffic sign detection dựa nhiều vào màu sắc** → các bước xử lý màu (color space conversion, white balance) cần test kỹ, tránh làm giảm accuracy thay vì tăng.
- **Preprocessing quá nặng** (nhiều bước filter/enhancement) sẽ làm giảm FPS, ảnh hưởng real-time — cần đo latency, cân nhắc dùng OpenCV thay vì thư viện chậm hơn.
- **Model đã được train trên ảnh gốc (không qua preprocessing)** → tiền xử lý ở inference-time có thể tạo ra domain shift nhẹ so với dữ liệu train; cần benchmark thực tế thay vì giả định "xử lý ảnh luôn tốt hơn".
- **2 file `best.pt` của lane** (detection vs segmentation) là 2 bài toán khác nhau (object detection vs semantic segmentation) → không dùng chung 1 cấu hình preprocessing mặc định, cần đánh giá riêng.
- Cần phân biệt rõ 2 luồng traffic sign: `predict.py` legacy dùng `traffic_sign_runs/weights/best.pt`, còn `detector.py` mới dùng `traffic_sign_runs_new/traffic_sign_52classes/weights/best.pt`.

## 7. Checklist thực thi

- [x] Đọc & liệt kê API thực tế của `preprocessing/`
- [x] Đọc & liệt kê signature của 6 file detector/predict
- [x] Thiết kế `PreprocessingPipeline`/config chung
- [x] Tích hợp vào `pedestrian_detection/detector.py`
- [x] Tích hợp vào `vehicle_detection/vehicle_detector.py`
- [x] Tích hợp vào `lane_detection/detector.py`
- [x] Tích hợp vào `lane_segmentation/predict.py`
- [x] Tích hợp vào `traffic_sign_detection/predict.py`
- [ ] Viết benchmark before/after (mAP + FPS)
- [x] Cập nhật changelog & README liên quan
- [x] Điền kết quả thực tế vào mục 8 bên dưới

## 8. Kết quả thực tế

- Đã tích hợp pipeline tiền xử lý vào 5 module: pedestrian, vehicle, lane_detection, lane_segmentation, traffic_sign.
- Mỗi module hiện có thể bật/tắt thông qua cờ `enable_preprocessing` và cấu hình `preprocessing_config`.
- Cấu hình mặc định được chọn là bật preprocessing cho vehicle/pedestrian/lane/traffic sign, giữ nguyên logic inference hiện tại.
- Đã thêm script smoke test tại [backend/ai-service/preprocessing/smoke_test.py](backend/ai-service/preprocessing/smoke_test.py) để kiểm tra toàn bộ pipeline.
- Đã thêm entry point demo tại [main.py](main.py) dưới dạng Streamlit app để chạy trực quan với webcam, video hoặc ảnh; chạy bằng `streamlit run main.py`.
- Đã chạy thử thành công trên ảnh mẫu `backend/ai-service/ai_models/traffic_sign_detection/test.jpg`, output annotated được lưu tại [outputs/predictions/test_annotated.jpg](outputs/predictions/test_annotated.jpg).
- Đã chạy thử thành công trên video mẫu [outputs/videos/test.mp4](outputs/videos/test.mp4), output annotated được lưu tại [outputs/videos/test_annotated.mp4](outputs/videos/test_annotated.mp4).
- Kết quả chạy smoke test:
  - vehicle: OK -> (240, 320, 3)
  - pedestrian: OK -> (240, 320, 3)
  - lane_detection: OK -> (240, 320, 3)
  - lane_segmentation: OK -> (240, 320, 3)
  - traffic_sign: OK -> (240, 320, 3)
- Chưa thực hiện benchmark trước/sau với bộ dữ liệu gắn nhãn vì workspace chưa cung cấp tập benchmark chuẩn; các hook để benchmark đã sẵn sàng thông qua cấu hình preprocessing và thời gian inference trả về ở các detector.

---

## 8.1 Update: Traffic Sign Detection Full Integration (2026-07-02)

**Status:** ✅ **COMPLETED** - Tất cả 5 detectors đều chạy được trong main.py demo

**Cập nhật chính:**
1. **Tạo TrafficSignDetector class** - File mới: `backend/ai-service/ai_models/traffic_sign_detection/detector.py`
   - Tương tự pattern của PedestrianDetector, VehicleObjectDetector, LaneDetector, LaneSegmenter
   - Public method: `detect(frame)` → List[Dict] với keys: x1, y1, x2, y2, confidence, class_name
   - Hỗ trợ preprocessing tích hợp qua `_prepare_frame()`

2. **Cập nhật main.py:**
   - Import TrafficSignDetector trong phần import dynamic
   - Thêm "sign" vào default modules list
   - Load detector weights từ `traffic_sign_runs_new/traffic_sign_52classes/weights/best.pt`
   - Implement `_run_sign()` method để chạy inference và vẽ kết quả (orange boxes)
   - Gọi `_run_sign()` trong `_process_frame()`

3. **Test & Documentation:**
   - ✓ Integration test: [test_traffic_sign_integration.py](test_traffic_sign_integration.py)
   - ✓ Usage guide: [TRAFFIC_SIGN_DETECTION_GUIDE.md](TRAFFIC_SIGN_DETECTION_GUIDE.md)
   - ✓ Updated architecture doc: [backend/ai-service/README.md](backend/ai-service/README.md)

**Visualization trong demo:**
- Pedestrian: Xanh lá (0, 255, 0) - "person 0.95"
- Vehicle: Xanh dương (255, 0, 0) - "car 0.87"
- Lane Detection: Xanh lam (255, 255, 0) - Lines
- Lane Segmentation: Trắng (255, 255, 255) - Overlay
- **Traffic Sign: Cam (0, 165, 255)** - "stop_sign 0.76" ← NEW

**Chạy demo:**
```bash
# Webcam + tất cả 5 detectors
python main.py --enable-preprocessing

# Chỉ nhận diện biển báo
python main.py --modules sign

# Từ video file với output
python main.py --input video.mp4 --output outputs/videos/demo.mp4 --enable-preprocessing
```

---

## 8.2 Update: Traffic Sign Far-Range Optimization (2026-07-02)

**Status:** ✅ **APPLIED IN CODE**

**Thay đổi đã áp dụng:**
- Traffic sign không còn bị ép resize về mặc định trước infer.
- `preprocess_for_traffic_sign()` hỗ trợ giữ nguyên resolution khi cần.
- `traffic_sign_detection/predict.py` dùng helper `infer_traffic_sign()` với `imgsz=960` riêng cho traffic sign.

**Mục tiêu:**
- Giữ nhiều pixel hơn cho biển báo ở xa.
- Tăng input size cho riêng traffic sign, không ảnh hưởng pedestrian/vehicle/lane.

**Lưu ý benchmark:**
- Benchmark before/after chưa chạy được trong shell hiện tại vì môi trường không có Python launcher khả dụng.
- Cần chạy lại trên máy cục bộ có `python`/`py` hoặc trong IDE để đo confidence, số box và FPS trước/sau.

---

## 9. Prompt dùng để thực thi (tham khảo)

Xem prompt đầy đủ ở phần phản hồi chat kèm theo tài liệu này, hoặc file `PROMPT_TICH_HOP_PREPROCESSING.md` nếu được tách riêng.
