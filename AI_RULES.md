# BẢN NGUYÊN TẮC LÀM VIỆC DÀNH CHO AI (AI_RULES.md)

## 🎯 PHẠM VI CÔNG VIỆC HIỆN TẠI (CONTEXT FOCUS)
Bạn chỉ được phép tập trung hỗ trợ và xử lý các phần liên quan đến bài toán **Nhận diện biển báo giao thông (Traffic Sign Detection)**. Tuyệt đối KHÔNG tự ý sửa đổi hoặc can thiệp vào các module Vehicle Detection hay Lane Segmentation trừ khi có yêu cầu cụ thể.

Các đường dẫn thư mục được phép can thiệp:
- `backend/ai-service/preprocessing/` (Script tiền xử lý dữ liệu)
- `backend/ai-service/ai_models/traffic_sign_detection/` (Huấn luyện và lưu cấu hình YOLO11)
- `datasets/traffic_sign/` (Nơi chứa nhãn và ảnh thô)
- `frontend/src/pages/TrafficSign.jsx` và `frontend/src/components/TrafficSignPanel` (Giao diện)

---

## 🚫 NGUYÊN TẮC 1: CHỐNG XÓA VÀ MẤT CODE (ANTI-DELETION)
1. **Không viết code tắt/code giả:** TUYỆT ĐỐI KHÔNG sử dụng các đoạn comment như `// ... rest of code`, `# ... giữ nguyên phần cũ`. Khi cập nhật file, phải viết đầy đủ hoặc chỉ ra block code chính xác cần thay thế.
2. **Không tự ý xóa hàm:** Không được xóa bất kỳ hàm tiền xử lý (CVIP) nào có sẵn trong mục `preprocessing/` (ví dụ: CLAHE, Gaussian Blur) khi tạo module mới.
3. **Sao lưu trước khi ghi đè:** Nếu sửa đổi một file logic phức tạp, hãy yêu cầu người dùng xác nhận hoặc đề xuất tạo file version phụ (ví dụ: `script_v2.py`).

---

## 💸 NGUYÊN TẮC 2: TIẾT KIỆM TOKEN TUYỆT ĐỐI (TOKEN OPTIMIZATION)
1. **KHÔNG ĐỌC FILE DATA LỚN:** Nghiêm cấm AI đọc trực tiếp file `datasets/traffic_sign/train_traffic_sign_dataset.json` hoặc `annotation.csv`. Kích thước các file này quá lớn sẽ làm cạn kiệt Context Window.
2. **Lập trình dựa trên Snippet mẫu:** Chỉ yêu cầu người dùng cung cấp tối đa 3-5 dòng cấu trúc dữ liệu mẫu (JSON/CSV) dưới dạng text trong ô chat để hiểu cấu trúc nhãn, từ đó viết code parse dữ liệu.
3. **Phản hồi ngắn gọn:** Đi thẳng vào giải pháp code, loại bỏ các câu chào hỏi rườm rà, giải thích lý thuyết dông dài không cần thiết.

---

## 🛠️ HƯỚNG DẪN LUỒNG XỬ LÝ BIỂN BÁO GIAO THÔNG CHO AI

### Bước 1: Tiền xử lý dữ liệu (Data Pipeline)
- Sử dụng cấu trúc mẫu từ `datasets/traffic_sign/train_traffic_sign_dataset.json` (định dạng COCO).
- Viết script Python đặt vào `backend/ai-service/preprocessing/process_traffic_sign.py` để:
  1. Đọc ảnh từ `datasets/traffic_sign/raw_images/`.
  2. Chuyển đổi tọa độ `bbox` từ COCO `[x, y, w, h]` sang định dạng YOLO đã normalized `[class_id, x_center, y_center, w, h]`.
  3. Chia tập dữ liệu (80% Train / 20% Val) và xuất ra cấu trúc thư mục `datasets/traffic_sign/images/` và `datasets/traffic_sign/labels/`.

### Bước 2: Cấu hình và Huấn luyện (Training Configuration)
- Tạo file cấu hình `data.yaml` đặt tại: `backend/ai-service/ai_models/traffic_sign_detection/data.yaml`.
- Nội dung file sinh ra bắt buộc phải tuân theo cấu trúc relative path chính xác:
  ```yaml
  path: ../../../../datasets/traffic_sign
  train: images/train
  val: images/val
  nc: 6
  names:
    0: Cam nguoc chieu
    1: Cam dung va do
    2: Cam re
    3: Gioi han toc do
    4: Cam con lai
    5: Hieu lenh


    # AI Project Rules

## Mandatory Workflow

For every completed task, AI MUST update documentation.

Workflow:

User Requirement
→ Features
→ Tech Solutions
→ Logic + AI
→ Implementation
→ Testing

---

## Documentation Policy

Whenever AI creates or modifies:

* Feature
* API
* Database
* Prompt
* Agent Skill
* Memory
* Knowledge Base
* Business Logic
* UI
* Backend Service

AI MUST update corresponding markdown files.

Documentation is not optional.

---

## Completion Definition

A task is considered DONE only when:

1. Source code completed
2. Documentation updated
3. Tests added
4. Changelog updated

Otherwise status = INCOMPLETE



LƯU Ý QUAN TRỌNG TẤT CẢ FILE md ĐIỀU PHẢI ĐƯỢC VIẾT BẰNG TIẾNG VIỆT 