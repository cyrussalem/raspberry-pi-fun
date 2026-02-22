from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from .base import Camera


class WebcamCamera(Camera):
    """OpenCV VideoCapture-based camera for USB webcams."""

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480):
        self._device_index = device_index
        self._width = width
        self._height = height
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self._device_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {self._device_index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

    def read_frame(self) -> NDArray[np.uint8]:
        if self._cap is None:
            raise RuntimeError("Camera is not open")
        ret, frame = self._cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
