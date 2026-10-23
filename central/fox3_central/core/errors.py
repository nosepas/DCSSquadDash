"""Application errors, mapped to {"error": {"code", "message"}} responses by the API layer."""
from __future__ import annotations


class AppError(Exception):
    status = 500
    code = "internal_error"

    def __init__(self, message: str = "", details: object | None = None):
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details


class BadRequest(AppError):
    status, code = 400, "bad_request"


class Unauthorized(AppError):
    status, code = 401, "unauthorized"


class Forbidden(AppError):
    status, code = 403, "forbidden"


class NotFound(AppError):
    status, code = 404, "not_found"


class Invalid(AppError):
    status, code = 422, "invalid_payload"


class RateLimited(AppError):
    status, code = 429, "rate_limited"


class NotImplementedYet(AppError):
    status, code = 501, "not_implemented"
