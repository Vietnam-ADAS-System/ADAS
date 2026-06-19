import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from api.detection_routes import router as detection_router


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(
    title="ADAS AI Service",
    version="0.1.0",
    description="AI service endpoints for the ADAS project.",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "adas-ai-service"}


@app.get("/")
def service_info():
    return {
        "service": "adas-ai-service",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "vehicle_detection": {
            "json": "POST /detect/vehicles",
            "annotated_image": "POST /detect/vehicles/annotated",
            "classes": ["person", "car", "motorcycle"],
        },
    }


app.include_router(detection_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AI_SERVICE_PORT", "8000"))
    reload = os.getenv("APP_ENV", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
