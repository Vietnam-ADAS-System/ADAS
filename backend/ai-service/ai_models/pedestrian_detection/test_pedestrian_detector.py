"""
Script test PedestrianDetector
- Chỉ dùng best.pt đã train — KHÔNG dùng logic YOLO gốc
- Chỉ nhận diện người ĐI BỘ, bỏ qua người dùng phương tiện
- Lọc bằng tỉ lệ khung hình (aspect ratio) để loại xe máy/xe đạp
"""

import cv2
import os
import sys
from tkinter import Tk, filedialog
from datetime import datetime
from ultralytics import YOLO

# ──────────────────────────────────────────────
# CẤU HÌNH
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BEST_MODEL_PATH = os.path.join(BASE_DIR, "runs/pedestrian/walking_v1/weights/best.pt")

PERSON_CONF_THRESHOLD = 0.55   # Tăng lên để loại false positive
MIN_ASPECT_RATIO      = 1.3    # height/width — người đứng/đi bộ cao hơn rộng
MAX_ASPECT_RATIO      = 5.0    # loại trường hợp quá hẹp (nhiễu)
MIN_BOX_HEIGHT        = 40     # pixel — loại box quá nhỏ (xa, không rõ)


def pick_image():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="Chọn ảnh để nhận diện người đi bộ",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
            ("All files", "*.*")
        ]
    )
    root.destroy()
    return file_path


def is_pedestrian(x1, y1, x2, y2):
    """
    Lọc để chỉ giữ người ĐI BỘ, bỏ người đang ngồi trên xe.
    
    Logic:
    - Người đi bộ: đứng thẳng → height >> width (aspect ratio cao)
    - Người trên xe máy/xe đạp: ngồi thấp, body bị che → box thường
      vuông hơn hoặc lẫn với xe → aspect ratio thấp hơn
    """
    w = x2 - x1
    h = y2 - y1

    if w <= 0 or h <= 0:
        return False

    aspect_ratio = h / w  # > 1 nghĩa là cao hơn rộng

    if h < MIN_BOX_HEIGHT:
        return False  # Box quá nhỏ

    if aspect_ratio < MIN_ASPECT_RATIO:
        return False  # Quá vuông → có thể đang ngồi trên xe

    if aspect_ratio > MAX_ASPECT_RATIO:
        return False  # Quá hẹp → nhiễu

    return True


def detect_pedestrians(frame, model):
    """
    Chạy best.pt và chỉ giữ lại người đi bộ thực sự.
    classes=[0] ép YOLO chỉ detect class 0 ngay từ inference — nhanh hơn.
    """
    results = model(
        frame,
        verbose=False,
        classes=[0],            # Chỉ detect person, bỏ qua class khác
        conf=PERSON_CONF_THRESHOLD,
        iou=0.45,               # NMS threshold — giảm để tránh merge box
        agnostic_nms=False,
    )[0]

    pedestrians = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])

        if cls_id != 0:
            continue

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # ── Lọc người đi bộ vs người trên phương tiện ──
        if not is_pedestrian(x1, y1, x2, y2):
            continue

        pedestrians.append({
            "x1": x1, "y1": y1,
            "x2": x2, "y2": y2,
            "confidence": conf
        })

    return pedestrians


def draw_detections(frame, pedestrians):
    """Vẽ bounding box và label"""
    for i, det in enumerate(pedestrians):
        x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
        conf  = det['confidence']
        label = f"Walker {i+1} ({conf:.2f})"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), (0, 255, 0), -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

    # Thống kê góc trên trái
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (340, 55), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    cv2.putText(frame, f"Pedestrians: {len(pedestrians)}", (10, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    return frame


def save_output(frame, input_path):
    output_dir = os.path.join(BASE_DIR, "outputs", "nhandiennguoidibo")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{base_name}_detected_{timestamp}.jpg")

    cv2.imwrite(output_path, frame)
    return output_path


def main():
    # 1. Kiểm tra model trước
    if not os.path.exists(BEST_MODEL_PATH):
        print(f"❌ Không tìm thấy best.pt tại:\n   {BEST_MODEL_PATH}")
        sys.exit(1)

    print(f"⏳ Load model: {BEST_MODEL_PATH}")
    model = YOLO(BEST_MODEL_PATH)
    print(f"✅ Model loaded | Classes: {model.names}")

    # Xác nhận class 0 là person
    if model.names.get(0, "").lower() not in ("person", "pedestrian", "nguoi"):
        print(f"⚠️  Cảnh báo: class 0 = '{model.names.get(0)}' — kiểm tra lại dataset!")

    # 2. Chọn ảnh
    print("📂 Mở hộp thoại chọn ảnh...")
    image_path = pick_image()
    if not image_path:
        print("❌ Không có ảnh nào được chọn.")
        sys.exit(0)

    # 3. Đọc ảnh
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"❌ Không đọc được ảnh: {image_path}")
        sys.exit(1)
    print(f"✅ Ảnh: {image_path} ({frame.shape[1]}x{frame.shape[0]})")

    # 4. Detect
    print("🔍 Nhận diện người đi bộ...")
    pedestrians = detect_pedestrians(frame, model)

    # 5. Kết quả
    print(f"\n📊 KẾT QUẢ: {len(pedestrians)} người đi bộ")
    for i, det in enumerate(pedestrians):
        h = det['y2'] - det['y1']
        w = det['x2'] - det['x1']
        print(f"   [Walker {i+1}] conf={det['confidence']:.2f} | "
              f"ratio={h/w:.2f} | "
              f"box=({det['x1']:.0f},{det['y1']:.0f},{det['x2']:.0f},{det['y2']:.0f})")

    # 6. Vẽ + lưu
    result_frame = draw_detections(frame.copy(), pedestrians)
    output_path  = save_output(result_frame, image_path)
    print(f"\n💾 Lưu tại: {output_path}")

    # 7. Hiển thị
    cv2.imshow("Pedestrian Detection (best.pt)", result_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("✅ Hoàn tất!")


if __name__ == "__main__":
    main()