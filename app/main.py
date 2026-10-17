import os
import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from src.predict import predict_single_record

app = FastAPI(title="Heart Disease Prediction API", version="1.0.0")
Instrumentator().instrument(app).expose(app, include_in_schema=False)
request_logger = logging.getLogger("api.requests")
request_logger.setLevel(logging.INFO)
request_logger.propagate = False
if not request_logger.handlers:
    request_logger.addHandler(logging.StreamHandler())


@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    started_at = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        request_logger.info(
            "method=%s path=%s status_code=%d duration_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
        )


class PatientRecord(BaseModel):
    age: float
    sex: float
    cp: float
    trestbps: float
    chol: float
    fbs: float
    restecg: float
    thalach: float
    exang: float
    oldpeak: float
    slope: float
    ca: float | None = None
    thal: float | None = None


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(record: PatientRecord) -> Dict[str, Any]:
    payload = record.model_dump()
    try:
        result = predict_single_record(payload)
    except Exception as exc:  # pragma: no cover - API defensive guard
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
