from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import NDArray


class Camera(ABC):
    """Abstract base class for camera implementations."""

    @abstractmethod
    def open(self) -> None:
        """Initialize and open the camera."""
        ...

    @abstractmethod
    def read_frame(self) -> NDArray[np.uint8]:
        """Capture and return a single frame as a BGR numpy array.

        Returns:
            numpy array of shape (height, width, 3) in BGR color order.

        Raises:
            RuntimeError: If frame capture fails.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Release camera resources."""
        ...

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
