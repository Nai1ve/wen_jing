from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value.strip()


def _int_env(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _csv_env(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw = _env(name)
    if not raw:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class CommunityConfig:
    base_url: str = "https://openapi.zhihu.com"
    app_key: str = ""
    app_secret: str = ""
    writable_ring_ids: tuple[str, ...] = ()
    default_ring_id: str = ""


@dataclass(frozen=True)
class OAuthConfig:
    base_url: str = "https://openapi.zhihu.com"
    app_id: str = ""
    app_key: str = ""
    redirect_uri: str = "http://127.0.0.1:8787/zhihu/oauth/callback"
    authorize_path: str = "/authorize"
    token_path: str = "/access_token"
    access_token: str = ""
    token_file: Path = Path(".local/zhihu/oauth_token.json")
    user_path: str = "/user"
    moments_path: str = "/user/moments"
    followed_path: str = "/user/followed"
    followers_path: str = "/user/followers"
    content_path: str = "/user/content"
    collections_path: str = "/user/collections"
    collection_path: str = "/user/collection/{collection_id}"


@dataclass(frozen=True)
class DataPlatformConfig:
    base_url: str = "https://developer.zhihu.com"
    access_secret: str = ""
    default_model: str = "zhida-thinking-1p5"


@dataclass(frozen=True)
class Settings:
    provider_mode: str = "mock"
    request_timeout_seconds: int = 20
    community: CommunityConfig = field(default_factory=CommunityConfig)
    oauth: OAuthConfig = field(default_factory=OAuthConfig)
    data_platform: DataPlatformConfig = field(default_factory=DataPlatformConfig)

    @property
    def live(self) -> bool:
        return self.provider_mode.lower() == "live"


def load_settings() -> Settings:
    """Build settings from environment variables without ever printing secrets."""

    token_file = Path(_env("ZHIHU_TOKEN_FILE", ".local/zhihu/oauth_token.json")).expanduser()
    return Settings(
        provider_mode=_env("ZHIHU_PROVIDER_MODE", "mock").lower(),
        request_timeout_seconds=_int_env("ZHIHU_REQUEST_TIMEOUT_SECONDS", 20),
        community=CommunityConfig(
            base_url=_env("ZHIHU_COMMUNITY_BASE_URL", "https://openapi.zhihu.com").rstrip("/"),
            app_key=_env("ZHIHU_APP_KEY"),
            app_secret=_env("ZHIHU_APP_SECRET"),
            writable_ring_ids=_csv_env("ZHIHU_WRITABLE_RING_IDS"),
            default_ring_id=_env("ZHIHU_DEFAULT_RING_ID"),
        ),
        oauth=OAuthConfig(
            base_url=_env("ZHIHU_OAUTH_BASE_URL", "https://openapi.zhihu.com").rstrip("/"),
            app_id=_env("ZHIHU_OAUTH_APP_ID"),
            app_key=_env("ZHIHU_OAUTH_APP_KEY"),
            redirect_uri=_env(
                "ZHIHU_OAUTH_REDIRECT_URI",
                "http://127.0.0.1:8787/zhihu/oauth/callback",
            ),
            authorize_path=_env("ZHIHU_OAUTH_AUTHORIZE_PATH", "/authorize"),
            token_path=_env("ZHIHU_OAUTH_TOKEN_PATH", "/access_token"),
            access_token=_env("ZHIHU_ACCESS_TOKEN"),
            token_file=token_file,
            user_path=_env("ZHIHU_OAUTH_USER_PATH", "/user"),
            moments_path=_env("ZHIHU_OAUTH_MOMENTS_PATH", "/user/moments"),
            followed_path=_env("ZHIHU_OAUTH_FOLLOWED_PATH", "/user/followed"),
            followers_path=_env("ZHIHU_OAUTH_FOLLOWERS_PATH", "/user/followers"),
            content_path=_env("ZHIHU_OAUTH_CONTENT_PATH", "/user/content"),
            collections_path=_env("ZHIHU_OAUTH_COLLECTIONS_PATH", "/user/collections"),
            collection_path=_env("ZHIHU_OAUTH_COLLECTION_PATH", "/user/collection/{collection_id}"),
        ),
        data_platform=DataPlatformConfig(
            base_url=_env("ZHIHU_DATA_PLATFORM_BASE_URL", "https://developer.zhihu.com").rstrip("/"),
            access_secret=_env("ZHIHU_ACCESS_SECRET"),
            default_model=_env("ZHIHU_DEFAULT_MODEL", "zhida-thinking-1p5"),
        ),
    )
