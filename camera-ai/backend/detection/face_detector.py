import cv2
import numpy as np
from numpy.typing import NDArray


class FaceDetector:
    """Haar cascade-based face detector with overlay drawing."""

    def __init__(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._classifier = cv2.CascadeClassifier(cascade_path)
        if self._classifier.empty():
            raise RuntimeError(f"Failed to load cascade from {cascade_path}")

    def detect_and_draw(self, frame: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Detect faces and draw rectangles on the frame.

        Modifies the frame in-place and returns it.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        for x, y, w, h in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame,
                "Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        return frame
