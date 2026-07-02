# Báo cáo tổng hợp — Hệ thống ADAS

**Ngày cập nhật:** 2026-07-02  
**Người/agent thực hiện:** AI coding agent thực hiện theo yêu cầu  
**Phạm vi báo cáo:** Tổng hợp 4 hạng mục: Preprocessing Integration, App demo main.py, Tối ưu Traffic Sign xa, Tracking DeepSORT

## 1. Tóm tắt điều hành (Executive Summary)

Trong khoảnh khắc hiện tại, dự án ADAS đã có những thay đổi thực tế ở cả tầng tiền xử lý ảnh, tầng demo giao diện và tầng theo dõi đối tượng. Điểm nổi bật nhất là module tiền xử lý chung đã được tích hợp vào các detector chính: pedestrian, vehicle, lane detection, lane segmentation và traffic sign. Cấu trúc này cho phép bật/tắt preprocessing thông qua cấu hình và giúp các module inference có thể dùng chung một interface. Ở tầng demo, file root main.py đã được chuyển thành ứng dụng Streamlit hỗ trợ ảnh, video và webcam, cho phép người dùng lựa chọn module và xem kết quả trực quan trên giao diện. Về traffic sign, mã đã được bổ sung các tùy chọn để giữ độ phân giải cao hơn cho ảnh đầu vào và tăng tham số inference phù hợp cho biển báo ở xa. Ở tầng tracking, module DeepSORT đã được thêm vào repo với lớp tracker riêng cho vehicle và pedestrian, cùng fallback IoU khi DeepSORT không sẵn sàng. Tuy nhiên, các benchmark trước/sau chưa được đo bằng bộ dữ liệu gắn nhãn chuẩn trong workspace, nên các kết luận về tăng accuracy vẫn cần được kiểm chứng thêm trên dữ liệu thực tế.

## 2. Sơ đồ phụ thuộc giữa các hạng mục

Các hạng mục đã thực hiện nằm ở các tầng khác nhau của pipeline ADAS, nhưng chúng có sự liên kết chặt chẽ. Khung xử lý tổng thể có thể hiểu như sau: camera/video frame đi vào preprocessing để chuẩn hoá chất lượng ảnh, sau đó các detector thực hiện phát hiện đối tượng/làn đường/biển báo, kết quả được đưa vào tracking để gán ID ổn định, rồi tiếp tục đi vào fusion và cảnh báo. Trong sơ đồ này, preprocessing là tầng nền cho tất cả detector, main.py là giao diện demo để chạy trực quan đầu vào/đầu ra, traffic sign optimization là cải tiến cho một detector cụ thể, và DeepSORT là tầng trung gian trước fusion. Tức là tracking không thay thế được detector, mà dựa trên kết quả phát hiện của detector để tạo chuỗi hành vi ổn định qua nhiều frame.

## 3. Chi tiết từng hạng mục

### 3.1 Tích hợp Preprocessing
- Mục tiêu ban đầu: chuẩn hoá pipeline ảnh trước inference cho 5 module nhận diện, giảm ảnh hưởng của điều kiện ánh sáng và nhiễu, đồng thời tạo interface bật/tắt preprocessing để so sánh baseline và phiên bản đã cải tiến.
- File đã sửa: backend/ai-service/preprocessing/image_processor.py, backend/ai-service/preprocessing/enhancement/equalizer.py, backend/ai-service/ai_models/pedestrian_detection/detector.py, backend/ai-service/ai_models/vehicle_detection/vehicle_detector.py, backend/ai-service/ai_models/lane_detection/detector.py, backend/ai-service/ai_models/lane_segmentation/predict.py, backend/ai-service/ai_models/traffic_sign_detection/predict.py.
- Nội dung thay đổi cụ thể: module ImageProcessor được triển khai như entry point chung cho preprocessing. Trong file đó có các pipeline riêng cho vehicle/pedestrian, lane detection/segmentation, traffic sign và tracking. Vehicle/pedestrian dùng gaussian filter + CLAHE, lane dùng grayscale/hsv/clahe/gaussian, traffic sign dùng CLAHE mạnh hơn để tăng độ tương phản, tracking dùng histogram equalization để ổn định brightness. Các detector đã thêm tham số enable_preprocessing và preprocessing_config, và gọi processor.apply_module_preprocessing ngay trước khi gọi model.predict hoặc model(...). Trong equalizer.py, hàm clahe và histogram_equalization được triển khai bằng OpenCV bằng cách dùng cv2.createCLAHE và chuyển đổi màu YCrCb/LAB.
- Kết quả benchmark trước/sau: trong workspace hiện tại chưa có bộ benchmark chuẩn với ground truth để đo accuracy/mAP trước/sau preprocessing. Các file CSV training metrics hiện có ở các thư mục evaluation/train results chỉ phản ánh quá trình training, không phải benchmark inference trước/sau. Vì vậy, số liệu thực tế về mAP, precision, recall trước/sau preprocessing chưa được ghi nhận trong repo.
- Vấn đề phát sinh: preprocessing làm tăng độ phức tạp xử lý, có thể làm giảm FPS nếu dùng nhiều bước nâng cao. Ngoài ra, traffic sign dựa nhiều vào màu sắc nên việc tăng contrast phải được kiểm thử cẩn thận để không làm lệch lớp màu quan trọng.
- Trạng thái: Hoàn thành một phần. Phần tích hợp code đã có mặt và dùng được, nhưng phần benchmark trước/sau chưa được thực hiện đầy đủ với dữ liệu chuẩn.

### 3.2 App demo main.py (Streamlit)
- Chức năng đã triển khai: file root main.py đã được xây dựng như ứng dụng Streamlit với 3 chế độ: Ảnh, Video và Webcam. Trong sidebar có toggle bật/tắt preprocessing và checkbox chọn từng module: pedestrian, vehicle, lane detection, lane segmentation, traffic sign. Giao diện hỗ trợ upload ảnh/video, xem kết quả được annotate trực tiếp, hiển thị số lượng phát hiện và FPS tính được cho từng frame. Ở chế độ video, app cũng xuất ra video đã annotate và cho phép tải về. Ở chế độ webcam, app dùng st.camera_input để chụp ảnh và hiển thị kết quả ngay sau đó.
- File liên quan: main.py, backend/ai-service/ai_models/pedestrian_detection/detector.py, backend/ai-service/ai_models/vehicle_detection/vehicle_detector.py, backend/ai-service/ai_models/lane_detection/detector.py, backend/ai-service/ai_models/lane_segmentation/predict.py, backend/ai-service/ai_models/traffic_sign_detection/predict.py, backend/ai-service/preprocessing/image_processor.py.
- Cách chạy, kết quả test thực tế: README đã ghi lệnh streamlit run main.py. Từ cấu trúc code, app có thể load models từ các file weights có trong repo và chạy trên ảnh/video/webcam. Tuy nhiên, trong môi trường hiện tại chưa có báo cáo chạy thành công đầy đủ với đầu vào thật được ghi lại trong repo; vì vậy, cách chạy là có sẵn, nhưng kết quả runtime thực tế chưa được lưu thành artifact benchmark riêng trong workspace.
- Vấn đề phát sinh: app phụ thuộc vào các thư viện ultralytics, opencv, streamlit và weights thực tế. Nếu môi trường thiếu dependency hoặc không có file weights phù hợp thì app sẽ không khởi động đúng như kỳ vọng. Ngoài ra, webcam mode phụ thuộc vào browser/client, nên không thể kiểm thử tự động trong terminal ở mọi môi trường.
- Trạng thái: Hoàn thành. Code demo đã có và cấu trúc UI/logic đầy đủ cho 3 chế độ.

### 3.3 Tối ưu Traffic Sign khoảng cách xa
- Từng hướng đã thử: trong code hiện có, có 4 hướng được thể hiện rõ thông qua cấu hình và logic: (1) điều chỉnh input size / crop-ROI thông qua các tham số imgsz và khả năng không ép resize trong preprocessing, (2) tăng contrast bằng CLAHE (clip_limit 3.0 trong traffic sign preprocessing), (3) điều chỉnh confidence threshold và agnostic_nms trong infer_traffic_sign, (4) chuẩn hoá nhãn và mapping fix để giảm lỗi nhận diện tên biển báo. Trong thực tế, công việc này chủ yếu được thể hiện bằng các thay đổi trong traffic_sign_detection/predict.py và preprocessing/image_processor.py hơn là bằng file training mới.  
- Tham số cụ thể: preprocessing cho traffic sign dùng CLAHE clip_limit 3.0 thay vì giá trị thông thường 2.0; infer_traffic_sign dùng imgsz=960 và conf=0.1; agnostic_nms=True. Ngoài ra, hàm preprocess_for_traffic_sign hỗ trợ tham số apply_resize và target_size để có thể giữ resolution hoặc resize theo nhu cầu. Đây là thay đổi rõ ràng về phương diện kỹ thuật so với cấu hình mặc định dùng resize chuẩn.
- Kết quả benchmark từng hướng: chưa có số liệu trước/sau được lưu trong repo. Những file metrics hiện có ở traffic_sign_runs/results.csv chỉ là kết quả huấn luyện, không phải benchmark on validation set với preprocessing. Vì vậy, không thể công bố một cách khách quan rằng hướng nào hiệu quả nhất.
- Hướng nào hiệu quả nhất, hướng nào chưa có cải thiện rõ: theo dữ liệu thực tế có sẵn, hướng tăng input size và tăng contrast là hướng có nền tảng kỹ thuật rõ ràng nhất, nhưng chưa được validate bằng benchmark trên dữ liệu gắn nhãn. Đối với phần mapping_fix và điều chỉnh confidence, code đã có sẵn nhưng chưa có evidence về mức cải thiện trên tập test.
- Trạng thái: Hoàn thành một phần. Logic tối ưu đã được tích hợp vào code, nhưng chưa có benchmark thực nghiệm chi tiết và thống kê cải thiện rõ ràng.

### 3.4 Module Tracking (DeepSORT)
- Kiến trúc đã triển khai: module tracking được đặt tại backend/ai-service/tracking/ với file deepsort_tracker.py và README.md. Trình theo dõi chính là lớp ObjectTracker, sử dụng dataclass Track và TrackerConfig. Mã hỗ trợ cả DeepSORT (appearance-based) và IoU matching fallback. Khi DeepSORT không sẵn sàng, logic sẽ chuyển sang matching dựa trên bounding box geometry.
- Cách hoạt động: tracker nhận đầu vào là detections từ vehicle detector và pedestrian detector, chuẩn hóa sang format [x1, y1, x2, y2, confidence], lọc theo ngưỡng min_confidence, rồi cập nhật tracks. Mỗi track có track_id, class_name, bbox, confidence, frame_count và time_since_update. Output này phù hợp cho việc dùng tiếp ở fusion hoặc các cảnh báo tiếp theo.
- Kết quả test: repo có tài liệu project-state.md ghi rằng tracking module đã được test bằng mock detections, frame 1→2 ID consistency và serialization to_dict. Tuy nhiên, không có file test thực thi mới trong workspace được cung cấp cùng với report này, và không có số liệu FPS cụ thể được ghi lại trong repo. Vì vậy, có thể nói module đã được triển khai và có logic test, nhưng chưa có benchmark runtime bằng video thực tế được lưu ở đâu đó.
- Trạng thái: Hoàn thành. Mã tracking và tài liệu mô tả đã có trong repo, nhưng các kiểm thử thực tế với video dài và số liệu FPS chưa được ghi nhận đầy đủ.

## 4. Bảng tổng hợp file bị ảnh hưởng

| Đường dẫn file | Loại thay đổi | Hạng mục liên quan | Mô tả ngắn |
|---|---|---|---|
| backend/ai-service/preprocessing/image_processor.py | Sửa | Preprocessing | Entry point chung cho preprocessing theo module |
| backend/ai-service/preprocessing/enhancement/equalizer.py | Sửa | Preprocessing | Cung cấp CLAHE và histogram equalization |
| backend/ai-service/ai_models/pedestrian_detection/detector.py | Sửa | Preprocessing | Gắn preprocessing trước inference |
| backend/ai-service/ai_models/vehicle_detection/vehicle_detector.py | Sửa | Preprocessing | Gắn preprocessing cho vehicle detection |
| backend/ai-service/ai_models/lane_detection/detector.py | Sửa | Preprocessing | Gắn preprocessing cho lane detection |
| backend/ai-service/ai_models/lane_segmentation/predict.py | Sửa | Preprocessing | Gắn preprocessing cho segmentation |
| backend/ai-service/ai_models/traffic_sign_detection/predict.py | Sửa | Preprocessing + Traffic Sign | Cấu hình preprocessing và inference cho traffic sign |
| main.py | Sửa | App demo | Streamlit app cho ảnh/video/webcam |
| backend/ai-service/requirements.txt | Sửa | App demo + Tracking | Thêm streamlit và deep-sort-realtime |
| backend/ai-service/tracking/deepsort_tracker.py | Mới | Tracking | Tracker DeepSORT + fallback IoU |
| backend/ai-service/tracking/README.md | Mới | Tracking | Tài liệu module tracking |
| docs/project-state.md | Sửa | Documentation | Cập nhật trạng thái tracking |
| docs/changelog.md | Sửa | Documentation | Ghi nhận tích hợp preprocessing và demo |
| README.md | Sửa | Documentation | Ghi lệnh chạy và mô tả chức năng |

## 5. Bảng tổng hợp kết quả benchmark

| Hạng mục | Chỉ số có sẵn | Giá trị thực tế trong repo | Ghi chú |
|---|---|---|---|
| Pedestrian training | mAP50, mAP50-95 | Có file results.csv, nhưng chưa có benchmark inference trước/sau | Dữ liệu training, không phải benchmark preprocessing |
| Vehicle detection | mAP50, mAP50-95 | Có file evaluation/results.csv | Chỉ phản ánh training/evaluation ban đầu |
| Traffic sign training | mAP50, mAP50-95 | Có file traffic_sign_runs/results.csv | Chưa có benchmark trước/sau với preprocessing |
| App demo | FPS hiển thị trong code | Có logic tính FPS tại runtime, nhưng chưa có số liệu lưu trữ | FPS thay đổi theo machine và input |
| DeepSORT | Số track, ID stability | Đã có logic và docs, chưa có số liệu thực nghiệm video dài | Cần validate trên video thực tế |

## 6. Vấn đề còn tồn đọng / chưa hoàn thành

- Benchmark trước/sau preprocessing chưa được thực hiện đầy đủ bằng dữ liệu gắn nhãn chuẩn. Đây là điểm thiếu nhất trong báo cáo hiện tại. 
- Chưa có số liệu FPS/latency thực tế được ghi nhận từ video chạy trên môi trường cụ thể, mặc dù code đã in và tính toán FPS ở runtime.
- Traffic sign far-range optimization có logic tích hợp, nhưng cần kiểm chứng trên tập ảnh biển báo xa với ground truth để biết mức cải thiện thực sự.
- DeepSORT hiện có fallback IoU và support cho appearance matching, nhưng độ ổn định ID trên video thực tế vẫn cần kiểm thử thêm trong tình huống nhiều đối tượng chồng lấp, che khuất hoặc chuyển động nhanh.
- Một số tài liệu prompt cũ và file plan cũ có thể không còn ở trạng thái đúng như quá trình code hiện tại; vì vậy, báo cáo này dựa trên code và tài liệu hiện có trong repo, không dựa trên suy đoán từ tên file.

## 7. Đề xuất bước tiếp theo

Dựa trên timeline hệ thống, các bước tiếp theo nên ưu tiên theo thứ tự sau. Trước tiên, nên xây dựng một bộ benchmark thực tế cho preprocessing, dùng tập ảnh/video có gắn nhãn để đo mAP, confidence, false positive và FPS trước/sau cho từng module. Tiếp theo, nên tích hợp kết quả tracking vào fusion để tạo luồng cảnh báo cho xe và người đi bộ. Sau đó, có thể mở rộng sang cảnh báo lệch làn đường và cảnh báo biển báo theo logic ADAS. Cuối cùng, nên chuẩn bị một dashboard đơn giản để hiển thị quá trình phát hiện, tracking và cảnh báo cho người dùng. Trong chuỗi phát triển này, tracking là tầng nối giữa detection và fusion, nên nếu muốn tiến tới cảnh báo thực tế thì module này cần được kiểm thử trên video dài hơn và chuẩn hóa output tốt hơn.

## 8. Phụ lục — Ghi chú kỹ thuật bổ sung

- Việc tích hợp preprocessing được thực hiện bằng cách giữ nguyên API inference của từng detector và chèn một bước xử lý ảnh ngay trước khi gọi model. Điều này giúp giảm rủi ro phá vỡ luồng hiện có.
- Traffic sign preprocessing được thiết kế riêng để tránh dùng chung cấu hình với vehicle/pedestrian. Cấu hình này tập trung vào tăng contrast và giữ nhiều pixel hơn cho biển báo ở xa.
- DeepSORT được cấu hình lazy-load để tránh tải embedder ngay khi khởi tạo tracker, giảm khả năng bị treo trong lúc init ban đầu.
- Mặc dù README và docs đã nêu rõ workflow chạy demo, việc chạy thật vẫn phụ thuộc vào environment, file weights và hardware. Đây là điểm cần chú ý khi triển khai trên máy khác.
- Báo cáo này ưu tiên độ chính xác và mức độ phản ánh hiện trạng repo, nên những phần chưa có evidence thực tế sẽ được ghi là chưa đo được hoặc chưa hoàn thành đầy đủ thay vì suy đoán rằng tất cả đều đã được verify bằng benchmark.
