from abc import ABC, abstractmethod


class GpioController(ABC):
    """Abstract base class for GPIO control."""

    @abstractmethod
    def setup(self, pin: int) -> None:
        """Configure a pin as output and set to LOW."""
        ...

    @abstractmethod
    def set_high(self, pin: int) -> None:
        """Set pin to HIGH."""
        ...

    @abstractmethod
    def set_low(self, pin: int) -> None:
        """Set pin to LOW."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release GPIO resources."""
        ...
