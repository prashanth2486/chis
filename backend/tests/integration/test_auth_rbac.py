def test_login_returns_jwt(client):
    response = client.post("/login", json={"user_id": "admin", "password": "admin123", "role": "admin"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("access_token")
    assert body.get("token_type") == "bearer"


def test_users_requires_auth(client):
    response = client.get("/users")
    assert response.status_code == 401


def test_users_allows_admin(client, admin_token):
    response = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    payload = response.json()
    assert "farmers" in payload
    assert "doctors" in payload
