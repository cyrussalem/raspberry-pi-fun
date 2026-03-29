from __future__ import annotations

import json
import logging
import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import StaffRecord

logger = logging.getLogger(__name__)


class StaffStore:
    """File-based staff registry and photo storage."""

    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._staff_dir = self._data_dir / "staff"
        self._staff_file = self._staff_dir / "staff.json"
        self._lock = threading.Lock()
        self._staff: list[StaffRecord] = []
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self) -> None:
        self._staff_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        if self._staff_file.exists():
            data = json.loads(self._staff_file.read_text())
            self._staff = [StaffRecord(**s) for s in data.get("staff", [])]
            logger.info("Loaded %d staff records", len(self._staff))
        else:
            self._staff = []

    def _save(self) -> None:
        data = {"staff": [s.model_dump() for s in self._staff]}
        self._staff_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self, name: str) -> str:
        base_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        if not self.get_staff(base_id):
            return base_id
        counter = 2
        while self.get_staff(f"{base_id}_{counter}"):
            counter += 1
        return f"{base_id}_{counter}"

    def list_staff(self) -> list[StaffRecord]:
        with self._lock:
            return list(self._staff)

    def get_staff(self, staff_id: str) -> StaffRecord | None:
        for s in self._staff:
            if s.id == staff_id:
                return s
        return None

    def register_staff(self, name: str) -> StaffRecord:
        with self._lock:
            staff_id = self._generate_id(name)
            staff_photo_dir = self._staff_dir / staff_id
            staff_photo_dir.mkdir(parents=True, exist_ok=True)

            record = StaffRecord(
                id=staff_id,
                name=name,
                photos=[],
                registered_at=datetime.now(timezone.utc).isoformat(),
            )
            self._staff.append(record)
            self._save()
            logger.info("Registered staff: %s (%s)", name, staff_id)
            return record

    def add_photo(self, staff_id: str, photo_data: bytes) -> str:
        with self._lock:
            record = self.get_staff(staff_id)
            if record is None:
                raise ValueError(f"Staff member '{staff_id}' not found")

            staff_photo_dir = self._staff_dir / staff_id
            staff_photo_dir.mkdir(parents=True, exist_ok=True)

            photo_num = len(record.photos) + 1
            photo_filename = f"photo_{photo_num:03d}.jpg"
            photo_path = staff_photo_dir / photo_filename
            photo_path.write_bytes(photo_data)

            relative_path = f"staff/{staff_id}/{photo_filename}"
            record.photos.append(relative_path)
            self._save()
            logger.info("Added photo for %s: %s", staff_id, relative_path)
            return relative_path

    def get_photo_full_path(self, relative_path: str) -> Path:
        return self._data_dir / relative_path

    def delete_staff(self, staff_id: str) -> str | None:
        with self._lock:
            record = self.get_staff(staff_id)
            if record is None:
                return None

            name = record.name
            staff_photo_dir = self._staff_dir / staff_id
            if staff_photo_dir.exists():
                shutil.rmtree(staff_photo_dir)

            self._staff = [s for s in self._staff if s.id != staff_id]
            self._save()
            logger.info("Deleted staff: %s (%s)", name, staff_id)
            return name

    def delete_photo(self, staff_id: str, relative_path: str) -> bool:
        with self._lock:
            record = self.get_staff(staff_id)
            if record is None or relative_path not in record.photos:
                return False

            full_path = self._data_dir / relative_path
            if full_path.exists():
                full_path.unlink()

            record.photos.remove(relative_path)
            self._save()
            return True
