from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_upload_missing_file():
    response = client.post("/upload")
    assert response.status_code in (400, 422)


