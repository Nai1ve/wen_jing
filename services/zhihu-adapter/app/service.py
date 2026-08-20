from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from . import mappers, mock_data
from .config import Settings, load_settings
from .errors import OAuthStateError, ZhihuInvalidRequest, ZhihuRingNotWritable
from .transport import ClientBundle


@dataclass
class OAuthStateStore:
    ttl_seconds: int = 600

    def __post_init__(self) -> None:
        self._states: dict[str, float] = {}
        self._lock = threading.Lock()

    def issue(self) -> str:
        state = secrets.token_urlsafe(32)
        self.remember(state)
        return state

    def remember(self, state: str) -> None:
        if not state:
            raise OAuthStateError("OAuth state is missing")
        with self._lock:
            self._prune()
            self._states[state] = time.time() + self.ttl_seconds

    def consume(self, state: str | None) -> None:
        if not state:
            raise OAuthStateError("OAuth state is missing")
        with self._lock:
            self._prune()
            expires_at = self._states.pop(state, None)
        if expires_at is None or expires_at < time.time():
            raise OAuthStateError("OAuth state is invalid or expired")

    def _prune(self) -> None:
        now = time.time()
        for key, expires_at in list(self._states.items()):
            if expires_at < now:
                self._states.pop(key, None)


class ZhihuService:
    """One business-facing facade over the three Zhihu Open Platform surfaces."""

    def __init__(
        self,
        settings: Settings | None = None,
        clients: ClientBundle | None = None,
        state_store: OAuthStateStore | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.clients = clients or ClientBundle(self.settings)
        self.state_store = state_store or OAuthStateStore()

    def status(self) -> dict[str, Any]:
        oauth_token = self.settings.oauth.access_token or self.clients.oauth.token_store.load_access_token()
        return {
            "providerMode": self.settings.provider_mode,
            "live": self.settings.live,
            "configured": {
                "dataPlatform": bool(self.settings.data_platform.access_secret),
                "community": bool(self.settings.community.app_key and self.settings.community.app_secret),
                "oauthApp": bool(
                    self.settings.oauth.app_id
                    and self.settings.oauth.app_key
                    and self.settings.oauth.redirect_uri
                ),
                "oauthToken": bool(oauth_token),
            },
            "redirectUri": self.settings.oauth.redirect_uri,
            "tokenFile": str(self.settings.oauth.token_file),
        }

    # ---- Data Platform ---------------------------------------------------------

    def hot_list(self, limit: int = 30) -> list[dict[str, Any]]:
        normalized = min(max(limit, 1), 50)
        raw = (
            self.clients.data.get("/api/v1/content/hot_list", {"Limit": normalized})
            if self.settings.live
            else mock_data.hot_list()
        )
        return mappers.map_hot_list(raw)[:normalized]

    def search(self, query: str, count: int = 10) -> list[dict[str, Any]]:
        if not query.strip():
            raise ZhihuInvalidRequest("query is required")
        normalized = min(max(count, 1), 50)
        raw = (
            self.clients.data.get("/api/v1/content/zhihu_search", {"Query": query, "Count": normalized})
            if self.settings.live
            else mock_data.search(query, normalized)
        )
        return mappers.map_search(raw, source_type="zhihu_search")[:normalized]

    def global_search(self, query: str, count: int = 10) -> list[dict[str, Any]]:
        if not query.strip():
            raise ZhihuInvalidRequest("query is required")
        normalized = min(max(count, 1), 50)
        raw = (
            self.clients.data.get("/api/v1/content/global_search", {"Query": query, "Count": normalized})
            if self.settings.live
            else mock_data.search(query, normalized)
        )
        return mappers.map_search(raw, source_type="global_search")[:normalized]

    def direct_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ZhihuInvalidRequest("messages must be a non-empty list")
        if payload.get("stream"):
            raise ZhihuInvalidRequest("stream=true is not supported by the synchronous adapter endpoint")
        model = str(payload.get("model") or self.settings.data_platform.default_model)
        request = {"model": model, "messages": messages, "stream": False}
        raw = self.clients.data.post("/v1/chat/completions", request) if self.settings.live else mock_data.direct_answer(model)
        return mappers.map_direct_answer(raw)

    # ---- Community -------------------------------------------------------------

    def ring_detail(self, ring_id: str, page_num: int = 1, page_size: int = 20) -> dict[str, Any]:
        if not ring_id:
            raise ZhihuInvalidRequest("ring_id is required")
        raw = (
            self.clients.community.get(
                "/openapi/ring/detail",
                {"ring_id": ring_id, "page_num": max(page_num, 1), "page_size": min(max(page_size, 1), 50)},
            )
            if self.settings.live
            else mock_data.ring()
        )
        return mappers.map_ring(raw)

    def comments(self, content_type: str, content_token: str) -> Any:
        if not content_type or not content_token:
            raise ZhihuInvalidRequest("content_type and content_token are required")
        raw = (
            self.clients.community.get(
                "/openapi/comment/list",
                {"content_type": content_type, "content_token": content_token},
            )
            if self.settings.live
            else mock_data.comments()
        )
        return mappers.map_comments(raw)

    def story_list(self) -> Any:
        raw = self.clients.community.get("/openapi/hackathon_story/list") if self.settings.live else mock_data.story_list()
        return mappers.map_story_list(raw)

    def story_detail(self, work_id: str) -> Any:
        if not work_id:
            raise ZhihuInvalidRequest("work_id is required")
        raw = (
            self.clients.community.get("/openapi/hackathon_story/detail", {"work_id": work_id})
            if self.settings.live
            else mock_data.story_detail(work_id)
        )
        return mappers.map_story_detail(raw)

    def publish_pin(self, payload: dict[str, Any]) -> Any:
        self._require_writable_ring(payload.get("ring_id"))
        if not self.settings.live:
            return {"mode": "mock", "success": True, "request": payload}
        return self.clients.community.post("/openapi/publish/pin", payload)

    def create_comment(self, payload: dict[str, Any]) -> Any:
        if not payload.get("content_type") or not payload.get("content_token"):
            raise ZhihuInvalidRequest("content_type and content_token are required")
        if not self.settings.live:
            return {"mode": "mock", "success": True, "request": payload}
        return self.clients.community.post("/openapi/comment/create", payload)

    def reaction(self, payload: dict[str, Any]) -> Any:
        if payload.get("action_type") not in {"like", "unlike"}:
            raise ZhihuInvalidRequest("action_type must be like or unlike")
        if not self.settings.live:
            return {"mode": "mock", "success": True, "request": payload}
        return self.clients.community.post("/openapi/reaction", payload)

    # ---- OAuth -----------------------------------------------------------------

    def authorize_url(self, state: str | None = None) -> dict[str, Any]:
        issued_state = state or self.state_store.issue()
        if state:
            self.state_store.remember(state)
        return {
            "url": self.clients.oauth.authorize_url(issued_state),
            "state": issued_state,
            "redirectUri": self.settings.oauth.redirect_uri,
        }

    def exchange_oauth_code(self, code: str, state: str | None = None) -> dict[str, Any]:
        if self.settings.live and state is None:
            raise OAuthStateError("OAuth state is required for a live callback")
        if state is not None:
            self.state_store.consume(state)
        if not self.settings.live:
            token = {"access_token": "mock-access-token", "token_type": "Bearer", "expires_in": 3600}
            self.clients.oauth.token_store.save(token)
            return token
        return self.clients.oauth.exchange_code(code)

    def oauth_user(self, access_token: str | None = None) -> dict[str, Any]:
        raw = mock_data.user() if not self.settings.live else self.clients.oauth.get(self.settings.oauth.user_path, access_token=access_token)
        return mappers.map_oauth_user(raw)

    def oauth_moments(self, access_token: str | None = None) -> list[dict[str, Any]]:
        raw = mock_data.moments() if not self.settings.live else self.clients.oauth.get(self.settings.oauth.moments_path, access_token=access_token)
        return mappers.map_moments(raw)

    def oauth_followed(self, page: int = 0, per_page: int = 10, access_token: str | None = None) -> list[dict[str, Any]]:
        raw = (
            mock_data.users()
            if not self.settings.live
            else self.clients.oauth.get(
                self.settings.oauth.followed_path,
                {"page": max(page, 0), "per_page": min(max(per_page, 1), 50)},
                access_token=access_token,
            )
        )
        return mappers.map_oauth_users(raw)

    def oauth_followers(self, page: int = 0, per_page: int = 10, access_token: str | None = None) -> list[dict[str, Any]]:
        raw = (
            mock_data.users()
            if not self.settings.live
            else self.clients.oauth.get(
                self.settings.oauth.followers_path,
                {"page": max(page, 0), "per_page": min(max(per_page, 1), 50)},
                access_token=access_token,
            )
        )
        return mappers.map_oauth_users(raw)

    def oauth_content(self, params: dict[str, Any] | None = None, access_token: str | None = None) -> Any:
        return self._oauth_generic(self.settings.oauth.content_path, params, access_token)

    def oauth_collections(self, params: dict[str, Any] | None = None, access_token: str | None = None) -> Any:
        return self._oauth_generic(self.settings.oauth.collections_path, params, access_token)

    def oauth_collection(self, collection_id: str, params: dict[str, Any] | None = None, access_token: str | None = None) -> Any:
        if not collection_id:
            raise ZhihuInvalidRequest("collection_id is required")
        path = self.settings.oauth.collection_path.format(collection_id=collection_id)
        return self._oauth_generic(path, params, access_token)

    def oauth_raw(self, path: str, params: dict[str, Any] | None = None, access_token: str | None = None) -> Any:
        """Escape hatch for newly published user-data endpoints."""
        if not path.startswith("/"):
            path = f"/{path}"
        segments = [segment for segment in path.split("/") if segment]
        if (not path.startswith("/user/") and path != "/user") or ".." in segments:
            raise ZhihuInvalidRequest("oauth raw path must stay under /user")
        return self._oauth_generic(path, params, access_token)

    def _oauth_generic(self, path: str, params: dict[str, Any] | None, access_token: str | None) -> Any:
        if not self.settings.live:
            return {"items": [], "mode": "mock", "path": path}
        return self.clients.oauth.get(path, params, access_token=access_token)

    def _require_writable_ring(self, ring_id: str | None) -> None:
        whitelist = self.settings.community.writable_ring_ids
        if whitelist and (not ring_id or str(ring_id) not in whitelist):
            raise ZhihuRingNotWritable(
                f"ring_id is not in configured writable list: {ring_id}",
                detail={"writableRingIds": list(whitelist)},
            )
