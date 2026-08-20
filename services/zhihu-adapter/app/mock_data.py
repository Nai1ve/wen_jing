from __future__ import annotations

from typing import Any


def hot_list() -> dict[str, Any]:
    return {
        "Code": 0,
        "Data": {
            "Items": [
                {
                    "Title": "慢查询优化应该先看执行计划吗？",
                    "Url": "https://www.zhihu.com/question/mock-index",
                    "Summary": "从访问模式、执行计划和写入成本讨论索引设计。",
                },
                {
                    "Title": "并发库存问题一定需要分布式锁吗？",
                    "Url": "https://www.zhihu.com/question/mock-lock",
                    "Summary": "比较原子更新、事务、锁和幂等。",
                },
            ]
        },
    }


def search(query: str, count: int = 10) -> dict[str, Any]:
    return {
        "Code": 0,
        "Data": {
            "Items": [
                {
                    "Title": f"{query}：知乎工程观点",
                    "ContentType": "Article",
                    "ContentID": "mock-answer-001",
                    "ContentText": "性能问题应先定位瓶颈，再根据真实查询模式决定索引、缓存或查询改写。",
                    "Url": "https://zhuanlan.zhihu.com/p/mock-answer-001",
                    "AuthorName": "问径演示作者",
                    "VoteUpCount": 128,
                    "CommentCount": 12,
                }
            ][:count]
        },
    }


def direct_answer(model: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-wenjing-mock",
        "model": model,
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "先观察执行计划，再用真实运行结果判断索引是否解决了瓶颈。",
                    "reasoning_content": "把主观判断拆成可验证的学习动作。",
                },
                "finish_reason": "stop",
            }
        ],
    }


def user() -> dict[str, Any]:
    return {"uid": "demo-user", "fullname": "问径演示用户", "headline": "工程学习者"}


def users() -> list[dict[str, Any]]:
    return [{"uid": "demo-author", "fullname": "知乎工程作者", "headline": "数据库与并发"}]


def moments() -> dict[str, Any]:
    return {
        "data": [
            {
                "action_text": "回答了问题",
                "action_time": 1767928220,
                "target": {
                    "title": "索引设计如何考虑真实查询模式",
                    "excerpt": "联合索引服务访问模式，而不是孤立字段。",
                    "author": {"name": "知乎工程作者"},
                },
            }
        ]
    }


def comments() -> dict[str, Any]:
    return {
        "status": 0,
        "msg": "success",
        "data": {
            "comments": [
                {
                    "comment_id": "mock-comment-001",
                    "content": "先看执行计划，再决定是否需要联合索引。",
                    "author_name": "知乎工程作者",
                    "like_count": 12,
                    "reply_count": 2,
                    "publish_time": 1767928220,
                }
            ]
        },
    }


def story_list() -> dict[str, Any]:
    return {
        "status": 0,
        "msg": "success",
        "data": [
            {
                "work_id": "mock-story-001",
                "title": "一条可验证的工程经验",
                "description": "把观点转成实验，再用结果判断。",
                "artwork": "",
                "labels": ["工程", "学习"],
            }
        ],
    }


def story_detail(work_id: str) -> dict[str, Any]:
    return {
        "status": 0,
        "msg": "success",
        "data": {
            "work_id": work_id,
            "chapter_name": "先做实验再下结论",
            "author_name": "问径演示作者",
            "introduction": "工程判断需要可复现实验支撑。",
            "content": "把一个猜想拆成最小实验，记录基线、改动和结果。",
            "labels": ["工程", "学习"],
        },
    }


def ring() -> dict[str, Any]:
    return {
        "status": 0,
        "msg": "success",
        "data": {
            "ring_info": {
                "ring_id": "2029619126742656657",
                "ring_name": "黑客松脑洞补给站",
                "ring_desc": "黑客松讨论圈",
                "membership_num": 100,
                "discussion_num": 42,
            },
            "contents": [],
        },
    }
