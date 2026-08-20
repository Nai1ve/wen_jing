from __future__ import annotations

import html
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .errors import ZhihuError
from .service import ZhihuService


app = FastAPI(title="Wenjing Zhihu Adapter", version="0.1.0")
service = ZhihuService()


def _call(fn):
    try:
        return fn()
    except ZhihuError as error:
        raise HTTPException(status_code=error.status_code, detail=error.as_dict()) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": str(error)}) from error


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "wenjing-zhihu-adapter", "version": "0.1.0"}


@app.get("/zhihu/status")
def status() -> dict[str, Any]:
    return {"ok": True, "data": service.status()}


# ---- Data Platform ------------------------------------------------------------

@app.get("/zhihu/hot-list")
@app.get("/zhihu/data/hot-list")
def hot_list(limit: int = Query(30, ge=1, le=50)) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.hot_list(limit))}


@app.get("/zhihu/zhihu-search")
@app.get("/zhihu/data/search")
def search(query: str = Query(..., min_length=1), count: int = Query(10, ge=1, le=50)) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.search(query, count))}


@app.get("/zhihu/global-search")
@app.get("/zhihu/data/global-search")
def global_search(query: str = Query(..., min_length=1), count: int = Query(10, ge=1, le=50)) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.global_search(query, count))}


@app.post("/zhihu/direct-answer")
@app.post("/zhihu/data/direct-answer")
def direct_answer(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.direct_answer(payload))}


# ---- Community ---------------------------------------------------------------

@app.get("/zhihu/ring-detail")
@app.get("/zhihu/community/ring-detail")
def ring_detail(
    ring_id: str,
    page_num: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.ring_detail(ring_id, page_num, page_size))}


@app.get("/zhihu/comments")
@app.get("/zhihu/community/comments")
def comments(content_type: str, content_token: str) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.comments(content_type, content_token))}


@app.get("/zhihu/story-list")
@app.get("/zhihu/community/story-list")
def story_list() -> dict[str, Any]:
    return {"ok": True, "data": _call(service.story_list)}


@app.get("/zhihu/story-detail")
@app.get("/zhihu/community/story-detail")
def story_detail(work_id: str) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.story_detail(work_id))}


@app.post("/zhihu/publish")
@app.post("/zhihu/publish/mock-or-live")
@app.post("/zhihu/community/publish")
def publish(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.publish_pin(payload))}


@app.post("/zhihu/comment")
@app.post("/zhihu/comment/create")
@app.post("/zhihu/community/comment")
def create_comment(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.create_comment(payload))}


@app.post("/zhihu/reaction")
@app.post("/zhihu/community/reaction")
def reaction(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.reaction(payload))}


# ---- OAuth -------------------------------------------------------------------

@app.get("/zhihu/oauth/authorize")
def oauth_authorize(redirect: bool = False, state: str | None = None) -> Any:
    result = _call(lambda: service.authorize_url(state))
    if redirect:
        return RedirectResponse(result["url"])
    return {"ok": True, "data": result}


@app.get("/zhihu/oauth/callback")
def oauth_callback(
    request: Request,
    code: str | None = None,
    authorization_code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> Any:
    if error:
        message = html.escape(error_description or error)
        if "application/json" in request.headers.get("accept", ""):
            raise HTTPException(status_code=400, detail={"code": "OAUTH_DENIED", "message": message})
        return HTMLResponse(
            f"<h1>知乎授权未完成</h1><p>{message}</p>",
            status_code=400,
        )
    auth_code = code or authorization_code
    if not auth_code:
        raise HTTPException(status_code=400, detail={"code": "OAUTH_CODE_MISSING", "message": "code is required"})
    token = _call(lambda: service.exchange_oauth_code(auth_code, state))
    safe = {
        "ok": True,
        "accessTokenSaved": True,
        "tokenType": token.get("token_type", "Bearer"),
        "expiresIn": token.get("expires_in"),
        "tokenFile": str(service.settings.oauth.token_file),
    }
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(safe)
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'>"
        "<title>问径 · 知乎授权完成</title>"
        "<main style='font-family:system-ui;max-width:620px;margin:64px auto;line-height:1.7'>"
        "<h1>知乎授权完成</h1>"
        "<p>授权令牌已经由本地适配服务保存，浏览器不会显示令牌。</p>"
        f"<p>令牌文件：<code>{html.escape(str(service.settings.oauth.token_file))}</code></p>"
        "<p>现在可以关闭本页，并运行 <code>wenjing-zhihu whoami</code> 验证。</p>"
        "</main>"
    )


@app.get("/zhihu/user")
@app.get("/zhihu/oauth/user")
def oauth_user(access_token: str | None = None) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.oauth_user(access_token))}


@app.get("/zhihu/following-feed")
@app.get("/zhihu/oauth/moments")
def oauth_moments(access_token: str | None = None) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.oauth_moments(access_token))}


@app.get("/zhihu/user-followed")
@app.get("/zhihu/oauth/followed")
def oauth_followed(page: int = 0, per_page: int = 10, access_token: str | None = None) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.oauth_followed(page, per_page, access_token))}


@app.get("/zhihu/user-followers")
@app.get("/zhihu/oauth/followers")
def oauth_followers(page: int = 0, per_page: int = 10, access_token: str | None = None) -> dict[str, Any]:
    return {"ok": True, "data": _call(lambda: service.oauth_followers(page, per_page, access_token))}


@app.get("/zhihu/user-content")
@app.get("/zhihu/oauth/content")
def oauth_content(request: Request, access_token: str | None = None) -> dict[str, Any]:
    params = {key: value for key, value in request.query_params.multi_items() if key != "access_token"}
    return {"ok": True, "data": _call(lambda: service.oauth_content(params, access_token))}


@app.get("/zhihu/user-collections")
@app.get("/zhihu/oauth/collections")
def oauth_collections(request: Request, access_token: str | None = None) -> dict[str, Any]:
    params = {key: value for key, value in request.query_params.multi_items() if key != "access_token"}
    return {"ok": True, "data": _call(lambda: service.oauth_collections(params, access_token))}


@app.get("/zhihu/user-collection/{collection_id}")
@app.get("/zhihu/oauth/collection/{collection_id}")
def oauth_collection(request: Request, collection_id: str, access_token: str | None = None) -> dict[str, Any]:
    params = {key: value for key, value in request.query_params.multi_items() if key != "access_token"}
    return {"ok": True, "data": _call(lambda: service.oauth_collection(collection_id, params, access_token))}


@app.get("/zhihu/oauth/raw")
def oauth_raw(request: Request, path: str, access_token: str | None = None) -> dict[str, Any]:
    params = {
        key: value
        for key, value in request.query_params.multi_items()
        if key not in {"path", "access_token"}
    }
    return {"ok": True, "data": _call(lambda: service.oauth_raw(path, params, access_token))}
