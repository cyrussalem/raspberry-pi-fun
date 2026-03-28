from __future__ import annotations

import logging
import threading
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..access.models import AccessResponse, UpdateCodeRequest, VerifyCodeRequest
from ..access.storage import AccessCodeStorage
from ..config import settings
from ..gpio.base import GpioController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/access", tags=["access"])

_storage: AccessCodeStorage | None = None
_gpio: GpioController | None = None
_unlock_in_progress = False
_unlock_lock = threading.Lock()


def init_access_router(storage: AccessCodeStorage, gpio: GpioController) -> None:
    global _storage, _gpio
    _storage = storage
    _gpio = gpio


def _trigger_unlock() -> None:
    """Run the GPIO unlock sequence in a background thread."""
    global _unlock_in_progress
    try:
        _gpio.set_high(settings.gpio_pin)
        logger.info("GPIO pin %d set HIGH — unlock started", settings.gpio_pin)
        time.sleep(settings.gpio_unlock_duration)
    finally:
        _gpio.set_low(settings.gpio_pin)
        logger.info("GPIO pin %d set LOW — unlock ended", settings.gpio_pin)
        with _unlock_lock:
            _unlock_in_progress = False


@router.post("/verify", response_model=AccessResponse)
async def verify_code(request: VerifyCodeRequest):
    """Verify an access code and trigger GPIO unlock if valid."""
    global _unlock_in_progress

    stored_code = _storage.read_code()

    if request.code != stored_code:
        return JSONResponse(
            status_code=403,
            content=AccessResponse(
                status="error",
                message="Access denied. Invalid access code.",
            ).model_dump(),
        )

    with _unlock_lock:
        if _unlock_in_progress:
            return JSONResponse(
                status_code=429,
                content=AccessResponse(
                    status="error",
                    message="Unlock already in progress. Please wait.",
                ).model_dump(),
            )
        _unlock_in_progress = True

    thread = threading.Thread(target=_trigger_unlock, daemon=True)
    thread.start()

    return AccessResponse(
        status="success",
        message="Access granted. Door unlocked for {duration} seconds.".format(
            duration=settings.gpio_unlock_duration
        ),
    )


@router.post("/update", response_model=AccessResponse)
async def update_code(request: UpdateCodeRequest):
    """Update the access code. Requires the current code for authentication."""
    stored_code = _storage.read_code()

    if request.current_code != stored_code:
        return JSONResponse(
            status_code=403,
            content=AccessResponse(
                status="error",
                message="Current access code is incorrect.",
            ).model_dump(),
        )

    _storage.write_code(request.new_code)

    return AccessResponse(
        status="success",
        message="Access code updated successfully.",
    )
