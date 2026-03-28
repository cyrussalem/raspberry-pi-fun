import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class AccessCodeStorage:
    """File-based access code storage with thread-safe reads and writes."""

    def __init__(self, file_path: str, default_code: str = "0000"):
        self._file_path = Path(file_path)
        self._default_code = default_code
        self._lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(self._default_code)
            logger.info("Created access code file with default code at %s", self._file_path)

    def read_code(self) -> str:
        with self._lock:
            return self._file_path.read_text().strip()

    def write_code(self, code: str) -> None:
        with self._lock:
            self._file_path.write_text(code)
            logger.info("Access code updated")
