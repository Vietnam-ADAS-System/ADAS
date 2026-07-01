import os
import shutil
from ultralytics import YOLO

def delete_old_caches():
    """Tự động tìm và xóa các file cache cũ để YOLO bắt buộc phải quét lại dữ liệu mới"""
    dataset_labels_dir = r"D:\Xử lý ảnh bk\datasets\traffic_sign\labels"
    train_cache = os.path.join(dataset_labels_dir, "train.cache")
    val_cache = os.path.join(dataset_labels_dir, "val.cache")
    
    if os.path.exists(train_cache):
        try:
            os.remove(train_cache)
            print("🧹 Đã xóa file cache cũ của tập Train để cập nhật dữ liệu mới.")
        except Exception as e:
            print(f"⚠️ Không thể xóa train.cache: {e}")
            
    if os.path.exists(val_cache):
        try:
            os.remove(val_cache)
            print("🧹 Đã xóa file cache cũ của tập Val để cập nhật dữ liệu mới.")
        except Exception as e:
            print(f"⚠️ Không thể xóa val.cache: {e}")

def main():
    # 1. Đường dẫn lấy file weights cũ làm nền tảng cốt lõi (Kết quả hôm qua)
    pretrained_weights = r"D:\Xử lý ảnh bk\backend\ai-service\ai_models\traffic_sign_detection\traffic_sign_runs\weights\best.pt"
    
    # 2. Đường dẫn tới file data.yaml (Chứa cấu hình 52 lớp mới)
    data_yaml_path = r"D:\Xử lý ảnh bk\backend\ai-service\ai_models\traffic_sign_detection\data.yaml"
    
    # 3. Thư mục gốc lưu kết quả train mới độc lập hoàn toàn (Không lo đè lên file cũ)
    output_project_dir = r"D:\Xử lý ảnh bk\backend\ai-service\ai_models\traffic_sign_detection\traffic_sign_runs_new"

    # Kiểm tra xem file trọng số cũ của ngày hôm qua có tồn tại không
    if not os.path.exists(pretrained_weights):
        print(f"❌ Không tìm thấy file weights cũ tại: {pretrained_weights}")
        print("💡 Hãy kiểm tra lại đường dẫn hoặc copy file best.pt hôm qua vào đúng vị trí trên.")
        return

    # Dọn dẹp cache dữ liệu cũ trước khi train
    delete_old_caches()

    print("\n🚀 Đang nạp mô hình cũ (best.pt) làm nền tảng tri thức...")
    model = YOLO(pretrained_weights)

    print("🏋️‍♂️ AI đang bắt đầu huấn luyện tăng cường với danh sách 52 lớp mới...")
    
    # Kích hoạt quá trình Train
    model.train(
        data=data_yaml_path,
        epochs=50,                     # 50 epochs để học thêm dữ liệu mới
        imgsz=640,                     # Kích thước ảnh chuẩn hóa cấu trúc đồ họa YOLO
        batch=8,                       # Bạn có thể sửa thành 4 nếu bị báo lỗi tràn bộ nhớ (Out of Memory - OOM)
        project=output_project_dir,    # Thư mục cha độc lập
        name="traffic_sign_52classes", # Thư mục con chứa kết quả đợt này
        device="cpu",                  # ĐỔI THÀNH 0 hoặc "cuda" NẾU MÁY BẠN CÓ CARD ĐỒ HỌA RỜI NVIDIA
        workers=2,                     # Số lượng tiến trình xử lý nạp ảnh (để 2 cho nhẹ CPU máy văn phòng)
        exist_ok=True                  # Nếu chạy lại nhiều lần sẽ ghi đè vào thư mục mới này, không tạo thêm folder _2, _3 bừa bãi
    )
    
    print("\n🎉 QUÁ TRÌNH HUẤN LUYỆN BỔ SUNG ĐÃ HOÀN THÀNH HOÀN HẢO!")
    print(f"📂 Trọng số thông minh mới nhất của bạn nằm tại: {output_project_dir}\\traffic_sign_52classes\\weights\\best.pt")

if __name__ == "__main__":
    main()