import cv2
import numpy as np


def rgb_to_hsv(image: np.ndarray, color_format: str = "BGR") -> np.ndarray:
    """
    Dùng cho: Lane Detection (tách màu làn đường), Traffic Sign (phân biệt màu biển)
    Input : BGR hoặc RGB uint8 HxWx3
    Output: HSV uint8 HxWx3
    """
    if color_format == "BGR":
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)


def rgb_to_gray(image: np.ndarray, color_format: str = "BGR") -> np.ndarray:
    """
    Dùng cho: Lane Detection CVIP (chuẩn bị cho Canny / Hough Transform)
    Input : BGR hoặc RGB uint8 HxWx3
    Output: Grayscale uint8 HxW
    """
    if color_format == "BGR":
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
