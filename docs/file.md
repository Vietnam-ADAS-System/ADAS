# Module: Lane Departure Warning (LDW)

## 1. User's Requirement

| Mục | Nội dung |
|------|----------|
| Module | Lane Departure Warning (LDW) |
| Mục tiêu | Phát hiện xe có đang đi đúng làn hay không và đưa ra cảnh báo khi xe lệch hoặc vượt khỏi làn đường. |
| Đầu vào | Dữ liệu từ Fusion (Vehicle Detection, Lane Detection, Tracking). |
| Đầu ra | Trạng thái xe (SAFE / NEAR BOUNDARY / LEFT LANE DEPARTURE / RIGHT LANE DEPARTURE) và cảnh báo hiển thị trên Dashboard. |
| Vai trò | Đây là module Decision Logic của ADAS, không trực tiếp chạy AI Model. |

---

# 2. Features

| Feature | Mô tả | Kết quả mong đợi |
|----------|-------|------------------|
| Receive Fusion Data | Nhận Vehicle Center, Lane Center, Lane Boundary, Tracking ID từ Fusion | Có đầy đủ dữ liệu đầu vào |
| Calculate Vehicle Offset | Tính khoảng cách giữa tâm xe và tâm làn | Offset (pixel) |
| Determine Vehicle Position | Xác định xe đang ở giữa làn, gần vạch hay vượt làn | SAFE / NEAR BOUNDARY / LANE DEPARTURE |
| Determine Departure Direction | Xác định xe lệch trái hay phải | LEFT / RIGHT |
| Generate Warning | Sinh cảnh báo khi vượt ngưỡng | Warning = TRUE/FALSE |
| Visualize Result | Hiển thị cảnh báo lên Dashboard và Video | Dashboard cập nhật theo thời gian thực |

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Vehicle Detection | YOLOv11 | Phát hiện xe và Bounding Box |
| Lane Detection | DeepLabV3+ hoặc Traditional CV | Phân đoạn làn đường |
| Tracking | DeepSORT | Theo dõi xe giữa các frame |
| Fusion | Fusion Module | Tổng hợp kết quả AI thành dữ liệu chuẩn |
| ADAS | Lane Departure Warning | Đưa ra quyết định và cảnh báo |
| Dashboard | React + NodeJS | Hiển thị kết quả theo thời gian thực |

---

# 4. Logic + AI Workflow

## Pipeline

```text
Video
    │
    ▼
YOLO Detection
    │
    ▼
Vehicle Center
    │
    ▼
DeepLab Lane Segmentation
    │
    ▼
Lane Center
    │
    ▼
Tracking
    │
    ▼
Fusion
    │
    ▼
Lane Departure Warning
    │
    ▼
Dashboard
```

---

## Logic xử lý

| Bước | Logic | Output |
|------|-------|--------|
| Step 1 | Nhận Vehicle Center và Lane Center | Vehicle Center, Lane Center |
| Step 2 | Tính Offset = VehicleCenterX - LaneCenterX | Offset |
| Step 3 | Xác định hướng lệch | Left / Right |
| Step 4 | So sánh Offset với Threshold | SAFE / NEAR BOUNDARY / LANE DEPARTURE |
| Step 5 | Sinh cảnh báo | Warning = TRUE/FALSE |
| Step 6 | Gửi kết quả sang Dashboard | JSON Result |

---

# 5. Decision Logic

| Điều kiện | Trạng thái | Warning |
|------------|------------|----------|
| abs(offset) < SAFE_THRESHOLD | SAFE | FALSE |
| SAFE_THRESHOLD ≤ abs(offset) < WARNING_THRESHOLD | NEAR BOUNDARY | FALSE |
| abs(offset) ≥ WARNING_THRESHOLD | LANE DEPARTURE | TRUE |

---

# 6. Output Data Structure

## Input từ Fusion

| Thuộc tính | Kiểu dữ liệu | Mô tả |
|------------|-------------|------|
| vehicle_id | Integer | ID xe |
| vehicle_center | Tuple(x,y) | Tâm xe |
| lane_left | Integer | Biên trái |
| lane_right | Integer | Biên phải |
| lane_center | Integer | Tâm làn |
| tracking_id | Integer | ID Tracking |

---

## Output của LDW

| Thuộc tính | Kiểu dữ liệu | Mô tả |
|------------|-------------|------|
| vehicle_id | Integer | ID xe |
| offset | Float | Độ lệch khỏi tâm làn |
| direction | String | LEFT / RIGHT |
| status | String | SAFE / NEAR BOUNDARY / LANE DEPARTURE |
| warning | Boolean | Có cảnh báo hay không |

Ví dụ

```json
{
    "vehicle_id":5,
    "offset":42,
    "direction":"LEFT",
    "status":"LEFT_LANE_DEPARTURE",
    "warning":true
}
```

---

# 7. Folder Structure

| File | Chức năng |
|------|-----------|
| lane_center.py | Tính tâm làn đường |
| vehicle_center.py | Tính tâm xe |
| lane_offset.py | Tính khoảng lệch |
| lane_status.py | Xác định trạng thái xe |
| lane_warning.py | Sinh cảnh báo |
| lane_visualizer.py | Vẽ cảnh báo lên video |
| config.py | Threshold và cấu hình |

---

# 8. Implementation

| Thành phần | Yêu cầu |
|------------|----------|
| Input | Chỉ nhận dữ liệu từ Fusion |
| Output | JSON chuẩn gửi Dashboard |
| Dependency | Không gọi trực tiếp YOLO hoặc DeepLab |
| Interface | process(frame_data) |
| Khả năng mở rộng | Có thể thay đổi Threshold trong config.py |

---

# 9. Test Cases

| Test Case | Điều kiện | Kết quả mong đợi |
|------------|----------|------------------|
| TC01 | Xe ở giữa làn | SAFE |
| TC02 | Xe lệch trái nhẹ | NEAR BOUNDARY |
| TC03 | Xe lệch phải nhẹ | NEAR BOUNDARY |
| TC04 | Xe vượt làn trái | LEFT LANE DEPARTURE |
| TC05 | Xe vượt làn phải | RIGHT LANE DEPARTURE |
| TC06 | Tracking mất ID | Không crash |
| TC07 | Lane Detection mất một biên | Không crash, báo Lane Unknown hoặc dùng dữ liệu trước |
| TC08 | Video ban đêm | Hệ thống vẫn hoạt động nếu Lane Detection còn nhận diện được |

---

# 10. Done Criteria

| Tiêu chí | Hoàn thành |
|----------|------------|
| Nhận dữ liệu từ Fusion | ✅ |
| Tính Vehicle Center | ✅ |
| Tính Lane Center | ✅ |
| Tính Offset | ✅ |
| Xác định hướng lệch | ✅ |
| Phân loại trạng thái | ✅ |
| Sinh cảnh báo | ✅ |
| Hiển thị Dashboard | ✅ |
| API hoạt động ổn định | ✅ |
| Không crash khi mất Tracking hoặc Lane | ✅ |
| Unit Test đầy đủ | ✅ |
| Integration Test đầy đủ | ✅ |

---

# 11. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Lane Center Calculation | YOLO Training |
| Vehicle Center Calculation | DeepLab Training |
| Offset Calculation | DeepSORT Training |
| Lane Status Classification | Vehicle Detection |
| Warning Generation | Lane Segmentation |
| Dashboard Visualization | Traffic Sign Detection |
| API Response | Fusion Logic |


2. Luồng xử lý của Lane Departure Warning
Video
   │
   ▼
YOLO
   │
   ▼
Vehicle Center
   │
   ▼
DeepLab
   │
   ▼
Lane Mask
   │
   ▼
Fusion
   │
   ▼
Lane Departure Warning
   │
   ▼
Dashboard


# Lane Departure Warning - Input Data Specification

---

# 1. User's Requirement

## Objective

Module Lane Departure Warning (LDW) không trực tiếp xử lý Video hoặc AI Model.

Nhiệm vụ của module là nhận dữ liệu đã được xử lý từ các module trước đó (YOLO, Lane Detection, Tracking và Fusion), sau đó tính toán trạng thái của xe so với làn đường để đưa ra cảnh báo.

Module phải đảm bảo:

- Không tự chạy YOLO.
- Không tự chạy DeepLab.
- Không tự Tracking.
- Chỉ sử dụng dữ liệu đầu vào đã chuẩn hóa.
- Mọi dữ liệu đều được đồng bộ theo cùng một Frame ID.

---

## Expected Input Sources

| Module | Vai trò |
|----------|----------|
| YOLO Detection | Cung cấp Bounding Box của xe |
| Lane Detection | Cung cấp Lane Mask |
| Tracking | Cung cấp Vehicle ID |
| Fusion | Chuẩn hóa dữ liệu đầu vào cho LDW |

---

## Expected Output

LDW phải nhận được đầy đủ thông tin sau:

```python
{
    vehicle_id,
    frame_id,
    vehicle_center,
    lane_left,
    lane_right,
    lane_center
}
```

---

# 2. Features

## Feature 1

Receive Vehicle Detection Data

Mục tiêu

Nhận thông tin xe từ YOLO.

---

Input

```python
Bounding Box

x1

y1

x2

y2
```

Ví dụ

```python
{
    "class":"car",
    "bbox":[250,300,450,600],
    "confidence":0.95
}
```

---

Output

```python
Vehicle Center

(cx,cy)
```

Ví dụ

```python
cx = (250+450)/2

cy = (300+600)/2

↓

(350,450)
```

---

Feature Result

```python
vehicle_center
```

---

## Feature 2

Receive Lane Detection Data

Mục tiêu

Nhận Lane Mask từ DeepLab hoặc Traditional CV.

---

Input

```text
Lane Mask
```

---

Lane Mask sẽ được chuyển thành

```python
Lane Left

Lane Right
```

Ví dụ

```python
Lane Left = 240

Lane Right = 460
```

---

Sau đó tính

```python
Lane Center

=

(LaneLeft+LaneRight)/2
```

Ví dụ

```python
(240+460)/2

=

350
```

---

Feature Result

```python
lane_left

lane_right

lane_center
```

---

## Feature 3

Receive Tracking Data

Tracking chịu trách nhiệm duy trì ID của xe.

Ví dụ

Frame 1

```python
Car

ID = 5
```

↓

Frame 2

```python
Car

ID = 5
```

↓

Frame 3

```python
Car

ID = 5
```

---

Mục tiêu

Không đổi ID khi xe vẫn còn trong Camera.

---

Feature Result

```python
tracking_id
```

---

## Feature 4

Synchronize Frame Data

Mọi dữ liệu phải thuộc cùng một Frame.

Ví dụ

```python
Frame 102

Vehicle Center

↓

Frame 102

Lane Center

↓

Frame 102

Tracking
```

Không được

```python
Vehicle

Frame 100

Lane

Frame 102
```

---

Feature Result

```python
frame_data
```

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Output |
|------------|-----------|---------|
| Vehicle Detection | YOLOv11 | Bounding Box |
| Vehicle Center | OpenCV / NumPy | Center Point |
| Lane Detection | DeepLabV3+ | Lane Mask |
| Lane Geometry | OpenCV | Lane Left, Lane Right, Lane Center |
| Tracking | DeepSORT | Vehicle ID |
| Fusion | Fusion Module | Chuẩn hóa Input |

---

# 4. Logic + AI

## Pipeline

```text
Video
      │
      ▼
YOLO Detection
      │
      ▼
Bounding Box
      │
      ▼
Vehicle Center
      │
      ▼
DeepLab
      │
      ▼
Lane Mask
      │
      ▼
Lane Geometry
      │
      ▼
Tracking
      │
      ▼
Fusion
      │
      ▼
Lane Departure Warning
```

---

## Step 1

YOLO

Input

```
Video Frame
```

Output

```python
Bounding Box
```

Ví dụ

```python
bbox

=

250

300

450

600
```

---

## Step 2

Vehicle Center

Tính

```python
cx=(x1+x2)/2

cy=(y1+y2)/2
```

Output

```python
Vehicle Center
```

---

## Step 3

DeepLab

Output

```
Lane Mask
```

---

## Step 4

Lane Geometry

Từ Lane Mask

↓

Tìm

```python
Lane Left

Lane Right
```

↓

Tính

```python
Lane Center
```

---

## Step 5

Tracking

Output

```python
Vehicle ID
```

---

## Step 6

Fusion

Fusion sẽ gom toàn bộ dữ liệu

```python
vehicle_center

lane_left

lane_right

lane_center

tracking_id

frame_id
```

↓

Sinh

```python
FrameData
```

Ví dụ

```python
{
    "frame_id":105,

    "vehicle_id":5,

    "vehicle_center":[350,480],

    "lane_left":240,

    "lane_right":460,

    "lane_center":350
}
```

↓

LDW sử dụng trực tiếp.

---

# 5. Implement

## Folder

```text
fusion/

├── vehicle_parser.py

├── lane_parser.py

├── tracking_parser.py

├── frame_synchronizer.py

└── fusion_output.py
```

---

## API

Fusion xuất

```python
FrameData
```

Ví dụ

```python
FrameData

{

vehicle_id,

frame_id,

vehicle_center,

lane_left,

lane_right,

lane_center

}
```

LDW chỉ nhận

```python
FrameData
```

Không được phép gọi trực tiếp

- YOLO
- DeepLab
- Tracking

---

# 6. Test

## Test Case 1

Vehicle Detection

Input

Bounding Box

↓

Expected

Vehicle Center chính xác.

---

## Test Case 2

Lane Detection

Input

Lane Mask

↓

Expected

Lane Left

Lane Right

Lane Center.

---

## Test Case 3

Tracking

Xe chạy liên tục.

↓

Expected

Vehicle ID không đổi.

---

## Test Case 4

Frame Synchronization

Vehicle

Lane

Tracking

↓

Expected

Cùng Frame ID.

---

## Test Case 5

Fusion Output

Expected

```python
FrameData
```

đầy đủ

```python
vehicle_id

frame_id

vehicle_center

lane_left

lane_right

lane_center
```

---

# 7. Done Criteria

| Tiêu chí | Hoàn thành |
|----------|------------|
| Nhận Bounding Box từ YOLO | ✅ |
| Tính Vehicle Center | ✅ |
| Nhận Lane Mask | ✅ |
| Tính Lane Left | ✅ |
| Tính Lane Right | ✅ |
| Tính Lane Center | ✅ |
| Nhận Tracking ID | ✅ |
| Đồng bộ Frame | ✅ |
| Fusion sinh FrameData | ✅ |
| LDW chỉ sử dụng FrameData | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Bounding Box Parsing | YOLO Training |
| Vehicle Center Calculation | YOLO Inference |
| Lane Geometry Extraction | DeepLab Training |
| Tracking ID Integration | DeepSORT Inference |
| Frame Synchronization | Camera Capture |
| Fusion Output Formatting | Dashboard Rendering |

# Lane Departure Warning - Input Validation & Data Preparation

---

# 1. User's Requirement

## Objective

Sau khi nhận `FrameData` từ Fusion, Lane Departure Warning (LDW) không được phép tính toán ngay.

Module phải kiểm tra tính hợp lệ của toàn bộ dữ liệu đầu vào nhằm tránh:

- Missing Data
- Invalid Coordinate
- Lost Tracking
- Invalid Lane Detection
- Frame Synchronization Error

Nếu dữ liệu không hợp lệ, hệ thống phải xử lý lỗi an toàn (Fail-safe) thay vì gây crash hoặc đưa ra cảnh báo sai.

Module phải đảm bảo:

- Chỉ xử lý khi FrameData hợp lệ.
- Không sử dụng dữ liệu thiếu.
- Không sử dụng dữ liệu từ Frame khác.
- Không sử dụng Bounding Box rỗng.
- Không sử dụng Lane Geometry không hợp lệ.

---

## Expected Input

```python
FrameData
{
    frame_id,
    vehicle_id,
    vehicle_center,
    lane_left,
    lane_right,
    lane_center
}
```

---

## Expected Output

```python
ValidatedFrameData
```

hoặc

```python
ValidationError
```

---

# 2. Features

---

## Feature 1

Validate Vehicle Center

### Mục tiêu

Kiểm tra Vehicle Center có hợp lệ hay không.

### Validation Rule

Vehicle Center phải tồn tại.

```python
vehicle_center != None
```

Vehicle Center phải nằm trong kích thước Frame.

```python
0 <= cx <= image_width

0 <= cy <= image_height
```

---

### Feature Result

```python
vehicle_center_valid = True
```

---

## Feature 2

Validate Lane Geometry

### Mục tiêu

Kiểm tra Lane Detection có hợp lệ.

---

Lane Left phải nhỏ hơn Lane Right.

```python
lane_left < lane_right
```

Lane Width phải lớn hơn Threshold.

Ví dụ

```python
lane_width

=

lane_right-lane_left
```

Nếu

```python
lane_width < MIN_LANE_WIDTH
```

↓

Lane Invalid

---

### Feature Result

```python
lane_valid=True
```

---

## Feature 3

Validate Tracking

Tracking ID phải tồn tại.

```python
tracking_id != None
```

Tracking ID phải trùng với Frame hiện tại.

Không được

```text
Frame 100

↓

Tracking Frame 95
```

---

### Feature Result

```python
tracking_valid=True
```

---

## Feature 4

Validate Frame Synchronization

Vehicle

Lane

Tracking

phải thuộc cùng

```python
frame_id
```

Ví dụ

```python
Vehicle

Frame 205
```

↓

```python
Lane

Frame 205
```

↓

```python
Tracking

Frame 205
```

---

Nếu

```python
Vehicle

Frame205

Lane

Frame210
```

↓

Reject.

---

### Feature Result

```python
frame_valid=True
```

---

## Feature 5

Build ValidatedFrameData

Nếu toàn bộ dữ liệu hợp lệ

↓

Sinh

```python
ValidatedFrameData
```

Ví dụ

```python
{
    "frame_id":205,

    "vehicle_id":5,

    "vehicle_center":[350,480],

    "lane_left":240,

    "lane_right":460,

    "lane_center":350
}
```

---

# 3. Tech Solutions

| Component | Technology | Purpose |
|------------|------------|----------|
| Validation | Python | Validate Input |
| Coordinate Checking | NumPy | Coordinate Validation |
| Frame Synchronization | Fusion | Đồng bộ Frame |
| Error Handling | Python Exception | Fail-safe |
| Logging | Python Logging | Debug |

---

# 4. Logic + AI

## Pipeline

```text
Fusion

↓

FrameData

↓

Vehicle Validation

↓

Lane Validation

↓

Tracking Validation

↓

Frame Synchronization

↓

ValidatedFrameData

↓

Lane Offset Calculation
```

---

## Step 1

Receive FrameData

↓

Kiểm tra

```python
None
```

---

## Step 2

Validate Vehicle Center

```python
cx

cy
```

phải nằm trong

```
Image Width

Image Height
```

---

## Step 3

Validate Lane

```python
lane_left

lane_right
```

↓

Lane Width

↓

Threshold

---

## Step 4

Validate Tracking

Tracking ID

↓

Exist

↓

Active

---

## Step 5

Validate Frame

Vehicle

↓

Lane

↓

Tracking

↓

Same Frame

---

## Step 6

Output

Nếu hợp lệ

↓

ValidatedFrameData

Nếu lỗi

↓

ValidationError

---

# 5. Implement

## Folder

```text
adas/

└── lane_departure/

    ├── validator.py

    ├── vehicle_validator.py

    ├── lane_validator.py

    ├── tracking_validator.py

    ├── frame_validator.py

    └── validation_result.py
```

---

## API

```python
validate(FrameData)
```

Input

```python
FrameData
```

Output

```python
ValidatedFrameData
```

hoặc

```python
ValidationError
```

---

# 6. Test

## Test Case 1

Vehicle Center hợp lệ

↓

Expected

Pass

---

## Test Case 2

Vehicle Center ngoài Frame

↓

Expected

Reject

---

## Test Case 3

Lane Width quá nhỏ

↓

Expected

Reject

---

## Test Case 4

Lane Left > Lane Right

↓

Expected

Reject

---

## Test Case 5

Tracking ID mất

↓

Expected

Reject

---

## Test Case 6

Frame không đồng bộ

↓

Expected

Reject

---

## Test Case 7

FrameData đầy đủ

↓

Expected

ValidatedFrameData

---

## Test Case 8

Thiếu vehicle_center

↓

Expected

ValidationError

---

# 7. Done Criteria

| Requirement | Status |
|-------------|--------|
| Validate Vehicle Center | ✅ |
| Validate Lane Geometry | ✅ |
| Validate Tracking | ✅ |
| Validate Frame Synchronization | ✅ |
| Build ValidatedFrameData | ✅ |
| Handle Invalid Data | ✅ |
| Logging Error | ✅ |
| Unit Test Passed | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Vehicle Validation | YOLO Detection |
| Lane Validation | DeepLab Segmentation |
| Tracking Validation | DeepSORT Tracking |
| Frame Validation | Fusion Logic |
| Error Handling | Dashboard |
| Validation Logging | AI Training |

# Lane Departure Warning - Lane Offset Calculation

---

# 1. User's Requirement

## Objective

Sau khi dữ liệu đầu vào đã được Validation thành công, hệ thống phải tính toán vị trí tương đối của xe so với làn đường.

Mục tiêu của module này là xác định:

- Tâm xe (Vehicle Center)
- Tâm làn đường (Lane Center)
- Độ rộng làn đường (Lane Width)
- Khoảng cách lệch (Lane Offset)
- Độ lệch đã chuẩn hóa (Normalized Offset)

Đây là dữ liệu đầu vào quan trọng nhất cho toàn bộ hệ thống Lane Departure Warning.

Module này không được đưa ra cảnh báo, không quyết định trạng thái, mà chỉ thực hiện tính toán hình học.

---

## Expected Input

```python
ValidatedFrameData
{
    frame_id,
    vehicle_id,
    vehicle_center,
    lane_left,
    lane_right,
    lane_center
}
```

---

## Expected Output

```python
OffsetData
{
    frame_id,
    vehicle_id,
    vehicle_center,
    lane_center,
    lane_width,
    offset,
    normalized_offset
}
```

---

# 2. Features

---

## Feature 1

Calculate Lane Width

### Objective

Tính độ rộng của làn đường.

### Formula

```text
Lane Width

=

Lane Right

-

Lane Left
```

Ví dụ

```text
Lane Left = 240

Lane Right = 460

↓

Lane Width = 220 px
```

---

Output

```python
lane_width
```

---

## Feature 2

Calculate Vehicle Offset

### Objective

Tính khoảng cách từ tâm xe đến tâm làn.

### Formula

```text
Offset

=

VehicleCenterX

-

LaneCenterX
```

Ví dụ

```text
Vehicle Center = 365

Lane Center = 350

↓

Offset = +15 px
```

---

Output

```python
offset
```

---

## Feature 3

Determine Offset Direction

### Objective

Xác định hướng lệch.

| Điều kiện | Direction |
|------------|-----------|
| offset < 0 | LEFT |
| offset = 0 | CENTER |
| offset > 0 | RIGHT |

---

Output

```python
direction
```

---

## Feature 4

Normalize Offset

### Objective

Chuẩn hóa Offset theo chiều rộng làn.

### Formula

```text
Normalized Offset

=

Offset

/

Lane Width
```

Ví dụ

```text
Offset = 20

Lane Width = 200

↓

Normalized Offset = 0.10
```

Lý do:

Camera có thể thay đổi độ phân giải.

Không nên dùng pixel tuyệt đối.

---

Output

```python
normalized_offset
```

---

## Feature 5

Package Offset Data

Sau khi tính xong

↓

Sinh

```python
OffsetData
```

Ví dụ

```python
{
    "vehicle_id":5,
    "frame_id":205,
    "vehicle_center":[360,480],
    "lane_center":350,
    "lane_width":220,
    "offset":10,
    "normalized_offset":0.045,
    "direction":"RIGHT"
}
```

---

# 3. Tech Solutions

| Component | Technology | Purpose |
|------------|------------|----------|
| Coordinate Calculation | NumPy | Tính toán tọa độ |
| Geometry | OpenCV | Tính hình học làn đường |
| Math Engine | Python | Offset Calculation |
| Data Model | Dataclass / Pydantic | Chuẩn hóa dữ liệu |

---

# 4. Logic + AI

## Pipeline

```text
ValidatedFrameData
        │
        ▼
Calculate Lane Width
        │
        ▼
Calculate Vehicle Offset
        │
        ▼
Determine Offset Direction
        │
        ▼
Normalize Offset
        │
        ▼
Generate OffsetData
        │
        ▼
Lane Status Classification
```

---

## Step 1

Receive ValidatedFrameData

↓

Đảm bảo dữ liệu đã hợp lệ.

---

## Step 2

Calculate Lane Width

```python
lane_width

=

lane_right

-

lane_left
```

---

## Step 3

Calculate Offset

```python
offset

=

vehicle_center_x

-

lane_center
```

---

## Step 4

Determine Direction

```python
offset < 0

↓

LEFT
```

```python
offset > 0

↓

RIGHT
```

```python
offset == 0

↓

CENTER
```

---

## Step 5

Normalize Offset

```python
normalized_offset

=

offset

/

lane_width
```

---

## Step 6

Generate OffsetData

↓

Gửi sang

```
Lane Status Classification
```

---

# 5. Implement

## Folder Structure

```text
adas/

└── lane_departure/

    ├── lane_width.py

    ├── lane_offset.py

    ├── direction.py

    ├── normalize_offset.py

    ├── offset_model.py

    └── offset_service.py
```

---

## API

```python
calculate_offset(
    validated_frame_data
)
```

Input

```python
ValidatedFrameData
```

Output

```python
OffsetData
```

---

## Data Model

```python
OffsetData

{
    frame_id,
    vehicle_id,
    lane_width,
    vehicle_center,
    lane_center,
    offset,
    normalized_offset,
    direction
}
```

---

# 6. Test

## Test Case 1

Offset = 0

↓

Expected

CENTER

---

## Test Case 2

Offset > 0

↓

Expected

RIGHT

---

## Test Case 3

Offset < 0

↓

Expected

LEFT

---

## Test Case 4

Lane Width = 220

Offset = 22

↓

Expected

Normalized Offset = 0.10

---

## Test Case 5

Lane Width = 0

↓

Expected

Reject Calculation

---

## Test Case 6

Vehicle Center đúng

↓

Expected

Offset chính xác

---

## Test Case 7

Lane Center sai

↓

Expected

Offset thay đổi tương ứng

---

## Test Case 8

OffsetData

↓

Expected

Đầy đủ tất cả trường dữ liệu

---

# 7. Done Criteria

| Requirement | Status |
|-------------|--------|
| Calculate Lane Width | ✅ |
| Calculate Offset | ✅ |
| Determine Direction | ✅ |
| Normalize Offset | ✅ |
| Generate OffsetData | ✅ |
| API hoạt động | ✅ |
| Unit Test Passed | ✅ |
| Integration Test Passed | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Lane Width Calculation | Lane Detection |
| Vehicle Offset Calculation | YOLO Detection |
| Direction Calculation | DeepSORT Tracking |
| Offset Normalization | Fusion Module |
| Offset Data Model | Dashboard Rendering |



# Lane Departure Warning - Module Architecture & Completion Criteria

---

# 1. User's Requirement

## Objective

Module Lane Departure Warning (LDW) phải được thiết kế theo kiến trúc module hóa (Modular Architecture), đảm bảo mỗi thành phần chỉ thực hiện một nhiệm vụ duy nhất.

Mục tiêu của module là:

- Dễ mở rộng.
- Dễ bảo trì.
- Dễ kiểm thử.
- Có thể thay thế từng thành phần mà không ảnh hưởng toàn hệ thống.
- Tuân thủ kiến trúc ADAS chuẩn.

Module phải bao gồm toàn bộ quy trình từ:

- Nhận dữ liệu Fusion
- Tính toán hình học
- Phân loại trạng thái
- Quyết định cảnh báo
- Hiển thị cảnh báo
- Xuất dữ liệu cho Dashboard

---

## Expected Folder

```text
adas/

└── lane_departure/

```

Mỗi file phải đảm nhiệm duy nhất một nhiệm vụ.

---

# 2. Features

---

## Feature 1

Lane Center Calculation

### Objective

Tính tâm làn đường từ Lane Geometry.

Input

```
Lane Left

Lane Right
```

Output

```
Lane Center
```

---

## Feature 2

Vehicle Center Calculation

### Objective

Tính tâm xe từ Bounding Box.

Input

```
Bounding Box
```

Output

```
Vehicle Center
```

---

## Feature 3

Lane Offset Calculation

### Objective

Tính khoảng cách giữa tâm xe và tâm làn.

Input

```
Vehicle Center

Lane Center
```

Output

```
Offset
```

---

## Feature 4

Lane Status Classification

### Objective

Phân loại trạng thái hiện tại.

Output

```
SAFE

NEAR_BOUNDARY

LANE_DEPARTURE
```

---

## Feature 5

Warning Decision

### Objective

Quyết định có phát cảnh báo hay không.

Output

```
Warning

True

False
```

---

## Feature 6

Visualization

### Objective

Hiển thị:

- Lane
- Vehicle Center
- Offset
- Warning
- Status

lên Video.

---

## Feature 7

Dashboard Output

### Objective

Đưa toàn bộ dữ liệu sang Dashboard thông qua API.

Output

```
LaneStatusData
```

---

# 3. Tech Solutions

| Module | Technology | Purpose |
|----------|------------|----------|
| Geometry | OpenCV | Tính toán hình học |
| Offset | NumPy | Tính khoảng cách |
| Decision Engine | Python | Phân loại trạng thái |
| Visualization | OpenCV Drawing API | Hiển thị kết quả |
| API | FastAPI | Gửi dữ liệu Dashboard |
| Logging | Python Logging | Debug |

---

# 4. Logic + AI

## Module Pipeline

```text
Fusion
      │
      ▼
Lane Center
      │
      ▼
Vehicle Center
      │
      ▼
Lane Offset
      │
      ▼
Lane Status
      │
      ▼
Warning Decision
      │
      ▼
Visualization
      │
      ▼
Dashboard API
```

---

## Processing Flow

### Step 1

Receive

```
FrameData
```

↓

---

### Step 2

Calculate

```
Lane Center
```

↓

---

### Step 3

Calculate

```
Vehicle Center
```

↓

---

### Step 4

Calculate

```
Lane Offset
```

↓

---

### Step 5

Determine

```
Lane Status
```

↓

---

### Step 6

Generate

```
Warning
```

↓

---

### Step 7

Visualize

↓

---

### Step 8

Send

```
LaneStatusData
```

↓

Dashboard

---

# 5. Implement

## Recommended Folder Structure

```text
adas/

└── lane_departure/

    ├── lane_center.py
    │
    │   => Calculate lane center
    │
    ├── vehicle_center.py
    │
    │   => Calculate vehicle center
    │
    ├── lane_width.py
    │
    │   => Calculate lane width
    │
    ├── lane_offset.py
    │
    │   => Calculate offset
    │
    ├── direction.py
    │
    │   => Determine LEFT / RIGHT
    │
    ├── lane_status.py
    │
    │   => SAFE / WARNING / DEPARTURE
    │
    ├── warning_engine.py
    │
    │   => Decision Logic
    │
    ├── lane_warning.py
    │
    │   => Generate Warning Object
    │
    ├── lane_visualizer.py
    │
    │   => Draw overlay on Video
    │
    ├── dashboard_sender.py
    │
    │   => Send data to Dashboard
    │
    ├── config.py
    │
    │   => Threshold Configuration
    │
    ├── models.py
    │
    │   => Data Model
    │
    ├── utils.py
    │
    │   => Common Utility Functions
    │
    └── lane_departure_service.py
        │
        => Main Pipeline Controller
```

---

## Main Controller

```
LaneDepartureService

↓

Receive FrameData

↓

Run Validation

↓

Calculate Geometry

↓

Calculate Offset

↓

Determine Status

↓

Decision Engine

↓

Visualization

↓

Dashboard API
```

---

# 6. Test

## Unit Test

| Test | Expected |
|---------|----------|
| Lane Center | Correct |
| Vehicle Center | Correct |
| Lane Width | Correct |
| Offset | Correct |
| Direction | LEFT / RIGHT |
| Lane Status | SAFE / WARNING / DEPARTURE |
| Warning Engine | TRUE / FALSE |
| Visualization | Draw Successfully |
| Dashboard Sender | API Success |

---

## Integration Test

Pipeline

```
Fusion

↓

Lane Center

↓

Vehicle Center

↓

Offset

↓

Status

↓

Warning

↓

Visualization

↓

Dashboard
```

Expected

```
No Error
```

---

## Performance Test

| Test | Target |
|---------|---------|
| FPS | >25 FPS |
| Delay | <100 ms |
| Memory | Stable |
| CPU Usage | Acceptable |

---

## Robustness Test

| Condition | Expected |
|------------|----------|
| Lane Missing | Continue Running |
| Tracking Lost | No Crash |
| Vehicle Missing | Skip Frame |
| Empty Frame | Continue |
| Multiple Vehicles | Correct Vehicle Selection |

---

# 7. Done Criteria

| Requirement | Status |
|-------------|--------|
| Receive FrameData | ✅ |
| Validate Input | ✅ |
| Calculate Lane Center | ✅ |
| Calculate Vehicle Center | ✅ |
| Calculate Lane Width | ✅ |
| Calculate Lane Offset | ✅ |
| Normalize Offset | ✅ |
| Determine Direction | ✅ |
| Determine Lane Status | ✅ |
| Warning Decision Engine | ✅ |
| Warning Object Generation | ✅ |
| Video Visualization | ✅ |
| Dashboard Integration | ✅ |
| API Response | ✅ |
| Unit Test Passed | ✅ |
| Integration Test Passed | ✅ |
| Performance Test Passed | ✅ |
| Robustness Test Passed | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Lane Geometry | YOLO Training |
| Offset Calculation | DeepLab Training |
| Lane Classification | DeepSORT Training |
| Warning Decision | Vehicle Detection |
| Visualization | Lane Segmentation |
| Dashboard Communication | Model Training |
| API Integration | Dataset Preparation |
| Configuration Management | Hyperparameter Tuning |


=>> Sau khi thực hiện được được đầy đủ các yêu cầu này hãy viết ra 1 file md kết quả cho phần này và đặt tên là Phát hiện và cảnh báo xe lệch làn.md  và quan trọng nhất là tận dụng tối đa các file được train sẵn như MODEL_PATHS = {
    "pedestrian": AI_SERVICE_ROOT / "ai_models" / "pedestrian_detection" / "pedestrian_runs" / "pedestrian" / "walking_v1" / "weights" / "best.pt",
    "vehicle": AI_SERVICE_ROOT / "ai_models" / "vehicle_detection" / "weights" / "best.pt",
    "lane_detection": AI_SERVICE_ROOT / "ai_models" / "lane_detection" / "weights" / "best.pt",
    "lane_segmentation": AI_SERVICE_ROOT / "ai_models" / "lane_segmentation" / "weights" / "best.pt",
    "traffic_sign": AI_SERVICE_ROOT / "ai_models" / "traffic_sign_detection" / "traffic_sign_runs_new" / "traffic_sign_52classes" / "weights" / "best.pt",
}