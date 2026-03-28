import pytest
from pydantic import ValidationError

from backend.access.models import AccessResponse, UpdateCodeRequest, VerifyCodeRequest


class TestVerifyCodeRequest:
    def test_valid_code(self):
        req = VerifyCodeRequest(code="1234")
        assert req.code == "1234"

    def test_empty_code_allowed(self):
        req = VerifyCodeRequest(code="")
        assert req.code == ""


class TestUpdateCodeRequest:
    def test_valid_update(self):
        req = UpdateCodeRequest(current_code="0000", new_code="1234")
        assert req.current_code == "0000"
        assert req.new_code == "1234"

    def test_long_code_allowed(self):
        req = UpdateCodeRequest(current_code="0000", new_code="123456")
        assert req.new_code == "123456"

    def test_new_code_too_short(self):
        with pytest.raises(ValidationError, match="4 or more digits"):
            UpdateCodeRequest(current_code="0000", new_code="12")

    def test_new_code_one_digit(self):
        with pytest.raises(ValidationError, match="4 or more digits"):
            UpdateCodeRequest(current_code="0000", new_code="1")

    def test_new_code_three_digits(self):
        with pytest.raises(ValidationError, match="4 or more digits"):
            UpdateCodeRequest(current_code="0000", new_code="123")

    def test_new_code_non_numeric(self):
        with pytest.raises(ValidationError, match="only digits"):
            UpdateCodeRequest(current_code="0000", new_code="abcd")

    def test_new_code_mixed_alphanumeric(self):
        with pytest.raises(ValidationError, match="only digits"):
            UpdateCodeRequest(current_code="0000", new_code="12ab")

    def test_new_code_empty(self):
        with pytest.raises(ValidationError):
            UpdateCodeRequest(current_code="0000", new_code="")


class TestAccessResponse:
    def test_success_response(self):
        resp = AccessResponse(status="success", message="Done")
        assert resp.status == "success"
        assert resp.message == "Done"

    def test_error_response(self):
        resp = AccessResponse(status="error", message="Failed")
        assert resp.status == "error"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            AccessResponse(status="unknown", message="test")
