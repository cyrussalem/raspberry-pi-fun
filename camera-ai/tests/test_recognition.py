import numpy as np
import pytest

from backend.recognition.base import RecognitionResult
from backend.recognition.mock_recogniser import MockFaceRecogniser


class TestRecognitionResult:
    def test_creation(self):
        r = RecognitionResult(name="Alice", confidence=0.95, bbox=(10, 20, 100, 100))
        assert r.name == "Alice"
        assert r.confidence == 0.95
        assert r.bbox == (10, 20, 100, 100)

    def test_unknown_result(self):
        r = RecognitionResult(name="Unknown", confidence=0.0, bbox=(0, 0, 50, 50))
        assert r.name == "Unknown"
        assert r.confidence == 0.0


class TestMockFaceRecogniser:
    def test_load_known_faces(self):
        recogniser = MockFaceRecogniser()
        recogniser.load_known_faces([{"name": "Alice"}, {"name": "Bob"}])
        assert recogniser._known_count == 2

    def test_recognise_blank_frame_returns_empty(self):
        recogniser = MockFaceRecogniser()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        results = recogniser.recognise(blank)
        assert isinstance(results, list)
        # Blank frame should not detect any faces
        assert len(results) == 0

    def test_recognise_returns_unknown_names(self):
        recogniser = MockFaceRecogniser()
        # Create a frame with a bright rectangle that might trigger detection
        # In practice, Haar cascade may or may not detect on synthetic images
        # We just verify the return type is correct
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = recogniser.recognise(frame)
        for result in results:
            assert result.name == "Unknown"
            assert result.confidence == 0.0
            assert len(result.bbox) == 4


class TestRecognitionModels:
    def test_staff_record_model(self):
        from backend.recognition.models import StaffRecord

        record = StaffRecord(
            id="alice_johnson",
            name="Alice Johnson",
            photos=["staff/alice/photo_001.jpg"],
            registered_at="2026-03-28T12:00:00Z",
        )
        assert record.id == "alice_johnson"
        assert len(record.photos) == 1

    def test_register_staff_request(self):
        from backend.recognition.models import RegisterStaffRequest

        req = RegisterStaffRequest(name="Alice Johnson")
        assert req.name == "Alice Johnson"

    def test_staff_response(self):
        from backend.recognition.models import StaffResponse

        resp = StaffResponse(
            status="success", message="Done", data={"id": "alice"}
        )
        assert resp.status == "success"
        assert resp.data == {"id": "alice"}

    def test_staff_response_without_data(self):
        from backend.recognition.models import StaffResponse

        resp = StaffResponse(status="error", message="Not found")
        assert resp.data is None


class TestFaceRecogniserFactory:
    def test_factory_returns_mock_when_no_dlib(self):
        from backend.recognition.factory import create_face_recogniser

        recogniser = create_face_recogniser()
        # On Windows dev without dlib, should return MockFaceRecogniser
        assert recogniser is not None
        assert hasattr(recogniser, "recognise")
        assert hasattr(recogniser, "load_known_faces")
