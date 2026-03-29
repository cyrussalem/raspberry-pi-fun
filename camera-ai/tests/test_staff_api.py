import io

import numpy as np
import cv2
import pytest


class TestRegisterStaff:
    def test_register_new_staff(self, staff_client):
        response = staff_client.post(
            "/api/staff/register",
            json={"name": "Alice Johnson"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Alice Johnson"
        assert data["data"]["id"] == "alice_johnson"
        assert data["data"]["photos"] == []

    def test_register_multiple_staff(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        staff_client.post("/api/staff/register", json={"name": "Bob Smith"})

        response = staff_client.get("/api/staff")
        data = response.json()
        assert len(data["data"]) == 2

    def test_register_duplicate_name(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.post(
            "/api/staff/register", json={"name": "Alice Johnson"}
        )
        assert response.status_code == 201
        assert response.json()["data"]["id"] == "alice_johnson_2"


class TestListStaff:
    def test_list_empty(self, staff_client):
        response = staff_client.get("/api/staff")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"] == []

    def test_list_after_register(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.get("/api/staff")
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Alice Johnson"


class TestGetStaff:
    def test_get_existing_staff(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.get("/api/staff/alice_johnson")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Alice Johnson"

    def test_get_nonexistent_staff(self, staff_client):
        response = staff_client.get("/api/staff/nonexistent")
        assert response.status_code == 404
        assert response.json()["status"] == "error"


class TestDeleteStaff:
    def test_delete_existing_staff(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.delete("/api/staff/alice_johnson")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "Alice Johnson" in response.json()["message"]

        # Verify deleted
        response = staff_client.get("/api/staff")
        assert response.json()["data"] == []

    def test_delete_nonexistent_staff(self, staff_client):
        response = staff_client.delete("/api/staff/nonexistent")
        assert response.status_code == 404


class TestUploadPhoto:
    def _make_test_image(self) -> bytes:
        """Create a minimal JPEG image for testing."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[30:70, 30:70] = 255  # White square
        _, buffer = cv2.imencode(".jpg", img)
        return buffer.tobytes()

    def test_upload_photo_staff_not_found(self, staff_client):
        image_data = self._make_test_image()
        response = staff_client.post(
            "/api/staff/nonexistent/photos",
            files={"file": ("photo.jpg", io.BytesIO(image_data), "image/jpeg")},
        )
        assert response.status_code == 404

    def test_upload_invalid_image(self, staff_client):
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.post(
            "/api/staff/alice_johnson/photos",
            files={"file": ("photo.jpg", io.BytesIO(b"not an image"), "image/jpeg")},
        )
        assert response.status_code == 400
        assert "Invalid image" in response.json()["message"]

    def test_upload_image_no_face(self, staff_client):
        """Mock recogniser uses Haar cascade - blank image won't have faces."""
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        image_data = self._make_test_image()
        response = staff_client.post(
            "/api/staff/alice_johnson/photos",
            files={"file": ("photo.jpg", io.BytesIO(image_data), "image/jpeg")},
        )
        assert response.status_code == 400
        assert "No face detected" in response.json()["message"]


class TestCapturePhoto:
    def test_capture_staff_not_found(self, staff_client):
        response = staff_client.post("/api/staff/nonexistent/photos/capture")
        assert response.status_code == 404

    def test_capture_no_face_in_frame(self, staff_client):
        """FakeCamera returns blank frame, no face will be detected."""
        staff_client.post("/api/staff/register", json={"name": "Alice Johnson"})
        response = staff_client.post("/api/staff/alice_johnson/photos/capture")
        assert response.status_code == 400
        assert "No face detected" in response.json()["message"]


class TestHealthEndpoint:
    def test_health_with_staff_client(self, staff_client):
        response = staff_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
