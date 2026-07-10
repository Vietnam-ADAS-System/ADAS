# Phương pháp nghiên cứu và huấn luyện AI trong dự án ADAS

Dựa trên các file train và tài liệu hiện có trong codebase, dự án đang sử dụng **học sâu có giám sát (supervised learning)** theo hướng **fine-tuning các mô hình YOLO đã pretrain** cho từng bài toán nhận diện riêng. Nói ngắn gọn, đây không phải là một mô hình duy nhất cho tất cả, mà là **nhiều model chuyên biệt** cho từng thành phần của hệ thống ADAS.

## 1. Phương pháp tổng quát

- **Transfer learning / fine-tuning**: lấy model YOLO pretrained làm nền, sau đó train lại trên dữ liệu gán nhãn của dự án.
- **Supervised learning**: dữ liệu huấn luyện đều có nhãn lớp, bounding box hoặc mask tùy bài toán.
- **Data augmentation**: dùng các kỹ thuật như xoay nhẹ, dịch, scale, mosaic, flip, mixup để tăng độ bền của model.
- **Training theo từng module**: mỗi thành phần của ADAS có một pipeline train riêng.

## 2. Từng bài toán cụ thể

| Thành phần | Phương pháp train hiện tại | Ghi chú |
|---|---|---|
| **Vehicle detection** | Fine-tune **YOLO detection** | File train dùng `ultralytics.YOLO`, model nền là `yolo26x.pt` hoặc `yolo11x.pt`, dữ liệu theo format YOLO. |
| **Pedestrian detection** | Fine-tune **YOLO11 detection** | Script train dùng `yolo11n.pt`, train trên dataset người đi bộ với augmentation và AdamW. |
| **Traffic sign detection** | Fine-tune **YOLO detection** | Train từ trọng số có sẵn `best.pt`, sau đó tiếp tục huấn luyện trên bộ dữ liệu biển báo mới. |
| **Lane detection** | **YOLOv11 detection** cho các loại vạch/làn | Model học 11 lớp lane bằng bounding box, không phải mạng segmentation trong module này. |
| **Lane segmentation** | **YOLOv11 segmentation** | Dùng `yolo11n-seg.pt`, train mask cho lane line và road. |

## 3. Kết luận ngắn

Nếu viết theo văn phong báo cáo, có thể mô tả dự án như sau:

> Hệ thống ADAS sử dụng phương pháp học sâu có giám sát, trong đó các mô hình YOLO được fine-tune trên dữ liệu gán nhãn riêng cho từng nhiệm vụ. Bài toán phát hiện phương tiện, người đi bộ và biển báo giao thông được giải bằng YOLO object detection, còn nhận diện làn đường được triển khai bằng cả YOLO detection và YOLO segmentation tùy module. Quá trình huấn luyện có sử dụng transfer learning và data augmentation để tăng độ chính xác và khả năng tổng quát hóa.

## 4. Lưu ý quan trọng

Tài liệu tổng quan trong `README.md` có nhắc đến DeepLabV3+ và Traditional CV cho lane, nhưng code train hiện tại trong thư mục `backend/ai-service/ai_models/` cho thấy pipeline thực tế đang nghiêng về **YOLO-based training**. Vì vậy, phần mô tả ở trên phản ánh **cách dự án đang train trong code**, không chỉ mô tả theo tài liệu cũ.
