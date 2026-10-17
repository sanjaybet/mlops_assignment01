import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.predict import predict_single_record

app = FastAPI(title="Heart Disease Prediction API", version="1.0.0")


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
    payload = record.model_dump(exclude_none=True)
    try:
        result = predict_single_record(payload)
    except Exception as exc:  # pragma: no cover - API defensive guard
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
