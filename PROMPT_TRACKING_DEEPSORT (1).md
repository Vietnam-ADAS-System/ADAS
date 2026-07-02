# Prompt: Triển khai Module Theo dõi (Tracking) bằng DeepSORT — ADAS

> Copy nội dung dưới đây đưa cho Claude Code (agent đang mở trực tiếp repo `ADAS/`).

---

## Bối cảnh

Theo timeline hệ thống ADAS, đây là bước đầu tiên trong chuỗi phụ thuộc:

```
Tracking (DeepSORT) → Fusion → Cảnh báo lệch làn → Cảnh báo biển báo → Dashboard → Đánh giá
```

Tracking phải làm trước vì **Fusion cần biết cùng 1 đối tượng qua nhiều khung hình** — nếu chỉ có detection (mỗi frame detect độc lập), không biết xe/người ở frame N và frame N+1 có phải cùng 1 object hay không, ID bị đổi liên tục thì các bước sau (cảnh báo, dashboard) không thể hoạt động đúng.

**Mục tiêu**: Theo dõi đối tượng qua nhiều frame, gán ID ổn định cho xe và người đi bộ, dùng thuật toán DeepSORT.

**Vị trí code**: `backend/ai-service/tracking/` (hiện đang trống, cần xây từ đầu).

## Yêu cầu bắt buộc — làm theo đúng thứ tự

### Bước 1: Khảo sát trước khi code
1. Đọc `ai_models/vehicle_detection/vehicle_detector.py` và `ai_models/pedestrian_detection/detector.py` — xác nhận:
   - Format output của mỗi detector (bounding box dạng gì: `[x1,y1,x2,y2]` hay `[x,y,w,h]`, có confidence score và class label kèm theo không).
   - Detector trả về theo từng frame hay xử lý cả batch.
2. Kiểm tra `backend/ai-service/tracking/` xem đã có file gì chưa (dù tree ban đầu cho thấy trống, vẫn kiểm tra lại thực tế vì có thể đã có thay đổi từ các task trước).
3. Kiểm tra `requirements.txt` xem đã có sẵn thư viện tracking nào chưa (`deep-sort-realtime`, `motpy`, `filterpy`...).
4. Kiểm tra `fusion/` xem đã có sẵn code nào kỳ vọng input từ tracking theo format cụ thể không (để tracking output đúng format fusion cần, tránh phải sửa lại sau).
5. Báo cáo lại những gì tìm thấy trước khi code.

### Bước 2: Thiết kế module tracking

**Thư viện đề xuất**: dùng package `deep-sort-realtime` (pip) — đây là implementation DeepSORT sẵn có, ổn định, không cần tự viết lại Kalman filter + Hungarian algorithm + feature extractor từ đầu. Nếu agent thấy có lý do kỹ thuật để không dùng (ví dụ conflict dependency), báo lại trước khi đổi hướng.

**Cấu trúc file đề xuất trong `tracking/`:**
```
tracking/
├── __init__.py
├── deepsort_tracker.py    # wrapper class quanh DeepSORT
└── README.md               # giải thích cách dùng module
```

**Thiết kế class `ObjectTracker` (hoặc tên tương tự) trong `deepsort_tracker.py`:**
- Constructor nhận config cơ bản: `max_age` (số frame giữ track khi mất detection), `n_init` (số frame liên tiếp cần detect để confirm 1 track mới), `max_cosine_distance` (ngưỡng matching appearance).
- Method chính `update(detections, frame)`:
  - Input: list các detection ở frame hiện tại (mỗi detection gồm bbox + confidence + class — xe hoặc người), và frame ảnh gốc (DeepSORT cần frame để extract appearance feature).
  - Output: list các track đã được gán ID ổn định, mỗi track gồm: `track_id`, `bbox`, `class` (vehicle/pedestrian), `confidence`.
- Xử lý riêng 2 loại object (vehicle và pedestrian) — có thể dùng 2 tracker instance riêng (1 cho vehicle, 1 cho pedestrian) để tránh nhầm lẫn ID giữa 2 loại, hoặc 1 tracker chung có phân biệt theo class tuỳ theo cách `deep-sort-realtime` hỗ trợ — khảo sát API của thư viện trước khi quyết định.

**Xử lý mất track / object khuất tạm thời:**
- Đảm bảo config `max_age` đủ để giữ ID khi object bị che khuất vài frame (ví dụ xe khác cắt ngang tạm thời) nhưng không quá lớn để tránh giữ ID "ma" quá lâu khi object đã thực sự rời khỏi khung hình.

### Bước 3: Triển khai
- Viết code sạch, có type hint, docstring rõ ràng cho từng method.
- Class `ObjectTracker` phải độc lập, dễ import và gọi từ `main.py` hoặc từ `fusion/` sau này — không phụ thuộc cứng vào cách main.py xử lý video.
- Thêm `deep-sort-realtime` (và các dependency liên quan như `opencv-python`, đã có sẵn) vào `requirements.txt`.
- Viết 1 hàm/script demo nhỏ (`tracking/demo.py` hoặc test riêng) để tự test tracker với 1 video mẫu có sẵn trong `outputs/videos/`, chạy detect (dùng lại vehicle_detector + pedestrian detector đã có) rồi đưa qua tracker, vẽ ID lên video output để kiểm tra bằng mắt ID có ổn định qua các frame không.

### Bước 4: Chạy thử và báo cáo kết quả
- Chạy demo script với video mẫu, xuất video có vẽ track ID.
- Kiểm tra bằng mắt: 1 xe/người đi xuyên suốt video có giữ nguyên ID không, có bị nhảy ID (identity switch) bất thường không.
- Đo thêm FPS/latency của tracking (cộng thêm bao nhiêu so với chỉ detection thuần) — vì ADAS cần real-time.
- Báo cáo lại: file đã tạo, kết quả video demo (đường dẫn), số liệu FPS, có vấn đề gì về identity switch không.

### Bước 5: Tài liệu hoá
- Viết `tracking/README.md` giải thích: cách dùng class `ObjectTracker`, các tham số config, output format (để `fusion/` sau này biết cách dùng lại).
- Cập nhật `PREPROCESSING_INTEGRATION_PLAN.md` hoặc tạo ghi chú riêng trong `docs/project-state.md` (nếu file này đang track tiến độ theo timeline) — đánh dấu module Tracking đã hoàn thành, kèm ngày và kết quả benchmark.

## Ràng buộc quan trọng
- KHÔNG tự ý sửa logic của `vehicle_detector.py` hay `pedestrian_detection/detector.py` — tracking chỉ tiêu thụ output của 2 detector này, không đụng vào detection logic.
- Output format của tracker phải rõ ràng, có docstring, vì đây là input trực tiếp cho bước Fusion tiếp theo — thiết kế sai format ở bước này sẽ phải sửa lại khi làm Fusion.
- Không giả định API của `deep-sort-realtime` — đọc doc/source thật của thư viện trước khi code (agent có thể cần cài thử và đọc docstring/type hint của thư viện).
- Báo cáo từng bước, đừng im lặng code hết rồi mới báo 1 lần.
- **Chỉ kết nối và chỉnh sửa** — không tạo file mới trừ khi thực sự cần thiết cho chức năng cuối cùng (ví dụ `deepsort_tracker.py` là cần thiết, nhưng đừng tạo thêm file phụ không dùng đến).
- **Không tạo markdown vô tội vạ** — chỉ sửa file `.md` đã có sẵn trong repo (như `tracking/README.md` nếu đã tồn tại, hoặc `docs/project-state.md`), không tự ý thêm file `.md` mới ngoài những gì đã được yêu cầu rõ ràng trong prompt này.
- **Cleanup sau khi hoàn thành** — xoá các file debug/test tạo ra trong lúc thực hiện nhưng không cần cho kết quả cuối cùng (ví dụ script thử nghiệm nhanh, file test tạm để kiểm tra API của `deep-sort-realtime`). Giữ lại demo script chính thức đã nêu ở Bước 3, xoá những gì chỉ dùng để debug tạm thời.
