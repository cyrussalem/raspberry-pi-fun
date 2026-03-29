import json

import pytest

from backend.recognition.store import StaffStore


@pytest.fixture
def store(tmp_path):
    return StaffStore(str(tmp_path))


class TestStaffStore:
    def test_creates_staff_directory(self, tmp_path):
        StaffStore(str(tmp_path))
        assert (tmp_path / "staff").is_dir()

    def test_empty_store_returns_no_staff(self, store):
        assert store.list_staff() == []

    def test_register_staff(self, store):
        record = store.register_staff("Alice Johnson")
        assert record.name == "Alice Johnson"
        assert record.id == "alice_johnson"
        assert record.photos == []
        assert record.registered_at is not None

    def test_register_creates_photo_directory(self, store, tmp_path):
        store.register_staff("Alice Johnson")
        assert (tmp_path / "staff" / "alice_johnson").is_dir()

    def test_register_saves_to_json(self, store, tmp_path):
        store.register_staff("Alice Johnson")
        staff_file = tmp_path / "staff" / "staff.json"
        assert staff_file.exists()
        data = json.loads(staff_file.read_text())
        assert len(data["staff"]) == 1
        assert data["staff"][0]["name"] == "Alice Johnson"

    def test_register_multiple_staff(self, store):
        store.register_staff("Alice Johnson")
        store.register_staff("Bob Smith")
        assert len(store.list_staff()) == 2

    def test_register_duplicate_name_gets_suffix(self, store):
        r1 = store.register_staff("Alice Johnson")
        r2 = store.register_staff("Alice Johnson")
        assert r1.id == "alice_johnson"
        assert r2.id == "alice_johnson_2"

    def test_get_staff_by_id(self, store):
        store.register_staff("Alice Johnson")
        record = store.get_staff("alice_johnson")
        assert record is not None
        assert record.name == "Alice Johnson"

    def test_get_staff_not_found(self, store):
        assert store.get_staff("nonexistent") is None

    def test_add_photo(self, store):
        store.register_staff("Alice Johnson")
        path = store.add_photo("alice_johnson", b"fake jpeg data")
        assert path == "staff/alice_johnson/photo_001.jpg"

        record = store.get_staff("alice_johnson")
        assert len(record.photos) == 1

    def test_add_multiple_photos(self, store):
        store.register_staff("Alice Johnson")
        store.add_photo("alice_johnson", b"photo 1")
        store.add_photo("alice_johnson", b"photo 2")
        store.add_photo("alice_johnson", b"photo 3")

        record = store.get_staff("alice_johnson")
        assert len(record.photos) == 3
        assert record.photos[2] == "staff/alice_johnson/photo_003.jpg"

    def test_add_photo_writes_file(self, store, tmp_path):
        store.register_staff("Alice Johnson")
        store.add_photo("alice_johnson", b"fake jpeg data")
        photo_file = tmp_path / "staff" / "alice_johnson" / "photo_001.jpg"
        assert photo_file.exists()
        assert photo_file.read_bytes() == b"fake jpeg data"

    def test_add_photo_unknown_staff_raises(self, store):
        with pytest.raises(ValueError, match="not found"):
            store.add_photo("nonexistent", b"data")

    def test_delete_staff(self, store):
        store.register_staff("Alice Johnson")
        name = store.delete_staff("alice_johnson")
        assert name == "Alice Johnson"
        assert store.list_staff() == []

    def test_delete_staff_removes_directory(self, store, tmp_path):
        store.register_staff("Alice Johnson")
        store.add_photo("alice_johnson", b"photo data")
        store.delete_staff("alice_johnson")
        assert not (tmp_path / "staff" / "alice_johnson").exists()

    def test_delete_staff_not_found(self, store):
        assert store.delete_staff("nonexistent") is None

    def test_delete_photo(self, store, tmp_path):
        store.register_staff("Alice Johnson")
        path = store.add_photo("alice_johnson", b"photo data")
        assert store.delete_photo("alice_johnson", path) is True

        record = store.get_staff("alice_johnson")
        assert len(record.photos) == 0
        assert not (tmp_path / path).exists()

    def test_delete_photo_not_found(self, store):
        store.register_staff("Alice Johnson")
        assert store.delete_photo("alice_johnson", "nonexistent.jpg") is False

    def test_persistence_across_instances(self, tmp_path):
        store1 = StaffStore(str(tmp_path))
        store1.register_staff("Alice Johnson")
        store1.add_photo("alice_johnson", b"photo data")

        store2 = StaffStore(str(tmp_path))
        staff = store2.list_staff()
        assert len(staff) == 1
        assert staff[0].name == "Alice Johnson"
        assert len(staff[0].photos) == 1

    def test_get_photo_full_path(self, store, tmp_path):
        full = store.get_photo_full_path("staff/alice/photo_001.jpg")
        assert str(full) == str(tmp_path / "staff" / "alice" / "photo_001.jpg")
