import os
import cv2
from ultralytics import YOLO
from tkinter import filedialog, Tk

def process_frame(frame, results, model_names, mapping_fix):
    """Hàm phụ trợ để vẽ bounding box và nhãn lên frame/ảnh"""
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            class_id = int(box.cls[0])
            
            # Lấy tên gốc từ mô hình đang bị lệch
            model_text = model_names[class_id]
            confidence = box.conf[0].item()
            
            # Kiểm tra và đổi tên chuẩn theo bảng mapping
            final_text = mapping_fix.get(model_text, model_text)

            # Vẽ hộp bọc màu đỏ lên hình ảnh hiển thị
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3) 
            
            # Gắn nhãn kết quả chuẩn lên hình (Chữ xanh lá cây)
            label_display = f"{final_text} {confidence:.2f}"
            cv2.putText(frame, label_display, (x1, max(y1 - 10, 15)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

def main():
    # 1. Tự động bật cửa sổ chọn file (File Dialog)
    root = Tk()
    root.withdraw() 
    root.attributes('-topmost', True) 
    
    print("📂 Đang mở cửa sổ chọn file... Bạn hãy bấm chọn 1 bức ảnh hoặc video muốn test nhé!")
    
    # Đưa All files lên đầu tiên để ép Windows hiển thị mọi file, kết hợp dùng dấu chấm phẩy (;)
    file_to_test = filedialog.askopenfilename(
        title="Chọn ảnh/video biển báo giao thông để chạy thử nghiệm AI mới",
        filetypes=[
            ("All files", "*.*"),
            ("Video files", "*.mp4;*.avi;*.mov;*.mkv"),
            ("Image files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")
        ]
    )
    
    if not file_to_test:
        print("⚠️ Bạn đã hủy chọn file. Chương trình kết thúc.")
        return
        
    print(f"📸 File bạn đã chọn: {file_to_test}")

    # Lấy đường dẫn tuyệt đối của thư mục chứa file code hiện tại
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Nội suy đường dẫn model và thư mục output từ vị trí file code
    model_path = os.path.join(base_dir, "traffic_sign_runs_new", "traffic_sign_52classes", "weights", "best.pt")
    output_project_dir = os.path.join(base_dir, "inference_outputs")

    if not os.path.exists(model_path):
        print(f"❌ Không tìm thấy file weights mới tại: {model_path}")
        return
        
    print("🚀 Đang nạp hệ thống phân tích YOLO11n...")
    model = YOLO(model_path)
    
    mapping_fix = {
        "Cam re phai": "Cam quay dau",
        "Gioi han toc do 40kmh": "Gioi han toc do 50kmh",  
        "Gioi han toc do 60kmh": "Gioi han toc do 50kmh",  
    }
    
    output_dir = os.path.join(output_project_dir, "prediction_results")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(file_to_test)
    
    # Kiểm tra định dạng file
    ext = os.path.splitext(file_to_test)[1].lower()
    is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

    if not is_video:
        # ---------------- XỬ LÝ ẢNH ----------------
        results = model.predict(source=file_to_test, conf=0.1, agnostic_nms=True, verbose=False)
        img_cv = cv2.imread(file_to_test)
        
        print("\n--- KẾT QUẢ PHÂN TÍCH BIỂN BÁO ---")
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                conf = box.conf[0].item()
                name = mapping_fix.get(model.names[class_id], model.names[class_id])
                print(f"🎯 Phát hiện ──> {name} ({conf*100:.1f}%)")
                
        img_cv = process_frame(img_cv, results, model.names, mapping_fix)
        
        output_path = os.path.join(output_dir, base_name)
        cv2.imwrite(output_path, img_cv)
        print("\n================ ĐÃ HOÀN THÀNH XỬ LÝ ================")
        print(f"🎉 Kết quả ảnh trực quan đã được xuất tại: {output_path}")

    else:
        # ---------------- XỬ LÝ VIDEO ----------------
        cap = cv2.VideoCapture(file_to_test)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        output_path = os.path.join(output_dir, f"result_{base_name}")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        print("\n🎥 Đang xử lý video... Vui lòng đợi trong giây lát.")
        
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"⏳ Đang xử lý frame {frame_count}/{total_frames}...")
                
            results = model.predict(source=frame, conf=0.1, agnostic_nms=True, verbose=False)
            frame = process_frame(frame, results, model.names, mapping_fix)
            out.write(frame)
            
        cap.release()
        out.release()
        print("\n================ ĐÃ HOÀN THÀNH XỬ LÝ ================")
        print(f"🎉 Kết quả video trực quan đã được xuất tại: {output_path}")

if __name__ == "__main__":
    main()