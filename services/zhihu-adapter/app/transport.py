from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import Settings, load_settings
from .errors import (
    ZhihuAuthError,
    ZhihuError,
    ZhihuRateLimited,
    ZhihuUnavailable,
    classify_response,
)
from .security import sign_community_request


logger = logging.getLogger("wenjing.zhihu")


def _url(base_url: str, path: str, params: dict[str, Any] | None = None) -> str:
    base = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    values = {key: value for key, value in (params or {}).items() if value is not None}
    if not values:
        return base
    return f"{base}?{urllib.parse.urlencode(values, doseq=True)}"


def _json_body(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class HttpTransport:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        payload: Any = None,
        form: dict[str, Any] | None = None,
    ) -> Any:
        # Preserve endpoint paths and avoid logging query values, which can
        # contain OAuth codes or access tokens.
        if params:
            parsed = urllib.parse.urlsplit(url)
            existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            additions = [(key, value) for key, value in params.items() if value is not None]
            query = urllib.parse.urlencode([*existing, *additions], doseq=True)
            target = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))
        else:
            target = url

        body: bytes | None = None
        request_headers = dict(headers or {})
        if form is not None:
            body = urllib.parse.urlencode({key: value for key, value in form.items() if value is not None}).encode()
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif payload is not None:
            body = _json_body(payload)
            request_headers.setdefault("Content-Type", "application/json")

        request = urllib.request.Request(target, data=body, headers=request_headers, method=method.upper())
        started = time.perf_counter()
        parsed_url = urllib.parse.urlsplit(target)
        logger.info(
            "zhihu_request",
            extra={
                "method": method.upper(),
                "path": parsed_url.path,
                "query_keys": sorted(urllib.parse.parse_qs(parsed_url.query)),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
                status_code = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            status_code = exc.code
            logger.warning(
                "zhihu_http_error",
                extra={
                    "method": method.upper(),
                    "path": parsed_url.path,
                    "status": status_code,
                    "duration_ms": int((time.perf_counter() - started) * 1000),
                },
            )
            parsed = self._decode(raw)
            if status_code in (401, 403):
                raise ZhihuAuthError("Zhihu upstream authentication failed", detail=parsed) from exc
            if status_code == 429:
                raise ZhihuRateLimited("Zhihu upstream rate limited", detail=parsed) from exc
            raise ZhihuError(f"Zhihu upstream HTTP {status_code}", detail=parsed) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ZhihuUnavailable(f"Zhihu network request failed: {exc}") from exc

        parsed_payload = self._decode(raw)
        logger.info(
            "zhihu_response",
            extra={
                "method": method.upper(),
                "path": parsed_url.path,
                "status": status_code,
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "response_type": type(parsed_payload).__name__,
                "response_keys": sorted(parsed_payload) if isinstance(parsed_payload, dict) else [],
            },
        )
        return parsed_payload

    @staticmethod
    def _decode(raw: bytes) -> Any:
        text = raw.decode("utf-8", errors="replace")
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ZhihuError("Zhihu returned invalid JSON", detail={"body_prefix": text[:256]}) from exc


class CommunityClient:
    """Client for HMAC-signed openapi.zhihu.com community endpoints."""

    def __init__(self, settings: Settings, transport: HttpTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport or HttpTransport(settings.request_timeout_seconds)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self._require_credentials()
        return self._call("GET", path, params=params)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        self._require_credentials()
        return self._call("POST", path, payload=payload)

    def _call(self, method: str, path: str, *, params: dict[str, Any] | None = None, payload: Any = None) -> Any:
        community = self.settings.community
        timestamp = str(int(time.time()))
        log_id = f"wenjing_{time.time_ns()}"
        extra_info = ""
        headers = {
            "X-App-Key": community.app_key,
            "X-Timestamp": timestamp,
            "X-Log-Id": log_id,
            "X-Sign": sign_community_request(
                community.app_secret,
                community.app_key,
                timestamp,
                log_id,
                extra_info,
            ),
            "X-Extra-Info": extra_info,
        }
        raw = self.transport.request(
            method,
            _url(community.base_url, path),
            headers=headers,
            params=params,
            payload=payload,
        )
        error = classify_response(raw, platform="community")
        if error:
            raise error
        return raw

    def _require_credentials(self) -> None:
        if not self.settings.community.app_key or not self.settings.community.app_secret:
            raise ZhihuAuthError("ZHIHU_APP_KEY and ZHIHU_APP_SECRET are required")


class TokenStore:
    """Small 0600 JSON token store for the local callback service."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_access_token(self) -> str:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return ""
        return str(payload.get("access_token", "")) if isinstance(payload, dict) else ""

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            self.path.chmod(0o600)
        except OSError:
            logger.warning("token_file_permissions_not_changed", extra={"path": str(self.path)})


class OAuthClient:
    """OAuth authorization-code and Bearer API client."""

    def __init__(
        self,
        settings: Settings,
        transport: HttpTransport | None = None,
        token_store: TokenStore | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport or HttpTransport(settings.request_timeout_seconds)
        self.token_store = token_store or TokenStore(settings.oauth.token_file)

    def authorize_url(self, state: str | None = None) -> str:
        oauth = self.settings.oauth
        values: dict[str, str] = {
            "redirect_uri": oauth.redirect_uri,
            "app_id": oauth.app_id,
            "response_type": "code",
        }
        if state:
            values["state"] = state
        query = urllib.parse.urlencode(values)
        return f"{_url(oauth.base_url, oauth.authorize_path)}?{query}"

    def exchange_code(self, code: str) -> dict[str, Any]:
        oauth = self.settings.oauth
        if not (oauth.app_id and oauth.app_key and oauth.redirect_uri):
            raise ZhihuAuthError("ZHIHU_OAUTH_APP_ID, ZHIHU_OAUTH_APP_KEY and redirect URI are required")
        if not code:
            raise ZhihuAuthError("OAuth authorization code is missing")
        response = self.transport.request(
            "POST",
            _url(oauth.base_url, oauth.token_path),
            form={
                "app_id": oauth.app_id,
                "app_key": oauth.app_key,
                "grant_type": "authorization_code",
                "redirect_uri": oauth.redirect_uri,
                "code": code,
            },
        )
        error = classify_response(response, platform="oauth")
        if error:
            raise error
        if not isinstance(response, dict) or not response.get("access_token"):
            raise ZhihuAuthError("OAuth token response did not include access_token", detail=response)
        self.token_store.save(response)
        return response

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        access_token: str | None = None,
    ) -> Any:
        token = self.resolve_token(access_token)
        response = self.transport.request(
            "GET",
            _url(self.settings.oauth.base_url, path),
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        error = classify_response(response, platform="oauth")
        if error:
            raise error
        return response

    def resolve_token(self, access_token: str | None = None) -> str:
        token = access_token or self.settings.oauth.access_token or self.token_store.load_access_token()
        if not token:
            raise ZhihuAuthError("OAuth access token is missing; run oauth authorize first")
        return token


class DataPlatformClient:
    """Client for developer.zhihu.com search, hot-list and Zhida APIs."""

    def __init__(self, settings: Settings, transport: HttpTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport or HttpTransport(settings.request_timeout_seconds)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self._require_secret()
        response = self.transport.request(
            "GET",
            _url(self.settings.data_platform.base_url, path),
            params=params,
            headers={
                "Authorization": f"Bearer {self.settings.data_platform.access_secret}",
                "X-Request-Timestamp": str(int(time.time())),
                "Content-Type": "application/json",
            },
        )
        error = classify_response(response, platform="data")
        if error:
            raise error
        return response

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        self._require_secret()
        response = self.transport.request(
            "POST",
            _url(self.settings.data_platform.base_url, path),
            payload=payload,
            headers={
                "Authorization": f"Bearer {self.settings.data_platform.access_secret}",
                "X-Request-Timestamp": str(int(time.time())),
                "Content-Type": "application/json",
            },
        )
        error = classify_response(response, platform="data")
        if error:
            raise error
        return response

    def _require_secret(self) -> None:
        if not self.settings.data_platform.access_secret:
            raise ZhihuAuthError("ZHIHU_ACCESS_SECRET is required")


class ClientBundle:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.community = CommunityClient(self.settings)
        self.oauth = OAuthClient(self.settings)
        self.data = DataPlatformClient(self.settings)
