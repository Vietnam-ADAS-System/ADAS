"""Recognize digits inside speed-limit traffic signs using OpenCV."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Any, ClassVar, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class DigitRecognition:
    value: Optional[int]
    confidence: float

    @property
    def succeeded(self) -> bool:
        return self.value is not None


class DigitRecognizer:
    """Read supported speed values with fast CV and an EasyOCR fallback."""

    _easyocr_reader: ClassVar[Optional[Any]] = None
    _easyocr_unavailable: ClassVar[bool] = False

    def __init__(
        self,
        allowed_values: Iterable[int] = (40, 50, 60, 80),
        min_confidence: float = 0.55,
        use_easyocr: bool = True,
    ) -> None:
        self.allowed_values = tuple(sorted({int(value) for value in allowed_values}))
        self.min_confidence = float(min_confidence)
        self.use_easyocr = bool(use_easyocr)
        self._templates = self._build_templates()

    def recognize(self, sign_crop: np.ndarray) -> DigitRecognition:
        if not isinstance(sign_crop, np.ndarray) or sign_crop.size == 0:
            return DigitRecognition(None, 0.0)
        if min(sign_crop.shape[:2]) < 18:
            return DigitRecognition(None, 0.0)

        gray = (
            cv2.cvtColor(sign_crop, cv2.COLOR_BGR2GRAY)
            if sign_crop.ndim == 3
            else sign_crop.copy()
        )
        gray = cv2.resize(gray, (180, 180), interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        binaries = self._build_binary_variants(gray)

        structural_values = [
            value
            for binary in binaries
            if (value := self._recognize_by_structure(binary)) is not None
        ]
        if structural_values:
            vote_counts = Counter(structural_values)
            value, vote_count = vote_counts.most_common(1)[0]
            runner_up = vote_counts.most_common(2)[1][1] if len(vote_counts) > 1 else 0
            confidence = min(0.97, 0.70 + 0.07 * vote_count)
            if vote_count >= 2 and vote_count > runner_up and confidence >= self.min_confidence:
                return DigitRecognition(value, confidence)

        easyocr_result = self._recognize_with_easyocr(sign_crop)
        if easyocr_result is not None:
            value, confidence = easyocr_result
            if confidence >= self.min_confidence:
                return DigitRecognition(value, confidence)

        best_value, best_score, second_score = None, 0.0, 0.0
        for binary in binaries:
            digits = self._extract_digits(binary)
            if digits is None:
                continue
            feature = self._normalize(digits).astype(np.float32).ravel() / 255.0
            feature /= max(float(np.linalg.norm(feature)), 1e-6)
            scores = sorted(
                (
                    max(
                        float(template @ feature)
                        for template_value, template in self._templates
                        if template_value == value
                    ),
                    value,
                )
                for value in self.allowed_values
            )
            score, value = scores[-1]
            runner_up = scores[-2][0] if len(scores) > 1 else 0.0
            if score > best_score:
                best_value, best_score, second_score = value, score, runner_up

        margin = max(0.0, best_score - second_score)
        confidence = float(np.clip(0.55 * best_score + 3.0 * margin, 0.0, 1.0))
        if confidence < self.min_confidence:
            return DigitRecognition(None, confidence)
        return DigitRecognition(best_value, confidence)

    @staticmethod
    def _build_binary_variants(gray: np.ndarray) -> Tuple[np.ndarray, ...]:
        height, width = gray.shape
        crop_ratios = (
            (0.10, 0.12, 0.90, 0.88),
            (0.16, 0.18, 0.84, 0.84),
            (0.20, 0.20, 0.80, 0.82),
        )
        binaries = []
        for left, top, right, bottom in crop_ratios:
            region = gray[
                int(height * top):int(height * bottom),
                int(width * left):int(width * right),
            ]
            if region.size == 0:
                continue
            binaries.append(
                cv2.threshold(
                    region,
                    0,
                    255,
                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
                )[1]
            )
            binaries.append(
                cv2.adaptiveThreshold(
                    region,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV,
                    31,
                    7,
                )
            )
        return tuple(binaries)

    def _recognize_with_easyocr(
        self,
        sign_crop: np.ndarray,
    ) -> Optional[Tuple[int, float]]:
        if not self.use_easyocr:
            return None

        reader = self._get_easyocr_reader()
        if reader is None:
            return None

        enlarged = cv2.resize(sign_crop, (256, 256), interpolation=cv2.INTER_CUBIC)
        allowlist = "".join(sorted({digit for value in self.allowed_values for digit in str(value)}))
        try:
            results = reader.readtext(
                enlarged,
                allowlist=allowlist,
                detail=1,
                min_size=5,
                text_threshold=0.4,
                low_text=0.2,
                link_threshold=0.2,
                mag_ratio=1.5,
            )
        except Exception:
            return None

        candidates = []
        for _, text, confidence in results:
            digits = re.sub(r"\D", "", str(text))
            if not digits:
                continue
            value = int(digits)
            if value in self.allowed_values:
                candidates.append((value, float(confidence)))

        return max(candidates, key=lambda item: item[1]) if candidates else None

    @classmethod
    def _get_easyocr_reader(cls) -> Optional[Any]:
        if cls._easyocr_unavailable:
            return None
        if cls._easyocr_reader is not None:
            return cls._easyocr_reader

        try:
            import easyocr

            cls._easyocr_reader = easyocr.Reader(
                ["en"],
                gpu=False,
                verbose=False,
            )
        except Exception:
            cls._easyocr_unavailable = True
            return None
        return cls._easyocr_reader

    def _find_digit_boxes(
        self,
        binary: np.ndarray,
    ) -> Optional[List[Tuple[int, int, int, int]]]:
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        height, width = binary.shape
        boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if height * 0.32 <= h <= height * 0.92 and w <= width * 0.45:
                if cv2.contourArea(contour) >= height * width * 0.004:
                    boxes.append((x, y, w, h))

        boxes.sort(key=lambda box: box[2] * box[3], reverse=True)
        filtered = []
        for box in boxes:
            if any(self._bbox_overlap_ratio(box, kept) >= 0.35 for kept in filtered):
                continue
            filtered.append(box)

        if len(filtered) < 2:
            return None

        pairs = []
        for first_index, first in enumerate(filtered):
            for second in filtered[first_index + 1:]:
                left, right = sorted((first, second))
                lx, ly, lw, lh = left
                rx, ry, rw, rh = right
                height_ratio = min(lh, rh) / max(lh, rh)
                center_delta = abs((ly + lh / 2.0) - (ry + rh / 2.0)) / max(lh, rh)
                horizontal_gap = rx - (lx + lw)
                if height_ratio < 0.55 or center_delta > 0.35:
                    continue
                if horizontal_gap < -0.15 * min(lw, rw) or horizontal_gap > 1.25 * max(lh, rh):
                    continue
                score = height_ratio - center_delta + (lh + rh) / (2.0 * height)
                pairs.append((score, [left, right]))

        if not pairs:
            return None
        return max(pairs, key=lambda item: item[0])[1]

    @staticmethod
    def _bbox_overlap_ratio(
        first: Tuple[int, int, int, int],
        second: Tuple[int, int, int, int],
    ) -> float:
        ax, ay, aw, ah = first
        bx, by, bw, bh = second
        overlap_width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
        overlap_height = max(0, min(ay + ah, by + bh) - max(ay, by))
        overlap = overlap_width * overlap_height
        return overlap / max(1, min(aw * ah, bw * bh))

    def _recognize_by_structure(self, binary: np.ndarray) -> Optional[int]:
        boxes = self._find_digit_boxes(binary)
        if boxes is None or len(boxes) != 2:
            return None

        x, y, width, height = boxes[0]
        first_digit = binary[y:y + height, x:x + width]
        contours, hierarchy = cv2.findContours(
            first_digit,
            cv2.RETR_CCOMP,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if hierarchy is None:
            return None

        minimum_hole_area = first_digit.size * 0.015
        holes = [
            contour
            for index, contour in enumerate(contours)
            if hierarchy[0][index][3] >= 0
            and cv2.contourArea(contour) >= minimum_hole_area
        ]

        if len(holes) >= 2:
            value = 80
        elif not holes:
            value = 50
        else:
            _, hole_y, _, hole_height = cv2.boundingRect(holes[0])
            relative_center = (hole_y + hole_height / 2.0) / max(height, 1)
            value = 60 if relative_center >= 0.52 else 40

        return value if value in self.allowed_values else None

    def _extract_digits(self, binary: np.ndarray) -> Optional[np.ndarray]:
        boxes = self._find_digit_boxes(binary)
        if boxes is None:
            return None
        x1 = min(box[0] for box in boxes)
        y1 = min(box[1] for box in boxes)
        x2 = max(box[0] + box[2] for box in boxes)
        y2 = max(box[1] + box[3] for box in boxes)
        return binary[y1:y2, x1:x2]

    @staticmethod
    def _normalize(image: np.ndarray) -> np.ndarray:
        canvas = np.zeros((48, 80), dtype=np.uint8)
        height, width = image.shape
        scale = min(72 / max(width, 1), 40 / max(height, 1))
        resized = cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        x = (80 - resized.shape[1]) // 2
        y = (48 - resized.shape[0]) // 2
        canvas[y:y + resized.shape[0], x:x + resized.shape[1]] = resized
        return canvas

    def _build_templates(self) -> Tuple[Tuple[int, np.ndarray], ...]:
        templates = []
        fonts = (cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX)
        for value in self.allowed_values:
            for font in fonts:
                for thickness in (2, 3, 4):
                    image = np.zeros((80, 140), dtype=np.uint8)
                    cv2.putText(
                        image, str(value), (8, 62), font, 2.0,
                        255, thickness, cv2.LINE_AA
                    )
                    points = cv2.findNonZero(image)
                    if points is None:
                        continue
                    x, y, width, height = cv2.boundingRect(points)
                    feature = self._normalize(
                        image[y:y + height, x:x + width]
                    ).astype(np.float32).ravel() / 255.0
                    feature /= max(float(np.linalg.norm(feature)), 1e-6)
                    templates.append((value, feature))
        return tuple(templates)


def crop_bbox(
    image: np.ndarray,
    bbox: Sequence[float],
    padding: float = 0.03,
) -> np.ndarray:
    """Crop a clipped (x1, y1, x2, y2) bounding box."""
    height, width = image.shape[:2]
    x1, y1, x2, y2 = map(float, bbox)
    pad_x = max(0.0, x2 - x1) * padding
    pad_y = max(0.0, y2 - y1) * padding
    left = max(0, int(x1 - pad_x))
    top = max(0, int(y1 - pad_y))
    right = min(width, int(x2 + pad_x))
    bottom = min(height, int(y2 + pad_y))
    return image[top:bottom, left:right].copy()
