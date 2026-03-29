import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.access.storage import AccessCodeStorage
from backend.camera.base import Camera
from backend.gpio.mock import MockGpioController
from backend.recognition.mock_recogniser import MockFaceRecogniser
from backend.recognition.store import StaffStore
from backend.routers import access, health, staff


class FakeCamera(Camera):
    """Camera that returns a blank frame for testing."""

    def open(self) -> None:
        pass

    def read_frame(self):
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def close(self) -> None:
        pass


def create_test_app() -> FastAPI:
    """Create a FastAPI app for testing without the real lifespan."""
    test_app = FastAPI(title="Camera AI Test")
    test_app.include_router(access.router)
    test_app.include_router(health.router)
    test_app.include_router(staff.router)
    return test_app


@pytest.fixture
def mock_gpio():
    return MockGpioController()


@pytest.fixture
def storage(tmp_path):
    return AccessCodeStorage(str(tmp_path / "access_code.txt"), default_code="0000")


@pytest.fixture
def staff_store(tmp_path):
    return StaffStore(str(tmp_path))


@pytest.fixture
def mock_recogniser():
    return MockFaceRecogniser()


@pytest.fixture
def fake_camera():
    cam = FakeCamera()
    cam.open()
    yield cam
    cam.close()


@pytest.fixture
def client(storage, mock_gpio):
    """FastAPI test client for access code tests."""
    import backend.routers.access as access_module

    # Reset unlock state between tests
    with access_module._unlock_lock:
        access_module._unlock_in_progress = False

    mock_gpio.setup(17)
    access.init_access_router(storage, mock_gpio)

    test_app = create_test_app()

    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def staff_client(staff_store, mock_recogniser, fake_camera, storage, mock_gpio):
    """FastAPI test client for staff management tests."""
    import backend.routers.access as access_module

    with access_module._unlock_lock:
        access_module._unlock_in_progress = False

    mock_gpio.setup(17)
    access.init_access_router(storage, mock_gpio)
    staff.init_staff_router(staff_store, mock_recogniser, fake_camera)

    test_app = create_test_app()

    with TestClient(test_app) as c:
        yield c
