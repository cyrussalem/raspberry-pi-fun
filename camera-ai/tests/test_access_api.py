import time
import threading

import pytest


class TestVerifyEndpoint:
    def test_verify_correct_code(self, client):
        response = client.post(
            "/api/access/verify",
            json={"code": "0000"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Access granted" in data["message"]

    def test_verify_wrong_code(self, client):
        response = client.post(
            "/api/access/verify",
            json={"code": "9999"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert "Access denied" in data["message"]

    def test_verify_empty_code(self, client):
        response = client.post(
            "/api/access/verify",
            json={"code": ""},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"

    def test_verify_missing_code_field(self, client):
        response = client.post(
            "/api/access/verify",
            json={},
        )
        assert response.status_code == 422

    def test_verify_returns_json_content_type(self, client):
        response = client.post(
            "/api/access/verify",
            json={"code": "0000"},
        )
        assert "application/json" in response.headers["content-type"]

    def test_verify_unlock_in_progress(self, client, storage, mock_gpio):
        """Second verify while GPIO is still HIGH should return 429."""
        from backend.routers import access as access_module

        # First request — starts the unlock
        response1 = client.post("/api/access/verify", json={"code": "0000"})
        assert response1.status_code == 200

        # The background thread is running — _unlock_in_progress should be True
        # Send another request immediately
        response2 = client.post("/api/access/verify", json={"code": "0000"})
        assert response2.status_code == 429
        data = response2.json()
        assert data["status"] == "error"
        assert "already in progress" in data["message"]

        # Wait for the unlock to finish (use shorter duration in tests)
        # The default is 5 seconds but we need to wait it out
        # Reset the flag manually for subsequent tests
        time.sleep(0.5)
        with access_module._unlock_lock:
            access_module._unlock_in_progress = False


class TestUpdateEndpoint:
    def test_update_with_correct_current_code(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "updated" in data["message"]

    def test_update_persists_new_code(self, client):
        # Update the code
        client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "5678"},
        )
        # Verify with the new code
        response = client.post(
            "/api/access/verify",
            json={"code": "5678"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_update_old_code_no_longer_works(self, client):
        # Update the code
        client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "5678"},
        )
        # Verify with the old code should fail
        response = client.post(
            "/api/access/verify",
            json={"code": "0000"},
        )
        assert response.status_code == 403

    def test_update_with_wrong_current_code(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "9999", "new_code": "1234"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert "incorrect" in data["message"]

    def test_update_new_code_too_short(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "12"},
        )
        assert response.status_code == 422

    def test_update_new_code_non_numeric(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "abcd"},
        )
        assert response.status_code == 422

    def test_update_missing_fields(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "0000"},
        )
        assert response.status_code == 422

    def test_update_returns_json_content_type(self, client):
        response = client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "1234"},
        )
        assert "application/json" in response.headers["content-type"]

    def test_sequential_updates(self, client):
        """Update code multiple times in sequence."""
        # 0000 -> 1111
        r1 = client.post(
            "/api/access/update",
            json={"current_code": "0000", "new_code": "1111"},
        )
        assert r1.status_code == 200

        # 1111 -> 2222
        r2 = client.post(
            "/api/access/update",
            json={"current_code": "1111", "new_code": "2222"},
        )
        assert r2.status_code == 200

        # 2222 -> 3333
        r3 = client.post(
            "/api/access/update",
            json={"current_code": "2222", "new_code": "3333"},
        )
        assert r3.status_code == 200

        # Verify final code works
        verify = client.post("/api/access/verify", json={"code": "3333"})
        assert verify.status_code == 200


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
