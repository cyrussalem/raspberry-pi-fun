from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class StaffRecord(BaseModel):
    id: str
    name: str
    photos: list[str] = []
    registered_at: str


class RegisterStaffRequest(BaseModel):
    name: str


class StaffResponse(BaseModel):
    status: Literal["success", "error"]
    message: str
    data: Optional[Any] = None
