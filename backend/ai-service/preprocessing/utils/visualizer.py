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


def save_comparison(original: np.ndarray, processed: np.ndarray,
                    save_path: str, title: str = "Before | After") -> None:
    """
    Lưu ảnh so sánh before/after vào file (thay vì chỉ hiển thị).
    Hữu dụng cho CI/CD hoặc khi không có display.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Tạo ảnh đôi (side-by-side)
    if len(original.shape) == 3 and original.shape[2] == 3:
        h, w = original.shape[:2]
        combined = np.zeros((h, w * 2, 3), dtype=original.dtype)
        combined[:, :w] = original
        combined[:, w:] = processed if len(processed.shape) == 3 else cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
    else:
        # Grayscale
        h, w = original.shape[:2]
        combined = np.zeros((h, w * 2), dtype=original.dtype)
        combined[:, :w] = original if len(original.shape) == 2 else cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        combined[:, w:] = processed
    
    cv2.imwrite(save_path, combined)
    print(f"[visualizer] Lưu ảnh so sánh: {save_path}")
