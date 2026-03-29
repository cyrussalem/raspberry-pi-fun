from __future__ import annotations

import logging

import cv2
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from ..camera.base import Camera
from ..recognition.base import FaceRecogniser
from ..recognition.models import RegisterStaffRequest, StaffResponse
from ..recognition.store import StaffStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/staff", tags=["staff"])

_store: StaffStore | None = None
_recogniser: FaceRecogniser | None = None
_camera: Camera | None = None


def init_staff_router(
    store: StaffStore, recogniser: FaceRecogniser, camera: Camera
) -> None:
    global _store, _recogniser, _camera
    _store = store
    _recogniser = recogniser
    _camera = camera


def _reload_known_faces() -> None:
    """Reload face encodings from staff store into the recogniser."""
    staff_list = _store.list_staff()

    class _StaffAdapter:
        """Adapts StaffRecord for the recogniser's load_known_faces interface."""

        def __init__(self, record, data_dir):
            self.name = record.name
            self.photo_paths = [
                str(data_dir / p) for p in record.photos
            ]

    adapted = [_StaffAdapter(s, _store._data_dir) for s in staff_list]
    _recogniser.load_known_faces(adapted)


@router.post("/register", response_model=StaffResponse)
async def register_staff(request: RegisterStaffRequest):
    """Register a new staff member."""
    record = _store.register_staff(request.name)
    return JSONResponse(
        status_code=201,
        content=StaffResponse(
            status="success",
            message="Staff member registered successfully.",
            data=record.model_dump(),
        ).model_dump(),
    )


@router.get("", response_model=StaffResponse)
async def list_staff():
    """List all registered staff members."""
    staff_list = _store.list_staff()
    return StaffResponse(
        status="success",
        message=f"{len(staff_list)} staff member(s) found.",
        data=[s.model_dump() for s in staff_list],
    )


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: str):
    """Get a specific staff member."""
    record = _store.get_staff(staff_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message=f"Staff member '{staff_id}' not found.",
            ).model_dump(),
        )
    return StaffResponse(
        status="success",
        message="Staff member found.",
        data=record.model_dump(),
    )


@router.delete("/{staff_id}", response_model=StaffResponse)
async def delete_staff(staff_id: str):
    """Remove a staff member and all their photos."""
    name = _store.delete_staff(staff_id)
    if name is None:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message=f"Staff member '{staff_id}' not found.",
            ).model_dump(),
        )
    _reload_known_faces()
    return StaffResponse(
        status="success",
        message=f"Staff member '{name}' removed.",
    )


@router.post("/{staff_id}/photos", response_model=StaffResponse)
async def upload_photo(staff_id: str, file: UploadFile = File(...)):
    """Upload a face photo for a staff member."""
    record = _store.get_staff(staff_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message=f"Staff member '{staff_id}' not found.",
            ).model_dump(),
        )

    photo_data = await file.read()

    # Validate that the image contains a face
    import numpy as np

    nparr = np.frombuffer(photo_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse(
            status_code=400,
            content=StaffResponse(
                status="error",
                message="Invalid image file.",
            ).model_dump(),
        )

    # Check for faces using the recogniser
    results = _recogniser.recognise(img)
    if len(results) == 0:
        return JSONResponse(
            status_code=400,
            content=StaffResponse(
                status="error",
                message="No face detected in the uploaded photo. Please upload a clear photo with a visible face.",
            ).model_dump(),
        )

    relative_path = _store.add_photo(staff_id, photo_data)
    _reload_known_faces()

    return StaffResponse(
        status="success",
        message="Photo added. Face encoding generated successfully.",
        data={"photo_path": relative_path, "faces_found": len(results)},
    )


@router.post("/{staff_id}/photos/capture", response_model=StaffResponse)
async def capture_photo(staff_id: str):
    """Capture a photo from the live camera feed."""
    record = _store.get_staff(staff_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message=f"Staff member '{staff_id}' not found.",
            ).model_dump(),
        )

    frame = _camera.read_frame()

    # Check for faces
    results = _recogniser.recognise(frame)
    if len(results) == 0:
        return JSONResponse(
            status_code=400,
            content=StaffResponse(
                status="error",
                message="No face detected in the camera frame. Please position your face in view and try again.",
            ).model_dump(),
        )

    # Encode frame as JPEG
    success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        return JSONResponse(
            status_code=500,
            content=StaffResponse(
                status="error",
                message="Failed to encode camera frame.",
            ).model_dump(),
        )

    relative_path = _store.add_photo(staff_id, buffer.tobytes())
    _reload_known_faces()

    return StaffResponse(
        status="success",
        message="Photo captured and face encoding generated successfully.",
        data={"photo_path": relative_path, "faces_found": len(results)},
    )


@router.delete("/{staff_id}/photos", response_model=StaffResponse)
async def delete_photo(staff_id: str, photo_path: str):
    """Delete a specific photo from a staff member.

    Pass the relative photo path as a query parameter, e.g.:
    DELETE /api/staff/alice_johnson/photos?photo_path=staff/alice_johnson/photo_001.jpg
    """
    record = _store.get_staff(staff_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message=f"Staff member '{staff_id}' not found.",
            ).model_dump(),
        )

    success = _store.delete_photo(staff_id, photo_path)
    if not success:
        return JSONResponse(
            status_code=404,
            content=StaffResponse(
                status="error",
                message="Photo not found.",
            ).model_dump(),
        )

    _reload_known_faces()

    return StaffResponse(
        status="success",
        message="Photo removed.",
    )
