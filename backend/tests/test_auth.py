from __future__ import annotations

from fastapi.testclient import TestClient


def test_signup_and_login(test_client: TestClient):
    # 1. Signup
    signup_res = test_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "securepassword123",
        },
    )
    assert signup_res.status_code == 201
    data = signup_res.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    assert "token" in data
    assert len(data["token"]) > 10

    # 2. Login with correct credentials
    login_res = test_client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["email"] == "newuser@example.com"
    assert "token" in login_data


def test_signup_duplicate_email(test_client: TestClient):
    # alex@example.com is in seed data
    res = test_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "alex@example.com",
            "name": "Duplicate Alex",
            "password": "password123",
        },
    )
    assert res.status_code == 400
    assert "error" in res.json()


def test_signup_short_password(test_client: TestClient):
    res = test_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "shortpw@example.com",
            "name": "Short PW",
            "password": "123",  # min_length is 6
        },
    )
    assert res.status_code == 400


def test_login_invalid_password(test_client: TestClient):
    res = test_client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert "error" in res.json()


def test_login_nonexistent_user(test_client: TestClient):
    res = test_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert res.status_code == 401
    assert "error" in res.json()


def test_get_me_authenticated(test_client: TestClient, auth_headers: dict):
    res = test_client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    user = res.json()
    assert user["email"] == "alex@example.com"
    assert user["name"] == "Alex Taylor"


def test_get_me_unauthorized(test_client: TestClient):
    # Missing authorization header
    res = test_client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "error" in res.json()

    # Invalid authorization token
    res_invalid = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_jwt_token_123"},
    )
    assert res_invalid.status_code == 401
    assert "error" in res_invalid.json()


def test_logout(test_client: TestClient):
    res = test_client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.json()["message"] == "Logged out successfully"
