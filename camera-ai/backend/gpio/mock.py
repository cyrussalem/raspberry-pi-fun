import logging

from .base import GpioController

logger = logging.getLogger(__name__)


class MockGpioController(GpioController):
    """Mock GPIO controller for development on non-Pi platforms."""

    def setup(self, pin: int) -> None:
        logger.info("[Mock GPIO] Setup pin %d as output (LOW)", pin)

    def set_high(self, pin: int) -> None:
        logger.info("[Mock GPIO] Pin %d → HIGH", pin)

    def set_low(self, pin: int) -> None:
        logger.info("[Mock GPIO] Pin %d → LOW", pin)

    def cleanup(self) -> None:
        logger.info("[Mock GPIO] Cleanup")
