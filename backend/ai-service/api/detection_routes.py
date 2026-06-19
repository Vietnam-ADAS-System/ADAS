from typing import Optional

import cv2
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile

from ai_models.detection.vehicle_detector import VehicleObjectDetector


router = APIRouter(prefix="/detect", tags=["vehicle-object-detection"])
_detector: Optional[VehicleObjectDetector] = None


def get_detector() -> VehicleObjectDetector:
    global _detector
    if _detector is None:
        _detector = VehicleObjectDetector.from_env()
    return _detector


@router.post("/vehicles")
async def detect_vehicles(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(
        None,
        ge=0.01,
        le=0.99,
        description="Override confidence threshold for this request.",
    ),
    image_size: Optional[int] = Query(
        None,
        ge=320,
        le=1536,
        description="Override inference image size for this request.",
    ),
    augment: Optional[bool] = Query(
        None,
        description="Enable test-time augmentation for higher recall but slower inference.",
    ),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()
    try:
        return get_detector().detect_image_bytes(
            image_bytes,
            confidence=confidence,
            image_size=image_size,
            augment=augment,
            source_name=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/vehicles/annotated")
async def detect_vehicles_annotated(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(None, ge=0.01, le=0.99),
    image_size: Optional[int] = Query(None, ge=320, le=1536),
    augment: Optional[bool] = Query(None),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()
    try:
        result, image = get_detector().detect_image_bytes(
            image_bytes,
            confidence=confidence,
            image_size=image_size,
            augment=augment,
            source_name=file.filename,
            return_image=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    annotated = get_detector().draw_detections(image, result["detections"])
    ok, encoded = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise HTTPException(status_code=500, detail="Could not encode annotated image.")

    return Response(
        content=encoded.tobytes(),
        media_type="image/jpeg",
        headers={"X-Detection-Count": str(result["count"])},
    )
