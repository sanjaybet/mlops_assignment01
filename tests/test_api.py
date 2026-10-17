from fastapi.testclient import TestClient

from app.main import app, request_logger


def test_metrics_endpoint_exposes_request_metrics(caplog):
    client = TestClient(app)
    request_logger.addHandler(caplog.handler)

    try:
        health_response = client.get("/health")
        metrics_response = client.get("/metrics")
    finally:
        request_logger.removeHandler(caplog.handler)

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text
    assert 'handler="/health"' in metrics_response.text
    assert "method=GET path=/health status_code=200" in caplog.text


def test_prediction_accepts_omitted_optional_features():
    client = TestClient(app)
    payload = {
        "age": 63,
        "sex": 1,
        "cp": 1,
        "trestbps": 145,
        "chol": 233,
        "fbs": 1,
        "restecg": 2,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 2.3,
        "slope": 3,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] in [0, 1]
