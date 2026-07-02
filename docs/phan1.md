# SYSTEM_ARCHITECTURE.md

> **Tên tài liệu:** Kiến trúc tổng thể hệ thống ADAS
> **Phiên bản:** 1.0
> **Mục tiêu:** Mô tả toàn bộ kiến trúc hệ thống để AI hoặc lập trình viên có thể phát triển từng module độc lập nhưng vẫn đảm bảo khả năng tích hợp.

---

# 1. Mục tiêu hệ thống

Hệ thống ADAS (Advanced Driver Assistance System) có nhiệm vụ phân tích video từ camera phía trước của xe nhằm:

* Phát hiện phương tiện giao thông.
* Phát hiện người đi bộ.
* Phát hiện biển báo giao thông.
* Phát hiện làn đường.
* Theo dõi đối tượng qua nhiều khung hình.
* Hiểu ngữ cảnh giao thông (Scene Understanding).
* Đưa ra các cảnh báo hỗ trợ người lái.

Toàn bộ hệ thống được chia thành các module độc lập nhằm dễ bảo trì, mở rộng và nâng cấp.

---

# 2. Kiến trúc tổng thể

```text
                Camera / Video
                      │
                      ▼
              Image Preprocessing
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Vehicle Detection   Lane Detection   DeepSORT Tracking
 Pedestrian Detection
 Traffic Sign Detection
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                  FUSION
          (Scene Understanding)
                      │
                      ▼
            ADAS Decision Engine
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
Lane Departure Warning     Traffic Sign Warning
                      │
                      ▼
                Dashboard / UI
```

---

# 3. Luồng xử lý tổng thể

Hệ thống xử lý theo đúng thứ tự sau:

```
Video

↓

Frame

↓

Preprocessing

↓

Detection

↓

Tracking

↓

Fusion

↓

Scene Understanding

↓

ADAS Decision Engine

↓

Dashboard
```

Mỗi module chỉ được phép thực hiện đúng trách nhiệm của mình.

Không được để một module xử lý thay công việc của module khác.

---

# 4. Module Camera

## Nhiệm vụ

Đọc dữ liệu đầu vào từ:

* Camera
* Video
* Webcam

## Input

```python
Video Stream
```

## Output

```python
frame : numpy.ndarray
```

## Trách nhiệm

* Đọc frame
* Đồng bộ FPS
* Không xử lý AI
* Không chỉnh sửa hình ảnh

---

# 5. Module Preprocessing

Thư mục

```
backend/
└── ai-service/
    └── preprocessing/
```

## Nhiệm vụ

Chuẩn hóa ảnh trước khi đưa vào AI.

## Input

```python
frame
```

## Output

```python
processed_frame
```

## Chức năng

* Resize
* Normalize
* CLAHE
* Gaussian Blur
* Brightness Adjustment
* HSV Conversion
* Color Space Conversion
* Noise Reduction

## Không được phép

* Detect Object
* Tracking
* Fusion
* Decision

---

# 6. Module Detection

Detection bao gồm nhiều mô hình AI hoạt động độc lập.

## 6.1 Vehicle Detection

### Input

```
processed_frame
```

### Output

```python
[
    {
        "class":"car",
        "bbox":[x1,y1,x2,y2],
        "confidence":0.95
    }
]
```

---

## 6.2 Pedestrian Detection

Output

```python
[
    {
        "class":"person",
        "bbox":[...]
    }
]
```

---

## 6.3 Traffic Sign Detection

Output

```python
[
    {
        "type":"Speed Limit",
        "value":40
    }
]
```

---

## 6.4 Lane Detection

Output

```python
Lane Mask
```

Bao gồm

* Lane Left
* Lane Right
* Lane Center

---

# 7. Module Tracking

Thư mục

```
tracking/
```

## Công nghệ

DeepSORT

## Input

Vehicle Detection

Pedestrian Detection

## Output

```python
[
    {
        "track_id":5,
        "bbox":[...]
    }
]
```

## Trách nhiệm

* Gán ID
* Theo dõi đối tượng
* Không detect mới

---

# 8. Module Fusion

Đây là module quan trọng nhất của toàn hệ thống.

Fusion KHÔNG phải AI.

Fusion là tập hợp các thuật toán logic nhằm kết hợp kết quả từ các mô hình AI để tạo ra Scene Understanding.

Input của Fusion gồm:

* Vehicle Detection
* Pedestrian Detection
* Lane Detection
* Traffic Sign Detection
* Tracking

Output của Fusion là Scene Context.

---

## 8.1 Vehicle Lane Fusion

Input

```
Bounding Box
Lane Mask
```

Output

```python
Lane = Left
Lane = Center
Lane = Right
```

---

## 8.2 Lane Offset Calculation

Input

```
Vehicle Center
Lane Center
```

Output

```python
Offset = 25 pixel
```

---

## 8.3 Traffic Sign Fusion

Input

```
Traffic Sign Detection
```

Output

```python
Current Traffic Rule
```

Ví dụ

```
STOP

↓

Current Rule = STOP
```

---

## 8.4 Tracking Fusion

Input

```
Tracking ID
```

Output

```python
Vehicle #5
```

---

## 8.5 Scene Understanding

Đây là bước cuối của Fusion.

Scene Understanding tổng hợp toàn bộ thông tin của khung hình.

Ví dụ

```python
{
    "vehicles":[...],
    "traffic_sign":{},
    "lane":{},
    "tracking":[]
}
```

Đây là dữ liệu chuẩn để chuyển sang ADAS.

---

# 9. ADAS Decision Engine

ADAS chỉ đọc Scene Context.

ADAS tuyệt đối không đọc:

* Bounding Box
* Mask
* Tensor
* YOLO Result

Các quyết định gồm

## Lane Departure

Nếu

```
offset > threshold
```

↓

```
Lane Departure Warning
```

---

## Traffic Sign

Ví dụ

```
STOP

↓

Prepare To Stop
```

---

Ví dụ

```
Speed Limit = 40

Vehicle Speed = 60

↓

Overspeed Warning
```

---

Ví dụ

```
No Entry

↓

Warning
```

---

# 10. Dashboard

Dashboard chỉ hiển thị kết quả.

Ví dụ

* Bounding Box
* Lane
* Vehicle ID
* Speed Limit
* Warning
* FPS

Dashboard không được xử lý AI.

---

# 11. Quy tắc thiết kế

Mỗi module phải độc lập.

Không module nào được phép gọi trực tiếp logic của module khác.

Luồng dữ liệu chỉ được đi theo hướng:

```
Camera

↓

Preprocessing

↓

Detection

↓

Tracking

↓

Fusion

↓

ADAS

↓

Dashboard
```

Không được phép đảo ngược luồng xử lý.

---

# 12. Cấu trúc thư mục đề xuất

```text
backend/
└── ai-service/
    ├── preprocessing/
    ├── ai_models/
    │   ├── vehicle_detection/
    │   ├── pedestrian_detection/
    │   ├── traffic_sign_detection/
    │   └── lane_detection/
    ├── tracking/
    ├── fusion/
    ├── adas/
    └── evaluation/
```

---

# 13. Mục tiêu cuối cùng

Sau khi hoàn thành toàn bộ hệ thống:

* Camera chỉ đọc dữ liệu.
* Preprocessing chỉ chuẩn hóa ảnh.
* Detection chỉ nhận diện đối tượng.
* Tracking chỉ theo dõi đối tượng.
* Fusion chỉ tạo Scene Understanding.
* ADAS chỉ đưa ra quyết định.
* Dashboard chỉ hiển thị kết quả.

Mỗi module đều có Input, Output và trách nhiệm riêng, giúp hệ thống dễ mở rộng, dễ bảo trì và phù hợp với kiến trúc ADAS thực tế.
# 02_FUSION_INPUT_SPECIFICATION.md

> **Tên tài liệu:** Fusion Input Specification
> **Phiên bản:** 1.0
> **Mục tiêu:** Định nghĩa toàn bộ dữ liệu đầu vào mà module Fusion sẽ nhận từ các mô hình AI. Tài liệu này là chuẩn giao tiếp (Interface Specification) giữa các module AI và Fusion.

---

# 1. Mục đích

Fusion không thực hiện nhận diện đối tượng (Object Detection), phân đoạn làn đường (Lane Segmentation) hay theo dõi đối tượng (Tracking).

Fusion chỉ nhận dữ liệu đã được xử lý từ các mô hình AI và kết hợp chúng để tạo thành **Scene Understanding**.

Do đó, mọi module AI phải trả dữ liệu đúng theo định dạng được quy định trong tài liệu này.

---

# 2. Tổng quan dữ liệu đầu vào

Fusion nhận dữ liệu từ bốn nguồn chính:

```text
Vehicle Detection (YOLO)
          │
Lane Detection (DeepLabV3+)
          │
Traffic Sign Detection
          │
DeepSORT Tracking
          │
          ▼
       FUSION
```

Mỗi module phải hoạt động độc lập và chỉ chịu trách nhiệm trả về dữ liệu của mình.

---

# 3. Input 1 - Vehicle Detection

## Nguồn dữ liệu

```text
backend/
└── ai-service/
    └── ai_models/
        └── vehicle_detection/
```

Module này sử dụng YOLO để phát hiện các phương tiện giao thông.

---

## Mục tiêu

Fusion cần biết:

* Có bao nhiêu phương tiện trong khung hình.
* Loại phương tiện.
* Vị trí từng phương tiện.
* Độ tin cậy của kết quả nhận diện.

---

## Định dạng dữ liệu

```json
[
    {
        "id": 1,
        "class": "car",
        "bbox": [120,250,310,420],
        "confidence": 0.95
    },
    {
        "id": 2,
        "class": "motorcycle",
        "bbox": [420,260,480,360],
        "confidence": 0.91
    }
]
```

---

## Ý nghĩa từng trường

### id

ID của Detection trong frame hiện tại.

Lưu ý:

Đây **không phải Track ID**.

Ví dụ

```text
Frame 1

Car A

id = 3
```

Frame tiếp theo

```text
Frame 2

Car A

id = 5
```

Điều này hoàn toàn bình thường.

Track ID sẽ được DeepSORT xử lý sau.

---

### class

Loại phương tiện.

Ví dụ

```text
car

bus

truck

motorcycle

bicycle
```

Fusion sẽ sử dụng thông tin này để:

* Phân loại đối tượng.
* Áp dụng luật ADAS phù hợp.
* Hiển thị Dashboard.

---

### bbox

Bounding Box

Định dạng

```text
[x1, y1, x2, y2]
```

Ví dụ

```text
[120,250,310,420]
```

Fusion sử dụng Bounding Box để:

* Tính tâm xe.
* Xác định xe thuộc làn nào.
* Tính khoảng cách tới tâm làn.

---

### confidence

Độ tin cậy.

Ví dụ

```text
0.95
```

Fusion có thể loại bỏ Detection có confidence thấp hơn ngưỡng cấu hình.

Ví dụ

```text
confidence < 0.5
```

↓

```text
Bỏ qua Detection
```

---

## Output mong muốn

Fusion nhận

```python
List[VehicleDetection]
```

Trong đó mỗi VehicleDetection phải chứa:

* id
* class
* bbox
* confidence

Không được thiếu trường nào.

---

# 4. Input 2 - Lane Detection

## Nguồn dữ liệu

```text
backend/
└── ai-service/
    └── ai_models/
        └── lane_detection/
```

---

## Mục tiêu

Fusion cần biết:

* Biên trái làn đường.
* Biên phải làn đường.
* Tâm làn đường.
* Mask của làn đường.

---

## Đầu ra mong muốn

```python
{
    "lane_left": [...],
    "lane_right": [...],
    "lane_center": [...],
    "mask": ...
}
```

---

## Lane Left

Danh sách các điểm mô tả mép trái làn đường.

Ví dụ

```text
[(120,720),
 (180,500),
 (250,300)]
```

---

## Lane Right

Danh sách các điểm mô tả mép phải làn đường.

Ví dụ

```text
[(520,720),
 (470,500),
 (410,300)]
```

---

## Lane Center

Fusion không nên tự tính nếu Lane Detection đã trả sẵn.

Ví dụ

```text
Lane Center

x = 320
```

Hoặc

```text
[(320,720),
 (325,500),
 (330,300)]
```

---

## Lane Mask

Ảnh nhị phân của làn đường.

Fusion chỉ sử dụng khi cần:

* Kiểm tra xe có nằm trong làn hay không.
* Kiểm tra xe cắt vạch.

Fusion không chỉnh sửa Mask.

---

## Output mong muốn

```python
LaneInfo
```

Bao gồm:

* Lane Left
* Lane Right
* Lane Center
* Lane Mask

---

# 5. Input 3 - Traffic Sign Detection

## Nguồn dữ liệu

```text
backend/
└── ai-service/
    └── ai_models/
        └── traffic_sign_detection/
```

---

## Mục tiêu

Fusion cần biết biển báo hiện tại.

---

Ví dụ

```text
Speed Limit 40

STOP

No Entry

Yield

Parking
```

---

## Định dạng dữ liệu

```json
[
    {
        "class":"Speed Limit",
        "value":40,
        "bbox":[100,80,180,170],
        "confidence":0.96
    }
]
```

---

## Fusion sử dụng để

* Xác định luật giao thông hiện hành.
* Cập nhật Scene Context.
* Chuyển dữ liệu sang ADAS.

Ví dụ

```text
Speed Limit

↓

Current Rule

40 km/h
```

---

Nếu phát hiện

```text
STOP
```

↓

Fusion tạo

```text
Current Rule

STOP
```

---

## Output mong muốn

```python
List[TrafficSign]
```

---

# 6. Input 4 - DeepSORT Tracking

## Nguồn dữ liệu

```text
backend/
└── ai-service/
    └── tracking/
```

---

## Mục tiêu

Tracking giúp Fusion biết đối tượng ở nhiều frame thực chất là cùng một đối tượng.

Ví dụ

```text
Frame 1

Car

↓

Frame 2

↓

Frame 3
```

Fusion hiểu:

Đây vẫn là cùng một chiếc xe.

---

## Định dạng dữ liệu

```json
[
    {
        "track_id":5,
        "bbox":[120,250,310,420],
        "class":"car"
    }
]
```

---

## Ý nghĩa

Track ID là định danh duy nhất của đối tượng trong suốt quá trình theo dõi.

Ví dụ

```text
Frame 1

Track ID = 5
```

↓

```text
Frame 20

Track ID = 5
```

↓

```text
Frame 100

Track ID = 5
```

Fusion biết đây là cùng một chiếc xe.

---

## Fusion sử dụng Tracking để

* Theo dõi chuyển động.
* Không tạo trùng đối tượng.
* Tính vận tốc (nếu cần).
* Lưu lịch sử đối tượng.
* Ghép với Vehicle Detection.

---

# 7. Dữ liệu Fusion sẽ nhận

Sau khi tất cả module AI hoàn thành, Fusion sẽ nhận bốn nhóm dữ liệu:

```text
Vehicle Detection
│
├── id
├── class
├── bbox
└── confidence

Lane Detection
│
├── lane_left
├── lane_right
├── lane_center
└── lane_mask

Traffic Sign Detection
│
├── class
├── value
├── bbox
└── confidence

Tracking
│
├── track_id
├── bbox
└── class
```

---

# 8. Interface giữa AI và Fusion

Mọi module AI phải đảm bảo:

* Không trả về dữ liệu thiếu trường.
* Không thay đổi tên thuộc tính.
* Không thay đổi kiểu dữ liệu.
* Luôn trả về cấu trúc thống nhất giữa các frame.

Fusion sẽ giả định toàn bộ dữ liệu đầu vào đều tuân thủ chuẩn này và không chịu trách nhiệm sửa lỗi dữ liệu từ các module AI.

---

# 9. Mục tiêu của tài liệu

Sau khi hoàn thành tài liệu này:

* Module Vehicle Detection biết phải trả về dữ liệu gì.
* Module Lane Detection biết phải trả về dữ liệu gì.
* Module Traffic Sign Detection biết phải trả về dữ liệu gì.
* Module Tracking biết phải trả về dữ liệu gì.
* Module Fusion có thể nhận dữ liệu từ tất cả các module AI thông qua một giao diện thống nhất mà không cần phụ thuộc vào cách triển khai nội bộ của từng mô hình.
# 03_FUSION_PROCESSING.md

> **Tên tài liệu:** Fusion Processing Specification
> **Phiên bản:** 1.0
> **Mục tiêu:** Mô tả toàn bộ các thuật toán và logic mà module Fusion phải thực hiện sau khi nhận dữ liệu từ các mô hình AI. Tài liệu này **không mô tả cách huấn luyện AI**, mà chỉ định nghĩa cách Fusion xử lý dữ liệu để tạo ra **Scene Understanding**.

---

# 1. Mục đích

Sau khi các mô hình AI hoàn thành việc nhận diện và theo dõi đối tượng, Fusion sẽ tiếp nhận toàn bộ dữ liệu đầu vào và thực hiện các bước xử lý nhằm tạo ra một bản mô tả hoàn chỉnh về ngữ cảnh giao thông (Scene Context).

Fusion **không chạy AI**, **không thực hiện Detection**, **không thực hiện Segmentation** và **không thực hiện Tracking**.

Fusion chỉ sử dụng các thuật toán xử lý dữ liệu (Logic Processing).

---

# 2. Luồng xử lý của Fusion

```text
Vehicle Detection
        │
Lane Detection
        │
Traffic Sign Detection
        │
DeepSORT Tracking
        │
        ▼
=============================
          FUSION
=============================
        │
        ├── Vehicle Lane Fusion
        │
        ├── Lane Offset Calculation
        │
        ├── Traffic Sign Fusion
        │
        ├── Tracking Association
        │
        ├── Scene Understanding
        │
        ▼
      Scene Context
```

Fusion sẽ xử lý lần lượt từng bước theo đúng thứ tự trên.

---

# 3. Vehicle Lane Fusion

## Mục tiêu

Xác định mỗi phương tiện đang nằm trong làn đường nào.

Đây là bước đầu tiên và quan trọng nhất của Fusion.

---

## Input

Vehicle Detection

```python
{
    "class":"car",
    "bbox":[120,250,310,420]
}
```

Lane Detection

```python
{
    "lane_left":250,
    "lane_right":450
}
```

---

## Bước xử lý

### Bước 1

Tính tâm của Bounding Box.

```text
Car Center

(cx, cy)
```

Ví dụ

```text
bbox

[300,320,400,520]

↓

Car Center

(350,420)
```

---

### Bước 2

Lấy thông tin từ Lane Detection

```text
Lane Left = 250

Lane Right = 450
```

---

### Bước 3

So sánh

```text
Lane Left

≤

Car Center X

≤

Lane Right
```

---

Nếu điều kiện đúng

↓

```text
Vehicle nằm trong lane
```

Nếu không

↓

```text
Vehicle nằm ngoài lane
```

---

## Output

```python
{
    "lane":"center",
    "status":"inside_lane"
}
```

---

## Mục tiêu cuối cùng

Fusion phải biết:

* Xe đang ở làn nào.
* Xe có nằm trong làn hay không.
* Xe có cắt vạch hay không (nếu có dữ liệu).

---

# 4. Lane Offset Calculation

## Mục tiêu

Tính khoảng cách giữa tâm xe và tâm làn.

Đây là dữ liệu đầu vào quan trọng cho chức năng Lane Departure Warning.

---

## Input

```text
Lane Center

320
```

```text
Vehicle Center

350
```

---

## Thuật toán

```text
Offset

=

Vehicle Center X

-

Lane Center X
```

Ví dụ

```text
350

-

320

=

30 pixel
```

---

## Ý nghĩa

Offset > 0

↓

Xe lệch sang phải.

---

Offset < 0

↓

Xe lệch sang trái.

---

Offset = 0

↓

Xe nằm đúng tâm làn.

---

## Output

```python
{
    "offset":30
}
```

---

## Dữ liệu này dùng để

* Lane Departure Warning.
* Lane Keeping Assist.
* Dashboard.
* Báo cáo.

---

# 5. Traffic Sign Fusion

## Mục tiêu

Biến kết quả nhận diện biển báo thành luật giao thông hiện hành.

Fusion không chỉ lưu biển báo mà còn phải hiểu ý nghĩa của biển báo.

---

## Input

```python
{
    "class":"Speed Limit",
    "value":40
}
```

---

## Xử lý

Ví dụ

```text
Speed Limit

40
```

↓

Fusion tạo

```text
Current Rule

Speed Limit = 40
```

---

Ví dụ

```text
STOP
```

↓

```text
Current Rule

STOP
```

---

Ví dụ

```text
No Entry
```

↓

```text
Current Rule

NO_ENTRY
```

---

## Output

```python
{
    "current_rule":"Speed Limit",
    "value":40
}
```

---

## Mục tiêu

ADAS không cần đọc Bounding Box.

ADAS chỉ cần biết:

```text
Luật giao thông hiện tại
```

---

# 6. Tracking Association

## Mục tiêu

Liên kết Vehicle Detection với Track ID.

Tracking giúp Fusion biết đối tượng hiện tại có phải đối tượng đã xuất hiện ở các frame trước hay không.

---

## Input

```python
{
    "track_id":5,
    "bbox":[...]
}
```

---

## Xử lý

Fusion sẽ ghép

```text
Vehicle Detection

↓

Track ID
```

---

Ví dụ

```text
Frame 1

Car

Track ID = 5
```

↓

```text
Frame 30

Car

Track ID = 5
```

↓

Fusion hiểu

```text
Đây vẫn là cùng một chiếc xe.
```

---

## Output

```python
{
    "track_id":5,
    "tracking":true
}
```

---

## Mục tiêu

Fusion phải có khả năng:

* Theo dõi lịch sử đối tượng.
* Không tạo trùng xe.
* Liên kết dữ liệu giữa các frame.

---

# 7. Scene Understanding

Đây là bước cuối cùng của Fusion.

Sau khi hoàn thành tất cả các bước xử lý, Fusion sẽ tổng hợp toàn bộ thông tin của khung hình thành một Scene Context thống nhất.

---

## Input

* Vehicle Lane Fusion
* Lane Offset
* Traffic Rule
* Tracking

---

## Output

```python
{
    "frame":152,
    "vehicles":[
        {
            "track_id":5,
            "type":"car",
            "lane":"center",
            "status":"inside_lane",
            "offset":30
        }
    ],
    "traffic_rule":{
        "type":"Speed Limit",
        "value":40
    }
}
```

Scene Context chính là đầu ra chuẩn để chuyển sang ADAS Decision Engine.

---

# 8. Thứ tự xử lý trong Fusion

Fusion phải thực hiện đúng thứ tự sau:

```text
Vehicle Detection
        │
        ▼
Vehicle Lane Fusion
        │
        ▼
Lane Offset Calculation
        │
        ▼
Traffic Sign Fusion
        │
        ▼
Tracking Association
        │
        ▼
Scene Understanding
        │
        ▼
Scene Context
```

Không được thay đổi thứ tự xử lý.

---

# 9. Các module đề xuất trong thư mục Fusion

```text
fusion/
│
├── fusion_manager.py
│
├── vehicle_lane_fusion.py
│
├── lane_offset.py
│
├── traffic_sign_fusion.py
│
├── tracking_fusion.py
│
├── scene_understanding.py
│
├── scene_context.py
│
├── data_models.py
│
└── utils.py
```

Mỗi module chỉ đảm nhận **một nhiệm vụ duy nhất**, tuân theo nguyên tắc **Single Responsibility Principle (SRP)**.

---

# 10. Quy tắc thiết kế

Fusion không được:

* Chạy mô hình YOLO.
* Chạy DeepLabV3+.
* Chạy DeepSORT.
* Huấn luyện AI.
* Hiển thị giao diện.

Fusion chỉ thực hiện:

* Kết hợp dữ liệu.
* Phân tích ngữ cảnh.
* Chuẩn hóa dữ liệu.
* Sinh Scene Context.

---

# 11. Kết quả mong muốn

Sau khi Fusion hoàn thành, hệ thống sẽ không còn làm việc với Bounding Box, Lane Mask hay Track ID một cách riêng lẻ.

Thay vào đó, toàn bộ thông tin đã được chuyển thành một **Scene Context** có ý nghĩa, ví dụ:

```python
{
    "frame":152,
    "vehicles":[
        {
            "track_id":5,
            "type":"car",
            "lane":"center",
            "status":"inside_lane",
            "offset":30
        }
    ],
    "traffic_rule":{
        "type":"Speed Limit",
        "value":40
    }
}
```

Đây là dữ liệu chuẩn duy nhất mà **ADAS Decision Engine** được phép sử dụng để đưa ra các quyết định như:

* Lane Departure Warning.
* Lane Keeping Assist.
* Speed Limit Warning.
* STOP Warning.
* No Entry Warning.
* Dashboard Notification.

Từ thời điểm này, ADAS không còn phụ thuộc vào kết quả trực tiếp từ YOLO, DeepLabV3+ hay DeepSORT, mà chỉ làm việc với **Scene Context** do Fusion tạo ra.
# 04_FUSION_OUTPUT_SPECIFICATION.md

> **Tên tài liệu:** Fusion Output Specification
> **Phiên bản:** 1.0
> **Mục tiêu:** Định nghĩa chuẩn dữ liệu đầu ra của module Fusion. Đây là dữ liệu duy nhất mà ADAS Decision Engine được phép sử dụng để đưa ra các quyết định cảnh báo và hỗ trợ người lái.

---

# 1. Mục đích

Sau khi Fusion hoàn thành việc xử lý dữ liệu từ:

* Vehicle Detection
* Pedestrian Detection
* Lane Detection
* Traffic Sign Detection
* DeepSORT Tracking

Fusion phải tạo ra một **Scene Context** thống nhất.

ADAS sẽ **không làm việc trực tiếp với**:

* Bounding Box
* Lane Mask
* Tensor
* YOLO Output
* DeepLab Output
* DeepSORT Output

ADAS chỉ đọc dữ liệu từ **Fusion Output**.

Điều này giúp tách biệt hoàn toàn giữa tầng AI và tầng ra quyết định.

---

# 2. Luồng dữ liệu

```text
Camera
      │
      ▼
Preprocessing
      │
      ▼
AI Models
      │
      ▼
Fusion
      │
      ▼
=========================
     Scene Context
=========================
      │
      ▼
ADAS Decision Engine
      │
      ▼
Dashboard
```

---

# 3. Chuẩn dữ liệu đầu ra

Fusion phải tạo ra một Scene Context chứa toàn bộ thông tin cần thiết của khung hình.

Ví dụ:

```json
{
    "vehicle_id": 5,
    "vehicle_type": "car",

    "lane": "center",

    "offset": 25,

    "traffic_sign": "Speed Limit 40",

    "lane_status": "inside",

    "tracking": true
}
```

Đây chỉ là ví dụ tối giản.

Trong thực tế, Fusion nên trả về đầy đủ thông tin để ADAS có thể mở rộng trong tương lai.

---

# 4. Thiết kế Output chuẩn

## Đề xuất

```json
{
    "frame": 152,

    "vehicles": [

        {
            "track_id": 5,

            "type": "car",

            "lane": "center",

            "lane_status": "inside_lane",

            "offset": 25,

            "center": [350,420],

            "speed": null
        }

    ],

    "traffic_rule":{

        "type":"Speed Limit",

        "value":40

    },

    "timestamp":"00:00:05.233"
}
```

Đây là cấu trúc nên sử dụng trong toàn bộ hệ thống.

---

# 5. Ý nghĩa từng trường

## frame

Số thứ tự khung hình.

Ví dụ

```text
152
```

ADAS có thể sử dụng để:

* Đồng bộ Video.
* Ghi Log.
* Xuất báo cáo.

---

## vehicles

Danh sách toàn bộ phương tiện trong frame.

Ví dụ

```python
[
    {...},
    {...},
    {...}
]
```

Fusion phải trả về toàn bộ xe.

Không chỉ xe gần nhất.

---

## track_id

ID duy nhất của xe.

Nguồn

DeepSORT.

Ví dụ

```text
5
```

Nếu xe vẫn tồn tại

↓

Track ID không đổi.

---

## type

Loại xe.

Ví dụ

```text
car

bus

truck

motorcycle
```

ADAS sử dụng để

* Dashboard
* Warning
* Báo cáo

---

## lane

Làn hiện tại.

Ví dụ

```text
left

center

right
```

Nếu hệ thống mở rộng nhiều làn.

Có thể

```text
lane_1

lane_2

lane_3
```

---

## lane_status

Trạng thái xe so với làn.

Ví dụ

```text
inside_lane
```

```text
near_boundary
```

```text
outside_lane
```

```text
crossing_lane
```

ADAS sẽ dựa vào thông tin này để cảnh báo.

---

## offset

Khoảng cách giữa tâm xe và tâm làn.

Ví dụ

```text
25 pixel
```

Ý nghĩa

```text
0

↓

Xe ở giữa làn
```

---

```text
25

↓

Lệch phải
```

---

```text
-30

↓

Lệch trái
```

---

## center

Tâm xe.

Ví dụ

```text
(350,420)
```

Thông tin này có thể dùng cho

* Dashboard
* Debug
* Evaluation

---

## speed

Để mở rộng.

Hiện tại

```text
null
```

Sau này

Có thể lấy từ

* Optical Flow
* Tracking
* GPS

---

# 6. Traffic Rule

Fusion không chỉ trả về biển báo.

Fusion phải trả về luật giao thông hiện hành.

Ví dụ

```json
{
    "type":"Speed Limit",
    "value":40
}
```

---

Ví dụ

STOP

↓

```json
{
    "type":"STOP"
}
```

---

Ví dụ

No Entry

↓

```json
{
    "type":"NO_ENTRY"
}
```

---

# 7. Timestamp

Ví dụ

```text
00:00:05.233
```

Giúp

* Đồng bộ Video.
* Xuất báo cáo.
* Replay.

---

# 8. Dữ liệu ADAS sẽ sử dụng

ADAS chỉ cần đọc

```text
Scene Context
```

Ví dụ

```python
SceneContext

↓

vehicle.lane

↓

center
```

---

```python
SceneContext

↓

vehicle.offset

↓

25
```

---

```python
SceneContext

↓

traffic_rule

↓

Speed Limit 40
```

---

```python
SceneContext

↓

lane_status

↓

inside_lane
```

---

Không cần đọc

```text
Bounding Box
```

Không cần đọc

```text
Mask
```

Không cần đọc

```text
YOLO Output
```

Không cần đọc

```text
DeepSORT Output
```

---

# 9. Các quyết định ADAS có thể đưa ra

Ví dụ

Offset

```text
25
```

↓

Không cảnh báo.

---

Offset

```text
90
```

↓

Lane Departure Warning.

---

Traffic Rule

```text
STOP
```

↓

Prepare To Stop.

---

Traffic Rule

```text
Speed Limit 40
```

↓

Kiểm tra tốc độ hiện tại.

---

Lane Status

```text
outside_lane
```

↓

Lane Warning.

---

# 10. Thiết kế Data Model đề xuất

Fusion nên sinh ra một đối tượng SceneContext.

Ví dụ

```python
SceneContext
│
├── frame
├── timestamp
├── vehicles
│      ├── track_id
│      ├── type
│      ├── lane
│      ├── lane_status
│      ├── offset
│      ├── center
│      └── speed
│
└── traffic_rule
       ├── type
       └── value
```

ADAS chỉ cần đọc đối tượng này.

Không cần biết dữ liệu đến từ mô hình AI nào.

---

# 11. Quy tắc thiết kế

Fusion Output phải tuân thủ các nguyên tắc sau:

* Không chứa Tensor.
* Không chứa YOLO Result.
* Không chứa DeepLab Result.
* Không chứa DeepSORT Object.
* Không chứa dữ liệu trung gian.

Fusion chỉ được phép trả về dữ liệu đã được chuẩn hóa.

---

# 12. Mục tiêu cuối cùng

Sau khi hoàn thành Fusion, toàn bộ dữ liệu AI sẽ được chuyển đổi thành **Scene Context** có ý nghĩa.

Ví dụ:

```json
{
    "frame": 152,
    "vehicles": [
        {
            "track_id": 5,
            "type": "car",
            "lane": "center",
            "lane_status": "inside_lane",
            "offset": 25,
            "center": [350,420],
            "speed": null
        }
    ],
    "traffic_rule": {
        "type": "Speed Limit",
        "value": 40
    },
    "timestamp": "00:00:05.233"
}
```

Đây là **chuẩn dữ liệu duy nhất** mà ADAS Decision Engine được phép sử dụng để:

* Lane Departure Warning.
* Lane Keeping Assist.
* Speed Limit Warning.
* Stop Warning.
* No Entry Warning.
* Dashboard.
* Logging.
* Evaluation.

Việc chuẩn hóa đầu ra theo một cấu trúc thống nhất giúp hệ thống dễ mở rộng, dễ bảo trì và cho phép thay thế các mô hình AI (YOLO, DeepLab, DeepSORT...) mà không cần sửa đổi tầng ADAS.
# 05_ADAS_DECISION_ENGINE.md

> **Tên tài liệu:** ADAS Decision Engine Specification
> **Phiên bản:** 1.0
> **Mục tiêu:** Định nghĩa cách ADAS sử dụng dữ liệu đầu ra từ Fusion (Scene Context) để đưa ra các quyết định hỗ trợ người lái. ADAS không thực hiện AI mà chỉ phân tích dữ liệu ngữ cảnh và sinh ra cảnh báo.

---

# 1. Mục đích

Sau khi Fusion hoàn thành việc tổng hợp dữ liệu và tạo ra **Scene Context**, toàn bộ trách nhiệm tiếp theo thuộc về **ADAS Decision Engine**.

ADAS không còn làm việc với:

* YOLO Detection
* DeepLab Lane Mask
* DeepSORT Tracking
* Bounding Box
* Tensor

ADAS chỉ đọc duy nhất **Scene Context** do Fusion tạo ra.

---

# 2. Kiến trúc

```text
Fusion
      │
      ▼
==========================
      Scene Context
==========================
      │
      ▼
ADAS Decision Engine
      │
      ├── Lane Decision
      ├── Traffic Rule Decision
      ├── Vehicle Decision
      ├── Pedestrian Decision
      ├── Collision Decision
      └── Warning Manager
      │
      ▼
Dashboard / UI
```

ADAS không thực hiện nhận diện đối tượng.

ADAS chỉ đưa ra quyết định.

---

# 3. Dữ liệu đầu vào

ADAS nhận duy nhất một đối tượng.

Ví dụ

```python
SceneContext
```

Ví dụ

```json
{
    "frame":152,

    "vehicles":[
        {
            "track_id":5,
            "type":"car",
            "lane":"center",
            "lane_status":"inside_lane",
            "offset":80
        }
    ],

    "traffic_rule":{
        "type":"Speed Limit",
        "value":40
    }
}
```

---

# 4. Chức năng 1 - Lane Departure Warning

## Mục tiêu

Cảnh báo khi xe bắt đầu lệch khỏi làn đường.

---

## Input

```text
Vehicle Offset
```

Ví dụ

```text
Offset = 80 pixel
```

---

## Xử lý

Ví dụ

```text
Offset

↓

So sánh với Threshold
```

Nếu

```text
Offset > Threshold
```

↓

```text
Lane Departure Warning
```

---

Ví dụ

```text
Offset = 20
```

↓

```text
Không cảnh báo
```

---

Ví dụ

```text
Offset = 80
```

↓

```text
Lane Departure Warning
```

---

## Output

```json
{
    "warning":"Lane Departure",
    "level":"HIGH"
}
```

---

# 5. Chức năng 2 - STOP Sign Decision

## Mục tiêu

Cảnh báo người lái chuẩn bị dừng xe khi gặp biển STOP.

---

## Input

Fusion

```text
Current Rule

STOP
```

---

## Xử lý

```text
STOP

↓

Prepare To Stop
```

ADAS có thể:

* Hiển thị cảnh báo.
* Phát âm thanh.
* Hiển thị biểu tượng STOP.

---

## Output

```json
{
    "warning":"STOP",
    "action":"Prepare To Stop"
}
```

---

# 6. Chức năng 3 - No Entry Warning

## Input

Fusion

```text
Current Rule

NO_ENTRY
```

---

## Xử lý

```text
NO_ENTRY

↓

No Entry Warning
```

---

## Output

```json
{
    "warning":"No Entry"
}
```

---

# 7. Chức năng 4 - Speed Limit Warning

## Input

Fusion

```json
{
    "type":"Speed Limit",
    "value":40
}
```

---

## Xử lý

ADAS lấy

```text
Current Speed
```

↓

So sánh

```text
Vehicle Speed

>

Speed Limit
```

---

Ví dụ

```text
Vehicle Speed

60
```

```text
Speed Limit

40
```

↓

```text
Overspeed Warning
```

---

Nếu

```text
Vehicle Speed

35
```

↓

```text
Không cảnh báo
```

---

## Output

```json
{
    "warning":"Overspeed",
    "limit":40
}
```

---

# 8. Chức năng 5 - Lane Status Decision

Fusion trả

```text
inside_lane
```

↓

```text
Không cảnh báo
```

---

Fusion trả

```text
near_boundary
```

↓

```text
Low Warning
```

---

Fusion trả

```text
outside_lane
```

↓

```text
High Warning
```

---

Fusion trả

```text
crossing_lane
```

↓

```text
Emergency Warning
```

---

# 9. Chức năng 6 - Vehicle Decision (Mở rộng)

Trong tương lai.

Fusion có thể trả

```json
{
    "distance":8.5
}
```

↓

ADAS

↓

```text
Forward Collision Warning
```

---

Hoặc

```json
{
    "time_to_collision":1.5
}
```

↓

```text
Brake Warning
```

---

# 10. Chức năng 7 - Pedestrian Decision (Mở rộng)

Fusion trả

```json
{
    "pedestrian":true,
    "distance":6
}
```

↓

ADAS

↓

```text
Pedestrian Warning
```

---

# 11. Warning Manager

Đây là module cuối cùng của ADAS.

Nhiệm vụ

* Tổng hợp tất cả cảnh báo.
* Loại bỏ cảnh báo trùng.
* Xác định mức độ ưu tiên.
* Gửi cảnh báo đến Dashboard.

---

Ví dụ

```text
Lane Departure

Priority = Medium
```

---

```text
STOP

Priority = High
```

---

```text
Forward Collision

Priority = Critical
```

---

Nếu nhiều cảnh báo xuất hiện cùng lúc.

Warning Manager sẽ ưu tiên.

Ví dụ

```text
Forward Collision

>

STOP

>

Lane Departure
```

---

# 12. Output của ADAS

ADAS sẽ tạo ra danh sách cảnh báo.

Ví dụ

```json
{
    "frame":152,

    "warnings":[

        {
            "type":"Lane Departure",
            "priority":"HIGH"
        },

        {
            "type":"Speed Limit",
            "value":40
        }

    ]
}
```

---

# 13. Kiến trúc đề xuất

```text
adas/
│
├── decision_engine.py
│
├── lane_departure.py
│
├── traffic_rule.py
│
├── speed_limit.py
│
├── stop_warning.py
│
├── no_entry_warning.py
│
├── warning_manager.py
│
├── collision_warning.py
│
├── pedestrian_warning.py
│
├── dashboard_output.py
│
├── data_models.py
│
└── utils.py
```

Mỗi module chỉ xử lý **một loại quyết định**, giúp hệ thống dễ mở rộng và tuân thủ nguyên tắc **Single Responsibility Principle (SRP)**.

---

# 14. Luồng hoạt động

```text
Fusion
      │
      ▼
Scene Context
      │
      ▼
Decision Engine
      │
      ├── Lane Decision
      ├── Traffic Rule Decision
      ├── Speed Decision
      ├── Collision Decision
      ├── Pedestrian Decision
      │
      ▼
Warning Manager
      │
      ▼
Dashboard
```

---

# 15. Quy tắc thiết kế

ADAS không được:

* Chạy YOLO.
* Chạy DeepLab.
* Chạy DeepSORT.
* Thực hiện Fusion.
* Đọc Bounding Box.
* Đọc Lane Mask.
* Đọc Tensor.

ADAS chỉ được phép:

* Đọc Scene Context.
* Phân tích luật giao thông.
* Phân tích trạng thái phương tiện.
* Sinh cảnh báo.
* Gửi dữ liệu đến Dashboard.

---

# 16. Mục tiêu cuối cùng

ADAS Decision Engine là tầng ra quyết định của hệ thống.

Nó không quan tâm mô hình AI nào được sử dụng (YOLO, DeepLabV3+, DeepSORT...), mà chỉ làm việc với **Scene Context** do Fusion cung cấp.

Điều này mang lại các lợi ích:

* Tách biệt hoàn toàn giữa tầng AI và tầng quyết định.
* Dễ thay thế hoặc nâng cấp mô hình AI mà không ảnh hưởng đến ADAS.
* Dễ mở rộng thêm các chức năng như Forward Collision Warning, Pedestrian Warning, Adaptive Cruise Control hoặc Automatic Emergency Braking trong tương lai.
# 06_FUSION_MODULE_ARCHITECTURE.md

> **Tên tài liệu:** Fusion Module Architecture
> **Phiên bản:** 1.0
> **Mục tiêu:** Định nghĩa kiến trúc bên trong của thư mục `fusion/`, vai trò của từng module, Input, Output, quan hệ giữa các module và luồng xử lý dữ liệu trước khi chuyển sang ADAS Decision Engine.

---

# 1. Mục đích

Fusion là tầng trung gian giữa các mô hình AI và ADAS.

Fusion **không phải là một mô hình AI mới**.

Fusion là tập hợp các module xử lý dữ liệu nhằm:

* Kết hợp kết quả từ nhiều mô hình AI.
* Hiểu ngữ cảnh giao thông.
* Chuẩn hóa dữ liệu.
* Sinh ra Scene Context.
* Cung cấp dữ liệu thống nhất cho ADAS.

---

# 2. Kiến trúc Fusion

```text
AI Models
│
├── Vehicle Detection
├── Pedestrian Detection
├── Lane Detection
├── Traffic Sign Detection
└── DeepSORT Tracking
            │
            ▼
==========================
         FUSION
==========================
│
├── vehicle_lane_fusion.py
├── traffic_sign_fusion.py
├── tracking_fusion.py
├── scene_understanding.py
└── decision_engine.py
            │
            ▼
      Scene Context
            │
            ▼
ADAS Decision Engine
```

---

# 3. Cấu trúc thư mục

```text
backend/
└── ai-service/
    └── fusion/
        │
        ├── __init__.py
        │
        ├── vehicle_lane_fusion.py
        │
        ├── traffic_sign_fusion.py
        │
        ├── tracking_fusion.py
        │
        ├── scene_understanding.py
        │
        ├── decision_engine.py
        │
        ├── data_models.py
        │
        ├── config.py
        │
        ├── utils.py
        │
        └── README.md
```

---

# 4. vehicle_lane_fusion.py

## Mục tiêu

Xác định phương tiện đang nằm ở làn đường nào.

---

## Input

Vehicle Detection

```python
bbox
class
confidence
```

Lane Detection

```python
lane_left
lane_right
lane_center
lane_mask
```

---

## Xử lý

* Tính tâm xe.
* So sánh với Lane Center.
* Kiểm tra xe nằm trong Lane Mask.
* Xác định trạng thái xe.

---

## Output

```python
{
    "track_id":5,
    "lane":"center",
    "lane_status":"inside_lane",
    "offset":25
}
```

---

## Module này KHÔNG được

* Đọc biển báo.
* Theo dõi xe.
* Sinh Scene Context.

---

# 5. traffic_sign_fusion.py

## Mục tiêu

Biến kết quả nhận diện biển báo thành luật giao thông hiện hành.

---

## Input

Traffic Sign Detection

Ví dụ

```python
Speed Limit 40
```

---

## Xử lý

Ví dụ

```text
Speed Limit

↓

Current Rule

40 km/h
```

---

Ví dụ

```text
STOP

↓

Current Rule = STOP
```

---

Ví dụ

```text
No Entry

↓

Current Rule = NO_ENTRY
```

---

## Output

```python
{
    "current_rule":"Speed Limit",
    "value":40
}
```

---

## Module này KHÔNG được

* Tính Offset.
* Ghép Track ID.
* Xử lý Lane.

---

# 6. tracking_fusion.py

## Mục tiêu

Liên kết Detection với DeepSORT.

---

## Input

Vehicle Detection

Tracking

---

Ví dụ

Vehicle

```python
bbox
```

Tracking

```python
track_id
bbox
```

---

## Xử lý

* Ghép Detection với Track ID.
* Kiểm tra đối tượng còn tồn tại.
* Đồng bộ ID.

---

## Output

```python
{
    "track_id":5,
    "tracking":true
}
```

---

## Module này KHÔNG được

* Xử lý Lane.
* Xử lý biển báo.
* Sinh Scene Context.

---

# 7. scene_understanding.py

## Đây là module quan trọng nhất.

Nó nhận kết quả từ toàn bộ module Fusion.

Input

```text
Vehicle Lane Fusion

↓

Traffic Rule

↓

Tracking
```

↓

Tổng hợp.

---

## Nhiệm vụ

Tạo một bản mô tả hoàn chỉnh của khung hình.

Ví dụ

```python
Frame

↓

Vehicle

↓

Lane

↓

Offset

↓

Traffic Rule

↓

Tracking
```

↓

Scene Context.

---

## Output

```python
{
    "frame":152,

    "vehicles":[
        ...
    ],

    "traffic_rule":{

    }

}
```

---

## Module này KHÔNG được

* Sinh cảnh báo.
* Đưa ra quyết định.
* Hiển thị Dashboard.

---

# 8. decision_engine.py

Đây là module cuối cùng của Fusion.

Nhiệm vụ

Chuẩn hóa Scene Context trước khi chuyển sang ADAS.

---

## Input

Scene Context.

---

## Xử lý

* Kiểm tra dữ liệu.
* Chuẩn hóa kiểu dữ liệu.
* Kiểm tra trường thiếu.
* Đảm bảo đúng Data Model.

---

## Output

```python
SceneContext
```

Chuẩn để ADAS sử dụng.

---

## Không được

* Cảnh báo.
* Đưa quyết định.
* Hiển thị giao diện.

Các nhiệm vụ trên thuộc ADAS.

---

# 9. data_models.py

## Mục tiêu

Định nghĩa toàn bộ Data Model dùng trong Fusion.

Ví dụ

```python
VehicleInfo

LaneInfo

TrafficRule

SceneContext
```

Mọi module Fusion đều sử dụng các Model này.

Không tạo Dictionary tùy ý.

---

# 10. config.py

Lưu toàn bộ cấu hình.

Ví dụ

```python
Lane Threshold

Offset Threshold

Confidence Threshold
```

Không hard-code trong source.

---

# 11. utils.py

Chứa các hàm dùng chung.

Ví dụ

* Tính tâm Bounding Box.
* Tính khoảng cách.
* Chuyển đổi tọa độ.
* Kiểm tra giao nhau.
* Logging.

Không chứa Business Logic.

---

# 12. Quan hệ giữa các module

```text
Vehicle Detection
        │
        ▼
vehicle_lane_fusion.py
        │
        ▼
tracking_fusion.py
        │
        ▼
traffic_sign_fusion.py
        │
        ▼
scene_understanding.py
        │
        ▼
decision_engine.py
        │
        ▼
Scene Context
```

Không được gọi ngược.

Ví dụ

```text
scene_understanding.py

×

vehicle_lane_fusion.py
```

Điều này vi phạm kiến trúc.

---

# 13. Nguyên tắc thiết kế

Mỗi file chỉ đảm nhận **một nhiệm vụ duy nhất**.

| Module                 | Trách nhiệm                                 |
| ---------------------- | ------------------------------------------- |
| vehicle_lane_fusion.py | Xác định xe thuộc làn nào                   |
| traffic_sign_fusion.py | Phân tích luật giao thông hiện hành         |
| tracking_fusion.py     | Ghép Track ID với Detection                 |
| scene_understanding.py | Tổng hợp toàn bộ dữ liệu của frame          |
| decision_engine.py     | Chuẩn hóa Scene Context để chuyển sang ADAS |
| data_models.py         | Định nghĩa Data Model                       |
| config.py              | Quản lý cấu hình                            |
| utils.py               | Hàm hỗ trợ dùng chung                       |

---

# 14. Quy trình hoạt động

```text
Frame

↓

Vehicle Detection

↓

Lane Detection

↓

Traffic Sign Detection

↓

Tracking

↓

Vehicle Lane Fusion

↓

Traffic Sign Fusion

↓

Tracking Fusion

↓

Scene Understanding

↓

Decision Engine

↓

Scene Context

↓

ADAS
```

---

# 15. Quy tắc lập trình

Mỗi module phải tuân thủ:

* Chỉ xử lý đúng một nhiệm vụ (Single Responsibility Principle).
* Không truy cập trực tiếp module AI.
* Không xử lý giao diện.
* Không đọc Video.
* Không lưu dữ liệu xuống Database.
* Không sinh cảnh báo.

Toàn bộ module Fusion chỉ có nhiệm vụ **chuyển đổi dữ liệu AI thành dữ liệu ngữ cảnh giao thông (Scene Context)**.

---

# 16. Mục tiêu cuối cùng

Sau khi hoàn thành thư mục `fusion/`, hệ thống sẽ tạo ra một tầng xử lý trung gian hoàn chỉnh giữa AI và ADAS.

Mọi mô hình AI (YOLO, DeepLabV3+, DeepSORT...) đều chỉ cần cung cấp dữ liệu theo chuẩn đã định nghĩa.

Fusion sẽ chịu trách nhiệm:

* Phân tích vị trí phương tiện.
* Xác định làn đường.
* Theo dõi đối tượng.
* Áp dụng luật giao thông hiện hành.
* Tổng hợp toàn bộ thông tin thành **Scene Context**.

Kết quả cuối cùng là một đối tượng `SceneContext` thống nhất, ổn định và độc lập với các mô hình AI, giúp ADAS có thể đưa ra quyết định mà không cần biết dữ liệu ban đầu đến từ mô hình nào.
# 07_FUSION_DATA_FLOW.md

> **Tên tài liệu:** Fusion Data Flow
> **Phiên bản:** 1.0
> **Mục tiêu:** Mô tả chi tiết luồng dữ liệu bên trong Fusion, từ khi nhận kết quả của các mô hình AI cho đến khi sinh ra **Scene Context** và **Decision Data** cho ADAS Decision Engine.

---

# 1. Mục đích

Fusion không thực hiện nhận diện đối tượng.

Fusion không thực hiện phân đoạn làn đường.

Fusion không thực hiện Tracking.

Fusion chỉ tiếp nhận dữ liệu từ các mô hình AI, xử lý theo một quy trình thống nhất và tạo ra dữ liệu ngữ cảnh giao thông (Scene Context).

Luồng dữ liệu này là trung tâm của toàn bộ hệ thống ADAS.

---

# 2. Luồng dữ liệu tổng thể

```text
                   YOLO Detection
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
      Vehicle          Person        Traffic Sign
        │
        ▼
               DeepLabV3+
                    │
                    ▼
               Lane Mask
                    │
                    ▼
               DeepSORT
                    │
                    ▼
               Tracking ID
                    │
                    ▼
==============================================
                  FUSION
==============================================
                    │
                    ▼
          Vehicle Center Calculation
                    │
                    ▼
           Lane Center Extraction
                    │
                    ▼
            Lane Offset Calculation
                    │
                    ▼
         Lane Position Classification
                    │
                    ▼
        Traffic Rule Interpretation
                    │
                    ▼
         Object Tracking Association
                    │
                    ▼
          Scene Understanding Engine
                    │
                    ▼
            Scene Context Generator
                    │
                    ▼
              Decision Data Output
                    │
                    ▼
          ADAS Decision Engine
```

Đây là luồng xử lý chuẩn của Fusion.

Không được thay đổi thứ tự xử lý.

---

# 3. Bước 1 - Nhận dữ liệu từ AI Models

Fusion nhận dữ liệu từ bốn nguồn chính.

## Vehicle Detection

```python
[
    {
        "id":1,
        "class":"car",
        "bbox":[120,250,310,420]
    }
]
```

---

## Lane Detection

```python
{
    "lane_left":[...],
    "lane_right":[...],
    "lane_center":[...],
    "mask":...
}
```

---

## Traffic Sign Detection

```python
[
    {
        "type":"Speed Limit",
        "value":40
    }
]
```

---

## DeepSORT Tracking

```python
[
    {
        "track_id":5,
        "bbox":[120,250,310,420]
    }
]
```

---

Sau bước này Fusion vẫn chưa hiểu được ngữ cảnh giao thông.

Nó chỉ có dữ liệu thô.

---

# 4. Bước 2 - Vehicle Center Calculation

## Mục tiêu

Tính tâm của từng phương tiện.

Input

```text
Bounding Box
```

Ví dụ

```text
[300,320,400,520]
```

↓

Fusion tính

```text
Vehicle Center

(350,420)
```

---

## Output

```python
{
    "center":[350,420]
}
```

---

Mỗi xe đều phải có tâm.

Đây là dữ liệu quan trọng nhất cho các bước sau.

---

# 5. Bước 3 - Lane Center Extraction

Fusion lấy dữ liệu từ Lane Detection.

Ví dụ

```text
Lane Left = 250

Lane Right = 450
```

↓

Fusion xác định

```text
Lane Center

320
```

Nếu Lane Detection đã trả về Lane Center thì Fusion sử dụng trực tiếp.

Nếu chưa có thì Fusion sẽ tính toán.

---

# 6. Bước 4 - Lane Offset Calculation

Sau khi có

```text
Vehicle Center
```

và

```text
Lane Center
```

Fusion tính

```text
Offset

=

Vehicle Center

-

Lane Center
```

Ví dụ

```text
Vehicle Center

350
```

```text
Lane Center

320
```

↓

```text
Offset

30 pixel
```

---

Offset là dữ liệu quan trọng nhất của Lane Departure Warning.

---

# 7. Bước 5 - Lane Position Classification

Fusion xác định xe thuộc làn nào.

Ví dụ

```text
Lane Left

250
```

```text
Lane Right

450
```

```text
Vehicle Center

350
```

↓

```text
Vehicle nằm trong lane
```

Fusion sinh

```python
{
    "lane":"center",

    "lane_status":"inside_lane"
}
```

---

Nếu

```text
Vehicle Center

470
```

↓

Fusion

```python
{
    "lane_status":"outside_lane"
}
```

---

# 8. Bước 6 - Traffic Rule Interpretation

Fusion nhận kết quả từ Traffic Sign Detection.

Ví dụ

```text
Speed Limit 40
```

↓

Fusion tạo

```text
Current Rule

Speed Limit = 40
```

---

Ví dụ

```text
STOP
```

↓

```text
Current Rule

STOP
```

---

Ví dụ

```text
No Entry
```

↓

```text
Current Rule

NO_ENTRY
```

---

Fusion không chỉ lưu biển báo.

Fusion phải hiểu ý nghĩa của biển báo.

---

# 9. Bước 7 - Object Tracking Association

Fusion ghép Detection với DeepSORT.

Ví dụ

```text
Frame 1

Track ID = 5
```

↓

```text
Frame 2

Track ID = 5
```

↓

```text
Frame 3

Track ID = 5
```

Fusion hiểu

Đây vẫn là cùng một chiếc xe.

---

Fusion sẽ lưu

```python
{
    "track_id":5,

    "tracking":True
}
```

---

# 10. Bước 8 - Scene Understanding

Đây là bước quan trọng nhất.

Fusion bắt đầu tổng hợp tất cả dữ liệu.

Ví dụ

```text
Vehicle

+

Lane

+

Offset

+

Traffic Rule

+

Tracking
```

↓

Fusion tạo

```python
Scene Context
```

Ví dụ

```python
{
    "track_id":5,

    "vehicle_type":"car",

    "lane":"center",

    "offset":30,

    "traffic_rule":"Speed Limit",

    "tracking":True
}
```

Tại thời điểm này hệ thống đã hiểu được ngữ cảnh giao thông của khung hình.

---

# 11. Bước 9 - Decision Data Generation

Scene Context vẫn còn khá chi tiết.

Fusion sẽ chuẩn hóa dữ liệu để ADAS sử dụng.

Ví dụ

```python
Scene Context
```

↓

```python
Decision Data
```

Ví dụ

```python
{
    "lane_departure":False,

    "traffic_rule":"Speed Limit",

    "offset":30,

    "track_id":5
}
```

Decision Data là dữ liệu đầu vào trực tiếp của ADAS Decision Engine.

---

# 12. Luồng dữ liệu bên trong Fusion

```text
Vehicle Detection
        │
        ▼
Vehicle Center
        │
        ▼
Lane Center
        │
        ▼
Lane Offset
        │
        ▼
Lane Status
        │
        ▼
Traffic Rule
        │
        ▼
Tracking Association
        │
        ▼
Scene Understanding
        │
        ▼
Scene Context
        │
        ▼
Decision Data
```

Mỗi bước đều sử dụng kết quả của bước trước.

Không được bỏ qua bất kỳ bước nào.

---

# 13. Quan hệ giữa các module

| Module                        | Input                        | Output        |
| ----------------------------- | ---------------------------- | ------------- |
| vehicle_lane_fusion.py        | Vehicle + Lane               | Lane, Offset  |
| traffic_sign_fusion.py        | Traffic Sign                 | Current Rule  |
| tracking_fusion.py            | Detection + Tracking         | Track ID      |
| scene_understanding.py        | Lane + Offset + Rule + Track | Scene Context |
| decision_engine.py *(Fusion)* | Scene Context                | Decision Data |

---

# 14. Dữ liệu chuyển sang ADAS

Sau khi Fusion hoàn thành toàn bộ quy trình, ADAS chỉ nhận một đối tượng duy nhất.

```python
{
    "frame":152,

    "vehicles":[
        {
            "track_id":5,
            "type":"car",

            "lane":"center",

            "lane_status":"inside_lane",

            "offset":30
        }
    ],

    "traffic_rule":{
        "type":"Speed Limit",
        "value":40
    }
}
```

ADAS sẽ không cần biết:

* Xe được phát hiện bởi YOLO.
* Làn đường được tạo bởi DeepLabV3+.
* Track ID đến từ DeepSORT.

Tất cả đã được Fusion chuẩn hóa.

---

# 15. Quy tắc thiết kế

Fusion Data Flow phải tuân thủ các nguyên tắc sau:

* Dữ liệu chỉ đi theo một chiều.
* Mỗi bước chỉ thực hiện một nhiệm vụ.
* Không có xử lý lặp giữa các module.
* Không gọi trực tiếp mô hình AI trong Fusion.
* Mọi dữ liệu trung gian đều phải được chuẩn hóa trước khi chuyển sang bước tiếp theo.

---

# 16. Mục tiêu cuối cùng

Sau khi hoàn thành toàn bộ luồng dữ liệu, Fusion sẽ chuyển đổi kết quả từ nhiều mô hình AI thành một **Decision Data** thống nhất.

Quá trình này có thể được tóm tắt như sau:

```text
YOLO
   │
   ▼
DeepLabV3+
   │
   ▼
DeepSORT
   │
   ▼
Fusion
   │
   ├── Vehicle Center
   ├── Lane Center
   ├── Lane Offset
   ├── Lane Status
   ├── Traffic Rule
   ├── Tracking Association
   ├── Scene Understanding
   └── Decision Data
          │
          ▼
ADAS Decision Engine
          │
          ▼
Dashboard / Warning System
```

Nhờ luồng dữ liệu này, kiến trúc hệ thống được phân tách rõ ràng thành ba tầng:

1. **AI Layer**: Thực hiện nhận diện, phân đoạn và theo dõi đối tượng.
2. **Fusion Layer**: Tổng hợp dữ liệu, hiểu ngữ cảnh và chuẩn hóa thông tin giao thông.
3. **ADAS Layer**: Đưa ra quyết định, sinh cảnh báo và hiển thị cho người lái.

Sự phân tách này giúp hệ thống dễ bảo trì, dễ mở rộng và cho phép thay thế hoặc nâng cấp từng mô hình AI mà không ảnh hưởng đến tầng ra quyết định của ADAS.
# 08_FUSION_COMPLETION_OBJECTIVES.md

> **Tên tài liệu:** Fusion Completion Objectives
> **Phiên bản:** 1.0
> **Mục tiêu:** Xác định trạng thái cuối cùng mà module Fusion phải đạt được sau khi hoàn thành toàn bộ quá trình xử lý dữ liệu. Đây là tiêu chí đánh giá (Acceptance Criteria) cho toàn bộ tầng Fusion trước khi dữ liệu được chuyển sang ADAS.

---

# 1. Mục đích

Fusion là tầng trung gian giữa các mô hình AI và ADAS.

Mục tiêu cuối cùng của Fusion **không phải** là phát hiện thêm đối tượng hay cải thiện độ chính xác của mô hình AI.

Mục tiêu của Fusion là:

* Tổng hợp dữ liệu từ nhiều mô hình AI.
* Hiểu ngữ cảnh giao thông.
* Chuẩn hóa toàn bộ dữ liệu.
* Tạo ra **Scene Context**.
* Cung cấp dữ liệu thống nhất cho ADAS.

---

# 2. Trạng thái của hệ thống trước Fusion

Trước khi đi qua Fusion, hệ thống chỉ có các kết quả rời rạc.

Ví dụ

```text id="8ljowv"
YOLO
│
├── Car
├── Person
├── Motorcycle
└── Traffic Sign
```

↓

```text id="w5lmxs"
DeepLabV3+
│
└── Lane Mask
```

↓

```text id="u1gxmw"
DeepSORT
│
└── Track ID
```

Mỗi mô hình chỉ hiểu nhiệm vụ của chính nó.

Không mô hình nào hiểu toàn bộ bối cảnh giao thông.

Ví dụ

YOLO biết

```text id="b3wn8v"
Có một chiếc xe.
```

Nhưng không biết

* Xe đang ở làn nào.
* Xe có lệch làn không.
* Xe có vượt tốc độ không.
* Xe có đang vi phạm biển báo không.

---

DeepLab chỉ biết

```text id="y0e95o"
Lane Mask
```

Nhưng không biết

* Xe nào nằm trong làn.
* Xe nào đang cắt vạch.

---

DeepSORT chỉ biết

```text id="f4ht8d"
Track ID
```

Nhưng không biết

* Xe đó ở làn nào.
* Xe đó có đang vi phạm không.

---

# 3. Nhiệm vụ cuối cùng của Fusion

Fusion phải kết hợp tất cả dữ liệu trên thành một ngữ cảnh giao thông hoàn chỉnh.

Luồng xử lý

```text id="jlwmhj"
Vehicle Detection
        │
Lane Detection
        │
Traffic Sign Detection
        │
Tracking
        │
        ▼
==========================
         Fusion
==========================
        │
        ▼
   Scene Context
```

Scene Context là kết quả cuối cùng của tầng Fusion.

---

# 4. Scene Context

Scene Context là bản mô tả đầy đủ của một khung hình.

Nó không còn chứa dữ liệu AI thô.

Ví dụ

Fusion sẽ không lưu

```text id="zphbnp"
Bounding Box

Tensor

Mask
```

Thay vào đó.

Fusion sẽ lưu

```text id="k4mpg7"
Xe đang ở làn nào.

Xe lệch bao nhiêu.

Biển báo hiện tại.

Đối tượng nào đang được theo dõi.
```

---

# 5. Ví dụ Scene Context chuẩn

```json id="zkjlwm"
{
    "frame":152,

    "vehicles":[

        {
            "track_id":1,

            "type":"car",

            "lane":"center",

            "offset":12,

            "status":"inside_lane"
        },

        {
            "track_id":2,

            "type":"motorcycle",

            "lane":"left",

            "offset":-35,

            "status":"near_lane_boundary"
        }

    ],

    "traffic_rule":{

        "type":"Speed Limit",

        "value":40

    }
}
```

Đây là dữ liệu chuẩn mà ADAS sẽ sử dụng.

---

# 6. Ý nghĩa của Scene Context

Scene Context giúp hệ thống hiểu được toàn bộ tình trạng giao thông của một khung hình.

Ví dụ.

Fusion biết

```text id="06mjhm"
Có 2 phương tiện.
```

Fusion biết

```text id="h6g2r6"
Xe số 1

đang ở giữa làn.
```

Fusion biết

```text id="08cb6e"
Xe số 2

đang gần vạch phân làn.
```

Fusion biết

```text id="9z69r2"
Giới hạn tốc độ

40 km/h.
```

Toàn bộ thông tin này được gom lại thành một đối tượng duy nhất.

---

# 7. ADAS sử dụng Scene Context như thế nào

ADAS chỉ cần đọc Scene Context.

Ví dụ

```python id="ntmruk"
SceneContext

↓

vehicle.offset
```

↓

```text id="9e68fv"
12 pixel
```

↓

Không cảnh báo.

---

Ví dụ

```python id="wzzg4u"
SceneContext

↓

vehicle.offset
```

↓

```text id="e5mjlwm"
80 pixel
```

↓

```text id="c8d5zc"
Lane Departure Warning
```

---

Ví dụ

```python id="wjlwmj"
SceneContext

↓

traffic_rule
```

↓

```text id="ww7lml"
STOP
```

↓

```text id="i3e4yx"
Prepare To Stop
```

---

Ví dụ

```python id="6g1k0w"
SceneContext

↓

traffic_rule
```

↓

```text id="vzwjlwm"
NO_ENTRY
```

↓

```text id="31mgo8"
No Entry Warning
```

---

# 8. Dashboard sử dụng Scene Context

Dashboard không đọc YOLO.

Dashboard không đọc DeepLab.

Dashboard không đọc DeepSORT.

Dashboard chỉ đọc Scene Context.

Ví dụ

Dashboard hiển thị

```text id="0hsbwt"
Vehicle

Lane

Offset

Traffic Rule

Warning
```

Dashboard hoàn toàn độc lập với các mô hình AI.

---

# 9. Tiêu chí hoàn thành Fusion

Fusion được xem là hoàn thành khi đáp ứng toàn bộ các tiêu chí sau.

| Tiêu chí                                | Trạng thái |
| --------------------------------------- | ---------- |
| Nhận dữ liệu từ Vehicle Detection       | ✅          |
| Nhận dữ liệu từ Lane Detection          | ✅          |
| Nhận dữ liệu từ Traffic Sign Detection  | ✅          |
| Nhận dữ liệu từ Tracking                | ✅          |
| Xác định làn đường của từng phương tiện | ✅          |
| Tính Lane Offset                        | ✅          |
| Xác định Lane Status                    | ✅          |
| Xử lý Traffic Rule                      | ✅          |
| Liên kết Track ID                       | ✅          |
| Sinh Scene Context                      | ✅          |
| Chuẩn hóa dữ liệu                       | ✅          |
| Chuyển dữ liệu cho ADAS                 | ✅          |

Chỉ khi tất cả tiêu chí đều đạt thì Fusion mới được xem là hoàn thành.

---

# 10. Kiến trúc cuối cùng của tầng Fusion

```text id="u9jlwm"
AI Models
│
├── Vehicle Detection
├── Pedestrian Detection
├── Lane Detection
├── Traffic Sign Detection
└── DeepSORT Tracking
            │
            ▼
==============================
             Fusion
==============================
│
├── Vehicle Lane Fusion
├── Lane Offset Calculation
├── Traffic Rule Interpretation
├── Tracking Association
├── Scene Understanding
└── Scene Context Generation
            │
            ▼
        Scene Context
```

Đây là đầu ra duy nhất của Fusion.

---

# 11. Vai trò của ADAS

Sau khi nhận Scene Context.

ADAS sẽ thực hiện:

* Lane Departure Warning.
* Lane Keeping Assist.
* Speed Limit Warning.
* STOP Warning.
* No Entry Warning.
* Dashboard Notification.
* Các chức năng mở rộng như Collision Warning hoặc Pedestrian Warning trong tương lai.

ADAS không cần biết dữ liệu ban đầu đến từ mô hình AI nào.

---

# 12. Mô hình phân tầng của toàn hệ thống

```text id="b5jlwm"
=========================
       AI Layer
=========================
│
├── YOLO
├── DeepLabV3+
└── DeepSORT
        │
        ▼
=========================
     Fusion Layer
=========================
│
├── Vehicle Lane Fusion
├── Traffic Rule Fusion
├── Tracking Fusion
├── Scene Understanding
└── Scene Context
        │
        ▼
=========================
      ADAS Layer
=========================
│
├── Decision Engine
├── Warning Manager
├── Dashboard
└── Driver Notification
```

Ba tầng này phải hoàn toàn tách biệt để đảm bảo khả năng bảo trì và mở rộng hệ thống.

---

# 13. Acceptance Criteria

Fusion được xem là hoàn thành khi đáp ứng đầy đủ các điều kiện sau:

* Có thể nhận dữ liệu từ tất cả các mô hình AI.
* Không phụ thuộc vào cách triển khai nội bộ của YOLO, DeepLabV3+ hoặc DeepSORT.
* Có khả năng tổng hợp dữ liệu thành một Scene Context thống nhất.
* Sinh ra dữ liệu theo đúng chuẩn Data Model đã định nghĩa.
* Có thể truyền trực tiếp Scene Context cho ADAS mà không cần xử lý trung gian.
* Mọi quyết định của ADAS đều dựa trên Scene Context thay vì dữ liệu AI thô.

---

# 14. Kết luận

Fusion là tầng **Scene Understanding** của hệ thống ADAS.

Giá trị lớn nhất của Fusion không nằm ở việc phát hiện thêm đối tượng, mà ở khả năng **biến dữ liệu kỹ thuật của các mô hình AI thành thông tin giao thông có ý nghĩa**.

Kết quả cuối cùng của Fusion là một **Scene Context** chuẩn hóa, phản ánh đầy đủ trạng thái của từng khung hình.

Từ thời điểm này, ADAS không còn làm việc với Bounding Box, Lane Mask hay Track ID riêng lẻ nữa. Mọi quyết định như cảnh báo lệch làn, giới hạn tốc độ, biển STOP, biển cấm đi ngược chiều và các cảnh báo khác đều được đưa ra dựa trên **Scene Context** do Fusion tạo ra.

Đây là cách phân tách kiến trúc được sử dụng phổ biến trong các hệ thống ADAS hiện đại, giúp hệ thống dễ mở rộng, dễ bảo trì và cho phép thay thế hoặc nâng cấp các mô hình AI mà không ảnh hưởng đến tầng ra quyết định.
