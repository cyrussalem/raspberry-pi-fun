# Access Code Management — Backend Design

## Overview

Add two new API endpoints to the Python backend for managing an access code that controls a GPIO-driven lock mechanism on the Raspberry Pi. The access code is persisted to a local file and controls a GPIO pin that can trigger a relay, solenoid, or electric strike.

## Endpoints

### 1. `POST /api/access/verify`

Verify an access code and trigger the GPIO unlock sequence if it matches.

#### Request

```json
{
  "code": "1234"
}
```

#### Response — Success (200)

```json
{
  "status": "success",
  "message": "Access granted. Door unlocked for 5 seconds."
}
```

#### Response — Invalid Code (403)

```json
{
  "status": "error",
  "message": "Access denied. Invalid access code."
}
```

#### Response — Unlock In Progress (429)

If the GPIO is already in the middle of a 5-second unlock cycle from a previous request:

```json
{
  "status": "error",
  "message": "Unlock already in progress. Please wait."
}
```

#### Behavior

1. Read the current access code from the storage file.
2. Compare the provided `code` against the stored code.
3. If mismatch → return 403 error response.
4. If match → trigger GPIO high for 5 seconds, then set back to low.
5. The GPIO trigger runs in a background thread so the HTTP response returns immediately (the client does not wait 5 seconds).
6. A lock flag prevents concurrent unlock requests while the GPIO is active.

---

### 2. `POST /api/access/update`

Update the access code. Requires the current code for authentication.

#### Request

```json
{
  "current_code": "0000",
  "new_code": "1234"
}
```

#### Response — Success (200)

```json
{
  "status": "success",
  "message": "Access code updated successfully."
}
```

#### Response — Invalid Current Code (403)

```json
{
  "status": "error",
  "message": "Current access code is incorrect."
}
```

#### Response — Validation Error (422)

If `new_code` is empty or fails validation:

```json
{
  "status": "error",
  "message": "New access code must be 4 or more digits."
}
```

#### Behavior

1. Read the current access code from the storage file.
2. Compare the provided `current_code` against the stored code.
3. If mismatch → return 403 error response.
4. Validate the new code (minimum 4 digits, numeric only).
5. Write the new code to the storage file.
6. Return success response.

---

## Data Models

### Request Models (Pydantic)

```python
class VerifyCodeRequest(BaseModel):
    code: str

class UpdateCodeRequest(BaseModel):
    current_code: str
    new_code: str
```

### Response Model (Pydantic)

All responses use a consistent envelope:

```python
class AccessResponse(BaseModel):
    status: Literal["success", "error"]
    message: str
```

---

## Access Code Storage

### File-based persistence

The access code is stored in a plain text file at a configurable path (default: `data/access_code.txt` relative to the project root).

- The file contains only the access code string, no other data.
- If the file does not exist on startup, it is created with the default code `0000`.
- File reads and writes use a threading lock to prevent race conditions between concurrent verify/update requests.

### Why file-based?

- No database dependency — keeps the Pi deployment simple.
- Survives server restarts.
- Easy to manually reset (just edit the file or delete it to reset to `0000`).

### Configuration

Add to `config.py`:

```python
access_code_file: str = "data/access_code.txt"
default_access_code: str = "0000"
gpio_pin: int = 17
gpio_unlock_duration: int = 5  # seconds
```

---

## GPIO Control

### Pin Configuration

- **Pin**: BCM GPIO 17 (configurable via `GPIO_PIN` env var)
- **Default state**: LOW (locked)
- **Unlock state**: HIGH for 5 seconds, then returns to LOW

### Cross-platform Abstraction

The GPIO control follows the same abstraction pattern as the camera module:

```
GpioController (ABC)
    │
    ├── RpiGpioController    — Uses RPi.GPIO or gpiozero on the Pi
    │
    └── MockGpioController   — Logs actions on Windows (no hardware)
```

#### `GpioController` (Abstract Base Class)

```python
class GpioController(ABC):
    @abstractmethod
    def setup(self, pin: int) -> None: ...

    @abstractmethod
    def set_high(self, pin: int) -> None: ...

    @abstractmethod
    def set_low(self, pin: int) -> None: ...

    @abstractmethod
    def cleanup(self) -> None: ...
```

#### `RpiGpioController`

Uses `gpiozero` (preferred on modern Pi OS) or `RPi.GPIO` to control the physical pin:

```python
class RpiGpioController(GpioController):
    def setup(self, pin: int) -> None:
        from gpiozero import OutputDevice
        self._device = OutputDevice(pin)

    def set_high(self, pin: int) -> None:
        self._device.on()

    def set_low(self, pin: int) -> None:
        self._device.off()

    def cleanup(self) -> None:
        self._device.close()
```

#### `MockGpioController`

For development on Windows — logs GPIO state changes without hardware:

```python
class MockGpioController(GpioController):
    def setup(self, pin: int) -> None:
        logger.info(f"[Mock GPIO] Setup pin {pin} as output")

    def set_high(self, pin: int) -> None:
        logger.info(f"[Mock GPIO] Pin {pin} → HIGH")

    def set_low(self, pin: int) -> None:
        logger.info(f"[Mock GPIO] Pin {pin} → LOW")

    def cleanup(self) -> None:
        logger.info("[Mock GPIO] Cleanup")
```

#### Factory

Auto-detect like the camera factory — try importing `gpiozero`, fall back to mock:

```python
def create_gpio_controller() -> GpioController:
    try:
        import gpiozero
        return RpiGpioController()
    except ImportError:
        return MockGpioController()
```

### Unlock Sequence

The unlock runs in a background thread so the API responds immediately:

```python
def trigger_unlock(gpio: GpioController, pin: int, duration: int) -> None:
    gpio.set_high(pin)
    time.sleep(duration)
    gpio.set_low(pin)
```

A threading lock (`_unlock_lock`) prevents overlapping unlock sequences. If a request arrives while the pin is already HIGH, it returns a 429 response instead of queuing.

---

## Module Structure

New files to add to the backend:

```
backend/
├── access/
│   ├── __init__.py
│   ├── storage.py           # File-based access code read/write with thread lock
│   └── models.py            # Pydantic request/response models
├── gpio/
│   ├── __init__.py
│   ├── base.py              # GpioController ABC
│   ├── rpi.py               # RpiGpioController (gpiozero)
│   ├── mock.py              # MockGpioController (logging only)
│   └── factory.py           # Auto-detect GPIO backend
├── routers/
│   └── access.py            # POST /api/access/verify, POST /api/access/update
└── config.py                # + access_code_file, default_access_code, gpio_pin, gpio_unlock_duration
```

---

## Lifecycle Integration

In `main.py` lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    camera = ...
    gpio = create_gpio_controller()
    gpio.setup(settings.gpio_pin)
    code_storage = AccessCodeStorage(settings.access_code_file, settings.default_access_code)
    access.init_access_router(code_storage, gpio)

    yield

    # Shutdown
    gpio.set_low(settings.gpio_pin)
    gpio.cleanup()
    camera.close()
```

---

## Security Considerations

- **No authentication layer**: The access code itself serves as the authentication mechanism. This is acceptable for a local network Pi project but would not be suitable for a public-facing system.
- **Plaintext storage**: The access code is stored in plaintext. For a door lock on a home network this is a reasonable tradeoff. A future enhancement could hash the code using bcrypt.
- **Rate limiting**: Not implemented in the initial version. A future enhancement could add rate limiting to the verify endpoint to prevent brute-force attacks.
- **HTTPS**: Not handled at the application level. If needed, a reverse proxy (nginx) should terminate TLS.

---

## Request Flow Diagrams

### Verify (Success)

```
Client                    Backend                   GPIO
  │                         │                        │
  │  POST /api/access/verify│                        │
  │  { "code": "1234" }     │                        │
  │ ───────────────────────►│                        │
  │                         │  read access_code.txt  │
  │                         │  code matches ✓        │
  │                         │                        │
  │  200 { "status":        │  background thread:    │
  │    "success", ... }     │  pin HIGH ────────────►│
  │ ◄───────────────────────│                        │
  │                         │  (5 seconds later)     │
  │                         │  pin LOW ─────────────►│
  │                         │                        │
```

### Update (Success)

```
Client                    Backend
  │                         │
  │  POST /api/access/update│
  │  { "current_code":      │
  │    "0000",              │
  │    "new_code": "1234" } │
  │ ───────────────────────►│
  │                         │  read access_code.txt
  │                         │  current_code matches ✓
  │                         │  validate new_code ✓
  │                         │  write "1234" to file
  │                         │
  │  200 { "status":        │
  │    "success", ... }     │
  │ ◄───────────────────────│
```
