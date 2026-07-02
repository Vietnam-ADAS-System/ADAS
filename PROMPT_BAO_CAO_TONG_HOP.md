# Prompt: Tổng hợp báo cáo toàn bộ các phần đã thực hiện — ADAS

> Copy nội dung dưới đây đưa cho Claude Code (agent đang mở trực tiếp repo `ADAS/`), chạy SAU KHI đã hoàn thành các task theo các prompt trước: tích hợp preprocessing, tạo `main.py` (Streamlit app), tối ưu traffic sign xa, tracking DeepSORT (và bất kỳ task nào khác đã làm thêm).

---

## Bối cảnh

Trong quá trình phát triển ADAS gần đây, đã có nhiều task được thực hiện theo từng prompt riêng, gồm (nhưng không giới hạn):

1. **Tích hợp Preprocessing** vào 4 module nhận diện (pedestrian, vehicle, lane detection, lane segmentation, traffic sign).
2. **App demo `main.py`** dùng Streamlit — hỗ trợ import ảnh, video, quét webcam.
3. **Tối ưu nhận diện Traffic Sign ở khoảng cách xa** — theo 4 hướng: resolution/crop-ROI, tinh chỉnh CLAHE/sharpen, augment data, inference thông minh hơn.
4. **Module Tracking (DeepSORT)** — theo dõi và gán ID ổn định cho xe/người qua nhiều frame.

Mỗi task ở trên đều đã có 1 file `.md` mô tả yêu cầu chi tiết (dùng làm prompt đưa cho agent thực thi). Giờ cần **tổng hợp lại kết quả THỰC TẾ đã làm** (không phải chép lại yêu cầu ban đầu) thành 1 báo cáo đầy đủ, chi tiết.

## Nhiệm vụ

Tạo 1 file **duy nhất** `docs/report/BAO_CAO_TONG_HOP.md` (nếu `docs/report/` chưa tồn tại thì tạo folder này), tổng hợp toàn bộ các phần đã thực hiện, viết dưới dạng báo cáo kỹ thuật chi tiết. **File phải có tối thiểu 150 dòng** — vì đây là báo cáo tổng hợp nhiều hạng mục, nội dung phải đủ chi tiết để đạt độ dài đó một cách tự nhiên (không phải chèn thêm chữ vô nghĩa cho đủ dòng).

## Yêu cầu bắt buộc — làm theo đúng thứ tự

### Bước 1: Thu thập thông tin thật (không được bịa)
1. Nếu project dùng git: chạy `git log --oneline -30` và `git diff` giữa các commit liên quan để biết chính xác file nào đã đổi.
2. Đọc lại toàn bộ các file đã được nhắc tới trong 4 hạng mục ở phần Bối cảnh — xác nhận thực tế đã sửa gì, không dựa vào trí nhớ hay suy đoán từ tên file:
   - `backend/ai-service/preprocessing/` (toàn bộ, gồm cả `enhancement/equalizer.py` nếu có sửa)
   - 5 file detector: `pedestrian_detection/detector.py`, `vehicle_detection/vehicle_detector.py`, `lane_detection/detector.py`, `lane_segmentation/predict.py`, `traffic_sign_detection/predict.py`
   - `traffic_sign_detection/train.py`, `data.yaml` (nếu có thay đổi liên quan augmentation)
   - `backend/ai-service/tracking/` (toàn bộ file mới tạo)
   - `main.py` ở root project
   - `requirements.txt`
   - `README.md`, `PREPROCESSING_INTEGRATION_PLAN.md`, `docs/project-state.md`, `docs/changelog.md` (nếu đã được cập nhật ở các task trước)
3. Với mỗi hạng mục, nếu phát hiện **task đó thực ra chưa được code** (chỉ mới có prompt yêu cầu nhưng chưa thực thi), phải ghi nhận đúng thực tế — không báo cáo như đã hoàn thành.

### Bước 2: Cấu trúc nội dung báo cáo (bắt buộc đủ các phần sau)

```markdown
# Báo cáo tổng hợp — Hệ thống ADAS

**Ngày cập nhật:** <ngày thực tế>
**Người/agent thực hiện:** <ghi rõ là AI coding agent thực hiện theo yêu cầu>
**Phạm vi báo cáo:** Tổng hợp 4 hạng mục: Preprocessing Integration, App demo main.py, Tối ưu Traffic Sign xa, Tracking DeepSORT

## 1. Tóm tắt điều hành (Executive Summary)
(5-8 câu, người đọc lướt qua hiểu ngay bức tranh tổng thể: đã làm gì, kết quả chính, còn thiếu gì)

## 2. Sơ đồ phụ thuộc giữa các hạng mục
(Mô tả ngắn gọn quan hệ: Tracking -> Fusion -> Cảnh báo -> Dashboard -> Đánh giá, và các hạng mục đã làm nằm ở đâu trong chuỗi này)

## 3. Chi tiết từng hạng mục

### 3.1 Tích hợp Preprocessing
- Mục tiêu ban đầu
- File đã sửa (đường dẫn đầy đủ, chính xác)
- Nội dung thay đổi cụ thể (mô tả kỹ thuật: tham số, logic, config)
- Kết quả benchmark trước/sau (số liệu thật)
- Vấn đề phát sinh (nếu có)
- Trạng thái: Hoàn thành / Hoàn thành một phần / Chưa thực hiện

### 3.2 App demo main.py (Streamlit)
- Chức năng đã triển khai (3 chế độ, các option UI)
- File liên quan
- Cách chạy, kết quả test thực tế
- Vấn đề phát sinh
- Trạng thái

### 3.3 Tối ưu Traffic Sign khoảng cách xa
- Từng hướng đã thử (resolution/crop, CLAHE tuning, data augmentation, inference nâng cao)
- Tham số cụ thể (giá trị cũ → giá trị mới)
- Kết quả benchmark từng hướng
- Hướng nào hiệu quả nhất, hướng nào chưa có cải thiện rõ
- Trạng thái

### 3.4 Module Tracking (DeepSORT)
- Kiến trúc đã triển khai (thư viện dùng, cấu trúc file)
- Cách hoạt động (input/output format)
- Kết quả test: có bị identity switch không, FPS đo được
- Trạng thái

## 4. Bảng tổng hợp file bị ảnh hưởng
(Bảng: đường dẫn file | loại thay đổi [Mới/Sửa] | hạng mục liên quan | mô tả ngắn 1 dòng)

## 5. Bảng tổng hợp kết quả benchmark
(Bảng so sánh trước/sau cho từng hạng mục có đo được số liệu: accuracy/mAP, FPS, confidence score...)

## 6. Vấn đề còn tồn đọng / chưa hoàn thành
(Liệt kê rõ từng việc, kèm lý do chưa làm hoặc đang chờ quyết định gì)

## 7. Đề xuất bước tiếp theo
(Dựa trên timeline hệ thống: Fusion, Cảnh báo lệch làn, Cảnh báo biển báo, Dashboard, Đánh giá — hạng mục nào nên làm kế tiếp và vì sao)

## 8. Phụ lục — Ghi chú kỹ thuật bổ sung
(Bất kỳ chi tiết kỹ thuật nào không tiện đưa vào phần chính nhưng cần lưu lại, ví dụ quyết định thiết kế, trade-off đã cân nhắc)
```

### Bước 3: Nguyên tắc viết nội dung
- Viết tiếng Việt, giọng báo cáo kỹ thuật — rõ ràng, khách quan.
- Thuật ngữ kỹ thuật (function, parameter, endpoint, model, inference, FPS, mAP...) giữ nguyên tiếng Anh.
- Mọi số liệu phải lấy từ kết quả benchmark thật đã chạy ở các bước trước — không có số liệu thật thì ghi "chưa đo được", tuyệt đối không bịa số.
- Đường dẫn file chính xác tuyệt đối theo cấu trúc repo thật.
- Độ dài tự nhiên từ nội dung thật — nếu 1 hạng mục nào đó ít thay đổi thực tế, phần đó ngắn cũng được, không cố kéo dài giả tạo; tổng thể cả file đạt tối thiểu 150 dòng nhờ có đủ 4 hạng mục + các bảng tổng hợp + phần đề xuất, không phải nhờ nhồi chữ.

### Bước 4: Kiểm tra chéo trước khi hoàn thiện
- Đối chiếu lại từng mục với code thật lần nữa.
- Đếm số dòng file cuối cùng (`wc -l docs/report/BAO_CAO_TONG_HOP.md`), xác nhận đạt tối thiểu 150 dòng. Nếu chưa đạt, bổ sung thêm chi tiết THẬT (ví dụ giải thích kỹ hơn về quyết định thiết kế, thêm ví dụ code snippet ngắn minh hoạ thay đổi quan trọng) — không thêm nội dung lặp lại hoặc rỗng.
- Nếu phát hiện điểm nào giữa yêu cầu ban đầu (trong các file prompt) và code thực tế có sự khác biệt, phải nêu rõ trong báo cáo.

## Ràng buộc quan trọng
- **Chỉ kết nối và chỉnh sửa** — không tạo file code mới trong lúc làm báo cáo này; đây là task chỉ đọc và viết báo cáo, không sửa logic hệ thống.
- **Không tạo markdown vô tội vạ** — chỉ tạo đúng 1 file `docs/report/BAO_CAO_TONG_HOP.md` như yêu cầu, không tự ý tạo thêm file `.md` phụ nào khác (kể cả file nháp/draft).
- **Cleanup sau khi hoàn thành** — nếu trong lúc thu thập thông tin (Bước 1) có tạo script tạm để chạy `git diff`/đếm dòng/kiểm tra, xoá đi sau khi dùng xong, không để lại trong repo.
- Đây là báo cáo dùng để người khác tin tưởng và ra quyết định tiếp theo — độ chính xác quan trọng hơn độ dài hay độ "đẹp". Thà thiếu còn hơn sai.
- Sau khi tạo xong, in ra đường dẫn file và số dòng thực tế để tôi kiểm tra lại.
