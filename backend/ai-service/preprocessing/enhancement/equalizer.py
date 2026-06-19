import cv2
import numpy as np


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    Dùng cho: Tracking (DeepSORT) — ổn định brightness giữa các frame
    Input : BGR uint8 HxWx3 hoặc Grayscale HxW
    Output: cùng shape với input
    """
    if len(image.shape) == 2:
        return cv2.equalizeHist(image)
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def clahe(image: np.ndarray, clip_limit: float = 2.0,
          tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """
    Dùng cho: Vehicle / Pedestrian / Traffic Sign — local contrast enhancement
    Input : BGR uint8 HxWx3 hoặc Grayscale HxW
    Output: cùng shape với input
    """
    _clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    if len(image.shape) == 2:
        return _clahe.apply(image)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = _clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
