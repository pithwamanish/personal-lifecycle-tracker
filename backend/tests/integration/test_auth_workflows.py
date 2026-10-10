from __future__ import annotations

import uuid
import httpx
import pytest


@pytest.mark.integration
def test_signup_and_jwt_generation(api_client: httpx.Client):
    """
    Scenario: User registration and token issuance.
    Verifies user signup via live API, ensuring user creation and JWT token return.
    """
    unique_email = f"signup_test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "SecurePassword123!",
        "name": "Live Integration Tester",
    }
    res = api_client.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["name"] == "Live Integration Tester"
    assert "id" in data["user"]


@pytest.mark.integration
def test_duplicate_email_signup_rejected(api_client: httpx.Client, create_test_user):
    """
    Scenario: Duplicate email uniqueness enforcement.
    Attempting to register an already existing email returns 400 Bad Request.
    """
    existing_user = create_test_user(email_prefix="dup_test")
    res = api_client.post(
        "/api/v1/auth/signup",
        json={"email": existing_user["email"], "password": "AnyPassword123!", "name": "Duplicate User"},
    )
    assert res.status_code == 400
    assert "already registered" in res.json().get("error", "").lower() or "error" in res.json()


@pytest.mark.integration
def test_login_success_and_invalid_credentials(api_client: httpx.Client, create_test_user):
    """
    Scenario: Authentication verification with valid and invalid credentials.
    """
    user = create_test_user(email_prefix="login_test")

    # Valid credentials
    valid_res = api_client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert valid_res.status_code == 200
    assert "token" in valid_res.json()
    assert valid_res.json()["user"]["email"] == user["email"]

    # Invalid password
    bad_res = api_client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "WrongPassword999!"},
    )
    assert bad_res.status_code == 401
    assert "invalid" in bad_res.json().get("error", "").lower()


@pytest.mark.integration
def test_auth_me_endpoint_and_token_validation(api_client: httpx.Client, create_test_user):
    """
    Scenario: Protected profile retrieval and bearer token validation.
    """
    user = create_test_user(email_prefix="profile_test")

    # Authorized request
    res = api_client.get("/api/v1/auth/me", headers=user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == user["email"]
    assert data["id"] == user["id"]

    # Unauthorized request (no token)
    unauth_res = api_client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Malformed token
    bad_token_res = api_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
    assert bad_token_res.status_code == 401


@pytest.mark.integration
def test_logout_flow(api_client: httpx.Client, create_test_user):
    """
    Scenario: User logout acknowledgement.
    """
    user = create_test_user(email_prefix="logout_test")
    res = api_client.post("/api/v1/auth/logout", headers=user["headers"])
    assert res.status_code == 200
    assert "logged out" in res.json().get("message", "").lower()
