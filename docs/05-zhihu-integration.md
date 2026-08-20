# 知乎开放平台接入与 OAuth 回调

## 已完成的接入边界

`services/zhihu-adapter` 参考 `/Users/liupeize/code/kan_shan_nursery/services/zhihu-adapter` 重建为独立、可运行的适配层，业务层只需要依赖 `ZhihuService` 或 HTTP/CLI 契约。

三类鉴权彼此隔离：

| 表面 | Base URL | 鉴权 | 已接入能力 |
|---|---|---|---|
| Data Platform | `developer.zhihu.com` | `Authorization: Bearer` + `X-Request-Timestamp` | 知乎搜索、全网搜索、热榜、直答 |
| Community | `openapi.zhihu.com` | `X-App-Key`、`X-Timestamp`、`X-Log-Id`、HMAC `X-Sign` | 圈子、评论、故事、发布、评论、点赞 |
| OAuth User Data | `openapi.zhihu.com` | OAuth Bearer access token | 用户、关注动态、关注、粉丝、用户内容、收藏夹、任意 `/user/*` 只读路径 |

OAuth 用户数据的具体路径由环境变量覆盖，避免开放平台文档调整路径时修改业务代码。

## 参考了什么

- 现有工程：`/Users/liupeize/code/kan_shan_nursery/services/zhihu-adapter` 的三客户端拆分、HMAC 签名、错误归一化、OAuth code exchange 和用户数据映射；
- [知乎数据开放平台文档](https://developer.zhihu.com/)，当前文档目录包含搜索、直答、热榜、OAuth、用户内容、关注和收藏相关入口；
- 可选外部 API CLI：[dawnswwwww/zhihu-cli](https://github.com/dawnswwwww/zhihu-cli)。它可以提供 `auth`、`search`、`ask`，但本项目不依赖该二进制，避免 CLI 版本或安装状态阻塞 OAuth 服务；
- 另有基于 Cookie 的阅读型 CLI：[Xiaofan629/zhihu-cli](https://github.com/Xiaofan629/zhihu-cli)。它与开放平台 Access Secret/OAuth 不是同一套凭证，不作为本项目的授权来源。

## 本地启动

```bash
cd /Users/liupeize/Documents/ChatGPT/zhihu/services/zhihu-adapter
cp .env.example .env
# 编辑 .env，填入 OAuth app_id/app_key；live 调用再填 Access Secret 等
set -a
source .env
set +a

uv sync --extra dev
uv run wenjing-zhihu status
```

先用 mock 验证 HTTP 服务：

```bash
uv run wenjing-zhihu data search "联合索引" --count 3
uv run wenjing-zhihu serve --host 127.0.0.1 --port 8787
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/zhihu/status
```

## OAuth 流程

推荐使用一个进程完成授权 URL 生成和回调状态校验：

```bash
uv run wenjing-zhihu oauth serve --host 127.0.0.1 --port 8787
```

终端会打印一次性授权 URL。打开它后，知乎回调到：

```text
https://你的域名/zhihu/oauth/callback?code=...&state=...
```

服务会：

1. 校验 `state`（live 模式强制要求）；
2. 使用 `app_id + app_key + code + redirect_uri` 换取 access token；
3. 将 token 写入 `ZHIHU_TOKEN_FILE` 指定的 JSON 文件；
4. 文件权限尝试设置为 `0600`；
5. 浏览器只显示“授权完成”，不把 token 放在 URL 或 HTML 中。

验证：

```bash
uv run wenjing-zhihu whoami
uv run wenjing-zhihu moments
uv run wenjing-zhihu followed --per-page 10
uv run wenjing-zhihu collections
```

如果开放平台账号的用户内容或收藏路径和默认值不同，覆盖：

```bash
export ZHIHU_OAUTH_CONTENT_PATH=/user/content
export ZHIHU_OAUTH_COLLECTIONS_PATH=/user/collections
export ZHIHU_OAUTH_COLLECTION_PATH='/user/collection/{collection_id}'
```

也可以用安全边界内的通用只读路径：

```bash
uv run wenjing-zhihu oauth get /user/某个已确认的路径 --param page=0
```

## Cloudflare Tunnel

你提到的回调需要公网 HTTPS。建议使用稳定的 Named Tunnel；仓库里有模板 [infra/cloudflared/config.example.yml](../infra/cloudflared/config.example.yml)。

### 稳定域名（推荐）

```bash
cloudflared tunnel create wenjing-zhihu
cloudflared tunnel route dns wenjing-zhihu zhihu-auth.example.com
cloudflared tunnel --config infra/cloudflared/config.yml run wenjing-zhihu
```

本地适配服务仍监听 `127.0.0.1:8787`。然后设置：

```bash
export ZHIHU_OAUTH_REDIRECT_URI=https://zhihu-auth.example.com/zhihu/oauth/callback
```

最后把完全相同的 URL 填入知乎开放平台 OAuth 回调配置。协议、域名、路径和尾部斜杠必须一致。

### 临时 Quick Tunnel

适合短期验证：

```bash
cloudflared tunnel --url http://127.0.0.1:8787
```

它会生成随机的 `trycloudflare.com` 域名。把生成的域名填入 `ZHIHU_OAUTH_REDIRECT_URI` 后，重启适配服务，再把同一 URL 配到知乎；Quick Tunnel 重启后地址可能变化，不适合正式演示。

## 当前还需要你配置的内容

代码不包含任何凭证。你需要在知乎开放平台完成：

1. OAuth 应用的 `app_id`、`app_key`；
2. 公网 HTTPS 回调 URL；
3. 需要的用户数据 Scope（用户、内容、关注、收藏）；
4. Data Platform 的 Access Secret（如果要启用搜索/热榜/直答）；
5. Community 的 app key/secret（如果要启用圈子写操作）。

配置完成后先运行 `wenjing-zhihu status`，确认对应 `configured` 字段，再切换 `ZHIHU_PROVIDER_MODE=live`。

## 安全边界

- 不在前端暴露 `app_secret`、`access_secret` 或 OAuth token；
- 不在日志中打印 token、authorization code 或完整 query value；
- OAuth callback 不在页面中显示 token；
- `oauth raw` 只允许 `/user` 下的只读路径；
- Community 写操作继续受 `ZHIHU_WRITABLE_RING_IDS` 白名单约束；
- Open Platform 的邀测额度、Scope 和响应 schema 仍以当前账号文档为准。
