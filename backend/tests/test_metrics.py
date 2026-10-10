from __future__ import annotations

from fastapi.testclient import TestClient


def test_metrics_endpoint_available(client: TestClient):
    """Verify that the /metrics endpoint returns HTTP 200 and Prometheus text format."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    content = res.text
    # Check that golden triangle labels are present
    assert "deployment_environment=" in content
    assert "service_version=" in content
    assert "service_name=" in content


def test_http_request_metrics_recorded(client: TestClient, auth_headers: dict):
    """Verify that requests to API endpoints update request counters and latency histograms."""
    # Execute a few requests
    res = client.get("/api/v1/items", headers=auth_headers)
    assert res.status_code == 200

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    text = metrics_res.text

    assert "app_http_requests_total" in text
    assert 'http_route="/api/v1/items"' in text
    assert 'http_status_code="200"' in text
    assert "app_http_server_duration_milliseconds" in text


def test_lifecycle_items_metrics_lifecycle(client: TestClient, auth_headers: dict):
    """Verify creation, completion, and deletion of lifecycle items update domain metrics."""
    # 1. Create renewal item
    create_payload = {
        "name": "Passport Renewal Test",
        "lifecycleType": "renewal",
        "dueDate": "2027-01-15",
    }
    create_res = client.post("/api/v1/items", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    item = create_res.json()
    item_id = item["id"]

    # 2. Check items created metric
    metrics_res = client.get("/metrics")
    text = metrics_res.text
    assert "app_items_created_total" in text
    assert 'lifecycle_type="renewal"' in text

    # 3. Complete item
    complete_res = client.post(f"/api/v1/items/{item_id}/complete", headers=auth_headers)
    assert complete_res.status_code == 200

    metrics_res2 = client.get("/metrics")
    text2 = metrics_res2.text
    assert "app_items_completed_total" in text2
    assert 'lifecycle_type="renewal"' in text2

    # 4. Delete item
    del_res = client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert del_res.status_code == 204

    metrics_res3 = client.get("/metrics")
    text3 = metrics_res3.text
    assert "app_items_deleted_total" in text3


def test_auth_and_reminders_metrics(client: TestClient, auth_headers: dict):
    """Verify auth and reminder metrics tracking."""
    # 1. Signup metric
    new_user_payload = {
        "email": "metricstest@example.com",
        "name": "Metrics Test User",
        "password": "password123",
    }
    signup_res = client.post("/api/v1/auth/signup", json=new_user_payload)
    assert signup_res.status_code == 201

    # 2. Failed login metric
    client.post("/api/v1/auth/login", json={"email": "metricstest@example.com", "password": "wrongpassword"})

    # 3. Successful login metric
    client.post("/api/v1/auth/login", json={"email": "metricstest@example.com", "password": "password123"})

    # 4. Reminders summary
    summary_res = client.get("/api/v1/reminders/summary", headers=auth_headers)
    assert summary_res.status_code == 200

    # 5. Daily digest generation
    digest_res = client.post("/api/v1/reminders/digest/generate", headers=auth_headers)
    assert digest_res.status_code == 200

    # Inspect metrics output
    metrics_res = client.get("/metrics")
    text = metrics_res.text
    assert "app_user_signups_total" in text
    assert 'app_user_logins_total{deployment_environment="development",service_name="api-backend",service_version="dev-latest",status="success"}' in text
    assert 'app_user_logins_total{deployment_environment="development",service_name="api-backend",service_version="dev-latest",status="failure"}' in text
    assert "app_reminders_summary_requests_total" in text
    assert 'app_digests_generated_total{deployment_environment="development",service_name="api-backend",service_version="dev-latest",status="success"}' in text


def test_route_normalization_avoids_cardinality_explosion(client: TestClient, auth_headers: dict):
    """Verify that route paths with dynamic UUIDs are normalized to avoid high cardinality."""
    # Access an item by ID
    client.get("/api/v1/items/8f51a704-5853-41bb-9466-9e1234567890", headers=auth_headers)

    metrics_res = client.get("/metrics")
    text = metrics_res.text
    # The route should be normalized to /api/v1/items/{id} rather than raw UUID
    assert 'http_route="/api/v1/items/{id}"' in text
    assert "8f51a704-5853-41bb-9466-9e1234567890" not in text


def test_item_creation_failure_metrics(client: TestClient, auth_headers: dict):
    """Verify that failed item creation attempts increment app_item_creation_failures_total."""
    # Trigger an item creation failure (invalid lifecycle type or empty name)
    fail_res = client.post(
        "/api/v1/items",
        json={"name": "   ", "lifecycleType": "renewal"},
        headers=auth_headers,
    )
    # The store/endpoint rejects empty names with 400
    assert fail_res.status_code == 400

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    text = metrics_res.text

    assert "app_item_creation_failures_total" in text
    assert 'app_item_creation_failures_total{deployment_environment="development",lifecycle_type="renewal",service_name="api-backend",service_version="dev-latest"}' in text

