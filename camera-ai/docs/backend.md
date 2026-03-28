# Backend Documentation

The backend is a Python application built with **FastAPI** that captures video frames from a camera, runs face detection using **OpenCV**, and streams the processed video to the frontend via **MJPEG**.

## Technology Stack

- **FastAPI** - Async web framework, serves both API endpoints and the Angular static build
- **OpenCV** (`opencv-python-headless`) - Image processing, face detection, JPEG encoding
- **Picamera2** - Raspberry Pi camera interface (Pi only, installed via apt)
- **Pydantic Settings** - Configuration management via environment variables
- **Uvicorn** - ASGI server

## Architecture

```
Request Flow:

Browser GET /api/video/stream
    │
    ▼
FastAPI (StreamingResponse)
    │
    ▼
mjpeg.generate_frames()        ◄── loop: capture → detect → encode → yield
    │           │
    ▼           ▼
Camera      FaceDetector
(BGR frame)  (draws green rectangles)
    │
    ▼
cv2.imencode(".jpg")
    │
    ▼
multipart/x-mixed-replace boundary frame → Browser <img> tag
```

## Module Breakdown

### `main.py` — Application Entrypoint

The FastAPI application with:
- **Lifespan management**: Opens the camera on startup, closes it on shutdown via `asynccontextmanager`.
- **CORS middleware**: Allows requests from `http://localhost:4200` during development (Angular dev server).
- **Router registration**: Mounts the `/api/video` and `/api/health` routers.
- **Static file serving**: If `backend/static/` exists (from a production Angular build), mounts it at `/` with `html=True` for SPA fallback routing. API routes are registered first and take priority.

### `config.py` — Configuration

Uses `pydantic-settings` to load configuration from environment variables and an optional `.env` file.

| Setting              | Type                          | Default   | Description                                      |
|----------------------|-------------------------------|-----------|--------------------------------------------------|
| `CAMERA_BACKEND`     | `"picamera2"` / `"opencv"` / `None` | `None`    | Camera backend. `None` enables auto-detection.   |
| `CAMERA_DEVICE_INDEX`| `int`                         | `0`       | OpenCV camera device index (Windows/USB webcam). |
| `FRAME_WIDTH`        | `int`                         | `640`     | Capture frame width in pixels.                   |
| `FRAME_HEIGHT`       | `int`                         | `480`     | Capture frame height in pixels.                  |
| `STREAM_FPS`         | `int`                         | `15`      | Target frames per second for the MJPEG stream.   |
| `HOST`               | `str`                         | `0.0.0.0` | Server bind address.                             |
| `PORT`               | `int`                         | `8000`    | Server port.                                     |

### `camera/` — Camera Abstraction Layer

Provides a cross-platform camera interface so the same codebase runs on both Windows and Raspberry Pi.

#### `base.py` — Abstract Base Class

Defines the `Camera` ABC with three abstract methods:
- `open()` — Initialize and open the camera hardware.
- `read_frame()` — Capture and return a single frame as a BGR numpy array of shape `(height, width, 3)`.
- `close()` — Release camera resources.

Also implements `__enter__`/`__exit__` for context manager support.

**Contract**: All implementations must return frames in **BGR color order** (OpenCV's native format). This is the single contract that the detection and streaming pipeline depends on.

#### `webcam.py` — OpenCV VideoCapture (Windows/USB)

`WebcamCamera` uses `cv2.VideoCapture` to capture from a USB webcam or built-in camera. Used on Windows during development.

- Opens camera by device index (default `0`).
- Sets frame width/height via OpenCV properties.
- `read_frame()` returns BGR frames natively (OpenCV's default).

#### `picamera.py` — Picamera2 (Raspberry Pi)

`PiCameraDevice` uses the `picamera2` library to capture from a Raspberry Pi camera module (e.g., Camera Module 3 / IMX708).

- **Deferred import**: `from picamera2 import Picamera2` is inside `open()`, not at module level. This prevents import crashes on Windows where `picamera2` and `libcamera` are not available.
- **Color format**: Captures in `RGB888` (Picamera2's native format) and converts to BGR via `cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)`. This explicit conversion is used instead of requesting `BGR888` directly because some Picamera2 versions don't honor the BGR format correctly, resulting in swapped red/blue channels.

#### `factory.py` — Camera Factory

`create_camera()` selects the appropriate camera backend:

1. If `CAMERA_BACKEND` env var is set, use that.
2. Otherwise, auto-detect: attempt to `import picamera2`. If available, use `PiCameraDevice`; if `ImportError`, fall back to `WebcamCamera`.
3. Logs the actual error reason on failure for debugging.

This means zero configuration is needed — on the Pi (where `picamera2` is installed) it auto-selects Pi camera; on Windows (where it's not) it auto-selects the webcam.

### `detection/` — Face Detection

#### `face_detector.py`

`FaceDetector` uses OpenCV's Haar cascade classifier for face detection.

- Loads `haarcascade_frontalface_default.xml` from `cv2.data.haarcascades` (bundled with the opencv-python-headless package — no external download needed).
- `detect_and_draw(frame)` converts the frame to grayscale, runs `detectMultiScale`, and draws green rectangles and "Face" labels on detected faces.
- Detection parameters: `scaleFactor=1.1`, `minNeighbors=5`, `minSize=(30, 30)`.
- Modifies the frame **in-place** and returns it.

### `streaming/` — MJPEG Video Streaming

#### `mjpeg.py`

Handles the MJPEG streaming protocol over HTTP.

- `generate_frames(camera, detector)` is a synchronous generator that runs an infinite loop:
  1. Capture a frame from the camera.
  2. Run face detection and draw overlays.
  3. JPEG-encode the frame (`cv2.imencode` at quality 80).
  4. Yield the frame as a `multipart/x-mixed-replace` boundary part.
  5. Throttle to target FPS using `time.monotonic()`.
- `create_mjpeg_response()` wraps the generator in a FastAPI `StreamingResponse` with content type `multipart/x-mixed-replace; boundary=frame`.

**Threading note**: FastAPI runs on asyncio, but this is a synchronous generator. FastAPI automatically runs sync generators in a threadpool. Each connected browser client gets its own thread running an independent capture/detect/stream loop.

### `routers/` — API Endpoints

#### `health.py`

- `GET /api/health` — Returns `{"status": "ok"}`. Simple health check.

#### `video.py`

- `GET /api/video/stream` — Returns an MJPEG `StreamingResponse` (never-ending HTTP response). The browser renders this natively in an `<img>` tag.
- `init_video_router(camera, detector)` is called during app startup to inject the camera and detector instances.

## API Summary

| Method | Path               | Response                    | Description                       |
|--------|--------------------|-----------------------------|-----------------------------------|
| GET    | `/api/health`      | `{"status": "ok"}`          | Health check                      |
| GET    | `/api/video/stream`| MJPEG stream (never ends)   | Live video feed with face detection |
| GET    | `/`                | Angular SPA (if built)      | Static files from `backend/static/` |

## Testing

### Setup

Install test dependencies (pytest and httpx):

```bash
pip install -e ".[dev]"
```

### Running tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_access_api.py -v
python -m pytest tests/test_models.py -v
python -m pytest tests/test_storage.py -v

# Run a specific test class
python -m pytest tests/test_access_api.py::TestVerifyEndpoint -v

# Run a single test
python -m pytest tests/test_access_api.py::TestVerifyEndpoint::test_verify_correct_code -v
```

### Test structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures: test FastAPI app, mock GPIO, temp storage
├── test_storage.py          # AccessCodeStorage: file creation, read/write, defaults
├── test_models.py           # Pydantic models: validation rules, serialization
└── test_access_api.py       # API endpoints: verify, update, error responses, unlock locking
```

### Test architecture

Tests use a **separate FastAPI app instance** (created in `conftest.py`) that does not run the real application lifespan. This means:

- **No camera hardware needed** — the video router is not mounted in the test app.
- **No GPIO hardware needed** — tests use `MockGpioController` which only logs actions.
- **Isolated storage** — each test gets a fresh temp directory via pytest's `tmp_path` fixture.
- **Unlock state reset** — the `_unlock_in_progress` flag is reset between tests to prevent test interference.

### Configuration

Pytest is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

### Test coverage summary

| Test file            | Tests | What it covers                                                             |
|----------------------|-------|----------------------------------------------------------------------------|
| `test_storage.py`    | 7     | File creation, default code, read/write, whitespace handling, idempotency  |
| `test_models.py`     | 13    | All Pydantic models, validation (too short, non-numeric, empty, invalid)   |
| `test_access_api.py` | 16    | Both endpoints: correct/wrong codes, 403/422/429 responses, persistence, sequential updates, content-type headers, unlock-in-progress blocking |

## Dependencies

### Core (all platforms)
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.34.0`
- `opencv-python-headless>=4.10.0`
- `pydantic-settings>=2.7.0`
- `numpy>=1.26.0`

### Raspberry Pi only (installed via apt, not pip)
- `python3-picamera2` — Camera interface
- `python3-opencv` — OpenCV with native bindings
- `python3-numpy` — NumPy matching system library versions
- `libcap-dev` — Required build dependency for `python-prctl`

**Important**: On the Pi, `numpy`, `opencv`, and `picamera2` must come from apt (not pip) to avoid binary incompatibility with system libraries like `libcamera` and `simplejpeg`. The venv must be created with `--system-site-packages` and using `python3.11` (matching the system Python version that apt packages target).
