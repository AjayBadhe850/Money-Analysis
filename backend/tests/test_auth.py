from app.models.user import UserRole


def test_register_and_login_flow(client):
    # 1. Register new user
    register_payload = {
        "name": "Jane Finance",
        "email": "jane.finance@test.com",
        "password": "SecurePassword123!",
        "role": "Finance Manager",
        "company_name": "Test Finance Corp"
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane.finance@test.com"
    assert data["user"]["role"] == "Finance Manager"

    token = data["access_token"]

    # 2. Access /api/auth/me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Jane Finance"
    assert me_data["email"] == "jane.finance@test.com"

    # 3. Login with credentials
    login_payload = {
        "email": "jane.finance@test.com",
        "password": "SecurePassword123!"
    }
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Login with invalid password
    bad_login = {
        "email": "jane.finance@test.com",
        "password": "WrongPassword!"
    }
    bad_resp = client.post("/api/auth/login", json=bad_login)
    assert bad_resp.status_code == 401


def test_unauthenticated_request(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
