from fastapi.testclient import TestClient

from src.api.app import app


def test_health_reports_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/system/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
