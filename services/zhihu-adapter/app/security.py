from __future__ import annotations

import base64
import hashlib
import hmac


def build_community_sign_string(app_key: str, timestamp: str, log_id: str, extra_info: str = "") -> str:
    return f"app_key:{app_key}|ts:{timestamp}|logid:{log_id}|extra_info:{extra_info}"


def sign_community_request(
    app_secret: str,
    app_key: str,
    timestamp: str,
    log_id: str,
    extra_info: str = "",
) -> str:
    message = build_community_sign_string(app_key, timestamp, log_id, extra_info).encode("utf-8")
    digest = hmac.new(app_secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
