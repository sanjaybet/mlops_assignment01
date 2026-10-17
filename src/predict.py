import os
from typing import Any, Dict, List, Union

import pandas as pd
import joblib

MODEL_PATH = os.path.join("data", "processed", "model.joblib")
EXPECTED_FEATURES = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]


def load_model(model_path: str = MODEL_PATH) -> Any:
    """Load the trained model pipeline from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model artifact not found at '{model_path}'. Train the model first."
        )
    return joblib.load(model_path)


def _build_feature_frame(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
    """Normalize input records into a dataframe with the model feature order."""
    if isinstance(payload, dict):
        rows = [payload]
    else:
        rows = payload

    df = pd.DataFrame(rows)
    missing = [feature for feature in EXPECTED_FEATURES if feature not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required feature(s): {joined}")

    return df[EXPECTED_FEATURES]


def predict_single_record(payload: Dict[str, Any], model_path: str = MODEL_PATH) -> Dict[str, Any]:
    """Return a prediction and probability for a single patient record."""
    model = load_model(model_path)
    feature_frame = _build_feature_frame(payload)
    prediction = model.predict(feature_frame)[0]
    probability = model.predict_proba(feature_frame)[0]

    return {
        "prediction": int(prediction),
        "probability": {
            "no_disease": float(probability[0]),
            "disease_present": float(probability[1]),
        },
    }


def predict_records(payloads: List[Dict[str, Any]], model_path: str = MODEL_PATH) -> List[Dict[str, Any]]:
    """Return predictions for multiple patient records."""
    model = load_model(model_path)
    feature_frame = _build_feature_frame(payloads)
    predictions = model.predict(feature_frame)
    probabilities = model.predict_proba(feature_frame)

    output = []
    for index, prediction in enumerate(predictions):
        output.append(
            {
                "prediction": int(prediction),
                "probability": {
                    "no_disease": float(probabilities[index][0]),
                    "disease_present": float(probabilities[index][1]),
                },
            }
        )
    return output
