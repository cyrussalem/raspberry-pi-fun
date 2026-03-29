from __future__ import annotations

import logging

import cv2
import numpy as np
from numpy.typing import NDArray

from .base import FaceRecogniser, RecognitionResult

logger = logging.getLogger(__name__)


class MockFaceRecogniser(FaceRecogniser):
    """Mock face recogniser for development — detects faces but labels all as Unknown."""

    def __init__(self):
        self._classifier = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._known_count = 0

    def load_known_faces(self, staff_data: list) -> None:
        self._known_count = len(staff_data)
        logger.info(
            "[Mock Recognition] Loaded %d staff records (no actual recognition)",
            self._known_count,
        )

    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._classifier.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return [
            RecognitionResult(name="Unknown", confidence=0.0, bbox=(x, y, w, h))
            for (x, y, w, h) in faces
        ]
