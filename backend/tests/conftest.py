import os
import sys

import pytest
from fastapi.testclient import TestClient


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(client: TestClient) -> str:
    response = client.post("/login", json={"user_id": "admin", "password": "admin123", "role": "admin"})
    assert response.status_code == 200
    return response.json()["access_token"]
