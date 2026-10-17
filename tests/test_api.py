from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_exposes_request_metrics():
    client = TestClient(app)

    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text
    assert 'handler="/health"' in metrics_response.text
