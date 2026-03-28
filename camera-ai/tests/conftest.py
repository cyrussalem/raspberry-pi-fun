import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.access.storage import AccessCodeStorage
from backend.gpio.mock import MockGpioController
from backend.routers import access, health
from backend.routers.access import _unlock_lock, _unlock_in_progress


def create_test_app() -> FastAPI:
    """Create a FastAPI app for testing without the real lifespan."""
    test_app = FastAPI(title="Camera AI Test")
    test_app.include_router(access.router)
    test_app.include_router(health.router)
    return test_app


@pytest.fixture
def mock_gpio():
    return MockGpioController()


@pytest.fixture
def storage(tmp_path):
    return AccessCodeStorage(str(tmp_path / "access_code.txt"), default_code="0000")


@pytest.fixture
def client(storage, mock_gpio):
    """FastAPI test client with mocked dependencies."""
    import backend.routers.access as access_module

    # Reset unlock state between tests
    with access_module._unlock_lock:
        access_module._unlock_in_progress = False

    mock_gpio.setup(17)
    access.init_access_router(storage, mock_gpio)

    test_app = create_test_app()

    with TestClient(test_app) as c:
        yield c
