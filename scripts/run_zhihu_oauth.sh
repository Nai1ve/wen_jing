#!/usr/bin/env bash
set -euo pipefail

service_dir="$(cd "$(dirname "$0")/../services/zhihu-adapter" && pwd)"
host="${ZHIHU_OAUTH_HOST:-127.0.0.1}"
port="${ZHIHU_OAUTH_PORT:-8787}"

cd "$service_dir"
uv run wenjing-zhihu oauth serve --host "$host" --port "$port"
