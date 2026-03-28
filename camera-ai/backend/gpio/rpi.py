from .base import GpioController


class RpiGpioController(GpioController):
    """GPIO controller using gpiozero for Raspberry Pi."""

    def __init__(self):
        self._devices = {}

    def setup(self, pin: int) -> None:
        from gpiozero import OutputDevice  # Deferred import — not available on Windows

        device = OutputDevice(pin, initial_value=False)
        self._devices[pin] = device

    def set_high(self, pin: int) -> None:
        self._devices[pin].on()

    def set_low(self, pin: int) -> None:
        self._devices[pin].off()

    def cleanup(self) -> None:
        for device in self._devices.values():
            device.off()
            device.close()
        self._devices.clear()
