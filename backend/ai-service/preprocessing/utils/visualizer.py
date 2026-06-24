import os
import cv2
import numpy as np
import matplotlib.pyplot as plt


def show_comparison(original: np.ndarray, processed: np.ndarray, title: str = "Before | After"):
    """Hiển thị 2 ảnh side-by-side bằng matplotlib"""
    if original is None or processed is None:
        raise ValueError("Original and processed images must not be None")

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle(title)

    if original.ndim == 2:
        axes[0].imshow(original, cmap="gray")
    else:
        axes[0].imshow(original)
    axes[0].set_title("Original")
    axes[0].axis("off")

    if processed.ndim == 2:
        axes[1].imshow(processed, cmap="gray")
    else:
        axes[1].imshow(processed)
    axes[1].set_title("Processed")
    axes[1].axis("off")

    plt.tight_layout()
    plt.show()


def save_image(image: np.ndarray, save_path: str):
    """Tạo thư mục nếu chưa có, lưu ảnh bằng cv2.imwrite"""
    if image is None:
        raise ValueError("Image must not be None")
    if save_path is None or save_path == "":
        raise ValueError("save_path must be a non-empty string")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if image.ndim == 3 and image.shape[2] == 3:
        save_frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    else:
        save_frame = image

    if not cv2.imwrite(save_path, save_frame):
        raise IOError(f"Failed to write image to {save_path}")
