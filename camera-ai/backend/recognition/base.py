from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class RecognitionResult:
    """Result of face recognition for a single detected face."""

    name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # (x, y, w, h)


class FaceRecogniser(ABC):
    """Abstract base class for face recognition implementations."""

    @abstractmethod
    def load_known_faces(self, staff_data: list) -> None:
        """Load known face encodings from staff records."""
        ...

    @abstractmethod
    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        """Detect and identify all faces in a frame.

        Returns a list of RecognitionResult for each detected face.
        """
        ...
