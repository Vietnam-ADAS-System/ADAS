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


def rgb_to_hsv(image: np.ndarray, visualize=False, save_path=None) -> np.ndarray:
    """
    Dùng cho: Lane Detection (tách màu làn đường), Traffic Sign (phân biệt màu biển báo)
    Input: RGB uint8 HxWx3
    Output: HSV uint8 HxWx3
    """
    if image is None:
        raise ValueError("Input image must not be None")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb_to_hsv expects an RGB image with shape HxWx3")

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    if visualize:
        show_comparison(image, cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), title="RGB | HSV")
    if save_path is not None:
        out_path = _resolve_save_path(save_path, "rgb_to_hsv.png")
        save_image(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), out_path)
    return hsv


def rgb_to_gray(image: np.ndarray, visualize=False, save_path=None) -> np.ndarray:
    """
    Dùng cho: Edge Detection → Lane Detection (CVIP pipeline)
    Input: RGB uint8 HxWx3
    Output: Grayscale uint8 HxW
    """
    if image is None:
        raise ValueError("Input image must not be None")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb_to_gray expects an RGB image with shape HxWx3")

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    if visualize:
        show_comparison(image, gray, title="RGB | Gray")
    if save_path is not None:
        out_path = _resolve_save_path(save_path, "rgb_to_gray.png")
        save_image(gray, out_path)
    return gray
