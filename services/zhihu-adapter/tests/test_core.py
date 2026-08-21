from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from app.config import CommunityConfig, DataPlatformConfig, OAuthConfig, Settings
from app.errors import OAuthStateError, ZhihuAuthError, ZhihuInvalidRequest, ZhihuRingNotWritable
from app.mappers import map_comments, map_search, map_story_detail, map_story_list
from app.security import build_community_sign_string, sign_community_request
from app.service import OAuthStateStore, ZhihuService
from app.transport import CommunityClient, OAuthClient, TokenStore


def settings(*, live: bool = False, token_file: Path | None = None) -> Settings:
    return Settings(
        provider_mode="live" if live else "mock",
        community=CommunityConfig(
            app_key="app-key",
            app_secret="app-secret",
            writable_ring_ids=("ring-1",),
        ),
        oauth=OAuthConfig(
            app_id="oauth-id",
            app_key="oauth-key",
            redirect_uri="https://example.test/zhihu/oauth/callback",
            token_file=token_file or Path(".local/test-token.json"),
        ),
        data_platform=DataPlatformConfig(access_secret="data-secret"),
    )


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class SecurityTests(unittest.TestCase):
    def test_community_sign_string_matches_reference(self):
        self.assertEqual(
            build_community_sign_string("user-token", "1760000000", "req_1", ""),
            "app_key:user-token|ts:1760000000|logid:req_1|extra_info:",
        )

    def test_signature_is_stable(self):
        first = sign_community_request("secret", "user-token", "1760000000", "req_1")
        second = sign_community_request("secret", "user-token", "1760000000", "req_1")
        self.assertEqual(first, second)


class MapperTests(unittest.TestCase):
    def test_global_search_keeps_raw_html_and_strips_summary(self):
        items = map_search(
            {"Data": {"Items": [{"Title": "x", "ContentText": "先看<em>执行计划</em>"}]}},
            source_type="global_search",
        )
        self.assertEqual(items[0]["summary"], "先看执行计划")
        self.assertIn("<em>", items[0]["rawExcerptHtml"])

    def test_hot_list_uses_summary_and_url_as_fallback_id(self):
        items = map_search(
            {"Data": {"Items": [{"Title": "x", "Url": "https://example.test/q", "Summary": "摘要"}]}},
            source_type="hot_list",
        )
        self.assertEqual(items[0]["sourceId"], "https://example.test/q")
        self.assertEqual(items[0]["summary"], "摘要")
        self.assertEqual(items[0]["contentType"], "Unknown")

    def test_story_and_comment_mappers_keep_usage_notice_and_counts(self):
        story = map_story_list({"data": [{"work_id": "w1", "title": "t", "labels": ["x"]}]})
        detail = map_story_detail({"data": {"work_id": "w1", "chapter_name": "c", "author_name": "a"}})
        comments = map_comments({"data": {"comments": [{"comment_id": "c1", "content": "ok"}]}})
        self.assertTrue(story[0]["usageNotice"].startswith("Only for"))
        self.assertIn("知乎盐言故事", detail["usageNotice"])
        self.assertEqual(comments[0]["sourceId"], "c1")


class OAuthTests(unittest.TestCase):
    def test_state_is_one_time(self):
        store = OAuthStateStore(ttl_seconds=30)
        state = store.issue()
        store.consume(state)
        with self.assertRaises(OAuthStateError):
            store.consume(state)

    def test_authorize_url_contains_state_and_redirect(self):
        service = ZhihuService(settings())
        result = service.authorize_url()
        self.assertIn("response_type=code", result["url"])
        self.assertIn("app_id=oauth-id", result["url"])
        self.assertIn("redirect_uri=https%3A%2F%2Fexample.test%2Fzhihu%2Foauth%2Fcallback", result["url"])
        self.assertIn("state=", result["url"])

    def test_explicit_state_is_registered_for_callback(self):
        service = ZhihuService(settings(live=True))
        service.authorize_url("provided-state")
        service.state_store.consume("provided-state")

    def test_mock_exchange_persists_token_without_printing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            token_file = Path(directory) / "token.json"
            service = ZhihuService(settings(token_file=token_file))
            state = service.authorize_url()["state"]
            token = service.exchange_oauth_code("code", state)
            self.assertEqual(token["token_type"], "Bearer")
            self.assertEqual(TokenStore(token_file).load_access_token(), "mock-access-token")
            mode = stat.S_IMODE(token_file.stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_live_callback_requires_state(self):
        service = ZhihuService(settings(live=True))
        with self.assertRaises(OAuthStateError):
            service.exchange_oauth_code("code")


class ClientTests(unittest.TestCase):
    def test_community_client_adds_hmac_headers(self):
        fake = FakeTransport({"status": 0, "data": {}})
        config = settings()
        client = CommunityClient(config, fake)
        client.get("/openapi/ring/detail", {"ring_id": "ring-1"})
        headers = fake.calls[0][2]["headers"]
        self.assertEqual(headers["X-App-Key"], "app-key")
        self.assertTrue(headers["X-Sign"])
        self.assertEqual(headers["X-Extra-Info"], "")

    def test_oauth_client_exchange_saves_token(self):
        with tempfile.TemporaryDirectory() as directory:
            token_file = Path(directory) / "token.json"
            config = settings(live=True, token_file=token_file)
            fake = FakeTransport({"access_token": "secret-token", "expires_in": 3600})
            client = OAuthClient(config, fake, TokenStore(token_file))
            response = client.exchange_code("auth-code")
            self.assertEqual(response["access_token"], "secret-token")
            self.assertEqual(TokenStore(token_file).load_access_token(), "secret-token")
            form = fake.calls[0][2]["form"]
            self.assertEqual(form["redirect_uri"], config.oauth.redirect_uri)

    def test_missing_data_platform_secret_is_rejected(self):
        config = settings()
        config = Settings(
            provider_mode="live",
            community=config.community,
            oauth=config.oauth,
            data_platform=DataPlatformConfig(),
        )
        service = ZhihuService(config)
        with self.assertRaises(ZhihuAuthError):
            service.search("索引")

    def test_publish_rejects_unknown_ring(self):
        service = ZhihuService(settings())
        with self.assertRaises(ZhihuRingNotWritable):
            service.publish_pin({"ring_id": "unknown", "content": "test"})

    def test_global_search_rejects_unknown_search_db(self):
        service = ZhihuService(settings())
        with self.assertRaises(ZhihuInvalidRequest):
            service.global_search("索引", search_db="unknown")


if __name__ == "__main__":
    unittest.main()
