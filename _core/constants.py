# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 共享常量模块

定义所有 API 端点 URL 和通用请求头，供搜索、推荐、详情模块共用。
"""

# ── API 端点 ──────────────────────────────────────────────────────────
SEARCH_API: str = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
DETAIL_API: str = "https://www.zhipin.com/wapi/zpgeek/job/detail.json"
GREET_API: str = "https://www.zhipin.com/wapi/zpgeek/friend/add.json"

# ── 通用请求头（搜索/推荐/详情共用）─────────────────────────────���──────
API_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}
