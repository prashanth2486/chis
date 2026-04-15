def test_invalid_login_role_validation(client):
    response = client.post("/login", json={"user_id": "x", "password": "x", "role": "invalid"})
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


def test_invalid_doctor_email_validation(client):
    payload = {
        "ic_id": "IC_BAD",
        "password": "password123",
        "name": "Bad Email Doc",
        "address": "Address",
        "contact_no": "123456",
        "email_id": "not-an-email",
        "city_name": "City",
    }
    response = client.post("/register/vdoctor", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
