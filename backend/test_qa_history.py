import os
import sys

from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)


def run_tests():
    print("Running QA and History APIs checks...")

    farmer_payload = {
        "farmer_id": "F101",
        "password": "farmerpass",
        "name": "Farmer One",
        "contact_no": "555-0101",
        "address": "Village Road",
    }
    client.post("/register/farmer", json=farmer_payload)

    farmer_login = client.post("/login", json={"user_id": "F101", "password": "farmerpass", "role": "farmer"})
    assert farmer_login.status_code == 200
    farmer_token = farmer_login.json()["access_token"]

    admin_login = client.post("/login", json={"user_id": "admin", "password": "admin123", "role": "admin"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    query_payload = {"farmer_id": "F101", "query_text": "My cows are coughing and have fever. What should I do?"}
    q_res = client.post("/queries", json=query_payload, headers={"Authorization": f"Bearer {farmer_token}"})
    assert q_res.status_code == 200
    query_id = q_res.json()["id"]

    list_res = client.get("/queries", headers={"Authorization": f"Bearer {farmer_token}"})
    assert list_res.status_code == 200
    queries = list_res.json()
    assert len(queries) > 0

    reply_payload = {"reply_text": "Isolate the sick cows and ensure hydration. Visit is needed."}
    rep_res = client.post(
        f"/queries/{query_id}/reply",
        json=reply_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rep_res.status_code == 200

    hist_payload = {
        "farmer_id": "F101",
        "description": "Routine test",
        "symptoms": "coughing, fever",
        "disease": "Respiratory Infection",
        "treatments": "Antibiotics",
    }
    h_res = client.post("/history", json=hist_payload, headers={"Authorization": f"Bearer {farmer_token}"})
    assert h_res.status_code == 200

    hl_res = client.get("/history/F101", headers={"Authorization": f"Bearer {farmer_token}"})
    assert hl_res.status_code == 200
    assert len(hl_res.json()) > 0

    print("All integration tests passed successfully.")


if __name__ == "__main__":
    run_tests()
