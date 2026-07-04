# Dashboard - TV1: Camera Streaming & Video Visualization

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|-----------|---------|
| Module | Dashboard - TV1 |
| Chức năng | Camera Streaming & Video Visualization |
| Mục tiêu | Hiển thị luồng video (Camera hoặc Video Upload) theo thời gian thực trên Dashboard. |
| Vai trò | TV1 chỉ hiển thị video. Không thực hiện Detection, Tracking, Segmentation hoặc AI Inference. |
| Input | Camera Stream / Video Stream từ Backend |
| Output | Video Frame được hiển thị trên Dashboard |
| Module tiếp theo | TV2 - Vehicle Bounding Box Visualization |

---

## Objective

Dashboard phải đóng vai trò là giao diện trực quan của toàn bộ hệ thống ADAS.

TV1 chịu trách nhiệm:

- Nhận luồng video từ Backend.
- Hiển thị video theo thời gian thực.
- Đồng bộ FPS.
- Đồng bộ Frame ID.
- Làm nền để các Layer khác (Vehicle, Lane, Traffic Sign, Warning) hiển thị.

TV1 tuyệt đối không:

- Chạy YOLO.
- Chạy DeepLab.
- Chạy DeepSORT.
- Thực hiện bất kỳ xử lý AI nào.

---

## Expected Input

Video Stream

Ví dụ

```text
Camera

↓

RTSP

↓

Backend

↓

Dashboard
```

hoặc

```text
Video File

↓

Backend

↓

Dashboard
```

---

## Expected Output

```text
Realtime Video Frame
```

---

# 2. Features

---

## Feature 1

Receive Video Stream

### Objective

Nhận Video Stream từ Backend.

### Input

```text
Video Stream
```

Ví dụ

```text
1920x1080

30 FPS
```

### Output

```text
Video Frame
```

---

## Feature 2

Render Video Frame

### Objective

Hiển thị từng Frame lên Dashboard.

Dashboard phải luôn hiển thị Frame mới nhất.

Không lưu Frame cũ.

Output

```text
Realtime Camera View
```

---

## Feature 3

Frame Synchronization

### Objective

Đồng bộ Frame với Backend.

Ví dụ

Backend

```text
Frame 102
```

↓

Dashboard

```text
Frame 102
```

Không được

```text
Backend

Frame 105

↓

Dashboard

Frame 101
```

---

## Feature 4

FPS Display

### Objective

Hiển thị FPS hiện tại.

Ví dụ

```text
FPS

29.8
```

---

## Feature 5

Connection Monitoring

### Objective

Theo dõi trạng thái Camera.

Ví dụ

```text
CONNECTED
```

hoặc

```text
DISCONNECTED
```

---

## Feature 6

Video Resize

Dashboard phải tự động resize.

Ví dụ

```text
1920x1080

↓

1280x720

↓

Responsive
```

---

## Feature 7

Loading State

Nếu Camera chưa kết nối

↓

Dashboard hiển thị

```text
Loading Camera...
```

---

## Feature 8

Reconnect

Nếu Camera mất kết nối

↓

Dashboard tự reconnect.

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Frontend | React | Camera View |
| Video Rendering | HTML5 Video / Canvas | Hiển thị Video |
| API | REST/WebSocket | Nhận Video |
| State Management | React Hooks | Quản lý trạng thái |
| Resize | CSS Flex/Grid | Responsive |
| Connection | WebSocket | Theo dõi kết nối |

---

# 4. Logic + Flow

## Pipeline

```text
Camera

↓

Backend

↓

Video Stream

↓

Dashboard

↓

Camera Component

↓

Realtime Render

↓

Vehicle Layer

↓

Lane Layer

↓

Traffic Sign Layer

↓

Warning Layer
```

---

## Step 1

Receive Video Stream

↓

Kiểm tra kết nối.

---

## Step 2

Nhận Frame mới.

↓

Frame Buffer.

---

## Step 3

Render Frame.

↓

Camera Component.

---

## Step 4

Đồng bộ FPS.

↓

Hiển thị FPS.

---

## Step 5

Publish Current Frame

↓

TV2 Vehicle Layer.

---

# 5. Implement

## Folder

```text
frontend/

components/

Camera/

│

├── CameraView.jsx

│

├── CameraCanvas.jsx

│

├── CameraHeader.jsx

│

├── CameraStatus.jsx

│

├── CameraLoading.jsx

│

└── camera.service.js
```

---

## API

```text
GET

/api/video
```

hoặc

```text
WebSocket

/ws/video
```

---

# 6. Test

| Test Case | Expected |
|------------|----------|
| Camera Connected | Video hiển thị |
| Camera Disconnected | Loading |
| FPS | Hiển thị đúng |
| Resize | Responsive |
| Frame Sync | Không lệch Frame |
| Reconnect | Tự kết nối lại |

---

# 7. Done Criteria

| Requirement | Status |
|------------|---------|
| Receive Video | ✅ |
| Render Video | ✅ |
| Frame Sync | ✅ |
| FPS | ✅ |
| Resize | ✅ |
| Connection Status | ✅ |
| Loading | ✅ |
| Reconnect | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Video Streaming | YOLO Detection |
| Video Rendering | DeepLab |
| FPS Display | Tracking |
| Connection | AI Inference |
| Responsive | Warning Logic |

---

# 9. Deliverable

```text
CameraView

↓

Realtime Video

↓

Frame Synchronization

↓

Ready For Overlay Layer
```
# Dashboard - TV3: Lane Visualization Layer

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|-----------|---------|
| Module | Dashboard - TV3 |
| Chức năng | Lane Visualization Layer |
| Mục tiêu | Hiển thị trực quan toàn bộ thông tin làn đường đã được xử lý từ Backend lên Dashboard. |
| Vai trò | TV3 chỉ hiển thị Lane Geometry, Lane Center, Lane Status và Lane Departure Warning. Không thực hiện Lane Detection hoặc AI Inference. |
| Input | LaneVisualizationData từ Backend |
| Output | Lane Overlay hiển thị trên Camera View |
| Module tiếp theo | TV4 - Traffic Sign Visualization |

---

## Objective

TV3 chịu trách nhiệm hiển thị toàn bộ thông tin liên quan đến làn đường đã được Backend xử lý.

Dashboard phải trực quan hóa:

- Lane Mask
- Lane Left
- Lane Right
- Lane Center
- Safe Driving Area
- Vehicle Position
- Lane Offset
- Lane Status
- Lane Departure Warning

TV3 tuyệt đối không:

- Chạy DeepLabV3+.
- Chạy Canny.
- Chạy Hough Transform.
- Tính Lane Center.
- Tính Lane Offset.
- Đưa ra quyết định Lane Departure.

Toàn bộ dữ liệu đều nhận từ Backend.

---

## Expected Input

```python
LaneVisualizationData
{
    frame_id,
    lane_left,
    lane_right,
    lane_center,
    lane_width,
    vehicle_center,
    offset,
    normalized_offset,
    direction,
    lane_status,
    warning
}
```

---

## Expected Output

```text
Lane Overlay
```

Hiển thị trực tiếp lên Camera.

---

# 2. Features

---

## Feature 1

Receive Lane Visualization Data

### Objective

Nhận dữ liệu Lane từ Backend.

### Input

```python
LaneVisualizationData
```

### Output

Lane Layer

---

## Feature 2

Draw Lane Boundary

### Objective

Hiển thị biên trái và biên phải của làn đường.

Dashboard phải vẽ:

- Lane Left
- Lane Right

Ví dụ

```text
│              │
│              │
│              │
```

Output

```text
Lane Boundary
```

---

## Feature 3

Draw Lane Center

### Objective

Hiển thị tâm làn đường.

Ví dụ

```text
────────────
Lane Center
────────────
```

Output

```text
Lane Center Line
```

---

## Feature 4

Draw Safe Driving Area

### Objective

Hiển thị vùng xe được phép di chuyển.

Dashboard tô màu vùng nằm giữa hai làn.

Ví dụ

```text
Lane Left

██████████

Lane Right
```

Output

```text
Safe Zone
```

---

## Feature 5

Draw Vehicle Position

### Objective

Hiển thị vị trí tương đối của xe trong làn.

Dashboard nhận

```python
vehicle_center
```

↓

Vẽ

```text
Vehicle Center
```

trên Lane.

---

## Feature 6

Visualize Lane Offset

### Objective

Hiển thị khoảng lệch giữa xe và tâm làn.

Ví dụ

```text
Offset

+15 px
```

hoặc

```text
Offset

-22 px
```

Output

```text
Offset Indicator
```

---

## Feature 7

Display Lane Status

### Objective

Hiển thị trạng thái hiện tại.

Ví dụ

| Status | Hiển thị |
|----------|----------|
| SAFE | 🟢 SAFE |
| NEAR_BOUNDARY | 🟡 NEAR BOUNDARY |
| LANE_DEPARTURE | 🔴 LANE DEPARTURE |

---

## Feature 8

Highlight Lane Departure

### Objective

Nếu Backend phát hiện lệch làn.

↓

Dashboard đổi màu Lane.

Ví dụ

SAFE

↓

Green

Near Boundary

↓

Yellow

Lane Departure

↓

Red

---

## Feature 9

Realtime Update

Dashboard phải cập nhật theo từng Frame.

Ví dụ

```text
Frame 120

↓

Frame 121

↓

Frame 122
```

Không được giật hình.

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Frontend | React | Lane Layer |
| Rendering | HTML5 Canvas | Vẽ Lane |
| State Management | React Hooks | Quản lý Lane State |
| API | REST / WebSocket | Nhận LaneVisualizationData |
| Graphics | Canvas API | Overlay Lane |
| CSS | Responsive Layout | Hiển thị |

---

# 4. Logic + Flow

## Pipeline

```text
LaneVisualizationData
        │
        ▼
Receive Lane Data
        │
        ▼
Draw Lane Boundary
        │
        ▼
Draw Lane Center
        │
        ▼
Draw Safe Zone
        │
        ▼
Draw Vehicle Position
        │
        ▼
Display Lane Status
        │
        ▼
Highlight Lane Departure
        │
        ▼
Overlay On Camera
        │
        ▼
Realtime Update
```

---

## Step 1

Receive LaneVisualizationData.

↓

Không xử lý AI.

---

## Step 2

Vẽ

Lane Left

Lane Right.

---

## Step 3

Vẽ

Lane Center.

---

## Step 4

Tô vùng Safe Zone.

---

## Step 5

Hiển thị Vehicle Center.

---

## Step 6

Hiển thị Offset.

---

## Step 7

Hiển thị Lane Status.

---

## Step 8

Nếu Warning = TRUE

↓

Đổi màu Lane.

---

## Step 9

Render lên Camera Layer.

---

# 5. Implement

## Folder Structure

```text
frontend/

components/

Lane/

│

├── LaneLayer.jsx
│
├── LaneBoundary.jsx
│
├── LaneCenter.jsx
│
├── SafeZone.jsx
│
├── VehiclePosition.jsx
│
├── OffsetIndicator.jsx
│
├── LaneStatus.jsx
│
├── LaneDepartureAlert.jsx
│
├── lane.service.js
│
└── lane.style.css
```

---

## API

```text
GET

/api/lane
```

hoặc

```text
WebSocket

/ws/lane
```

---

## Data Model

```python
LaneVisualizationData
{
    frame_id,
    lane_left,
    lane_right,
    lane_center,
    lane_width,
    vehicle_center,
    offset,
    normalized_offset,
    direction,
    lane_status,
    warning
}
```

---

# 6. Test

| Test Case | Expected |
|------------|----------|
| Lane Boundary | Hiển thị đúng |
| Lane Center | Chính xác |
| Safe Zone | Đúng vùng |
| Vehicle Position | Đúng vị trí |
| Offset | Hiển thị đúng |
| SAFE | Màu xanh |
| NEAR_BOUNDARY | Màu vàng |
| LANE_DEPARTURE | Màu đỏ |
| Warning | Hiển thị cảnh báo |
| Frame Update | Realtime |

---

# 7. Done Criteria

| Requirement | Status |
|------------|---------|
| Receive LaneVisualizationData | ✅ |
| Draw Lane Boundary | ✅ |
| Draw Lane Center | ✅ |
| Draw Safe Zone | ✅ |
| Draw Vehicle Position | ✅ |
| Draw Offset | ✅ |
| Draw Lane Status | ✅ |
| Draw Lane Departure Warning | ✅ |
| Overlay Camera | ✅ |
| Realtime Update | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Lane Rendering | Lane Detection |
| Lane Boundary Visualization | DeepLabV3+ Inference |
| Lane Center Visualization | OpenCV Processing |
| Offset Visualization | Lane Geometry Calculation |
| Lane Status Display | Lane Departure Decision |
| Warning Overlay | AI Training |

---

# 9. Deliverable

```text
LaneVisualizationData
        │
        ▼
Lane Layer
        │
        ├── Lane Boundary
        ├── Lane Center
        ├── Safe Zone
        ├── Vehicle Position
        ├── Offset Indicator
        ├── Lane Status
        ├── Lane Departure Highlight
        └── Overlay on Camera
```

Dashboard TV3 chỉ thực hiện **Visualization Layer**. Mọi phép tính hình học, xử lý ảnh, phân đoạn làn đường và quyết định cảnh báo đều thuộc Backend (Traditional CV, AI Models, Fusion và ADAS), đảm bảo Frontend chỉ nhận dữ liệu và hiển thị theo thời gian thực.

# Dashboard - TV4: Traffic Sign Visualization Layer

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|-----------|---------|
| Module | Dashboard - TV4 |
| Chức năng | Traffic Sign Visualization Layer |
| Mục tiêu | Hiển thị trực quan toàn bộ thông tin biển báo giao thông đã được AI và ADAS xử lý lên Dashboard. |
| Vai trò | Chỉ hiển thị kết quả nhận diện và cảnh báo. Không chạy YOLO, không phân loại biển báo, không xử lý Rule Engine. |
| Input | TrafficSignVisualizationData |
| Output | Traffic Sign Overlay trên Camera |
| Module tiếp theo | TV5 - Warning Panel |

---

## Objective

TV4 chịu trách nhiệm trực quan hóa toàn bộ thông tin về biển báo giao thông.

Dashboard phải hiển thị:

- Bounding Box biển báo
- Tên biển báo
- Confidence
- Icon biển báo
- Rule được kích hoạt
- Trạng thái cảnh báo
- Vị trí biển báo trên Camera

TV4 tuyệt đối không:

- Chạy YOLO Detection
- Phân loại biển báo
- Sinh Rule
- Phân tích hành vi
- Ra quyết định Warning

Mọi dữ liệu đều được Backend xử lý trước.

---

## Expected Input

```python
TrafficSignVisualizationData
{
    frame_id,
    sign_id,
    class_id,
    class_name,
    confidence,
    bbox,
    center,
    icon,
    rule,
    warning,
    priority
}
```

---

## Expected Output

```text
Traffic Sign Overlay
```

Hiển thị trực tiếp trên Camera.

---

# 2. Features

---

## Feature 1

Receive Traffic Sign Data

### Objective

Nhận dữ liệu biển báo từ Backend.

Input

```python
TrafficSignVisualizationData
```

Output

```text
Traffic Sign Layer
```

---

## Feature 2

Draw Traffic Sign Bounding Box

### Objective

Hiển thị Bounding Box của biển báo.

Ví dụ

```text
┌────────────┐
│ STOP       │
└────────────┘
```

Output

```text
Bounding Box
```

---

## Feature 3

Display Traffic Sign Label

### Objective

Hiển thị tên biển báo.

Ví dụ

```text
STOP

Speed Limit 40

No Entry

Children

Pedestrian Crossing
```

Output

```text
Class Name
```

---

## Feature 4

Display Confidence

### Objective

Hiển thị độ tin cậy của AI.

Ví dụ

```text
98%
```

Output

```text
Confidence Score
```

---

## Feature 5

Display Traffic Sign Icon

### Objective

Hiển thị icon của biển báo.

Ví dụ

```text
🛑

🚫

40

60
```

Output

```text
Traffic Sign Icon
```

---

## Feature 6

Display Active Rule

### Objective

Hiển thị Rule đang được kích hoạt.

Ví dụ

STOP

↓

```text
Prepare To Stop
```

Speed Limit 40

↓

```text
Maximum Speed 40 km/h
```

No Entry

↓

```text
Do Not Enter
```

Output

```text
Current Rule
```

---

## Feature 7

Display Warning State

### Objective

Hiển thị trạng thái cảnh báo.

Ví dụ

| Warning | Display |
|-----------|----------|
| FALSE | No Warning |
| TRUE | Warning Active |

---

## Feature 8

Priority Highlight

### Objective

Hiển thị màu theo mức ưu tiên.

Ví dụ

| Priority | Color |
|------------|--------|
| LOW | Blue |
| MEDIUM | Yellow |
| HIGH | Orange |
| CRITICAL | Red |

---

## Feature 9

Realtime Update

Dashboard phải cập nhật theo từng Frame.

Không được giật hình.

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Frontend | React | Traffic Sign Layer |
| Rendering | HTML5 Canvas | Overlay |
| API | REST / WebSocket | Nhận dữ liệu |
| Graphics | Canvas API | Vẽ Bounding Box |
| State | React Hooks | Đồng bộ dữ liệu |
| CSS | Responsive | Hiển thị |

---

# 4. Logic + Flow

## Pipeline

```text
Traffic Sign Detection
        │
        ▼
Rule Engine
        │
        ▼
Warning Manager
        │
        ▼
TrafficSignVisualizationData
        │
        ▼
Receive Data
        │
        ▼
Draw Bounding Box
        │
        ▼
Draw Label
        │
        ▼
Draw Confidence
        │
        ▼
Draw Icon
        │
        ▼
Display Active Rule
        │
        ▼
Display Warning
        │
        ▼
Overlay Camera
        │
        ▼
Realtime Update
```

---

## Step 1

Receive TrafficSignVisualizationData.

↓

Không xử lý AI.

---

## Step 2

Draw Bounding Box.

---

## Step 3

Hiển thị tên biển báo.

---

## Step 4

Hiển thị Confidence.

---

## Step 5

Hiển thị Icon.

---

## Step 6

Hiển thị Rule.

---

## Step 7

Nếu Warning = TRUE

↓

Highlight biển báo.

---

## Step 8

Overlay lên Camera.

---

## Step 9

Cập nhật theo từng Frame.

---

# 5. Implement

## Folder Structure

```text
frontend/

components/

TrafficSign/

│

├── TrafficSignLayer.jsx

├── TrafficSignBox.jsx

├── TrafficSignLabel.jsx

├── TrafficSignIcon.jsx

├── TrafficSignConfidence.jsx

├── TrafficSignRule.jsx

├── TrafficSignWarning.jsx

├── traffic_sign.service.js

└── traffic_sign.style.css
```

---

## API

```text
GET

/api/traffic-sign
```

hoặc

```text
WebSocket

/ws/traffic-sign
```

---

## Data Model

```python
TrafficSignVisualizationData
{
    frame_id,
    sign_id,
    class_id,
    class_name,
    confidence,
    bbox,
    center,
    icon,
    rule,
    priority,
    warning
}
```

---

# 6. Test

| Test Case | Expected |
|------------|----------|
| Receive Traffic Sign Data | Pass |
| Draw Bounding Box | Chính xác |
| Display Label | Đúng tên biển báo |
| Display Confidence | Đúng Confidence |
| Display Icon | Đúng Icon |
| Display Rule | Đúng Rule |
| Display Warning | Chính xác |
| Priority Color | Đúng màu |
| Overlay Camera | Thành công |
| Frame Update | Realtime |

---

# 7. Done Criteria

| Requirement | Status |
|------------|---------|
| Receive TrafficSignVisualizationData | ✅ |
| Draw Bounding Box | ✅ |
| Draw Label | ✅ |
| Draw Confidence | ✅ |
| Draw Icon | ✅ |
| Draw Rule | ✅ |
| Draw Warning | ✅ |
| Draw Priority | ✅ |
| Overlay Camera | ✅ |
| Realtime Update | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Traffic Sign Rendering | YOLO Detection |
| Bounding Box Visualization | AI Training |
| Label Visualization | Rule Engine |
| Confidence Visualization | Traffic Sign Classification |
| Rule Display | Warning Decision |
| Warning Visualization | Backend Logic |

---

# 9. Deliverable

```text
TrafficSignVisualizationData
            │
            ▼
Traffic Sign Layer
            │
            ├── Bounding Box
            ├── Traffic Sign Label
            ├── Confidence Score
            ├── Traffic Sign Icon
            ├── Active Rule
            ├── Warning Status
            ├── Priority Highlight
            └── Overlay on Camera
```

---

# 10. Integration

| Dữ liệu hiển thị | Module cung cấp |
|------------------|-----------------|
| Bounding Box | AI - YOLO Traffic Sign Detection |
| Class Name | AI - Traffic Sign Detection |
| Confidence | AI - Traffic Sign Detection |
| Rule | ADAS - Traffic Sign Rule Engine |
| Warning | ADAS - Warning Manager |
| Priority | ADAS - Warning Manager |
| Frame ID | Fusion |

TV4 chỉ là **Visualization Layer**, chịu trách nhiệm hiển thị toàn bộ thông tin biển báo giao thông đã được xử lý bởi AI và ADAS. Module này không thực hiện bất kỳ phép xử lý ảnh, suy luận AI hay ra quyết định cảnh báo nào, đảm bảo tuân thủ kiến trúc phân tầng của toàn bộ hệ thống ADAS.

# Dashboard - TV5: Warning Panel & ADAS System Status

---

# 1. User's Requirement

| Hạng mục | Mô tả |
|-----------|---------|
| Module | Dashboard - TV5 |
| Chức năng | Warning Panel & ADAS Status |
| Mục tiêu | Hiển thị toàn bộ cảnh báo và trạng thái hoạt động của hệ thống ADAS theo thời gian thực. |
| Vai trò | Chỉ hiển thị Warning từ Backend. Không tự sinh cảnh báo hoặc xử lý AI. |
| Input | WarningPanelData |
| Output | Warning Panel trên Dashboard |
| Module cuối | Dashboard hoàn chỉnh |

---

## Objective

TV5 là lớp giao tiếp cuối cùng giữa hệ thống ADAS và người sử dụng.

Module chịu trách nhiệm:

- Hiển thị trạng thái hệ thống.
- Hiển thị cảnh báo đang kích hoạt.
- Hiển thị mức độ ưu tiên.
- Hiển thị lịch sử cảnh báo gần nhất.
- Đồng bộ toàn bộ trạng thái Dashboard.

TV5 tuyệt đối không:

- Chạy YOLO.
- Chạy DeepLab.
- Chạy DeepSORT.
- Tính Lane Offset.
- Phân loại biển báo.
- Sinh Rule.
- Sinh Warning.

Toàn bộ Warning đều do Backend xử lý.

---

## Expected Input

```python
WarningPanelData
{
    frame_id,
    vehicle_status,
    lane_status,
    traffic_sign_status,
    warning_type,
    warning_level,
    warning_message,
    active,
    timestamp
}
```

---

## Expected Output

```text
Warning Panel
```

Hiển thị trực tiếp trên Dashboard.

---

# 2. Features

---

## Feature 1

Receive Warning Data

### Objective

Nhận WarningPanelData từ Backend.

Input

```python
WarningPanelData
```

Output

```text
Warning State
```

---

## Feature 2

Display Lane Departure Warning

### Objective

Hiển thị cảnh báo lệch làn.

Ví dụ

```text
🟢 SAFE
```

```text
🟡 Near Boundary
```

```text
🔴 Lane Departure
```

---

## Feature 3

Display Traffic Sign Warning

### Objective

Hiển thị cảnh báo theo biển báo.

Ví dụ

```text
STOP
```

↓

```text
Prepare To Stop
```

Ví dụ

```text
Speed Limit 40
```

↓

```text
Maximum Speed 40 km/h
```

Ví dụ

```text
No Entry
```

↓

```text
Do Not Enter
```

---

## Feature 4

Display System Status

### Objective

Hiển thị trạng thái hoạt động của hệ thống.

Ví dụ

| Module | Status |
|----------|---------|
| Camera | Online |
| Vehicle Detection | Running |
| Lane Detection | Running |
| Traffic Sign Detection | Running |
| ADAS | Running |

---

## Feature 5

Display Warning Priority

### Objective

Hiển thị mức độ nguy hiểm.

| Priority | Color |
|------------|--------|
| INFO | Blue |
| LOW | Green |
| MEDIUM | Yellow |
| HIGH | Orange |
| CRITICAL | Red |

---

## Feature 6

Display Current Warning

### Objective

Dashboard luôn hiển thị cảnh báo đang kích hoạt.

Ví dụ

```text
⚠ Lane Departure
```

hoặc

```text
⚠ Speed Limit 40
```

hoặc

```text
🚫 No Entry
```

---

## Feature 7

Display Warning History

### Objective

Lưu lịch sử một số cảnh báo gần nhất.

Ví dụ

```text
14:22:05

Lane Departure
```

```text
14:22:12

Speed Limit 40
```

```text
14:22:30

STOP
```

---

## Feature 8

Realtime Update

Dashboard phải cập nhật theo từng Frame.

Warning phải thay đổi ngay khi Backend gửi dữ liệu mới.

---

# 3. Tech Solutions

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|----------|
| Frontend | React | Warning Panel |
| State Management | React Hooks | Đồng bộ trạng thái |
| API | REST / WebSocket | Nhận Warning |
| UI | Material UI / CSS | Hiển thị Warning |
| Notification | Toast / Banner | Popup cảnh báo |

---

# 4. Logic + Flow

## Pipeline

```text
Lane Departure Warning
           │
           ▼
Traffic Sign Warning
           │
           ▼
Warning Manager
           │
           ▼
WarningPanelData
           │
           ▼
Receive Warning
           │
           ▼
Update Dashboard State
           │
           ▼
Display Active Warning
           │
           ▼
Display System Status
           │
           ▼
Display Warning History
           │
           ▼
Realtime Update
```

---

## Step 1

Receive WarningPanelData.

↓

Không xử lý AI.

---

## Step 2

Hiển thị trạng thái Lane.

---

## Step 3

Hiển thị Traffic Sign Warning.

---

## Step 4

Hiển thị mức độ ưu tiên.

---

## Step 5

Hiển thị Warning Message.

---

## Step 6

Cập nhật lịch sử cảnh báo.

---

## Step 7

Render Warning Panel.

---

## Step 8

Đồng bộ toàn bộ Dashboard.

---

# 5. Implement

## Folder Structure

```text
frontend/

components/

Warning/

│

├── WarningPanel.jsx

├── WarningBanner.jsx

├── LaneWarningCard.jsx

├── TrafficSignWarningCard.jsx

├── SystemStatusCard.jsx

├── WarningHistory.jsx

├── WarningPriority.jsx

├── warning.service.js

└── warning.style.css
```

---

## API

```text
GET

/api/warning
```

hoặc

```text
WebSocket

/ws/warning
```

---

## Data Model

```python
WarningPanelData
{
    frame_id,
    vehicle_status,
    lane_status,
    traffic_sign_status,
    warning_type,
    warning_level,
    warning_message,
    active,
    timestamp
}
```

---

# 6. Test

| Test Case | Expected |
|------------|----------|
| Receive Warning Data | Pass |
| Lane Warning | Hiển thị đúng |
| Traffic Sign Warning | Hiển thị đúng |
| Warning Priority | Đúng màu |
| Warning Message | Chính xác |
| System Status | Đồng bộ |
| Warning History | Lưu đúng |
| Overlay Update | Realtime |

---

# 7. Done Criteria

| Requirement | Status |
|------------|---------|
| Receive WarningPanelData | ✅ |
| Display Lane Warning | ✅ |
| Display Traffic Sign Warning | ✅ |
| Display Warning Priority | ✅ |
| Display System Status | ✅ |
| Display Warning History | ✅ |
| Realtime Update | ✅ |
| Dashboard Integration | ✅ |

---

# 8. Scope

| In Scope | Out of Scope |
|-----------|--------------|
| Warning Visualization | Warning Decision |
| System Status Display | Lane Detection |
| Warning History | Traffic Sign Detection |
| Priority Display | YOLO Inference |
| Notification UI | DeepLab Inference |
| Dashboard Rendering | AI Training |

---

# 9. Deliverable

```text
WarningPanelData
        │
        ▼
Warning Panel
        │
        ├── Lane Warning
        ├── Traffic Sign Warning
        ├── System Status
        ├── Priority Indicator
        ├── Warning History
        ├── Active Warning Banner
        └── Realtime Update
```

---

# 10. Integration

| Dữ liệu hiển thị | Module cung cấp |
|------------------|-----------------|
| Lane Status | ADAS - Lane Departure Warning |
| Traffic Sign Warning | ADAS - Traffic Sign Warning |
| Warning Message | Warning Manager |
| Warning Priority | Warning Manager |
| System Status | Node Server |
| Frame ID | Fusion |

TV5 là lớp giao diện cuối cùng của hệ thống ADAS. Module này chỉ nhận `WarningPanelData` từ Backend và trực quan hóa thông tin cho người dùng. Mọi quyết định cảnh báo đều đã được xử lý bởi các module AI, Computer Vision, Fusion và ADAS trước đó.

                     AI SERVICE (Backend)
──────────────────────────────────────────────────────────

Camera / Video
        │
        ▼
Preprocessing (CVIP)
        │
        ▼
YOLO Vehicle Detection
        │
        ▼
YOLO Traffic Sign Detection
        │
        ▼
DeepLab Lane Segmentation
        │
        ▼
DeepSORT Tracking
        │
        ▼
Fusion Engine
        │
        ▼
ADAS Decision Engine
        │
        ├──────────────► Lane Departure Warning
        │
        ├──────────────► Traffic Sign Warning
        │
        ▼
Warning Manager
        │
        ▼
NodeJS API / WebSocket

──────────────────────────────────────────────────────────
                     FRONTEND DASHBOARD
──────────────────────────────────────────────────────────

TV1
Camera Stream
        │
        ▼
TV2
Vehicle Bounding Box Layer
        │
        ▼
TV3
Lane Visualization Layer
        │
        ▼
TV4
Traffic Sign Visualization Layer
        │
        ▼
TV5
Warning Panel
        │
        ▼
Final ADAS Dashboard
