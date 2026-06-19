import cv2
import numpy as np
import os

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def show_comparison(original: np.ndarray, processed: np.ndarray,
                    title: str = "Before | After") -> None:
    """Hiển thị 2 ảnh side-by-side"""
    if not MATPLOTLIB_AVAILABLE:
        print("[visualizer] matplotlib chưa được cài — bỏ qua visualize")
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Original")
    axes[0].axis("off")
    if len(processed.shape) == 2:
        axes[1].imshow(processed, cmap="gray")
    else:
        axes[1].imshow(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
    axes[1].set_title("Processed")
    axes[1].axis("off")
    plt.suptitle(title)
    plt.tight_layout()
    plt.show()


def save_image(image: np.ndarray, save_path: str) -> None:
    """Tạo thư mục nếu chưa có, lưu ảnh"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, image)
