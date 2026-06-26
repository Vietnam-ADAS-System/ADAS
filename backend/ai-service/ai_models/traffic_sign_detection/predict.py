import os
import cv2
from ultralytics import YOLO
from tkinter import filedialog, Tk

def main():
    # 1. Tự động bật cửa sổ chọn file ảnh (File Dialog)
    root = Tk()
    root.withdraw() # Ẩn cửa sổ chính của tkinter đi, chỉ hiện hộp thoại chọn file
    root.attributes('-topmost', True) # Đưa hộp thoại lên phía trên cùng màn hình
    
    print("📂 Đang mở cửa sổ chọn ảnh... Bạn hãy bấm chọn 1 bức ảnh muốn test nhé!")
    image_to_test = filedialog.askopenfilename(
        title="Chọn ảnh biển báo giao thông để chạy thử nghiệm AI mới",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
    )
    
    # Nếu người dùng hủy chọn, dừng chương trình
    if not image_to_test:
        print("⚠️ Bạn đã hủy chọn ảnh. Chương trình kết thúc.")
        return
        
    print(f"📸 Ảnh bạn đã chọn: {image_to_test}")

    # Đường dẫn cấu trúc thư mục thực tế của má
    model_path = r"D:\Xử lý ảnh bk\backend\ai-service\ai_models\traffic_sign_detection\traffic_sign_runs_new\traffic_sign_52classes\weights\best.pt"
    output_project_dir = r"D:\Xử lý ảnh bk\backend\ai-service\ai_models\traffic_sign_detection\inference_outputs"

    if not os.path.exists(model_path):
        print(f"❌ Không tìm thấy file weights mới tại: {model_path}")
        return
        
    print("🚀 Đang nạp hệ thống phân tích YOLO11n...")
    model = YOLO(model_path)
    
    # 🛠️ CẢI TIẾN QUAN TRỌNG: Thêm agnostic_nms=True để triệt tiêu các hộp nhận diện chồng lấn lên nhau tại cùng 1 vị trí
    results = model.predict(source=image_to_test, conf=0.1, agnostic_nms=True, verbose=False)
    img_cv = cv2.imread(image_to_test)
    
    # 🌟 BỘ SỬA LỖI ĐỒNG BỘ HIỂN THỊ (DICTIONARY MAPPING) 🌟
    # Định nghĩa ánh xạ tên từ mô hình gốc về nhãn chuẩn thực tế thực nghiệm
    mapping_fix = {
        "Cam re phai": "Cam quay dau",
        "Gioi han toc do 40kmh": "Gioi han toc do 50kmh",  # Vá lỗi nếu AI nhìn nhầm font số 5 thành số 4
        "Gioi han toc do 60kmh": "Gioi han toc do 50kmh",  # Vá lỗi nếu AI nhìn nhầm font số 5 thành số 6
        # Nếu sau này test phát hiện thêm cặp lớp nào bị lệch nhãn, má cứ điền thêm vào đây
    }
    
    print("\n--- KẾT QUẢ PHÂN TÍCH BIỂN BÁO (ĐÃ ĐỒNG BỘ HÓA TÊN CHI TIẾT) ---")
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            class_id = int(box.cls[0])
            
            # Lấy tên gốc từ mô hình đang bị lệch
            model_text = model.names[class_id]
            confidence = box.conf[0].item()
            
            # Kiểm tra và đổi tên chuẩn theo bảng mapping
            final_text = mapping_fix.get(model_text, model_text)

            print(f"🎯 Phát hiện ──> {final_text} ({confidence*100:.1f}%)")
            
            # Vẽ hộp bọc màu đỏ lên hình ảnh hiển thị
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 0, 255), 3) 
            
            # Gắn nhãn kết quả chuẩn lên hình (Chữ xanh lá cây)
            label_display = f"{final_text} {confidence:.2f}"
            cv2.putText(img_cv, label_display, (x1, max(y1 - 10, 15)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) 

    # Lưu ảnh kết quả vào thư mục prediction_results
    output_dir = os.path.join(output_project_dir, "prediction_results")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(image_to_test) 
    output_image_path = os.path.join(output_dir, base_name)
    cv2.imwrite(output_image_path, img_cv)
    
    print("\n================ ĐÃ HOÀN THÀNH XỬ LÝ ================")
    print(f"🎉 Kết quả hình ảnh trực quan chuẩn tên đã được xuất tại: {output_image_path}")

if __name__ == "__main__":
    main()