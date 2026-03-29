from __future__ import annotations

import logging

from .base import FaceRecogniser

logger = logging.getLogger(__name__)


def create_face_recogniser(tolerance: float = 0.5) -> FaceRecogniser:
    """Create the appropriate face recogniser based on platform."""
    try:
        import face_recognition  # noqa: F401

        from .dlib_recogniser import DlibFaceRecogniser

        logger.info(
            "face_recognition available, using dlib-based recogniser"
        )
        return DlibFaceRecogniser(tolerance=tolerance)
    except ImportError:
        from .mock_recogniser import MockFaceRecogniser

        logger.info(
            "face_recognition not available, using mock recogniser"
        )
        return MockFaceRecogniser()
