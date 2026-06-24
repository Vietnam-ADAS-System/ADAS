import os
import numpy as np
import cv2
from preprocessing.utils.visualizer import save_image, show_comparison


def _resolve_save_path(save_path: str, default_name: str) -> str:
    if save_path is None:
        return None
    if os.path.isdir(save_path) or save_path.endswith(('/', '\\')):
        os.makedirs(save_path, exist_ok=True)
        return os.path.join(save_path, default_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    return save_path


def histogram_equalization(image: np.ndarray, visualize=False, save_path=None) -> np.ndarray:
    """
    Dùng cho: cải thiện contrast trong điều kiện ánh sáng yếu (ban đêm, ngược sáng)
    Input: Grayscale HxW hoặc RGB HxWx3 (xử lý từng channel nếu RGB)
    Output: cùng shape với input
    """
    if image is None:
        raise ValueError("Input image must not be None")

    if image.ndim == 2:
        equalized = cv2.equalizeHist(image)
    elif image.ndim == 3 and image.shape[2] == 3:
        channels = cv2.split(image)
        equalized_channels = [cv2.equalizeHist(ch) for ch in channels]
        equalized = cv2.merge(equalized_channels)
    else:
        raise ValueError("histogram_equalization expects a grayscale or RGB image")

    if visualize:
        show_comparison(image, equalized, title="Original | Histogram Equalized")
    if save_path is not None:
        out_path = _resolve_save_path(save_path, "histogram_equalization.png")
        save_image(equalized, out_path)
    return equalized


def clahe(image: np.ndarray, clip_limit=2.0, tile_grid_size=(8, 8),
          visualize=False, save_path=None) -> np.ndarray:
    """
    Dùng cho: Lane Detection và Traffic Sign — CLAHE tốt hơn HE cho ảnh local contrast
    Input: Grayscale HxW (recommended) hoặc RGB
    Output: cùng shape với input
    Note: Nếu input RGB, convert sang LAB → apply CLAHE trên L channel → convert lại RGB
    """
    if image is None:
        raise ValueError("Input image must not be None")

    clahe_operator = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    if image.ndim == 2:
        processed = clahe_operator.apply(image)
    elif image.ndim == 3 and image.shape[2] == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l_clahe = clahe_operator.apply(l)
        lab_clahe = cv2.merge([l_clahe, a, b])
        processed = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
    else:
        raise ValueError("clahe expects a grayscale or RGB image")

    if visualize:
        show_comparison(image, processed, title="Original | CLAHE")
    if save_path is not None:
        out_path = _resolve_save_path(save_path, "clahe.png")
        save_image(processed, out_path)
    return processed
