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

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
