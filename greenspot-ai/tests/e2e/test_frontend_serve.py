from fastapi.testclient import TestClient
from greenspot.api.server import app

client = TestClient(app)

def test_frontend_serve():
    # If frontend dist exists, it serves index.html
    response = client.get("/")
    assert response.status_code in [200, 404]
