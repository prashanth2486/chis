import io
import os
import sys

import pandas as pd
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)


def test_eclat_endpoint():
    login = client.post("/login", json={"user_id": "admin", "password": "admin123", "role": "admin"})
    assert login.status_code == 200
    token = login.json().get("access_token")
    assert token

    data = {
        "Data": [
            "fever,cough",
            "fever,cough,nasal-discharge",
            "fever,nasal-discharge",
            "cough",
            "fever,cough,nasal-discharge",
        ]
    }
    df = pd.DataFrame(data)

    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    response = client.post(
        "/eclat/run",
        files={"file": ("test.csv", csv_buffer, "text/csv")},
        params={"min_support": 0.3, "min_confidence": 0.5},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Failed with {response.status_code}: {response.text}"
    print("Test passed successfully!")


if __name__ == "__main__":
    test_eclat_endpoint()
