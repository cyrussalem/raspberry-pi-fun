import os
import tempfile

import pytest

from backend.access.storage import AccessCodeStorage


@pytest.fixture
def storage(tmp_path):
    """Create a storage instance with a temporary file."""
    file_path = str(tmp_path / "access_code.txt")
    return AccessCodeStorage(file_path, default_code="0000")


@pytest.fixture
def storage_path(tmp_path):
    """Return a path for a storage file that doesn't exist yet."""
    return str(tmp_path / "subdir" / "access_code.txt")


class TestAccessCodeStorage:
    def test_creates_file_with_default_code(self, storage, tmp_path):
        file_path = tmp_path / "access_code.txt"
        assert file_path.exists()
        assert file_path.read_text() == "0000"

    def test_creates_parent_directories(self, storage_path):
        storage = AccessCodeStorage(storage_path, default_code="1111")
        assert os.path.exists(storage_path)
        assert storage.read_code() == "1111"

    def test_read_code_returns_default(self, storage):
        assert storage.read_code() == "0000"

    def test_write_code_persists(self, storage):
        storage.write_code("9876")
        assert storage.read_code() == "9876"

    def test_write_code_overwrites_previous(self, storage):
        storage.write_code("1111")
        storage.write_code("2222")
        assert storage.read_code() == "2222"

    def test_read_code_strips_whitespace(self, tmp_path):
        file_path = tmp_path / "access_code.txt"
        file_path.write_text("  5678  \n")
        storage = AccessCodeStorage(str(file_path))
        assert storage.read_code() == "5678"

    def test_does_not_overwrite_existing_file(self, tmp_path):
        file_path = tmp_path / "access_code.txt"
        file_path.write_text("existing_code")
        storage = AccessCodeStorage(str(file_path), default_code="0000")
        assert storage.read_code() == "existing_code"
