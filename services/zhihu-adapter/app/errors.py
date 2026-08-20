from __future__ import annotations

from typing import Any


class ZhihuError(Exception):
    code = "ZHIHU_UPSTREAM_ERROR"
    status_code = 502

    def __init__(self, message: str, *, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "detail": self.detail}


class ZhihuAuthError(ZhihuError):
    code = "ZHIHU_AUTH_FAILED"
    status_code = 401


class ZhihuInvalidRequest(ZhihuError):
    code = "ZHIHU_INVALID_REQUEST"
    status_code = 400


class ZhihuRateLimited(ZhihuError):
    code = "ZHIHU_RATE_LIMITED"
    status_code = 429


class ZhihuNotConfigured(ZhihuError):
    code = "ZHIHU_NOT_CONFIGURED"
    status_code = 503


class ZhihuUnavailable(ZhihuError):
    code = "ZHIHU_UNAVAILABLE"
    status_code = 502


class ZhihuRingNotWritable(ZhihuError):
    code = "ZHIHU_RING_NOT_WRITABLE"
    status_code = 400


class OAuthStateError(ZhihuError):
    code = "ZHIHU_OAUTH_STATE_INVALID"
    status_code = 400


def classify_response(payload: Any, *, platform: str) -> ZhihuError | None:
    """Translate common Zhihu response envelopes into stable adapter errors."""

    if not isinstance(payload, dict):
        return None
    if platform == "data":
        code = payload.get("Code", payload.get("code", 0))
        message = payload.get("Message") or payload.get("message") or "Zhihu data platform error"
        if code in (None, 0, "0") and not isinstance(payload.get("error"), dict):
            return None
        if isinstance(payload.get("error"), dict):
            error = payload["error"]
            code = error.get("code", code)
            message = error.get("message", message)
        if str(code) in {"10001", "400"}:
            return ZhihuInvalidRequest(message, detail=payload)
        if str(code) in {"20001", "401", "403"}:
            return ZhihuAuthError(message, detail=payload)
        if str(code) in {"30001", "429"}:
            return ZhihuRateLimited(message, detail=payload)
        return ZhihuError(message, detail=payload)

    if platform in {"community", "oauth"}:
        code = payload.get("status", payload.get("code", 0))
        if code in (None, 0, "0"):
            return None
        message = payload.get("msg") or payload.get("message") or payload.get("data") or "Zhihu API error"
        if str(code) in {"101", "401", "403"}:
            return ZhihuAuthError(str(message), detail=payload)
        if str(code) in {"400", "404"}:
            return ZhihuInvalidRequest(str(message), detail=payload)
        if str(code) == "429":
            return ZhihuRateLimited(str(message), detail=payload)
        return ZhihuError(str(message), detail=payload)

    return None
