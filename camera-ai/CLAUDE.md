# camera-ai

AI-powered camera with live face detection, streaming video via a web interface.

## Architecture

- **Backend**: Python (FastAPI + OpenCV + Picamera2) — captures frames, runs face detection, streams MJPEG
- **Frontend**: Angular 19 SPA — displays the MJPEG video stream in an `<img>` tag
- **Streaming**: MJPEG over HTTP (`multipart/x-mixed-replace`), no WebSocket needed
- **Face Detection**: OpenCV Haar cascades (`cv2.data.haarcascades`)

## Cross-platform camera support

Camera backend is auto-detected at startup:
- **Windows**: OpenCV `VideoCapture` (USB webcam) — `backend/camera/webcam.py`
- **Raspberry Pi**: Picamera2 with `BGR888` format — `backend/camera/picamera.py`
- Override with env var: `CAMERA_BACKEND=opencv` or `CAMERA_BACKEND=picamera2`

The `picamera2` import is deferred (inside `open()`) to prevent import crashes on Windows.

## Key files

- `backend/main.py` — FastAPI app entrypoint, lifespan (camera open/close), static file serving
- `backend/camera/base.py` — Abstract Camera class (the contract all implementations follow)
- `backend/camera/factory.py` — Auto-detection logic for selecting camera backend
- `backend/streaming/mjpeg.py` — MJPEG frame generator, ties camera + detection + streaming
- `backend/detection/face_detector.py` — Haar cascade face detection with overlay drawing
- `frontend/src/app/app.component.ts` — Root Angular component, points `<img>` at stream URL

## API endpoints

- `GET /api/health` — health check
- `GET /api/video/stream` — MJPEG video stream (never-ending response)
- `GET /` — Angular SPA (when `backend/static/` exists from a production build)

## Commands

### Development (Windows)
```bash
# Setup (first time)
./scripts/setup-dev.sh

# Run backend (terminal 1)
source .venv/Scripts/activate
python -m uvicorn backend.main:app --reload

# Run frontend (terminal 2)
cd frontend && npx ng serve

# Open http://localhost:4200
```

### Production (Raspberry Pi)
```bash
# Setup (first time)
./scripts/setup-pi.sh

# Build frontend into backend/static/
./scripts/build.sh

# Run
source .venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Open http://<pi-ip>:8000
```

## Dependencies

- Python: fastapi, uvicorn, opencv-python-headless, pydantic-settings, numpy
- Pi only: picamera2 (installed via apt as python3-picamera2, venv needs --system-site-packages)
- Frontend: Angular 19, zone.js

## Configuration (.env)

See `.env.example` for all options: camera backend, device index, resolution, FPS, host, port.
