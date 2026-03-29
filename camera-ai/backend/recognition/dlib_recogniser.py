from __future__ import annotations

import logging

import cv2
import numpy as np
from numpy.typing import NDArray

from .base import FaceRecogniser, RecognitionResult

logger = logging.getLogger(__name__)


class DlibFaceRecogniser(FaceRecogniser):
    """Face recogniser using the face_recognition (dlib) library."""

    def __init__(self, tolerance: float = 0.5):
        self._tolerance = tolerance
        self._known_encodings: list[NDArray] = []
        self._known_names: list[str] = []

    def load_known_faces(self, staff_data: list) -> None:
        import face_recognition  # Deferred import

        self._known_encodings = []
        self._known_names = []

        for staff in staff_data:
            for photo_path in staff.photo_paths:
                try:
                    image = face_recognition.load_image_file(photo_path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        self._known_encodings.append(encodings[0])
                        self._known_names.append(staff.name)
                except Exception as e:
                    logger.warning(
                        "Failed to encode face from %s: %s", photo_path, e
                    )

        logger.info(
            "Loaded %d face encodings from %d staff records",
            len(self._known_encodings),
            len(staff_data),
        )

    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        import face_recognition  # Deferred import

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        results = []
        for encoding, (top, right, bottom, left) in zip(
            face_encodings, face_locations
        ):
            name = "Unknown"
            confidence = 0.0

            if len(self._known_encodings) > 0:
                distances = face_recognition.face_distance(
                    self._known_encodings, encoding
                )
                best_idx = int(distances.argmin())
                if distances[best_idx] <= self._tolerance:
                    name = self._known_names[best_idx]
                    confidence = 1.0 - float(distances[best_idx])

            results.append(
                RecognitionResult(
                    name=name,
                    confidence=confidence,
                    bbox=(left, top, right - left, bottom - top),
                )
            )

        return results
