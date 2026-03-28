from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    camera_backend: Optional[Literal["picamera2", "opencv"]] = None
    camera_device_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    stream_fps: int = 15
    host: str = "0.0.0.0"
    port: int = 8000
    access_code_file: str = "data/access_code.txt"
    default_access_code: str = "0000"
    gpio_pin: int = 17
    gpio_unlock_duration: int = 5

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
