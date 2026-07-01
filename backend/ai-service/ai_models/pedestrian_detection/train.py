
from ultralytics import YOLO
import os
import torch
import yaml
import shutil
from pathlib import Path
from datetime import datetime

# ===== CẤU HÌNH TRAIN =====
DATA_YAML = "C:/Users/admin/Downloads/pedestrian/Vietnam-ADAS-System/datasets/pedestrian/data.yaml"
MODEL     = "yolo11n.pt"
EPOCHS    = 150
IMG_SIZE  = 640
BATCH     = 16
PROJECT   = "runs/pedestrian"
NAME      = "walking_v1"
# ==========================


def check_gpu():
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"  🎮 GPU  : {gpu_name}")
        print(f"  💾 VRAM : {vram:.1f} GB")
        return True, vram
    else:
        print("  ⚠️ Không tìm thấy GPU — dùng CPU")
        return False, 0


def check_dataset(data_yaml: str):
    with open(data_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    print(f"\n📁 Dataset:")
    print(f"   Classes : {data.get('names', [])}")
    print(f"   NC      : {data.get('nc', '?')}")

    total = 0
    train_count = 0

    for split in ["train", "val", "test"]:
        path = data.get(split)
        if path:
            p = Path(path)
            if not p.is_absolute():
                p = Path(data_yaml).parent / p

            imgs = list(p.glob("*.jpg")) + list(p.glob("*.png"))
            count = len(imgs)

            print(f"   {split:<5}: {count} ảnh")
            total += count

            if split == "train":
                train_count = count

    print(f"   Tổng : {total} ảnh")
    return data, train_count


def get_train_args(has_gpu: bool, vram: float, epochs: int, batch: int) -> dict:
    args = dict(
        data=DATA_YAML,
        epochs=epochs,
        imgsz=IMG_SIZE,
        batch=batch,
        project=PROJECT,
        name=NAME,
        exist_ok=True,

        optimizer="AdamW",
        lr0=0.0008,
        lrf=0.008,
        momentum=0.937,
        weight_decay=0.0008,
        warmup_epochs=10,
        warmup_momentum=0.8,
        warmup_bias_lr=0.05,
        cos_lr=True,

        label_smoothing=0.1,
        dropout=0.15,
        close_mosaic=20,

        patience=20,
        save=True,
        save_period=10,

        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.1,
        scale=0.6,
        shear=1.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.1,

        box=7.5,
        cls=0.5,
        dfl=1.5,

        iou=0.7,

        plots=True,
        verbose=True,
        seed=42,
        workers=2 if has_gpu else 0,
        amp=has_gpu,
        cache=False,
        val=True,
    )

    return args


def backup_best_model(project: str, name: str):
    best = Path(project) / name / "weights" / "best.pt"
    if best.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        backup_dir = Path(project) / "backups"
        backup_dir.mkdir(exist_ok=True)
        dest = backup_dir / f"best_{name}_{ts}.pt"
        shutil.copy2(best, dest)
        print(f"📦 Backup lưu tại: {dest}")


def evaluate(model_path: str, data_yaml: str):
    print("\n⏳ Đánh giá model...")
    model = YOLO(model_path)

    metrics = model.val(
        data=data_yaml,
        imgsz=IMG_SIZE,
        conf=0.25,
        iou=0.6,
        verbose=False,
    )

    print(f"mAP50: {metrics.box.map50:.4f}")


def main():
    print("\n" + "=" * 52)
    print(" TRAIN NHẬN DIỆN NGƯỜI ĐI BỘ - YOLO11 ")
    print("=" * 52)

    has_gpu, vram = check_gpu()

    if not os.path.exists(DATA_YAML):
        print(f"\n❌ Không tìm thấy: {DATA_YAML}")
        return

    _, train_count = check_dataset(DATA_YAML)

    print(f"\n⚙️ Config:")
    print(f"Model     : {MODEL}")
    print(f"Epochs    : {EPOCHS}")
    print(f"ImageSize : {IMG_SIZE}")
    print(f"Batch     : {BATCH}")

    est_hours = (EPOCHS * train_count) / (3600 * (50 if has_gpu else 2))
    print(f"⏱️ Ước tính train: ~{est_hours:.1f} giờ")

    print("\n⏳ Bắt đầu train...\n")

    model = YOLO(MODEL)
    train_args = get_train_args(has_gpu, vram, EPOCHS, BATCH)
    model.train(**train_args)

    backup_best_model(PROJECT, NAME)

    best_path = f"{PROJECT}/{NAME}/weights/best.pt"
    evaluate(best_path, DATA_YAML)

    print("\n✅ Hoàn tất!")


if __name__ == "__main__":
    main()
