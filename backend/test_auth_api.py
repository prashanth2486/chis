import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def run_auth_tests():
    print("Running Auth API checks...")

    farmer_payload = {
        "farmer_id": "F999",
        "password": "password123",
        "name": "Jane Doe",
        "contact_no": "555-1234",
        "address": "123 Farm Lane",
    }
    r_farmer = client.post("/register/farmer", json=farmer_payload)
    assert r_farmer.status_code in [200, 400]

    doc_payload = {
        "ic_id": "IC999",
        "password": "docpassword",
        "name": "Dr. Sarah",
        "address": "456 Vet Clinic",
        "contact_no": "555-9876",
        "email_id": "sarah@vet.com",
        "city_name": "Farmville",
    }
    r_doc = client.post("/register/vdoctor", json=doc_payload)
    assert r_doc.status_code in [200, 400]

    l1 = client.post("/login", json={"user_id": "F999", "password": "password123", "role": "farmer"})
    assert l1.status_code == 200
    farmer_token = l1.json().get("access_token")
    assert farmer_token

    l2 = client.post("/login", json={"user_id": "IC999", "password": "docpassword", "role": "doctor"})
    assert l2.status_code == 200
    assert l2.json().get("access_token")

    l3 = client.post("/login", json={"user_id": "admin", "password": "admin123", "role": "admin"})
    assert l3.status_code == 200
    admin_token = l3.json().get("access_token")
    assert admin_token

    u_res = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert u_res.status_code == 200
    data = u_res.json()
    assert len(data["farmers"]) > 0
    assert len(data["doctors"]) > 0

    own_queries = client.get("/queries", headers={"Authorization": f"Bearer {farmer_token}"})
    assert own_queries.status_code == 200

    print("All Auth integration tests passed successfully.")


if __name__ == "__main__":
    run_auth_tests()
