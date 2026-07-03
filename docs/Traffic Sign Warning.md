# Traffic Sign Warning - TV1: Traffic Sign Recognition Input

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|----------|------|
| Module | Traffic Sign Warning |
| Chức năng | TV1 - Đọc kết quả nhận diện biển báo từ AI Detection |
| Mục tiêu | Tiếp nhận kết quả nhận diện biển báo giao thông từ mô hình YOLO và chuẩn hóa dữ liệu để phục vụ Rule Engine. |
| Vai trò | Đây là điểm bắt đầu của toàn bộ luồng Traffic Sign Warning. Module không được phép tự nhận diện ảnh mà chỉ sử dụng kết quả từ AI Detection. |
| Input | Traffic Sign Detection Output (YOLO) |
| Output | StandardTrafficSignData |
| Module kế tiếp | TV2 - Rule Engine |

---

# 2. Features

## Feature 1 - Receive Detection Result

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Nhận kết quả nhận diện biển báo từ YOLO. |
| Input | Detection Result |
| Output | Raw Detection Data |
| Điều kiện | Chỉ nhận các Detection có Confidence lớn hơn Threshold. |

Ví dụ

```python
{
    "class_id":38,
    "confidence":0.96,
    "bbox":[120,80,200,180]
}
```

---

## Feature 2 - Read Class ID

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Đọc giá trị class_id từ Detection Result. |
| Input | class_id |
| Output | Traffic Sign ID |
| Validation | class_id phải nằm trong khoảng từ 0 đến 51. |

Ví dụ

```text
38
```

↓

```text
Traffic Sign ID = 38
```

---

## Feature 3 - Mapping Class Name

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Chuyển class_id thành tên biển báo dễ hiểu. |
| Công nghệ | Python Dictionary / JSON Mapping |
| Input | class_id |
| Output | class_name |

Ví dụ

| Class ID | Class Name |
|-----------|-------------|
| 2 | Cấm đi ngược chiều |
| 38 | Giới hạn tốc độ 50km/h |
| 39 | Giới hạn tốc độ 60km/h |
| 41 | Giới hạn tốc độ 40km/h |

Ví dụ

```python
38
```

↓

```python
"Gioi han toc do 50kmh"
```

---

## Feature 4 - Read Confidence

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Lấy độ tin cậy của mô hình AI. |
| Input | confidence |
| Output | Detection Confidence |
| Điều kiện | Confidence phải lớn hơn giá trị cấu hình (ví dụ 0.5). |

Ví dụ

```python
confidence = 0.95
```

---

## Feature 5 - Read Bounding Box

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Đọc vị trí biển báo trên Frame. |
| Input | Bounding Box |
| Output | bbox |
| Định dạng | [x1,y1,x2,y2] |

Ví dụ

```python
bbox

=

[150,80,240,190]
```

---

## Feature 6 - Generate Standard Traffic Sign Data

| Nội dung | Chi tiết |
|----------|-----------|
| Mục tiêu | Chuẩn hóa toàn bộ dữ liệu thành một cấu trúc thống nhất để truyền cho TV2. |
| Input | Detection Result |
| Output | StandardTrafficSignData |

Ví dụ

```python
{
    "frame_id":120,

    "tracking_id":5,

    "class_id":38,

    "class_name":"Gioi han toc do 50kmh",

    "confidence":0.95,

    "bbox":[150,80,240,190]
}
```

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Detection | YOLOv11 | Phát hiện biển báo |
| Data Model | Dataclass / Pydantic | Chuẩn hóa dữ liệu |
| Mapping | Python Dictionary | Chuyển class_id thành class_name |
| Validation | Python | Kiểm tra dữ liệu |
| Config | YAML | Confidence Threshold |

---

# 4. Logic + AI

## Pipeline

```text
Video Frame
      │
      ▼
YOLO Detection
      │
      ▼
Detection Result
      │
      ▼
Read Class ID
      │
      ▼
Mapping Class Name
      │
      ▼
Read Confidence
      │
      ▼
Read Bounding Box
      │
      ▼
Generate StandardTrafficSignData
      │
      ▼
TV2 - Rule Engine
```

---

## Step 1

YOLO Detection

Input

```
Video Frame
```

↓

Output

```
Detection Result
```

---

## Step 2

Read Class ID

Ví dụ

```
38
```

↓

```
Traffic Sign ID
```

---

## Step 3

Mapping

Ví dụ

```
38
```

↓

```
Giới hạn tốc độ 50km/h
```

---

## Step 4

Read Confidence

Ví dụ

```
0.96
```

↓

```
Detection Accepted
```

---

## Step 5

Read Bounding Box

Ví dụ

```
[120,80,200,180]
```

↓

```
Traffic Sign Position
```

---

## Step 6

Generate StandardTrafficSignData

↓

Truyền sang

```
TV2 - Rule Engine
```

---

# 5. Implement

## Folder

```text
adas/

traffic_sign/

│

├── sign_reader.py
│
│   => Đọc Detection Result từ YOLO
│
├── class_mapper.py
│
│   => Mapping 52 Class
│
├── confidence_filter.py
│
│   => Lọc Detection theo Confidence
│
├── bbox_parser.py
│
│   => Chuẩn hóa Bounding Box
│
├── sign_model.py
│
│   => StandardTrafficSignData
│
└── sign_input_service.py
    │
    => Điều phối toàn bộ TV1
```

---

## API

```python
read_sign_detection(
    detection_result
)
```

Input

```python
Detection Result
```

Output

```python
StandardTrafficSignData
```

---

# 6. Test

| Test Case | Input | Expected Output |
|------------|-------|-----------------|
| TC01 | class_id = 38 | class_name = Giới hạn tốc độ 50km/h |
| TC02 | class_id = 2 | class_name = Cấm đi ngược chiều |
| TC03 | confidence = 0.95 | Detection Accepted |
| TC04 | confidence = 0.30 | Detection Rejected |
| TC05 | bbox hợp lệ | Bounding Box Parsed |
| TC06 | class_id ngoài phạm vi | Validation Error |
| TC07 | Detection Result đầy đủ | StandardTrafficSignData |

---

# 7. Done Criteria

| Requirement | Hoàn thành |
|-------------|------------|
| Nhận Detection Result | ✅ |
| Đọc class_id | ✅ |
| Mapping class_name | ✅ |
| Kiểm tra Confidence | ✅ |
| Đọc Bounding Box | ✅ |
| Chuẩn hóa dữ liệu | ✅ |
| Sinh StandardTrafficSignData | ✅ |
| API hoạt động | ✅ |
| Unit Test Passed | ✅ |
| Integration Test Passed | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Đọc Detection Result | YOLO Training |
| Mapping 52 Class | Dataset Annotation |
| Confidence Validation | Model Optimization |
| Bounding Box Parsing | Dashboard |
| Chuẩn hóa dữ liệu | Rule Engine |
| Sinh StandardTrafficSignData | Warning Decision |

---

# 9. Output cho TV2

Module TV1 chỉ sinh đúng một đối tượng dữ liệu duy nhất để truyền sang TV2.

```python
StandardTrafficSignData
{
    frame_id,
    tracking_id,
    class_id,
    class_name,
    confidence,
    bbox
}
```

TV2 sẽ **không đọc trực tiếp kết quả YOLO**, mà chỉ nhận `StandardTrafficSignData` từ TV1 để xây dựng luật (Rule Engine).



# Traffic Sign Warning - TV3: Speed Limit State Management & Dashboard Synchronization

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|----------|------|
| Module | TV3 - Speed Limit State Management |
| Mục tiêu | Quản lý trạng thái giới hạn tốc độ hiện hành sau khi TV2 đã phân tích biển báo và sinh Driving Rule. |
| Vai trò | TV3 không thực hiện nhận diện biển báo, không tạo Rule, không phát Warning. Module chỉ quản lý trạng thái Speed Limit hiện hành và đồng bộ lên Dashboard. |
| Input | DrivingRuleData (TV2 Output) |
| Output | SpeedLimitState |
| Module kế tiếp | Dashboard, TV4 - Traffic Warning Decision |

---

# 2. Features

## Feature 1 - Receive Driving Rule

### Objective

Nhận dữ liệu DrivingRuleData từ TV2.

Ví dụ

```python
{
    "frame_id":120,
    "rule":"SET_SPEED_LIMIT",
    "speed_limit":50
}
```

Nếu Rule không thuộc nhóm Speed Limit thì bỏ qua.

---

## Feature 2 - Update Current Speed Limit

### Objective

Cập nhật giới hạn tốc độ hiện hành.

Ví dụ

```text
Current Speed Limit

40 km/h
```

↓

Nhận biển mới

```text
60 km/h
```

↓

```text
Current Speed Limit

60 km/h
```

Luôn chỉ tồn tại một Current Speed Limit.

---

## Feature 3 - Maintain Speed Limit State

### Objective

Lưu trạng thái Speed Limit để các module khác sử dụng.

Output

```python
SpeedLimitState
```

Ví dụ

```python
{
    "frame_id":120,
    "speed_limit":50,
    "status":"ACTIVE",
    "source":"Traffic Sign",
    "updated_at":"10:35:25"
}
```

---

## Feature 4 - Synchronize Dashboard

### Objective

Đồng bộ Current Speed Limit lên Dashboard.

Dashboard hiển thị

```
Current Speed Limit

50 km/h
```

Nếu có biển tốc độ mới thì Dashboard phải cập nhật ngay.

---

## Feature 5 - Publish SpeedLimitState

### Objective

Công bố SpeedLimitState để các module khác sử dụng.

Module sử dụng:

- Dashboard
- TV4 Traffic Warning Decision
- Overspeed Warning (mở rộng sau này)

TV3 không xử lý dữ liệu sau khi Publish.

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| State Manager | Python | Quản lý Current Speed Limit |
| Context Manager | Python | Duy trì trạng thái Speed Limit |
| REST API | FastAPI | Cung cấp dữ liệu cho Dashboard |
| Data Model | Pydantic / Dataclass | Chuẩn hóa SpeedLimitState |
| Logging | Python Logging | Ghi lịch sử thay đổi |

---

# 4. Logic + AI

## Pipeline

```text
DrivingRuleData
        │
        ▼
Check Speed Rule
        │
        ▼
Extract Speed Value
        │
        ▼
Update Current Speed Limit
        │
        ▼
Generate SpeedLimitState
        │
        ├──────────────► Dashboard
        │
        └──────────────► TV4 Decision Engine
```

---

## Step 1

Nhận DrivingRuleData.

↓

Kiểm tra Rule.

---

## Step 2

Nếu Rule =

```
SET_SPEED_LIMIT
```

↓

Lấy giá trị tốc độ.

Ví dụ

```
50
```

---

## Step 3

Cập nhật

```
Current Speed Limit
```

Nếu đã có Speed Limit trước đó thì ghi đè.

---

## Step 4

Sinh

```python
SpeedLimitState
```

---

## Step 5

Publish

↓

Dashboard

↓

TV4 Decision Engine

---

# 5. Implement

## Folder Structure

```text
adas/

traffic_sign/

│

├── speed_rule_parser.py
│
│   => Nhận DrivingRuleData
│
├── speed_limit_manager.py
│
│   => Quản lý Current Speed Limit
│
├── speed_state.py
│
│   => Data Model của SpeedLimitState
│
├── dashboard_sender.py
│
│   => Đồng bộ Dashboard
│
├── speed_limit_service.py
│
│   => Điều phối toàn bộ TV3
│
└── speed_logger.py
    │
    => Ghi lịch sử thay đổi Speed Limit
```

---

## API

```python
update_speed_limit(
    driving_rule
)
```

Input

```python
DrivingRuleData
```

Output

```python
SpeedLimitState
```

---

# 6. Test

| Test Case | Input | Expected |
|------------|-------|----------|
| TC01 | SET_SPEED_LIMIT 40 | Current = 40 |
| TC02 | SET_SPEED_LIMIT 50 | Current = 50 |
| TC03 | SET_SPEED_LIMIT 60 | Current = 60 |
| TC04 | STOP | Không cập nhật |
| TC05 | NO_ENTRY | Không cập nhật |
| TC06 | Dashboard | Hiển thị đúng |
| TC07 | TV4 | Nhận đúng SpeedLimitState |
| TC08 | Có biển mới | Current Speed cập nhật |
| TC09 | API | Trả đúng SpeedLimitState |

---

# 7. Done Criteria

| Requirement | Status |
|-------------|--------|
| Nhận DrivingRuleData | ✅ |
| Nhận biết Rule Speed Limit | ✅ |
| Cập nhật Current Speed Limit | ✅ |
| Sinh SpeedLimitState | ✅ |
| Đồng bộ Dashboard | ✅ |
| Publish sang TV4 | ✅ |
| API hoạt động | ✅ |
| Unit Test Passed | ✅ |
| Integration Test Passed | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Speed Rule Processing | YOLO Detection |
| Current Speed Limit Management | Traffic Sign Detection |
| SpeedLimitState | Warning Decision |
| Dashboard Synchronization | Warning Manager |
| Publish State | Voice Alert |
| State Logging | AI Training |

---

# 9. Deliverable

```python
SpeedLimitState
{
    frame_id,
    speed_limit,
    status,
    source,
    updated_at
}
```

### Module sử dụng

- Dashboard (Hiển thị giới hạn tốc độ hiện hành)
- TV4 Traffic Warning Decision (Làm ngữ cảnh để ra quyết định)
- Các module ADAS mở rộng như Overspeed Warning hoặc Adaptive Cruise Control (nếu phát triển thêm)

TV3 không phát cảnh báo, không quản lý hàng đợi cảnh báo và không hiển thị thông báo nguy hiểm. Vai trò duy nhất là duy trì và phân phối trạng thái giới hạn tốc độ hiện hành.


# Traffic Sign Warning - TV4: Traffic Warning Decision Engine

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|----------|------|
| Module | TV4 - Traffic Warning Decision Engine |
| Mục tiêu | Phân tích Driving Rule và Current Traffic Context để quyết định có phát cảnh báo hay không. |
| Vai trò | TV4 là tầng Decision của ADAS. Module không nhận diện biển báo, không quản lý Dashboard, mà chỉ đưa ra quyết định Warning. |
| Input | DrivingRuleData, SpeedLimitState |
| Output | TrafficWarning |
| Module kế tiếp | TV5 - Warning Manager |

---

# 2. Features

## Feature 1 - Receive Driving Rule

### Objective

Nhận DrivingRuleData từ TV2.

Ví dụ

```python
{
    "rule":"NO_ENTRY"
}
```

hoặc

```python
{
    "rule":"PREPARE_TO_STOP"
}
```

---

## Feature 2 - Receive Current Traffic Context

### Objective

Nhận trạng thái giao thông hiện tại từ TV3.

Ví dụ

```python
SpeedLimitState
```

hoặc

```python
Current Road Context
```

TV4 không cập nhật Context.

Chỉ sử dụng.

---

## Feature 3 - Rule Decision

### Objective

Áp dụng Decision Logic.

Ví dụ

| Rule | Decision |
|------|----------|
| NO_ENTRY | Warning |
| STOP | Prepare To Stop |
| SPEED_LIMIT | No Warning |
| PEDESTRIAN | Reduce Speed |
| ROUNDABOUT | Prepare To Turn |

---

## Feature 4 - Generate Warning Event

Sau khi Rule được xử lý

↓

Sinh

```python
TrafficWarning
```

Ví dụ

```python
{
    "type":"NO_ENTRY",
    "level":"HIGH",
    "message":"Cấm đi ngược chiều"
}
```

---

## Feature 5 - Warning Priority

Nếu nhiều Warning xuất hiện cùng lúc

↓

TV4 phải xếp mức ưu tiên.

Ví dụ

| Warning | Priority |
|-----------|----------|
| No Entry | HIGH |
| STOP | HIGH |
| Speed Limit | MEDIUM |
| School Zone | MEDIUM |
| Bus Stop | LOW |

Output

```python
priority
```

---

## Feature 6 - Warning Expiration

Warning không tồn tại mãi.

Ví dụ

```
STOP

↓

3 giây

↓

Tự hủy
```

Hoặc

```
No Entry

↓

Xe ra khỏi vùng

↓

Hủy Warning
```

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Decision Engine | Python | Quyết định Warning |
| Rule Evaluator | Python | Đánh giá Rule |
| Priority Manager | Python | Xếp mức ưu tiên |
| Timer | Python | Quản lý thời gian Warning |
| State Manager | Python | Theo dõi Warning hiện hành |

---

# 4. Logic + AI

## Pipeline

```text
DrivingRuleData
        │
        ▼
Decision Engine
        │
        ▼
Priority Evaluation
        │
        ▼
Generate Warning
        │
        ▼
Warning Queue
        │
        ▼
TV5 Warning Manager
```

---

## Step 1

Receive DrivingRuleData

↓

Không đọc lại YOLO.

---

## Step 2

Evaluate Rule

↓

Sinh Action.

---

## Step 3

Assign Priority

↓

HIGH

MEDIUM

LOW

---

## Step 4

Generate Warning

↓

TrafficWarning

---

## Step 5

Send To Warning Manager

↓

TV5

---

# 5. Implement

## Folder

```text
adas/

traffic_sign/

│

├── warning_decision.py
│
│   => Quyết định cảnh báo
│
├── priority_manager.py
│
│   => Xếp mức ưu tiên
│
├── warning_timer.py
│
│   => Quản lý thời gian hiển thị
│
├── warning_model.py
│
│   => TrafficWarning
│
└── warning_service.py
    │
    => Điều phối TV4
```

---

## API

```python
generate_warning(
    DrivingRuleData,
    SpeedLimitState
)
```

Output

```python
TrafficWarning
```

---

# 6. Test

| Test Case | Expected |
|------------|----------|
| STOP | Prepare To Stop |
| NO_ENTRY | High Warning |
| Speed Limit | Không sinh Warning |
| Bus Stop | Low Warning |
| School Zone | Medium Warning |
| Multiple Rule | Priority đúng |
| Warning Timeout | Warning tự hủy |
| TrafficWarning | Đúng Model |

---

# 7. Done Criteria

| Requirement | Status |
|-------------|--------|
| Nhận DrivingRuleData | ✅ |
| Quyết định Warning | ✅ |
| Xếp Priority | ✅ |
| Sinh TrafficWarning | ✅ |
| Quản lý Timeout | ✅ |
| API hoạt động | ✅ |
| Integration Test | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Decision Logic | YOLO Detection |
| Priority | Traffic Sign Detection |
| Warning Model | Dashboard |
| Warning Queue | AI Training |
| Timeout | Camera |

---

# 9. Output cho TV5

TV4 chỉ sinh đúng một đối tượng dữ liệu.

```python
TrafficWarning
{
    warning_id,
    type,
    level,
    message,
    priority,
    duration,
    timestamp
}
```

TV5 sẽ chỉ nhận `TrafficWarning`, không xử lý lại Rule.


TV1
Read Detection
        │
        ▼
TV2
Rule Engine
        │
        ▼
TV3
Speed Limit Manager
        │
        ▼
TV4
Traffic Warning Decision
        │
        ▼
TrafficWarning
        │
        ▼
==========================
TV5
Warning Manager
==========================
        │
        ├── Warning Queue
        ├── Duplicate Filter
        ├── Priority Manager
        ├── Warning History
        ├── Dashboard
        ├── Voice Alert
        └── Log System