# Prompt phụ: Tạo `main.py` (entry point demo) — ADAS

> Dùng SAU khi đã chạy xong prompt tích hợp preprocessing (`PROMPT_TICH_HOP_PREPROCESSING.md`). Copy nội dung dưới đây đưa cho Claude Code.
>
> Trạng thái hiện tại: `main.py` ở root project đã được tạo. Dùng prompt này để tiếp tục hoàn thiện, rà lỗi hoặc mở rộng demo runner nếu cần.

---

Bạn đang làm việc trên project `ADAS`. Sau khi đã tích hợp preprocessing vào 5 module nhận diện (pedestrian, vehicle, lane detection, lane segmentation, traffic sign), giờ tôi cần `main.py` ở **root project, cùng cấp với `backend/`** (`ADAS/main.py`) để chạy thử và xem kết quả trực quan.

## Yêu cầu bắt buộc — làm theo đúng thứ tự

### Bước 1: Khảo sát trước khi code
1. Đọc lại 5 luồng detector/entrypoint đã tích hợp preprocessing ở prompt trước, xác nhận:
   - Tên class/hàm chính để khởi tạo từng detector.
   - Hàm predict nhận input gì (frame numpy, path ảnh...) và trả về gì (boxes, labels, confidence, mask cho segmentation...).
   - Tham số bật/tắt preprocessing đã thêm ở bước trước (tên chính xác).
2. Kiểm tra `backend/ai-service/fusion/` — nếu đã có sẵn logic gộp kết quả từ nhiều model (fusion) thì tận dụng lại thay vì viết mới. Nếu chưa có gì hoặc còn rỗng, tự viết logic gộp đơn giản trong `main.py`.
3. Kiểm tra `outputs/` (predictions, videos, screenshots) xem có video/ảnh mẫu sẵn để test không, và convention đặt tên file output hiện tại của project (nếu có) để làm theo cho nhất quán.
4. Báo cáo lại những gì tìm thấy trước khi code.

### Bước 2: Thiết kế `main.py`
File `main.py` cần:
- Nhận input qua CLI argument: đường dẫn video, đường dẫn ảnh, hoặc webcam (mặc định webcam index 0 nếu không truyền gì).
- Có flag `--enable-preprocessing` / `--disable-preprocessing` (mặc định bật) để so sánh nhanh có/không preprocessing.
- Có flag chọn chạy module nào (`--modules pedestrian,vehicle,lane_detection,lane_segmentation,traffic_sign` hoặc mặc định chạy hết).
- Load tất cả detector cần thiết (dùng đúng class/hàm đã xác nhận ở Bước 1), mỗi cái load 1 lần lúc khởi động (không load lại mỗi frame).
- Vòng lặp xử lý từng frame:
  1. Đọc frame từ video/webcam/ảnh.
  2. Chạy qua từng detector đã bật. Preprocessing đã được tích hợp bên trong detector, nên `main.py` chỉ orchestration và không gọi preprocessing thủ công.
  3. Vẽ kết quả lên frame: bounding box + label + confidence cho pedestrian/vehicle/traffic sign; overlay mask hoặc đường lane cho lane detection/segmentation. Mỗi loại object dùng màu khác nhau để dễ phân biệt.
  4. Hiển thị FPS xử lý trung bình lên góc màn hình.
- Hiển thị kết quả:
  - Nếu môi trường có GUI: dùng `cv2.imshow()` để xem real-time, nhấn `q` để thoát.
  - Luôn lưu output ra `outputs/videos/` (nếu input là video/webcam) hoặc `outputs/predictions/` (nếu input là ảnh) — vì môi trường chạy có thể không có GUI (headless server), cần đảm bảo có cách xem lại kết quả kể cả khi không mở được cửa sổ.
  - Tự động phát hiện: nếu `cv2.imshow` lỗi (không có display), fallback về chỉ lưu file, không crash chương trình.
- Có docstring/help rõ ràng khi chạy `python main.py --help`.

### Bước 3: Triển khai
- Viết code sạch, có type hint, tách hàm rõ ràng (load models, process frame, draw results, main loop).
- Xử lý lỗi cơ bản: file input không tồn tại, model load lỗi, webcam không mở được — báo lỗi rõ ràng, không crash im lặng.
- Thêm `requirements.txt` cập nhật nếu `main.py` cần thêm thư viện chưa có (ví dụ `argparse` là built-in, không cần thêm; nhưng nếu dùng thêm lib gì mới thì note lại).

### Bước 4: Chạy thử và báo cáo kết quả
- Chạy thử `main.py` với ít nhất 1 input mẫu có sẵn trong project (ưu tiên video/ảnh có sẵn trong `outputs/` hoặc tập test của từng module).
- Báo cáo lại:
  - Lệnh đã chạy.
  - Có lỗi gì không, đã fix thế nào.
  - Kết quả output nằm ở đâu (đường dẫn file cụ thể).
  - FPS đo được, có đáp ứng real-time không (tham khảo: >15-20 FPS được coi là chấp nhận được cho ADAS demo).

### Kết quả mong muốn tối thiểu sau khi hoàn thiện
- `python main.py --help` hiển thị đầy đủ flag.
- Chạy không tham số sẽ mở webcam 0 và lưu output mặc định vào `outputs/videos/`.
- Chạy với ảnh/video sẽ lưu output vào `outputs/predictions/` hoặc `outputs/videos/` tương ứng.
- Nếu máy không có GUI, chương trình không crash mà vẫn lưu file output.

### Bước 5: Tài liệu hoá
- Thêm hướng dẫn chạy `main.py` vào `README.md` ở root project (cách chạy với webcam, với file video, với ảnh, các flag có sẵn).
- Cập nhật `PREPROCESSING_INTEGRATION_PLAN.md` — thêm mục ghi chú là đã có `main.py` để demo trực quan, kèm đường dẫn.

## Ràng buộc quan trọng
- KHÔNG giả định tên hàm/class — dùng đúng tên đã xác nhận ở Bước 1.
- `main.py` chỉ đóng vai trò orchestration (gọi các module có sẵn), KHÔNG viết lại logic detection hay preprocessing.
- Đảm bảo chạy được cả trường hợp có GUI lẫn không có GUI (server/container).
- Báo cáo từng bước, đừng im lặng code hết rồi mới báo 1 lần.
