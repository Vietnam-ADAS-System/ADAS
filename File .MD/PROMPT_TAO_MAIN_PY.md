# Prompt phụ: Tạo `main.py` — App demo đơn giản có FE (ảnh / video / webcam) — ADAS

> Dùng SAU khi đã chạy xong prompt tích hợp preprocessing (`PROMPT_TICH_HOP_PREPROCESSING.md`). Copy nội dung dưới đây đưa cho Claude Code.

---

Bạn đang làm việc trên project `ADAS`. Sau khi đã tích hợp preprocessing vào 4 module nhận diện (pedestrian, vehicle, lane detection, lane segmentation, traffic sign), giờ tôi cần 1 file `main.py` đặt tại **root project, cùng cấp với `backend/`** (tức `ADAS/main.py`), đóng vai trò 1 app demo đơn giản **có FE** (không phải chỉ chạy CLI/terminal), với 3 chế độ:

1. **Import ảnh** — upload 1 file ảnh qua giao diện, chạy detect, hiển thị + tải về ảnh kết quả.
2. **Import video** — upload 1 file video, chạy detect từng frame, hiển thị + tải về video kết quả.
3. **Quét webcam** — bật webcam ngay trên giao diện, chạy detect real-time, hiển thị trực tiếp.

**Lựa chọn công nghệ FE: dùng Streamlit.** Lý do: chỉ cần viết bằng Python (không cần biết HTML/CSS/JS riêng), có sẵn widget upload file và hiển thị ảnh/video, dựng nhanh, phù hợp app demo nội bộ như này. Không cần dựng FE riêng bằng React/Vue vì project đã có `frontend/` riêng cho mục đích khác — `main.py` chỉ là app demo nhanh, không phải sản phẩm chính thức.

> Nếu môi trường không cài được `streamlit` hoặc bạn (agent) thấy có lý do kỹ thuật không dùng được, báo lại rõ ràng trước khi đổi hướng, đừng tự ý âm thầm chuyển sang CLI thuần.

## Yêu cầu bắt buộc — làm theo đúng thứ tự

### Bước 1: Khảo sát trước khi code
1. Đọc lại 5 file detector đã tích hợp preprocessing ở prompt trước, xác nhận:
   - Tên class/hàm chính để khởi tạo từng detector.
   - Hàm predict nhận input gì (frame numpy, path ảnh...) và trả về gì (boxes, labels, confidence, mask cho segmentation...).
   - Tham số bật/tắt preprocessing đã thêm ở bước trước (tên chính xác).
2. Kiểm tra `backend/ai-service/fusion/` — nếu đã có sẵn logic gộp kết quả từ nhiều model thì tận dụng lại, chưa có thì viết logic gộp đơn giản ngay trong `main.py`.
3. Kiểm tra `outputs/` (predictions, videos, screenshots) xem có sẵn ảnh/video mẫu để test không.
4. Báo cáo lại những gì tìm thấy trước khi code.

### Bước 2: Thiết kế app

**Cách chạy:**

```bash
streamlit run main.py
```

App mở ra trên trình duyệt (`localhost:8501` mặc định). Giao diện gồm:

- **Sidebar (cấu hình chung, áp dụng cho cả 3 chế độ):**
  - Chọn chế độ: radio/selectbox với 3 lựa chọn `Ảnh`, `Video`, `Webcam`.
  - Checkbox chọn module chạy: Pedestrian, Vehicle, Lane, Traffic Sign (mặc định tick hết).
  - Toggle bật/tắt preprocessing (mặc định bật) — để so sánh nhanh có/không.

- **Khu vực chính (thay đổi theo chế độ đã chọn ở sidebar):**
  - **Chế độ Ảnh**: dùng `st.file_uploader` (chấp nhận jpg/png) → sau khi upload, chạy detect → hiển thị ảnh kết quả bằng `st.image` → có nút `st.download_button` để tải ảnh kết quả về.
  - **Chế độ Video**: dùng `st.file_uploader` (chấp nhận mp4) → chạy detect từng frame (có `st.progress` báo tiến độ vì video xử lý lâu) → xử lý xong, hiển thị video kết quả bằng `st.video` → có nút tải về.
  - **Chế độ Webcam**: dùng `st.camera_input` để chụp ảnh từ webcam ngay trên trình duyệt (đơn giản nhất, không cần cài thêm thư viện ngoài) → chạy detect trên ảnh chụp được → hiển thị kết quả.
    - Nếu muốn thử real-time streaming (video liên tục thay vì chụp từng ảnh), có thể dùng thêm thư viện `streamlit-webrtc`, nhưng đây là **tuỳ chọn nâng cao** — chỉ làm nếu `st.camera_input` (chụp ảnh đơn) chạy ổn trước, và phải hỏi lại tôi trước khi thêm dependency mới.

- Hiển thị thêm thông tin cơ bản dưới kết quả: số lượng object detect được theo từng loại, thời gian xử lý (giây) hoặc FPS ước tính.

### Bước 3: Triển khai
- Viết code sạch, có type hint, tách hàm rõ ràng: `load_models()` (dùng `@st.cache_resource` để chỉ load model 1 lần, không load lại mỗi lần tương tác UI), `process_image()`, `process_video()`, `draw_results()`, các hàm render UI theo từng chế độ.
- Load 4 model 1 lần duy nhất, cache lại qua session — Streamlit re-run toàn bộ script mỗi lần người dùng tương tác nên phần load model **bắt buộc** phải cache, không cache sẽ load lại model liên tục rất chậm.
- Xử lý lỗi cơ bản: chưa upload file mà bấm chạy, model load lỗi, file không đúng định dạng — hiển thị `st.error()` rõ ràng trên giao diện, không crash app.
- Thêm `streamlit` vào `requirements.txt`.

### Bước 4: Chạy thử và báo cáo kết quả
- Chạy `streamlit run main.py`, test cả 3 chế độ.
- Ưu tiên dùng ảnh/video mẫu có sẵn trong project (`outputs/`, tập test của từng module) để test chế độ Ảnh/Video.
- Chế độ Webcam có thể không test được trực tiếp trong môi trường agent (không có webcam thật) — nếu vậy, báo rõ là chỉ verify được code logic, cần tôi tự test lại trên máy có webcam.
- Báo cáo lại:
  - Lệnh chạy app.
  - Có lỗi gì không, đã fix thế nào.
  - Output/kết quả hiển thị đúng chưa (kèm mô tả hoặc ảnh chụp nếu có thể).
  - Thời gian xử lý đo được cho ảnh/video mẫu.

### Bước 5: Tài liệu hoá
- Thêm hướng dẫn chạy `main.py` (`streamlit run main.py`, cách dùng từng chế độ trên giao diện) vào `README.md` ở root project.
- Cập nhật `PREPROCESSING_INTEGRATION_PLAN.md` — thêm mục ghi chú là đã có `main.py` (Streamlit app) để demo, kèm đường dẫn và cách chạy.

## Ràng buộc quan trọng
- KHÔNG giả định tên hàm/class — dùng đúng tên đã xác nhận ở Bước 1.
- `main.py` chỉ đóng vai trò orchestration (gọi lại các module có sẵn), KHÔNG viết lại logic detection hay preprocessing.
- Giữ FE đơn giản — chỉ cần Streamlit là đủ, không cần React/Vue riêng, không cần thiết kế UI cầu kỳ, ưu tiên chạy được và rõ ràng hơn là đẹp.
- Không tự ý thêm `streamlit-webrtc` hoặc thư viện nặng khác nếu chưa hỏi lại, trừ khi `st.camera_input` thực sự không đáp ứng được nhu cầu.
- Báo cáo từng bước, đừng im lặng code hết rồi mới báo 1 lần.
