import logging

from .base import GpioController

logger = logging.getLogger(__name__)


def create_gpio_controller() -> GpioController:
    """Create the appropriate GPIO controller based on platform."""
    try:
        import gpiozero  # noqa: F401

        from .rpi import RpiGpioController

        logger.info("gpiozero available, using Raspberry Pi GPIO controller")
        return RpiGpioController()
    except ImportError:
        from .mock import MockGpioController

        logger.info("gpiozero not available, using mock GPIO controller")
        return MockGpioController()
