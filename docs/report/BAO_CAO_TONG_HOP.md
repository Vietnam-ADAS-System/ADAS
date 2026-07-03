# Báo cáo tổng hợp — Hệ thống ADAS

**Ngày cập nhật:** 2026-07-03  
**Người/agent thực hiện:** AI coding agent thực hiện theo yêu cầu  
**Phạm vi báo cáo:** Tổng hợp 5 hạng mục: Preprocessing Integration, App demo main.py, Tối ưu Traffic Sign xa, Tracking DeepSORT, Fusion Layer và ADAS Decision Engine

## 1. Tóm tắt điều hành (Executive Summary)

Trong khoảnh khắc hiện tại, dự án ADAS đã có những thay đổi thực tế ở cả tầng tiền xử lý ảnh, tầng demo giao diện, tầng theo dõi đối tượng và tầng hiểu ngữ cảnh. Điểm nổi bật nhất là module tiền xử lý chung đã được tích hợp vào các detector chính: pedestrian, vehicle, lane detection, lane segmentation và traffic sign. Cấu trúc này cho phép bật/tắt preprocessing thông qua cấu hình và giúp các module inference có thể dùng chung một interface. Ở tầng demo, file root main.py đã được chuyển thành ứng dụng Streamlit hỗ trợ ảnh, video và webcam, cho phép người dùng lựa chọn module, xem kết quả trực quan, đồng thời mở phần `Scene Context / ADAS Output` để xem dữ liệu Fusion và cảnh báo ADAS. Về traffic sign, mã đã được bổ sung các tùy chọn để giữ độ phân giải cao hơn cho ảnh đầu vào và tăng tham số inference phù hợp cho biển báo ở xa. Ở tầng tracking, module DeepSORT đã được thêm vào repo với lớp tracker riêng cho vehicle và pedestrian, cùng fallback IoU khi DeepSORT không sẵn sàng. Bổ sung quan trọng mới nhất là tầng Fusion tại `backend/ai-service/fusion/`, có nhiệm vụ tổng hợp detection, lane, traffic sign và tracking thành `SceneContext`; sau đó tầng `backend/ai-service/adas/` chỉ đọc `SceneContext` để sinh cảnh báo. Tuy nhiên, các benchmark trước/sau chưa được đo bằng bộ dữ liệu gắn nhãn chuẩn trong workspace, nên các kết luận về tăng accuracy vẫn cần được kiểm chứng thêm trên dữ liệu thực tế.

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

### 3.5 Fusion Layer và ADAS Decision Engine
- Mục tiêu ban đầu: xây dựng tầng trung gian đúng theo đặc tả Fusion, trong đó Fusion không chạy YOLO, không chạy lane segmentation, không chạy DeepSORT và không sinh cảnh báo. Fusion chỉ nhận dữ liệu đã có từ AI layer, chuẩn hóa dữ liệu, tính ngữ cảnh giao thông và tạo ra một đối tượng `SceneContext` duy nhất. ADAS Decision Engine sau đó chỉ đọc `SceneContext` để đưa ra cảnh báo, không đọc trực tiếp bbox, mask, tensor hoặc YOLO result.
- Cấu trúc đã triển khai: thư mục `backend/ai-service/fusion/` gồm các module chính `data_models.py`, `config.py`, `utils.py`, `vehicle_lane_fusion.py`, `tracking_fusion.py`, `traffic_sign_fusion.py`, `scene_understanding.py`, `decision_engine.py` và `README.md`. Thư mục `backend/ai-service/adas/` gồm `decision_engine.py`, `lane_departure.py`, `traffic_rule.py`, `speed_limit.py`, `stop_warning.py`, `no_entry_warning.py`, `warning_manager.py`, `dashboard_output.py`, `data_models.py`, `config.py` và `utils.py`. Cách chia file này bám theo nguyên tắc mỗi module chỉ xử lý một nhiệm vụ.
- Luồng xử lý Fusion: `FusionEngine.build_scene_context()` nhận `vehicle_detections`, `lane_detection`, `traffic_sign_detections`, `tracking`, `pedestrian_detections`, `frame_index` và `fps`. Dữ liệu đầu vào được chuẩn hóa thành các model như `VehicleDetection`, `LaneInfo`, `TrafficSign`, `TrackInfo` và `PedestrianDetection`. Sau đó hệ thống chạy lần lượt `VehicleLaneFusion`, `TrackingFusion`, `TrafficSignFusion`, `SceneUnderstandingEngine` và `FusionDecisionEngine` để trả về `SceneContext`.
- Logic Vehicle Lane Fusion: module `vehicle_lane_fusion.py` tính tâm phương tiện từ bbox, lấy lane left/right/center từ lane detection hoặc lane mask, tính `offset = vehicle_center_x - lane_center_x`, phân loại lane tương đối thành `left`, `center`, `right` hoặc `unknown`, đồng thời xác định `lane_status` gồm `inside_lane`, `near_boundary`, `outside_lane`, `crossing_lane` hoặc `unknown`. Đây là dữ liệu chính cho cảnh báo lệch làn.
- Logic Tracking Fusion: module `tracking_fusion.py` ghép detection với track bằng IoU, dùng ngưỡng `tracking_iou_threshold` trong `FusionConfig`. Module này bỏ qua track thuộc nhóm `person/pedestrian` khi ghép cho vehicle để tránh gán nhầm track người đi bộ cho phương tiện. Output là `TrackingAssociation` gồm `detection_id`, `track_id` và trạng thái `tracking`.
- Logic Traffic Sign Fusion: module `traffic_sign_fusion.py` chọn biển báo có confidence cao nhất, chuẩn hóa các kiểu biển báo như `Speed Limit`, `STOP`, `NO_ENTRY`, `YIELD`, `PARKING`, đồng thời tách giá trị tốc độ nếu biển báo là giới hạn tốc độ. Output là `TrafficRule` có `type` và `value`.
- Scene Context chuẩn: output cuối cùng của Fusion là `SceneContext` có các trường chính `frame`, `vehicles`, `traffic_rule`, `timestamp` và tùy chọn `pedestrians`. Mỗi phần tử vehicle gồm `track_id`, `type`, `lane`, `lane_status`, `offset`, `center`, `speed` và `tracking`. Cấu trúc này đúng với mục tiêu “ADAS chỉ đọc Scene Context”.
- ADAS Decision Engine: thư mục `backend/ai-service/adas/` nhận `SceneContext` và tạo `ADASOutput`. Các rule hiện có gồm lane departure/lane crossing, STOP warning, no-entry warning và speed limit/overspeed. `WarningManager` loại bỏ cảnh báo trùng theo cặp `(type, track_id)` và sắp xếp theo mức ưu tiên `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.
- Tích hợp vào main.py: root `main.py` đã load thêm `FusionEngine`, `ADASDecisionEngine` và `ObjectTracker`. Hàm `draw_results()` không chỉ vẽ output từ các model mà còn gom dữ liệu detection/lane/sign/tracking, gọi `build_scene_context()`, gọi `ADASDecisionEngine.evaluate()`, rồi trả về `FrameAnalysis` gồm ảnh annotate, counts, elapsed_seconds, scene_context và adas_output. Ở chế độ ảnh và webcam, Streamlit hiển thị thêm expander `Scene Context / ADAS Output` để kiểm tra dữ liệu Fusion và cảnh báo.
- Kết quả test logic: đã kiểm tra bằng dữ liệu mẫu không cần model thật. Với vehicle bbox `[300,320,400,520]`, lane center `320`, speed limit `40`, track_id `5` và current_speed `60`, Fusion sinh `SceneContext` có vehicle center `[350,420]`, offset `30`, track_id `5`, traffic_rule `Speed Limit 40`; ADAS sinh cảnh báo `Overspeed` mức `HIGH`. Ngoài ra, các file `main.py`, `fusion/` và `adas/` đã qua bước `python -m py_compile`.
- Trạng thái: Hoàn thành phần kiến trúc và logic lõi. Fusion/ADAS đã có code, data model, module độc lập và tích hợp vào app demo. Phần còn thiếu là benchmark với video thực tế, kiểm thử nhiều tình huống lane phức tạp, và kiểm chứng đầy đủ các cảnh báo trên dữ liệu gắn nhãn.

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
| main.py | Sửa | App demo + Fusion + ADAS | Streamlit app cho ảnh/video/webcam, tích hợp Scene Context và ADAS Output |
| backend/ai-service/requirements.txt | Sửa | App demo + Tracking | Thêm streamlit và deep-sort-realtime |
| backend/ai-service/tracking/deepsort_tracker.py | Mới | Tracking | Tracker DeepSORT + fallback IoU |
| backend/ai-service/tracking/README.md | Mới | Tracking | Tài liệu module tracking |
| backend/ai-service/fusion/data_models.py | Mới | Fusion | Định nghĩa BoundingBox, LaneInfo, TrafficRule, SceneContext và các model nội bộ |
| backend/ai-service/fusion/decision_engine.py | Mới | Fusion | Facade `FusionEngine` và bước chuẩn hóa SceneContext |
| backend/ai-service/fusion/vehicle_lane_fusion.py | Mới | Fusion | Tính center, offset, lane và lane_status cho từng phương tiện |
| backend/ai-service/fusion/tracking_fusion.py | Mới | Fusion | Ghép detection với track_id bằng IoU |
| backend/ai-service/fusion/traffic_sign_fusion.py | Mới | Fusion | Diễn giải biển báo thành luật giao thông hiện hành |
| backend/ai-service/fusion/scene_understanding.py | Mới | Fusion | Tổng hợp dữ liệu thành SceneContext |
| backend/ai-service/fusion/config.py | Mới | Fusion | Cấu hình threshold cho Fusion |
| backend/ai-service/fusion/utils.py | Mới | Fusion | Hàm chuẩn hóa bbox, lane geometry, traffic rule và timestamp |
| backend/ai-service/fusion/__init__.py | Mới | Fusion | Public API cho Fusion layer |
| backend/ai-service/fusion/README.md | Mới | Fusion | Tài liệu ngắn về đầu vào/đầu ra của Fusion |
| backend/ai-service/adas/decision_engine.py | Mới | ADAS | Đọc SceneContext và sinh ADASOutput |
| backend/ai-service/adas/lane_departure.py | Mới | ADAS | Rule cảnh báo lệch/cắt làn |
| backend/ai-service/adas/traffic_rule.py | Mới | ADAS | Router cho STOP, NO_ENTRY và Speed Limit |
| backend/ai-service/adas/speed_limit.py | Mới | ADAS | Rule Speed Limit/Overspeed |
| backend/ai-service/adas/stop_warning.py | Mới | ADAS | Rule STOP warning |
| backend/ai-service/adas/no_entry_warning.py | Mới | ADAS | Rule No Entry warning |
| backend/ai-service/adas/warning_manager.py | Mới | ADAS | Loại trùng và sắp xếp ưu tiên cảnh báo |
| backend/ai-service/adas/data_models.py | Mới | ADAS | Định nghĩa Warning và ADASOutput |
| backend/ai-service/adas/config.py | Mới | ADAS | Cấu hình threshold cảnh báo |
| backend/ai-service/adas/dashboard_output.py | Mới | ADAS | Chuẩn bị payload dashboard từ SceneContext và ADASOutput |
| backend/ai-service/adas/utils.py | Mới | ADAS | Helper chuyển đổi dữ liệu |
| backend/ai-service/adas/__init__.py | Mới | ADAS | Public API cho ADAS layer |
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
| Fusion + ADAS | SceneContext, ADASOutput | Đã test bằng dữ liệu mẫu: sinh `SceneContext` và cảnh báo `Overspeed` đúng logic | Chưa có benchmark bằng video thực tế/gắn nhãn |

## 6. Vấn đề còn tồn đọng / chưa hoàn thành

- Benchmark trước/sau preprocessing chưa được thực hiện đầy đủ bằng dữ liệu gắn nhãn chuẩn. Đây là điểm thiếu nhất trong báo cáo hiện tại. 
- Chưa có số liệu FPS/latency thực tế được ghi nhận từ video chạy trên môi trường cụ thể, mặc dù code đã in và tính toán FPS ở runtime.
- Traffic sign far-range optimization có logic tích hợp, nhưng cần kiểm chứng trên tập ảnh biển báo xa với ground truth để biết mức cải thiện thực sự.
- DeepSORT hiện có fallback IoU và support cho appearance matching, nhưng độ ổn định ID trên video thực tế vẫn cần kiểm thử thêm trong tình huống nhiều đối tượng chồng lấp, che khuất hoặc chuyển động nhanh.
- Fusion đã tạo được `SceneContext`, nhưng lane geometry hiện vẫn phụ thuộc mạnh vào chất lượng lane detection/lane segmentation đầu vào. Với các tình huống nhiều làn, đường cong, che khuất vạch kẻ hoặc mask rời rạc, cần thêm dữ liệu thực tế để kiểm chứng `lane`, `lane_status` và `offset`.
- ADAS Decision Engine đã có các rule lõi, nhưng current speed hiện chưa được lấy từ cảm biến/GPS/ước lượng tracking trong app demo. Vì vậy rule overspeed chỉ có thể kiểm thử đầy đủ khi truyền `current_speed` từ nguồn dữ liệu phù hợp.
- Một số tài liệu prompt cũ và file plan cũ có thể không còn ở trạng thái đúng như quá trình code hiện tại; vì vậy, báo cáo này dựa trên code và tài liệu hiện có trong repo, không dựa trên suy đoán từ tên file.

## 7. Đề xuất bước tiếp theo

Dựa trên timeline hệ thống, các bước tiếp theo nên ưu tiên theo thứ tự sau. Trước tiên, nên xây dựng một bộ benchmark thực tế cho preprocessing và Fusion, dùng tập ảnh/video có gắn nhãn để đo mAP, confidence, false positive, FPS, độ ổn định track_id, độ đúng của lane_status và độ đúng của traffic_rule. Tiếp theo, nên chạy pipeline đầy đủ trên video dài để kiểm tra chuỗi `Detection → Tracking → Fusion → ADAS`, đặc biệt trong tình huống nhiều xe, người đi bộ, đường cong, biển báo nhỏ và vật thể che khuất. Sau đó, nên bổ sung nguồn `current_speed` cho ADAS để rule Speed Limit/Overspeed hoạt động với dữ liệu thực tế thay vì chỉ kiểm thử bằng giá trị mẫu. Cuối cùng, nên mở rộng dashboard để hiển thị `SceneContext`, danh sách cảnh báo, lịch sử track và log theo frame nhằm phục vụ debug, evaluation và báo cáo.

## 8. Phụ lục — Ghi chú kỹ thuật bổ sung

- Việc tích hợp preprocessing được thực hiện bằng cách giữ nguyên API inference của từng detector và chèn một bước xử lý ảnh ngay trước khi gọi model. Điều này giúp giảm rủi ro phá vỡ luồng hiện có.
- Traffic sign preprocessing được thiết kế riêng để tránh dùng chung cấu hình với vehicle/pedestrian. Cấu hình này tập trung vào tăng contrast và giữ nhiều pixel hơn cho biển báo ở xa.
- DeepSORT được cấu hình lazy-load để tránh tải embedder ngay khi khởi tạo tracker, giảm khả năng bị treo trong lúc init ban đầu.
- Mặc dù README và docs đã nêu rõ workflow chạy demo, việc chạy thật vẫn phụ thuộc vào environment, file weights và hardware. Đây là điểm cần chú ý khi triển khai trên máy khác.
- Báo cáo này ưu tiên độ chính xác và mức độ phản ánh hiện trạng repo, nên những phần chưa có evidence thực tế sẽ được ghi là chưa đo được hoặc chưa hoàn thành đầy đủ thay vì suy đoán rằng tất cả đều đã được verify bằng benchmark.
