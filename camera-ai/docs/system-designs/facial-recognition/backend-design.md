# Facial Recognition — Backend Design

## Overview

Extend the backend to not only detect faces but **identify** them against a database of registered staff. When a recognised staff member's face is detected, the system automatically triggers the GPIO unlock sequence (HIGH for 5 seconds), identical to a successful access code entry. Unrecognised faces are still detected and displayed with an "Unknown" label.

## Technology Choice

### Recommended: `face_recognition` library (dlib-based)

| Option | Detection | Identification | Pi 5 Speed | Accuracy | Complexity |
|--------|-----------|----------------|------------|----------|------------|
| **face_recognition + dlib** | HOG or CNN | 128-d face encodings | ~2-5 FPS (HOG) | High | Low |
| OpenCV DNN + FaceNet | SSD MobileNet | 128-d embeddings | ~3-5 FPS | High | Medium |
| InsightFace (ArcFace) | RetinaFace | 512-d embeddings | ~1-2 FPS | Highest | High |

**Why `face_recognition`:**

- Simplest API — `face_recognition.face_encodings(image)` returns 128-dimensional vectors, `face_recognition.compare_faces()` handles matching.
- Well-proven on Raspberry Pi ([installation guide for Pi](https://gist.github.com/ageitgey/1ac8dbe8572f3f533df6269dab35df65)).
- Uses HOG-based detection by default which runs at 2-5 FPS on Pi 5 — adequate for a door access system where you don't need 15+ FPS recognition.
- dlib's face encoding model is accurate enough that 1-3 reference photos per person is sufficient.
- Pure Python API wrapping optimised C++ (dlib), no TensorFlow/PyTorch dependency.

**Trade-off:** Recognition runs slower than the current Haar cascade detection. The design handles this by running recognition at a lower frequency than the video stream (see Streaming Integration below).

### Installation

**Raspberry Pi:**
```bash
sudo apt-get install -y cmake libopenblas-dev liblapack-dev
pip install face_recognition
```

**Windows (dev):**
```bash
pip install cmake dlib face_recognition
```

Or on Windows where dlib compilation is difficult, fall back to a mock recogniser (similar to MockGpioController) that returns "Unknown" for all faces.

---

## Architecture

### New Module: `backend/recognition/`

Follows the same patterns as the existing `camera/` and `gpio/` modules.

```
backend/recognition/
├── __init__.py
├── base.py              # FaceRecogniser ABC
├── dlib_recogniser.py   # face_recognition library implementation
├── mock_recogniser.py   # Mock for dev (always returns "Unknown")
├── factory.py           # Auto-detect face_recognition availability
├── models.py            # Pydantic models for staff registration
└── store.py             # Staff face database (file-based)
```

### New Module: `backend/routers/staff.py`

API endpoints for managing staff face registrations.

---

## Face Recogniser Abstraction

### `base.py` — Abstract Base Class

```python
class RecognitionResult:
    name: str              # Staff name or "Unknown"
    confidence: float      # 0.0 to 1.0 (1.0 = perfect match)
    bbox: tuple[int, int, int, int]  # (x, y, w, h)

class FaceRecogniser(ABC):
    @abstractmethod
    def load_known_faces(self, staff_data: list[StaffRecord]) -> None:
        """Load known face encodings from staff records."""
        ...

    @abstractmethod
    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        """Detect and identify all faces in a frame.

        Returns a list of RecognitionResult for each detected face.
        """
        ...
```

**Contract:** Input is a BGR numpy array (same as Camera contract). Output is a list of results, each containing the person's name (or "Unknown"), confidence score, and bounding box coordinates.

### `dlib_recogniser.py` — Implementation

```python
class DlibFaceRecogniser(FaceRecogniser):
    def __init__(self, tolerance: float = 0.5):
        self._tolerance = tolerance
        self._known_encodings: list[NDArray] = []
        self._known_names: list[str] = []

    def load_known_faces(self, staff_data: list[StaffRecord]) -> None:
        for staff in staff_data:
            for photo_path in staff.photo_paths:
                image = face_recognition.load_image_file(photo_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self._known_encodings.append(encodings[0])
                    self._known_names.append(staff.name)

    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        # Convert BGR to RGB (face_recognition expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect face locations and compute encodings
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        results = []
        for encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            distances = face_recognition.face_distance(self._known_encodings, encoding)

            name = "Unknown"
            confidence = 0.0
            if len(distances) > 0:
                best_idx = distances.argmin()
                if distances[best_idx] <= self._tolerance:
                    name = self._known_names[best_idx]
                    confidence = 1.0 - distances[best_idx]

            results.append(RecognitionResult(
                name=name,
                confidence=confidence,
                bbox=(left, top, right - left, bottom - top),  # Convert to (x, y, w, h)
            ))
        return results
```

**Key details:**

- `face_recognition.face_locations()` uses the HOG model by default (fast on CPU). The CNN model is available but too slow for real-time on Pi.
- `face_recognition.face_distance()` returns Euclidean distances between the unknown face encoding and all known encodings. Lower distance = better match.
- **Tolerance** (default 0.5): Faces with distance ≤ 0.5 are considered a match. This can be tuned via config — lower values are stricter.
- **BGR→RGB conversion** is required because `face_recognition` expects RGB, but our camera pipeline outputs BGR.

### `mock_recogniser.py` — Development Mock

```python
class MockFaceRecogniser(FaceRecogniser):
    def load_known_faces(self, staff_data: list[StaffRecord]) -> None:
        logger.info("[Mock Recognition] Loaded %d staff records", len(staff_data))

    def recognise(self, frame: NDArray[np.uint8]) -> list[RecognitionResult]:
        # Fall back to Haar cascade for detection, label all as "Unknown"
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        classifier = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = classifier.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        return [
            RecognitionResult(name="Unknown", confidence=0.0, bbox=(x, y, w, h))
            for (x, y, w, h) in faces
        ]
```

This allows the full pipeline to work on Windows without installing dlib.

### `factory.py` — Auto-detection

```python
def create_face_recogniser(tolerance: float = 0.5) -> FaceRecogniser:
    try:
        import face_recognition  # noqa: F401
        from .dlib_recogniser import DlibFaceRecogniser
        return DlibFaceRecogniser(tolerance=tolerance)
    except ImportError:
        from .mock_recogniser import MockFaceRecogniser
        return MockFaceRecogniser()
```

---

## Staff Face Database

### Storage Structure

```
data/
├── access_code.txt          # Existing access code storage
└── staff/
    ├── staff.json           # Staff registry (metadata)
    ├── alice_johnson/
    │   ├── photo_001.jpg
    │   ├── photo_002.jpg
    │   └── photo_003.jpg
    └── bob_smith/
        ├── photo_001.jpg
        └── photo_002.jpg
```

### `staff.json` — Staff Registry

```json
{
  "staff": [
    {
      "id": "alice_johnson",
      "name": "Alice Johnson",
      "photos": [
        "staff/alice_johnson/photo_001.jpg",
        "staff/alice_johnson/photo_002.jpg",
        "staff/alice_johnson/photo_003.jpg"
      ],
      "registered_at": "2026-03-28T12:00:00Z"
    },
    {
      "id": "bob_smith",
      "name": "Bob Smith",
      "photos": [
        "staff/bob_smith/photo_001.jpg",
        "staff/bob_smith/photo_002.jpg"
      ],
      "registered_at": "2026-03-28T12:30:00Z"
    }
  ]
}
```

### `store.py` — Staff Data Store

```python
class StaffRecord(BaseModel):
    id: str
    name: str
    photos: list[str]
    registered_at: str

class StaffStore:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._staff_file = self._data_dir / "staff" / "staff.json"
        self._staff: list[StaffRecord] = []
        self._load()

    def _load(self) -> None: ...
    def _save(self) -> None: ...
    def list_staff(self) -> list[StaffRecord]: ...
    def get_staff(self, staff_id: str) -> StaffRecord | None: ...
    def register_staff(self, name: str) -> StaffRecord: ...
    def add_photo(self, staff_id: str, photo_data: bytes) -> str: ...
    def delete_staff(self, staff_id: str) -> None: ...
```

**ID generation:** Staff ID is derived from the name by lowercasing and replacing spaces with underscores (e.g., "Alice Johnson" → "alice_johnson"). Collisions are handled by appending a numeric suffix.

**Photo storage:** Photos are saved as JPEG files in each staff member's directory. File names are auto-generated sequentially (`photo_001.jpg`, `photo_002.jpg`, etc.).

---

## API Endpoints

### New Router: `POST /api/staff/register`

Register a new staff member.

#### Request

```json
{
  "name": "Alice Johnson"
}
```

#### Response — 201 Created

```json
{
  "status": "success",
  "message": "Staff member registered successfully.",
  "data": {
    "id": "alice_johnson",
    "name": "Alice Johnson",
    "photos": [],
    "registered_at": "2026-03-28T12:00:00Z"
  }
}
```

---

### `POST /api/staff/{staff_id}/photos`

Upload a face photo for a staff member. Accepts a JPEG/PNG image as multipart form data.

#### Request

```
Content-Type: multipart/form-data
file: <image file>
```

#### Response — 200

```json
{
  "status": "success",
  "message": "Photo added. Face encoding generated successfully.",
  "data": {
    "photo_path": "staff/alice_johnson/photo_003.jpg",
    "faces_found": 1
  }
}
```

#### Response — 400 (no face detected)

```json
{
  "status": "error",
  "message": "No face detected in the uploaded photo. Please upload a clear photo with a visible face."
}
```

#### Behavior

1. Save uploaded image to the staff member's directory.
2. Run face detection/encoding on the image.
3. If no face is found → delete the saved image, return 400.
4. If face is found → keep the image, reload the recogniser's known faces.
5. Return success with photo path and face count.

---

### `GET /api/staff`

List all registered staff members.

#### Response — 200

```json
{
  "status": "success",
  "data": [
    {
      "id": "alice_johnson",
      "name": "Alice Johnson",
      "photos": ["staff/alice_johnson/photo_001.jpg"],
      "registered_at": "2026-03-28T12:00:00Z"
    }
  ]
}
```

---

### `DELETE /api/staff/{staff_id}`

Remove a staff member and all their photos.

#### Response — 200

```json
{
  "status": "success",
  "message": "Staff member 'Alice Johnson' removed."
}
```

---

### `POST /api/staff/{staff_id}/photos/capture`

Capture a photo directly from the live camera feed instead of uploading a file.

#### Response — 200

```json
{
  "status": "success",
  "message": "Photo captured and face encoding generated successfully.",
  "data": {
    "photo_path": "staff/alice_johnson/photo_004.jpg",
    "faces_found": 1
  }
}
```

#### Behavior

1. Capture a frame from the active camera.
2. Save it as a JPEG in the staff member's directory.
3. Run face encoding — if no face found, delete and return 400.
4. Reload the recogniser's known faces.

---

## Streaming Integration

### The Performance Problem

Current pipeline: **capture → detect (Haar) → encode JPEG → stream** at 15 FPS.

If we replace Haar with `face_recognition`, recognition drops to ~2-5 FPS on Pi 5. Streaming the video at 2 FPS would feel laggy.

### Solution: Dual-frequency Pipeline

Run recognition at a lower frequency than the video stream:

```
Frame 1:  capture → recognise (slow) → draw overlays → encode → stream
Frame 2:  capture → reuse last results → draw overlays → encode → stream
Frame 3:  capture → reuse last results → draw overlays → encode → stream
Frame 4:  capture → reuse last results → draw overlays → encode → stream
Frame 5:  capture → recognise (slow) → draw overlays → encode → stream
...
```

- **Video streams at 15 FPS** — every frame is captured, overlaid with the last known results, and encoded.
- **Recognition runs every Nth frame** (configurable, default every 5th frame = ~3 recognition passes/second).
- Between recognition frames, the previous bounding boxes and names are drawn on new frames. Faces don't move that fast — the visual result is smooth.

### Modified `streaming/mjpeg.py`

```python
def generate_frames(camera, recogniser, gpio, settings):
    frame_interval = 1.0 / settings.stream_fps
    recognition_interval = settings.recognition_every_n_frames
    frame_count = 0
    last_results = []

    while True:
        frame = camera.read_frame()
        frame_count += 1

        if frame_count % recognition_interval == 0:
            last_results = recogniser.recognise(frame)
            handle_recognition_results(last_results, gpio, settings)

        # Draw overlays from last recognition
        for result in last_results:
            x, y, w, h = result.bbox
            color = (0, 255, 0) if result.name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f"{result.name} ({result.confidence:.0%})" if result.name != "Unknown" else "Unknown"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Encode and yield
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

        # Throttle
        ...
```

### Auto-unlock on Recognition

```python
_last_unlock_name: str | None = None
_recognition_cooldown = 30  # seconds — don't re-unlock for same person within 30s

def handle_recognition_results(results, gpio, settings):
    for result in results:
        if result.name != "Unknown" and result.confidence >= settings.recognition_threshold:
            if can_unlock(result.name):
                trigger_unlock(gpio, settings.gpio_pin, settings.gpio_unlock_duration)
                logger.info("Auto-unlock triggered for %s (confidence: %.0f%%)",
                           result.name, result.confidence * 100)
```

**Cooldown logic:** After unlocking for a person, don't unlock again for the same person for 30 seconds. This prevents the door from continuously triggering while someone stands in front of the camera.

---

## Overlay Behaviour

| Face State | Rectangle Color | Label |
|------------|----------------|-------|
| Known staff | Green `(0, 255, 0)` | `"Alice Johnson (94%)"` |
| Unknown face | Red `(0, 0, 255)` | `"Unknown"` |

---

## Configuration Additions

Add to `config.py`:

```python
# Face recognition
staff_data_dir: str = "data"
recognition_tolerance: float = 0.5
recognition_every_n_frames: int = 5
recognition_threshold: float = 0.5
recognition_cooldown: int = 30  # seconds
```

| Setting | Default | Description |
|---------|---------|-------------|
| `STAFF_DATA_DIR` | `"data"` | Root directory for staff photos and registry |
| `RECOGNITION_TOLERANCE` | `0.5` | Maximum face distance for a match (lower = stricter) |
| `RECOGNITION_EVERY_N_FRAMES` | `5` | Run recognition every Nth frame (higher = faster stream, slower recognition) |
| `RECOGNITION_THRESHOLD` | `0.5` | Minimum confidence to trigger auto-unlock |
| `RECOGNITION_COOLDOWN` | `30` | Seconds before re-unlocking for the same person |

---

## Lifecycle Integration

### Updated `main.py` lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Camera
    camera = create_camera()
    camera.open()

    # GPIO
    gpio = create_gpio_controller()
    gpio.setup(settings.gpio_pin)

    # Access code
    code_storage = AccessCodeStorage(...)
    access.init_access_router(code_storage, gpio)

    # Face recognition (NEW)
    recogniser = create_face_recogniser(tolerance=settings.recognition_tolerance)
    staff_store = StaffStore(settings.staff_data_dir)
    recogniser.load_known_faces(staff_store.list_staff())
    staff_router.init_staff_router(staff_store, recogniser, camera)

    # Video — now uses recogniser instead of FaceDetector
    video.init_video_router(camera, recogniser, gpio)

    yield

    gpio.set_low(settings.gpio_pin)
    gpio.cleanup()
    camera.close()
```

**Key change:** The video router now receives the `FaceRecogniser` instead of the `FaceDetector`. The `FaceDetector` class is no longer used directly — its role is absorbed by the recogniser (which both detects and identifies).

---

## Module Structure — Complete

```
backend/
├── recognition/                    # NEW
│   ├── __init__.py
│   ├── base.py                    # FaceRecogniser ABC + RecognitionResult
│   ├── dlib_recogniser.py         # face_recognition library implementation
│   ├── mock_recogniser.py         # Mock recogniser for Windows dev
│   ├── factory.py                 # Auto-detect face_recognition availability
│   ├── models.py                  # StaffRecord, API request/response models
│   └── store.py                   # Staff registry + photo file management
├── routers/
│   ├── staff.py                   # NEW — /api/staff/* endpoints
│   ├── access.py                  # Existing — unchanged
│   ├── health.py                  # Existing — unchanged
│   └── video.py                   # MODIFIED — uses FaceRecogniser
├── streaming/
│   └── mjpeg.py                   # MODIFIED — dual-frequency pipeline
├── detection/
│   └── face_detector.py           # DEPRECATED — kept for reference
└── config.py                      # MODIFIED — new recognition settings
```

---

## Dependencies

### New pip dependencies

```
face_recognition>=1.3.0
```

**Note:** `face_recognition` requires `dlib`, which requires `cmake` and C++ build tools.

### Pi system dependencies

```bash
sudo apt-get install -y cmake libopenblas-dev liblapack-dev libatlas-base-dev
pip install face_recognition
```

### Windows dev

On Windows, `dlib` can be difficult to compile. Options:
1. Install pre-built wheel: `pip install dlib` (may work with Visual Studio Build Tools)
2. Use conda: `conda install -c conda-forge dlib`
3. Fall back to `MockFaceRecogniser` (auto-detected by factory if import fails)

---

## Request Flow Diagrams

### Staff Registration + Photo Upload

```
Admin                     Backend                    Filesystem
  │                         │                           │
  │  POST /api/staff/       │                           │
  │  register               │                           │
  │  {"name":"Alice"}       │                           │
  │ ───────────────────────►│                           │
  │                         │  create staff/alice/dir ──►│
  │                         │  update staff.json ───────►│
  │  201 { id, name }      │                           │
  │ ◄───────────────────────│                           │
  │                         │                           │
  │  POST /api/staff/       │                           │
  │  alice/photos           │                           │
  │  [image file]           │                           │
  │ ───────────────────────►│                           │
  │                         │  save photo ─────────────►│
  │                         │  encode face              │
  │                         │  reload known faces       │
  │  200 { photo_path }    │                           │
  │ ◄───────────────────────│                           │
```

### Auto-unlock on Face Recognition

```
Camera              Recogniser              GPIO
  │                     │                     │
  │  frame (every       │                     │
  │  5th frame)         │                     │
  │ ───────────────────►│                     │
  │                     │  detect faces       │
  │                     │  encode faces       │
  │                     │  compare to known   │
  │                     │                     │
  │                     │  match: "Alice"     │
  │                     │  confidence: 94%    │
  │                     │  above threshold ✓  │
  │                     │  not in cooldown ✓  │
  │                     │                     │
  │                     │  trigger_unlock() ──►│ pin HIGH
  │                     │                     │ (5 seconds)
  │                     │                     │ pin LOW
  │                     │                     │
  │  frame (in between) │                     │
  │  draw last results  │                     │
  │  (green box: Alice) │                     │
```

---

## Security Considerations

- **Face recognition is not as secure as a PIN.** It can be spoofed with a photo. For higher security, combine face recognition with access code entry (two-factor).
- **Cooldown prevents door hammering.** A recognised person can only trigger one unlock per 30 seconds.
- **Photo storage is plaintext files.** No encryption. Acceptable for a local network Pi project.
- **No liveness detection.** A printed photo of a staff member could trigger the unlock. Liveness detection (blink detection, head movement) could be added as a future enhancement.
- **Staff management endpoints have no authentication.** Anyone on the network can register/delete staff. For production use, add an admin authentication layer.

---

## References

- [face_recognition library](https://github.com/ageitgey/face_recognition)
- [Installing face_recognition on Raspberry Pi](https://gist.github.com/ageitgey/1ac8dbe8572f3f533df6269dab35df65)
- [Face detection comparison: Dlib, OpenCV, Deep Learning](https://learnopencv.com/face-detection-opencv-dlib-and-deep-learning-c-python/)
- [Face Recognition with OpenCV on Raspberry Pi 5](https://www.cytron.io/tutorial/Face-Recognition-Using-OpenCV-on-Raspberry-Pi-5)
