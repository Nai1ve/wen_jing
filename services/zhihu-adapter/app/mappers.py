from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any

from .security import stable_hash


TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str | None) -> str:
    return html.unescape(TAG_RE.sub("", value or "")).strip()


def unix_to_iso(value: int | float | str | None) -> str | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _data(raw: Any) -> Any:
    return raw.get("Data", raw.get("data", raw)) if isinstance(raw, dict) else raw


def _first(item: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def _content_type(url: str, explicit: Any = "") -> str:
    if explicit:
        return str(explicit)
    if "/question/" in url:
        return "Question"
    if "zhuanlan.zhihu.com" in url or "/p/" in url:
        return "Article"
    if "/answer/" in url:
        return "Answer"
    return "Unknown"


def map_search(raw: Any, *, source_type: str) -> list[dict[str, Any]]:
    data = _data(raw)
    if isinstance(data, dict):
        items = data.get("Items", data.get("items", data.get("data", [])))
    else:
        items = data
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(_first(item, "Url", "url"))
        content_id = _first(item, "ContentID", "content_id", "id", "url", "Url")
        excerpt = _first(
            item,
            "ContentText",
            "Summary",
            "summary",
            "excerpt",
            "content",
            "description",
        )
        result.append(
            {
                "sourceType": source_type,
                "sourceId": str(content_id or stable_hash(url or repr(item))),
                "contentType": _content_type(url, _first(item, "ContentType", "content_type")),
                "title": _first(item, "Title", "title"),
                "url": url,
                "author": _first(item, "AuthorName", "author_name", "author"),
                "authorAvatar": _first(item, "AuthorAvatar", "author_avatar"),
                "authorBadgeText": _first(item, "AuthorBadgeText", "author_badge_text"),
                "publishedAt": unix_to_iso(_first(item, "EditTime", "created_at", "publish_time")),
                "summary": strip_html(excerpt),
                "rawExcerptHtml": excerpt if source_type == "global_search" else None,
                "thumbnailUrl": _first(item, "ThumbnailUrl", "thumbnail_url"),
                "likeCount": _first(item, "VoteUpCount", "like_count", default=0),
                "commentCount": _first(item, "CommentCount", "comment_count", default=0),
                "authorityLevel": _first(item, "AuthorityLevel", "authority_level"),
                "rankingScore": _first(item, "RankingScore", "ranking_score", default=None),
                "relevanceScore": _first(item, "RankingScore", "ranking_score", default=None),
                "selectedComments": [
                    str(_first(comment, "Content", "content"))
                    for comment in (_first(item, "CommentInfoList", "comment_info_list", default=[]) or [])
                    if isinstance(comment, dict) and _first(comment, "Content", "content")
                ],
                "raw": item,
            }
        )
    return result


def map_hot_list(raw: Any) -> list[dict[str, Any]]:
    items = map_search(raw, source_type="hot_list")
    for index, item in enumerate(items):
        item["heatScore"] = max(1, 100 - index * 2)
    return items


def map_oauth_user(raw: Any) -> dict[str, Any]:
    item = raw.get("data", raw) if isinstance(raw, dict) else {}
    if not isinstance(item, dict):
        item = {}
    sensitive = {"email", "phone_no", "phone", "access_token", "refresh_token"}
    return {
        "sourceType": "oauth_user",
        "sourceId": str(_first(item, "uid", "id", "hash_id")),
        "uid": _first(item, "uid", "id", default=None),
        "hashId": _first(item, "hash_id"),
        "fullname": _first(item, "fullname", "name"),
        "gender": _first(item, "gender"),
        "headline": _first(item, "headline"),
        "description": _first(item, "description"),
        "avatarPath": _first(item, "avatar_path", "avatar_url"),
        "raw": {key: value for key, value in item.items() if key not in sensitive},
    }


def map_oauth_users(raw: Any) -> list[dict[str, Any]]:
    items = raw.get("data", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mapped = map_oauth_user(item)
        mapped["sourceType"] = "oauth_user_relation"
        mapped["url"] = _first(item, "url")
        result.append(mapped)
    return result


def map_moments(raw: Any) -> list[dict[str, Any]]:
    items = raw.get("data", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        target = item.get("target", {}) if isinstance(item.get("target"), dict) else {}
        author = target.get("author", {}) if isinstance(target.get("author"), dict) else {}
        result.append(
            {
                "sourceType": "following",
                "sourceId": str(target.get("id", item.get("id", ""))) or stable_hash(repr(item)),
                "action": item.get("action_text", item.get("action", "")),
                "title": target.get("title", ""),
                "author": author.get("name", ""),
                "summary": target.get("excerpt", target.get("content", "")),
                "publishedAt": unix_to_iso(item.get("action_time", target.get("created_time"))),
                "raw": item,
            }
        )
    return result


def map_ring(raw: Any) -> dict[str, Any]:
    data = raw.get("data", {}) if isinstance(raw, dict) else {}
    info = data.get("ring_info", {}) if isinstance(data, dict) else {}
    contents = data.get("contents", []) if isinstance(data, dict) else []
    items = []
    for item in contents if isinstance(contents, list) else []:
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "sourceType": "ring",
                "sourceId": str(item.get("pin_id", item.get("id", ""))),
                "contentType": "Pin",
                "title": item.get("title") or strip_html(item.get("content", ""))[:40],
                "author": item.get("author_name", ""),
                "summary": strip_html(item.get("content", ""))[:240],
                "fullContent": item.get("content", ""),
                "publishedAt": unix_to_iso(item.get("publish_time")),
                "likeCount": item.get("like_num", 0),
                "commentCount": item.get("comment_num", 0),
                "favoriteCount": item.get("fav_num", 0),
                "shareCount": item.get("share_num", 0),
                "selectedComments": [
                    str(comment.get("content", ""))
                    for comment in (item.get("comments", []) or [])
                    if isinstance(comment, dict) and comment.get("content")
                ],
                "raw": item,
            }
        )
    return {
        "ring": {
            "ringId": str(info.get("ring_id", "")),
            "name": info.get("ring_name", ""),
            "description": info.get("ring_desc", ""),
            "avatarUrl": info.get("ring_avatar", ""),
            "memberCount": info.get("membership_num", 0),
            "discussionCount": info.get("discussion_num", 0),
        },
        "items": items,
        "raw": raw,
    }


def map_comments(raw: Any) -> list[dict[str, Any]]:
    data = raw.get("data", {}) if isinstance(raw, dict) else raw
    items = data.get("comments", []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "sourceType": "comment",
                "sourceId": str(_first(item, "comment_id", "id")),
                "content": _first(item, "content", "Content"),
                "author": _first(item, "author_name", "author"),
                "publishedAt": unix_to_iso(_first(item, "publish_time", "created_at")),
                "likeCount": _first(item, "like_count", default=0),
                "replyCount": _first(item, "reply_count", default=0),
                "raw": item,
            }
        )
    return result


def map_story_list(raw: Any) -> list[dict[str, Any]]:
    data = raw.get("data", []) if isinstance(raw, dict) else raw
    if not isinstance(data, list):
        return []
    return [
        {
            "sourceType": "story",
            "sourceId": str(_first(item, "work_id", "id")),
            "contentType": "Story",
            "title": _first(item, "title"),
            "summary": _first(item, "description", "summary"),
            "thumbnailUrl": _first(item, "artwork", "thumbnail_url"),
            "tags": _first(item, "labels", "tags", default=[]),
            "usageNotice": "Only for this hackathon. Credit the original Zhihu Yan story and author.",
            "raw": item,
        }
        for item in data
        if isinstance(item, dict)
    ]


def map_story_detail(raw: Any) -> dict[str, Any]:
    item = raw.get("data", {}) if isinstance(raw, dict) else raw
    if not isinstance(item, dict):
        item = {}
    chapter = _first(item, "chapter_name", "title")
    author = _first(item, "author_name", "author")
    return {
        "sourceType": "story",
        "sourceId": str(_first(item, "work_id", "id")),
        "contentType": "Story",
        "title": chapter,
        "author": author,
        "summary": _first(item, "introduction", "description", "summary"),
        "fullContent": _first(item, "content", "full_content"),
        "tags": _first(item, "labels", "tags", default=[]),
        "usageNotice": f"改编自知乎盐言故事《{chapter}》，作者：{author}",
        "raw": item,
    }


def map_direct_answer(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"content": "", "raw": raw}
    choice = (raw.get("choices") or [{}])[0]
    message = choice.get("message", {}) if isinstance(choice, dict) else {}
    return {
        "taskId": raw.get("id", ""),
        "model": raw.get("model", ""),
        "content": message.get("content", "") if isinstance(message, dict) else "",
        "reasoningContent": message.get("reasoning_content", "") if isinstance(message, dict) else "",
        "finishReason": choice.get("finish_reason", "") if isinstance(choice, dict) else "",
        "raw": raw,
    }
