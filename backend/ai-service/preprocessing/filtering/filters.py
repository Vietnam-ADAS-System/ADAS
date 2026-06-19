import cv2
import numpy as np


def gaussian_filter(image: np.ndarray, kernel_size: int = 5,
                    sigma: float = 1.0) -> np.ndarray:
    """
    Dùng cho: Làm mượt trước Canny edge detection trong lane detection
    Input : BGR hoặc Grayscale uint8
    Output: cùng shape, cùng dtype
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)


def median_filter(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """
    Dùng cho: Loại salt-and-pepper noise từ camera giao thông
    Input : BGR hoặc Grayscale uint8
    Output: cùng shape, cùng dtype
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.medianBlur(image, kernel_size)
