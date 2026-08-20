from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from typing import Any

from . import main as http_app
from .service import ZhihuService


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _payload(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"payload must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("payload must be a JSON object")
    return parsed


def _service() -> ZhihuService:
    return http_app.service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wenjing-zhihu", description="问径 · 知乎开放平台 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="显示三类凭证和回调配置状态")
    serve = sub.add_parser("serve", help="启动 HTTP 适配服务")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)

    oauth = sub.add_parser("oauth", help="OAuth 授权与用户数据")
    oauth_sub = oauth.add_subparsers(dest="oauth_command", required=True)
    authorize = oauth_sub.add_parser("authorize", help="打印授权 URL；推荐直接使用 oauth serve")
    authorize.add_argument("--open", action="store_true", help="用系统浏览器打开授权 URL")
    oauth_serve = oauth_sub.add_parser("serve", help="启动回调服务并打印一次性授权 URL")
    oauth_serve.add_argument("--host", default="127.0.0.1")
    oauth_serve.add_argument("--port", type=int, default=8787)
    exchange = oauth_sub.add_parser("exchange", help="用 code 换 token（通常由回调自动完成）")
    exchange.add_argument("code")
    exchange.add_argument("--state")
    exchange.add_argument("--show-token", action="store_true")
    oauth_get = oauth_sub.add_parser("get", help="调用 /user 下的 OAuth API")
    oauth_get.add_argument("path")
    oauth_get.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")

    data = sub.add_parser("data", help="Data Platform：搜索、热榜、直答")
    data_sub = data.add_subparsers(dest="data_command", required=True)
    data_hot = data_sub.add_parser("hot")
    data_hot.add_argument("--limit", type=int, default=10)
    data_search = data_sub.add_parser("search")
    data_search.add_argument("query")
    data_search.add_argument("--count", type=int, default=10)
    data_global = data_sub.add_parser("global-search")
    data_global.add_argument("query")
    data_global.add_argument("--count", type=int, default=10)
    data_answer = data_sub.add_parser("answer")
    data_answer.add_argument("query")
    data_answer.add_argument("--model")

    whoami = sub.add_parser("whoami", help="读取 OAuth 当前用户")
    whoami.add_argument("--access-token")
    moments = sub.add_parser("moments", help="读取关注动态")
    moments.add_argument("--access-token")
    followed = sub.add_parser("followed", help="读取关注列表")
    followed.add_argument("--page", type=int, default=0)
    followed.add_argument("--per-page", type=int, default=10)
    followed.add_argument("--access-token")
    followers = sub.add_parser("followers", help="读取粉丝列表")
    followers.add_argument("--page", type=int, default=0)
    followers.add_argument("--per-page", type=int, default=10)
    followers.add_argument("--access-token")
    content = sub.add_parser("content", help="读取用户内容（路径可由环境变量覆盖）")
    content.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    collections = sub.add_parser("collections", help="读取用户收藏夹")
    collections.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    collection = sub.add_parser("collection", help="读取指定收藏夹内容")
    collection.add_argument("collection_id")
    collection.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")

    community = sub.add_parser("community", help="社区 HMAC API")
    community_sub = community.add_subparsers(dest="community_command", required=True)
    ring = community_sub.add_parser("ring")
    ring.add_argument("ring_id")
    ring.add_argument("--page", type=int, default=1)
    ring.add_argument("--page-size", type=int, default=20)
    comments = community_sub.add_parser("comments")
    comments.add_argument("content_type")
    comments.add_argument("content_token")
    story_list = community_sub.add_parser("story-list")
    story_detail = community_sub.add_parser("story-detail")
    story_detail.add_argument("work_id")
    publish = community_sub.add_parser("publish")
    publish.add_argument("payload", help="JSON payload")
    comment = community_sub.add_parser("comment")
    comment.add_argument("payload", help="JSON payload")
    reaction = community_sub.add_parser("reaction")
    reaction.add_argument("payload", help="JSON payload")
    return parser


def _params(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--param must use KEY=VALUE: {value}")
        key, parsed = value.split("=", 1)
        result[key] = parsed
    return result


def run(args: argparse.Namespace) -> int:
    service = _service()
    if args.command == "status":
        _json(service.status())
        return 0
    if args.command == "serve":
        import uvicorn

        uvicorn.run(http_app.app, host=args.host, port=args.port, log_level="info")
        return 0
    if args.command == "oauth":
        if args.oauth_command == "authorize":
            result = service.authorize_url()
            _json(result)
            if args.open:
                webbrowser.open(result["url"])
            return 0
        if args.oauth_command == "serve":
            import uvicorn

            result = service.authorize_url()
            print("OAuth callback server is ready.")
            print(f"Authorize URL: {result['url']}")
            print(f"Callback URI:  {service.settings.oauth.redirect_uri}")
            uvicorn.run(http_app.app, host=args.host, port=args.port, log_level="info")
            return 0
        if args.oauth_command == "exchange":
            token = service.exchange_oauth_code(args.code, args.state)
            if not args.show_token:
                token = {
                    "access_token_saved": bool(token.get("access_token")),
                    "token_type": token.get("token_type", "Bearer"),
                    "expires_in": token.get("expires_in"),
                    "token_file": str(service.settings.oauth.token_file),
                }
            _json(token)
            return 0
        if args.oauth_command == "get":
            _json(service.oauth_raw(args.path, _params(args.param)))
            return 0
    if args.command == "data":
        if args.data_command == "hot":
            _json(service.hot_list(args.limit))
        elif args.data_command == "search":
            _json(service.search(args.query, args.count))
        elif args.data_command == "global-search":
            _json(service.global_search(args.query, args.count))
        elif args.data_command == "answer":
            payload = {"messages": [{"role": "user", "content": args.query}]}
            if args.model:
                payload["model"] = args.model
            _json(service.direct_answer(payload))
        return 0
    if args.command == "whoami":
        _json(service.oauth_user(args.access_token))
        return 0
    if args.command == "moments":
        _json(service.oauth_moments(args.access_token))
        return 0
    if args.command == "followed":
        _json(service.oauth_followed(args.page, args.per_page, args.access_token))
        return 0
    if args.command == "followers":
        _json(service.oauth_followers(args.page, args.per_page, args.access_token))
        return 0
    if args.command == "content":
        _json(service.oauth_content(_params(args.param)))
        return 0
    if args.command == "collections":
        _json(service.oauth_collections(_params(args.param)))
        return 0
    if args.command == "collection":
        _json(service.oauth_collection(args.collection_id, _params(args.param)))
        return 0
    if args.command == "community":
        if args.community_command == "ring":
            _json(service.ring_detail(args.ring_id, args.page, args.page_size))
        elif args.community_command == "comments":
            _json(service.comments(args.content_type, args.content_token))
        elif args.community_command == "story-list":
            _json(service.story_list())
        elif args.community_command == "story-detail":
            _json(service.story_detail(args.work_id))
        elif args.community_command == "publish":
            _json(service.publish_pin(_payload(args.payload)))
        elif args.community_command == "comment":
            _json(service.create_comment(_payload(args.payload)))
        elif args.community_command == "reaction":
            _json(service.reaction(_payload(args.payload)))
        return 0
    return 2


def main() -> None:
    parser = build_parser()
    try:
        raise SystemExit(run(parser.parse_args()))
    except Exception as exc:
        print(f"wenjing-zhihu: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
