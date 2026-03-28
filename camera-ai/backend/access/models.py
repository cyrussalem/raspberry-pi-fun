from typing import Literal

from pydantic import BaseModel, field_validator


class VerifyCodeRequest(BaseModel):
    code: str


class UpdateCodeRequest(BaseModel):
    current_code: str
    new_code: str

    @field_validator("new_code")
    @classmethod
    def validate_new_code(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("New access code must be 4 or more digits.")
        if not v.isdigit():
            raise ValueError("New access code must contain only digits.")
        return v


class AccessResponse(BaseModel):
    status: Literal["success", "error"]
    message: str
